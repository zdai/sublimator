import threading
import Queue
import json, os, sys, datetime, traceback
from exThread import ExternalExcThread

# The cryo-delegate is a daemon-like thread which
# runs in parallel to the web server thread. It queries
# the cryostat periodically, records and manages the log
# of data of the status of the cryostat, and also responds
# to queries about the status of the whole system.
class GenericDelegate(object):
	def __init__(self):
		self.stop_wake_thread = threading.Event()
		self.exc_queue = Queue.Queue()
		self.wakethread = WakeThread(self.stop_wake_thread,self,self.exc_queue)
		self.wakethread.start()

	# This function is used to call a function on itself based
	# upon a string argument.
	def invoke(self, action, arguments):
		if hasattr(self, action) and hasattr(getattr(self, action), '__call__'):
			try:
				return getattr(self, action)(arguments)
			except: ## process exceptions from sublimator_server
				print ("========exception from sublimator server==========")
				exc=sys.exc_info()
				exc_type, exc_obj, exc_trace = exc
				print exc_type, exc_obj
				traceback.print_tb(exc_trace)
				print ("*********************************************")
				raise exc
		else:
			return {'errCode':'ERR_00','alert':'Operation not supported!'}

	# I think this function will respond to queries in a queue-like
	# way, but it will also block until they respond. This function
	# should be called from whatever other thread, and should expect
	# a response object of some kind
	def ask(self, action, arguments):
		responder = self.invoke(action,arguments)
		return responder

	def wake(self, args=None):
		pass

	def __del__(self):
		pass


class WakeThread(ExternalExcThread):
	def __init__(self, event, owner,exc_queue):
		try:
			ExternalExcThread.__init__(self,exc_queue)
		except TypeError:
			print ("ExternalExcThread requires a valid external exception queue")
			raise
		self.stopped =event
		self.main_thread =owner

	def run_with_exception(self):
		while not self.stopped.wait(0.5):
			self.main_thread.wake()

