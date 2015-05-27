import threading
import Queue
import sqlite3, json, os, sys, numpy, datetime
#from StringIO import StringIO

database_connection = None

lib_path = os.path.abspath('./lib/peripherals')
sys.path.append(lib_path)
lib_path = os.path.abspath('./lib/operations')
sys.path.append(lib_path)

# The cryo-delegate is a daemon-like thread which
# runs in parallel to the web server thread. It queries
# the cryostat periodically, records and manages the log
# of data of the status of the cryostat, and also responds
# to queries about the status of the whole system.
class GenericDelegate(object):
	def __init__(self):
		self.thread 	= ManagerThread(self)
		self.operations 		= [ ]
		# Now, start the object which provokes the cryomanager every 30 seconds
		# via its "wake" method.
		self.stop_wake_thread = threading.Event()
		self.wakethread = WakeThread(self.stop_wake_thread, self)
		self.wakethread.start()

	# This function is used to call a function on itself based
	# upon a string argument.
	def invoke(self, action, arguments):
		if hasattr(self, action) and hasattr(getattr(self, action), '__call__'):
			try:
				return getattr(self, action)(arguments)

			except MemoryError as e:
				print ("exception: %s (AutotesterDelegate:%s)" % (e, action, arguments))
		else:
			error = {"error": "Invalid action: the requested action '%s' is not implemented." % action}
			print (error)
			return error

	# This function starts the thread, and lets the cryomanager loose.
	def start(self):
		self.thread.start()

	def print_log(self, log):
		print (log)

	def thread_initialize(self, database_file='data/database.db'):
		pass


	def __del__(self):
		pass

	# I think this function will respond to queries in a queue-like
	# way, but it will also block until they respond. This function
	# should be called from whatever other thread, and should expect
	# a response object of some kind
	def ask(self, action, arguments):
		# The responder object will be edited by the thread.
		responder = {}
		# Now we put the request into the mailbox of the thread...
		message = { "action": action, "arguments":arguments, "responder": responder}
		self.thread.mailbox.put(message)
		# Wait for the queue to be completed.
		self.thread.mailbox.join()
		# Return the responder object.
		return responder



	# This function is called periodically by a timer thread (e.g. every 30 seconds) via the
	# CryoManagerThread object. It does regular housekeeping things, checks on temperatures
	# and so on.
	def wake(self, args=None):
		pass

class ManagerThread(threading.Thread):
	def __init__(self, parent):
		threading.Thread.__init__(self)
		self.parent = parent
		self.mailbox = Queue.Queue()

	def run(self):
		while True:
			data = self.mailbox.get()
			# The data received via this mailbox must be formatted in a specific way,
			# including an action, arguments, and a responder hash.
			assert "responder" in data, "Thread ask has no responder object! I can't respond to it."
			try:
				assert "action" in data, "Thread ask has no action! I don't know what to do with it."
				response = self.parent.invoke( data['action'], data['arguments'])
				# Copy the response data into the responder object, which
				# we received by reference. That way the other thread can
				# read it when we are done with the queue.
				if response != None and hasattr(response, '__iter__'):
					for k,v in response.iteritems():
						data['responder'][k] = v
				# Mark the task as done (free up the queue).
			except Exception:
				print ("Error: invalid command sent to delegate.{}".format(data))
				data['responder']['error'] = { "error": "invalid command" }
				raise
			self.mailbox.task_done()

class WakeThread(threading.Thread):
	def __init__(self, event, cryomanager):
		threading.Thread.__init__(self)
		self.cryomanager = cryomanager
		# Connect to the SQLite database.
		self.stopped = event

	def run(self):
		self.cryomanager.ask('thread_initialize',{})
		index = 1
		while not self.stopped.wait(0.25):
			index = index % 60
			# Poll all sensors every 20 seconds.
			self.cryomanager.ask('wake', {})
			index += 1

