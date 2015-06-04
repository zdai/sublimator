from drivers.vacuum_reader import *
from drivers.temp_ctrl import *
from exThread import ExternalExcThread
import Queue

class SerialManager(ExternalExcThread):
	def __init__(self,conf,exc_queue):
		try:
			ExternalExcThread.__init__(self,exc_queue)
		except TypeError:
			print ("ExternalExcThread requires a valid external exception queue")
			raise
		else:
			self.config=conf
			self.debug=self.config.getboolean("APP","debug")
			self.vacuum =VacuumReader(self.config.get("Vacuum","port"),1)
			self.tc_cnt	=self.config.getint("Temperature_Controller","nTC")
			self.temp_ctrl =TempController(self.config.get("Temperature_Controller","port"))

			self.mailbox = Queue.Queue()
			self.retbox	 = Queue.Queue()

	def read_vacuum(self,args=None):
		self.mailbox.put({'action':'read-vacuum','arguments':args})
		reading =self.retbox.get()
		self.retbox.task_done()
		return reading

	def read_temp_ctrl(self,args=None):
		self.mailbox.put({'action':'read-tc','arguments':args})
		reading =self.retbox.get()
		self.retbox.task_done()
		return reading

	def run_with_exception(self):
		while True:
			job =self.mailbox.get()
			if not 'action' in job:
				print('No action specified')
			else:
				if job['action'] == 'read-vacuum':
					self._get_vacuum_reading(job['arguments'])
				if job['action'] == 'read-tc':
					self._get_tc_reg(job['arguments'])

			self.mailbox.task_done()

	def _get_vacuum_reading(self,args=None):
		reading =self.vacuum.get_vacuum()
		self.retbox.put(reading)
		raise TypeError

	def _get_tc_reg(self,args=None):
		if not 'dev' in args or not 'reg' in args:
			self.retbox.put(None)
			return

		reading =self.temp_ctrl.read_register(args['dev'],args['reg'])
		self.retbox.put(reading)



