

import serial,sys

class DummyVacuumReader(object):
	def __init__(self,port,timeout):
		pass

class VacuumReader(object):
	def __init__(self,port,timeout,echo=True,debug=True):
		try:
			self.serial_interface =serial.Serial(
				port=port,baudrate=9600,timeout=timeout,
				parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,
				bytesize=serial.EIGHTBITS)
			self.dummy=False
		except:
			print("unable to connect to the vacuum reader through port\
				 %s! Err message %s" % (port,sys.exc_info())
			self.serial_interface =DummyVacuumReader(port,baud,timeout)
			self.dummy=True

		self.debug 		=debug
		self.echo		=echo
		self.dev_addr	='01'
		self.func_code	='03'
		self.reg_addr	='006B'
		self.reg_cnt	='0002'
		self.rsp_dat	=0.0

		if not self.dummy:
			self.serial_interface.flushInput()
			self.serial_interface.flushOutput()
			self.serial_interface.flush()

	def read_vacuum(self):
		if self.dummy:
			return 0

		self.serial_interface.flush()
		time.sleep(0.1) # important! need to wait for the write buffer to be empty
		while (self.err_code != "OK00") and (self.retry < self.max_retry):
			self.cmd = self.dev_addr+self.func_code+self.reg_addr+self.reg_cnt
			self.serial_interface.write(self.cmd_str.decode('hex'))
			self.serial_interface.flush()
			self.recv_response()
			self.retry+=1

		return self.rsp_dat

	def serial_read(self):
		self.serial_interface.flushInput()
		time.sleep(0.1) # need to wait for the write buffer to be empty
		rspn=self.serial_interface.read(1) #waiting for time out
		rspn += self.serial_interface.readline()
		return rspn

	def recv_response(self):
		rspn =self.serial_read()
		if self.echo:
			expected =15
		else:
			expected =9
		if len(rspn) < expected:
			self.err_code ='ERR00'
			return

		dev  =rspn[0].encode('hex')
		func =rspn[1].encode('hex')
		cnt	 =rspn[2].encode('hex')

		if dev!=self.dev_addr or func!=self.func_code or cnt!=self.reg_cnt:
			self.err_code ='ERR01'
			return

		self.err_code ='OK00'
		decimal		=(int(rspn[expected-6],16)*100) + int(rspn[expected-5],16)
		exponent	=int(rspn[expected-3],16)
		if rspn[expected-4] == '-':
			exponent = -exponent
		exponent	=exponent-2
		self.rsp_dat  =pow(decimal,exponent)
