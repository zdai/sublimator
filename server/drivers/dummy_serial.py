
class DummySerial(object):
	def __init__(self,port, echo=True, debug=True):
		self.echo=echo
		self.debug=debug
		self.wbuf=''
		self.rbuf=''

	def flushInput(self):
		self.rbuf=''

	def flushOutput(self):
		self.wbuf=''

	def flush(self):
		self.wbuf=''

	def write(self,dat):
		self.wbuf=dat

	def read(self,cnt):
		if self.echo:
			return self.wbuf
		else:
			return ''


