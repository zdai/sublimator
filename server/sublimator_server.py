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

		self.temp_ctrl=[None for _ in range(3)]
		for x in range(3):
			self.temp_ctrl[x] = TempController('/dev/ttyUSB1',1)

		self.sample_interval=10 # seconds per sample
		self.window_size	=3  # window size in hour
		self.sample_points	=3600/self.sample_interval*self.window_size
		self.elapse 		=collections.deque(maxlen=self.sample_points)
		self.vacuum_record	=collections.deque(maxlen=self.sample_points)
		self.temp_record	=[collections.deque(maxlen=self.sample_points) for _ in range(3)]

	# This function is called every few seconds, to perform any routine action.
	def wake(self, args=None):
		super(SublimatorServer, self).wake(args)

	def get_status(self,args=None):
		dat={
			'label'		:'Test Run',
			'elapse'	:7350,
			'temp_pv'	:[34.5,47.5,98.6],
			'temp_sv'	:[66.0,75.0,105.0],
			'temp_pwr'	:[80.0,90.0,95.5],
			'temp_mode'	:['M','A','A'],
			'vacuum'	:self.vacuum.get_vacuum()
		}

		return {'errCode':'ERR_OK','logMsg':'Loop back experiment!','data':dat}


	def get_chart(self,args=None):

		dat={
			'time'	:self.elapse,
			'vacuum':self.vacuum_record,
			'temp'	:self.temp_record
		}

	def wake(self,args=None):
		if len(self.elapse):
			prev_point	=self.elapse[-1]
		else:
			prev_point	=datetime.now()-timedelta(seconds=self.sample_interval)
		seconds = int((datetime.now()-prev_point).total_seconds())

		if seconds >= self.sample_interval:
			#self.take_sample()
			pass

	def take_sample(self):
		self.elapse.append(datatime.now())
		self.vacuum_record.append(self.vacuum.get_vacuum())
		for x in range(3):
			self.temp_record[x].append(self.temp_ctrl[x].get_temp_pv())

