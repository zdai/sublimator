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

