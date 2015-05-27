

import serial,sys,time

class DummyTempController(object):
	def __init__(self,port,timeout):
		pass

class TempController(object):
	def __init__(self,port,baud=9600,timeout=1,echo=True,debug=True):
		try:
			self.serial_interface =serial.Serial(
				port=port,baudrate=baud,timeout=timeout,
				parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,
				bytesize=serial.EIGHTBITS)
			self.dummy=False
		except:
			print("unable to connect to the temperature controller through port\
			 %s! Err message %s" % (port,sys.exc_info()))
			self.serial_interface =DummyTempController(port,timeout)
			self.dummy=True

		self.debug 		=debug
		self.echo		=echo
		self.rsp_dat	=0.0
		self.err_code	='ER00'
		self.max_retry  =3
		self.retry  	=0

		if not self.dummy:
			self.serial_interface.flushInput()
			self.serial_interface.flushOutput()
			self.serial_interface.flush()

	def _read_register(self,reg_addr):
		if self.dummy:
			return 0

		self.err_code	='ER00'
		self.retry =0
		while (self.err_code != "OK00") and (self.retry < self.max_retry):
			self.cmd = '0103'+reg_addr
			self.serial_interface.write(self.cmd.decode('hex'))
			self._recv_response(dev_addr)
			self.retry+=1

	def _serial_read(self):
		rspn  =self.serial_interface.read(100) #waiting for time out
		return rspn

	def _recv_response(self,dev_addr):
		rspn =self._serial_read()
		if self.echo:
			expected =15
		else:
			expected =9
		if len(rspn) < expected:
			self.err_code ='ERR00'
			return

		dev  =rspn[expected-9].encode('hex')
		func =rspn[expected-8].encode('hex')
		if dev!=dev_addr or func!='03':
			self.err_code ='ERR01'
			return

		self.err_code ='OK00'
		self.rsp_dat  =rspn[expected-6:expected-2]

	def get_temp_pv(self):
		self._read_register('1000')
		return self.rsp_dat

	def get_temp_sv(self):
		self._read_register('1001')
		return self.rsp_dat