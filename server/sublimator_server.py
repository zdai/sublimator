from generic_delegate import *
import json
from datetime import datetime, timedelta
import collections
from drivers.vacuum_reader import *
from drivers.temp_ctrl import *
import ConfigParser
from serial_manager import *
import Queue,time

class SublimatorServer(GenericDelegate):
	def __init__(self):
		super(SublimatorServer, self).__init__()
		self.config=ConfigParser.ConfigParser()
		try:
			self.config.read('ini/sublimator.cfg')
		except IOError:
			print("config file failed to open! {}".format(sys.exc_info()))
			raise

		self.serial_exc	=Queue.Queue()
		self.peripherals =SerialManager(self.config,self.serial_exc)
		self.peripherals.start()

		self.debug			=self.config.getboolean("APP","debug")
		self.sample_interval=self.config.getint("Sample_Control","rate")
		self.window_size	=self.config.getint("Sample_Control","window_size")*3600
		self.tc_cnt			=self.config.getint("Temperature_Controller","nTC")
		self.sample_points	=int(self.window_size/self.sample_interval)
		self.elapse 		=collections.deque(maxlen=self.sample_points)
		self.vacuum_record	=collections.deque(maxlen=self.sample_points)
		self.temp_record	=[collections.deque(maxlen=self.sample_points) for _ in range(self.tc_cnt)]

		self.temp_sv		=[0 for _ in range(self.tc_cnt)]
		self.temp_pv		=[0 for _ in range(self.tc_cnt)]
		self.read_tc_sv()


	def read_tc_sv(self):
		for i,tc in enumerate(['01','02','03']):
			args={
				'dev':tc,
				'reg':'1001'
			}
			reading=self.peripherals.read_temp_ctrl(args)
			if reading:
				self.temp_sv[i]=reading/10.0
				if self.debug:
					print ("get temperature sv reading %f" % reading)

	def get_status(self,args=None):
		# check for exception from sub-threads here
		# because this function is called periodically
		# by user interface in the main thread
		self.check_exception()

		elapse_time = ''
		if len(self.elapse):
			elapse_time=self.elapse[-1].strftime("%H:%M:%S")

		vac=0
		if len(self.vacuum_record):
			vac=self.vacuum_record[-1]

		for tc in range(self.tc_cnt):
			if len(self.temp_record[tc]):
				self.temp_pv[tc] = self.temp_record[tc][-1]

		dat={
			'label'		:'Test Run',
			'elapse'	:elapse_time,
			'temp_pv'	:self.temp_pv,
			'temp_sv'	:self.temp_sv,
			'temp_pwr'	:[80.0,90.0,95.5],
			'temp_mode'	:['M','A','A'],
			'vacuum'	:vac
		}

		return {'errCode':'ERR_OK','data':dat}


	def get_chart(self,args=None):
		dat={
			'time'	:self._jsonize_elapse(),
			'temps'	:self._jsonize_temp_record(),
			'vacuum':self._jsonize_vacuum_record()
		}
		return {'errCode':'ERR_OK','logMsg':'Loop back experiment!','data':dat}

	def _jsonize_elapse(self):
		dt_array=[]
		for i,v in enumerate(self.elapse):
			dt_array.append(v.strftime("%H:%M:%S"))
		return dt_array

	def _jsonize_vacuum_record(self):
		vc_array=[]
		for i,v in enumerate(self.vacuum_record):
			vc_array.append(v)
		return vc_array

	def _jsonize_temp_record(self):
		temp_array=[[] for _ in range(self.tc_cnt)]
		for x in range(self.tc_cnt):
			for i,v in enumerate(self.temp_record[x]):
				temp_array[x].append(v)
		return temp_array

	############################################################
	## check if there are exceptions from sub-threads
	## including the serial manager and wake threads
	############################################################
	def check_exception(self):
		try:
			exc=self.serial_exc.get(block=False)
		except Queue.Empty:
			print self.serial_exc
			print "empty"
			pass
		else:
			print ("========exception from sub-threads==========")
			exc_type, exc_obj, exc_trace = exc
			print exc_type
			print exc_obj
			traceback.print_tb(exc_trace)
			print ("*********************************************")
			self.serial_exc.task_done()

			if exc_type == NotAlive:
				print ("========restart serial manager due to previous exception==========")
				self.peripherals =SerialManager(self.config,exc_queue)
				self.peripherals.start()
			else:
				raise exc

	def wake(self,args=None):
		super(SublimatorServer, self).wake(args)
		if len(self.elapse):
			prev_point	=self.elapse[-1]
		else:
			prev_point	=datetime.now()-timedelta(seconds=self.sample_interval)
		seconds = int((datetime.now()-prev_point).total_seconds())

		if seconds >= self.sample_interval:
			self.take_sample()

	def take_sample(self):
		self.elapse.append(datetime.now())
		vac=self.peripherals.read_vacuum()
		if vac:
			self.vacuum_record.append(vac)
			if self.debug:
				print ("get vacuum reading %f" % vac)

		for i,tc in enumerate(['01','02','03']):
			args={
				'dev':tc,
				'reg':'1000'
			}

			reading=self.peripherals.read_temp_ctrl(args)
			if reading:
				self.temp_record[i].append(reading/10.0)
				if self.debug:
					print ("get temperature pv reading %f" % reading)

