import time, sys
import tornado.ioloop
from tornado.web import *
import tornado.websocket
from tornado import httpserver
import inspect
import json, subprocess, os, sys
import threading, Queue
import urllib
import urlparse
import sublimator_server

# Configurable parameters for the server:
# -------------------------------------- #
# PORT: the operating port
PORT 		= 8080
RUN_DATE 	= time.strftime( "%H:%M:%S on %B %d %Y" )
VERSION 	= "0.1"
GIT_HASH	= 0
# -------------------------------------- #


# The JHandler handles WebSocket communication
# with the Javascript on the browser. It answers
# requests and so forth from the browser. Eventually,
# it will behave as a wrapper to another thing that
# will interface with measurement devices.

all_handlers = []

class JHandler(tornado.web.RequestHandler):
	def set_default_headers(self):
		self.set_header("Access-Control-Allow-Origin", '*')

	def prepare(self):
		if self.get_argument('OTI_DATA'):
			self.json_args=json.loads(self.get_argument('OTI_DATA'))
			print (self.json_args)
		else:
			self.json_args=None

	#@asynchronous
	def post(self):
		# The default response: it should be overwritten, or else some
		# kind of internal problem occured.
		response = "Transaction failed to handle: internal assertion failure occurred."

		if self.json_args != None:
			if 'action' in self.json_args:
				arguments = {}
				if 'arguments' in self.json_args:
					arguments = self.json_args['arguments']
				response = actionablerequesthandler.invoke( self.json_args['action'], arguments)
			else:
				response = "Invalid action: no action specified";
		else:
			response = "No arguments provided for OTI autotester"

		self.write(json.dumps(response))

	def on_finish(self):
		pass

# The JActionableRequestHandler class basically completes actions that the browser
# asks of it. It should be spoken to through the "invoke" function, which basically
# searches to see if the actionablerequesthandler can handle that action, and if so,
# does whatever is necessary. You could also return a hash from the actionable
# functions, and then the system will JSON your return value.
class JActionableRequestHandler:
	def invoke(self, action, arguments):
		if hasattr(self, action):
			return getattr(self, action)(arguments)
		else:
			return sublimator.ask(action, arguments)

	# This function tells us some information about the current running version
	# of the server, etc.
	def validate_version(self, arguments):
		return {
			'start_date'	: RUN_DATE,
			'git_hash'		: GIT_HASH,
			'version'		: VERSION
		}

# The global actionablrequesthandler: there is only one instance of this,
# even though there may be many instances of JHandlers for different clients.
# This means we can hog things like serial connections to thermometry devices,
# etc. and not worry about having clashes, etc.
actionablerequesthandler = JActionableRequestHandler()

# This static file handler override class is used
# to force caching to be turned off for all static
# files, which is a debugging measure.
class DebugStaticFileHandler(tornado.web.StaticFileHandler):
	def set_extra_headers(self, path):
		# This is necessary to prevent Chrome from caching everything. Can be safely
		# removed when debugging is over.
		self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

application = tornado.web.Application( [
	(r"/json", JHandler),
	(r"/()",   DebugStaticFileHandler, {'path': '../UI/html/index.html'} ),
	(r"/(.*)", DebugStaticFileHandler, {'path': '../UI/html/'}),
])

sublimator = sublimator_server.SublimatorServer()
def main():
	try:
		application.listen(PORT)
		tornado.ioloop.IOLoop.instance().start()
	except:
		print ("Interrupt due to exception {}".format(sys.exc_info()))
		os._exit(1)

	os._exit(0)

if __name__ ==  "__main__":
	main()

