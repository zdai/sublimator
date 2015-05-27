from generic_delegate import *
import json
from datetime import datetime

class SublimatorServer(GenericDelegate):
	def __init__(self):
		super(SublimatorServer, self).__init__()
		self.debug=False

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
			'vacuum'	:[1E-5,2E-8]
		}

		return {'errCode':'ERR_OK','logMsg':'Loop back experiment!','data':dat}

