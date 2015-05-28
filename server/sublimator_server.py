from generic_delegate import *
import json
from datetime import datetime, timedelta
import collections
from drivers.vacuum_reader import *
from drivers.temp_ctrl import *

class SublimatorServer(GenericDelegate):
	def __init__(self):
		super(SublimatorServer, self).__init__()
		self.debug=False
		self.vacuum = VacuumReader('/dev/ttyUSB0',1)

		self.tc_cnt	=3 	# number of temperature controller
		self.temp_ctrl=[None for _ in range(self.tc_cnt)]
		for x in range(self.tc_cnt):
			self.temp_ctrl[x] = TempController('/dev/ttyUSB'+str(x),1)

		self.sample_interval=10 # seconds per sample
		self.window_size	=1*3600  # window size in hour
		self.sample_points	=int(self.window_size/self.sample_interval)
		self.elapse 		=collections.deque(maxlen=self.sample_points)
		self.vacuum_record	=collections.deque(maxlen=self.sample_points)
		self.temp_record	=[collections.deque(maxlen=self.sample_points) for _ in range(self.tc_cnt)]

	def get_status(self,args=None):
		dat={
			'label'		:'Test Run',
			'elapse'	:self.elapse[-1].strftime("%H:%M:%S"),
			'temp_pv'	:[34.5,47.5,98.6],
			'temp_sv'	:[66.0,75.0,105.0],
			'temp_pwr'	:[80.0,90.0,95.5],
			'temp_mode'	:['M','A','A'],
			'vacuum'	:(self.vacuum_record[-1])
		}

		return {'errCode':'ERR_OK','logMsg':'Loop back experiment!','data':dat}


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
		self.vacuum_record.append(self.vacuum.get_vacuum())
		for x in range(self.tc_cnt):
			self.temp_record[x].append(self.temp_ctrl[x].get_temp_pv())

