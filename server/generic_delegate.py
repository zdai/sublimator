import threading
import Queue
import json, os, sys, datetime, traceback

# The cryo-delegate is a daemon-like thread which
# runs in parallel to the web server thread. It queries
# the cryostat periodically, records and manages the log
# of data of the status of the cryostat, and also responds
# to queries about the status of the whole system.
class GenericDelegate(object):
	def __init__(self):
		self.stop_wake_thread = threading.Event()
		self.wakethread = WakeThread(self.stop_wake_thread, self)
		self.wakethread.start()

	# This function is used to call a function on itself based
	# upon a string argument.
	def invoke(self, action, arguments):
		if hasattr(self, action) and hasattr(getattr(self, action), '__call__'):
			try:
				return getattr(self, action)(arguments)
			except: ## process exceptions from sublimator_server
				print ("========exception in sublimator server==========")
				exc=sys.exc_info()
				exc_type, exc_obj, exc_trace = exc
				print self
				print exc_type, exc_obj
				traceback.print_tb(exc_trace)
				print ("*********************************************")
				if not action == 'wake':
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

	# This function is called periodically by a timer thread (e.g. every 30 seconds) via the
	# CryoManagerThread object. It does regular housekeeping things, checks on temperatures
	# and so on.
	def wake(self, args=None):
		pass

	def __del__(self):
		pass


class WakeThread(threading.Thread):
	def __init__(self, event, cryomanager):
		threading.Thread.__init__(self)
		self.cryomanager = cryomanager
		self.stopped = event

	def run(self):
		index = 1
		while not self.stopped.wait(0.25):
			index = index % 60
			self.cryomanager.ask('wake', {})
			index += 1

