import sys
import threading
import Queue

class ExternalExcThread(threading.Thread):
	def __init__(self,exc_queue):
		threading.Thread.__init__(self)
		if not isinstance(exc_queue, Queue.Queue):
			raise TypeError
		else:
			self.external_exc = exc_queue

	def run_with_exception(self):
		raise NotImplementedError

	def run(self):
		try:
			self.run_with_exception()
		except: # catch all exceptions and pass to main thread
			print("Catch an excepton in {}, throws to main thread".format(self))
			print(sys.exc_info())
			self.external_exc.put(sys.exc_info())


