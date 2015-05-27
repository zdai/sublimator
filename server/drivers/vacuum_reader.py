

import serial,sys,time

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
			 %s! Err message %s" % (port,sys.exc_info()))
			self.serial_interface =DummyVacuumReader(port,timeout)
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

	def _read_vacuum(self,dev_addr):
		if self.dummy:
			return 0

		self.err_code	='ER00'
		self.retry =0
		while (self.err_code != "OK00") and (self.retry < self.max_retry):
			self.cmd = dev_addr+'03006B0002'
			self.serial_interface.write(self.cmd.decode('hex'))
			self._recv_response(dev_addr)
			self.retry+=1

		return self.rsp_dat

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

	def _get_decimal(self,hex_str):
		decimal		=(int(hex_str[0],16)*100) + int(hex_str[1],16)
		exponent	=int(hex_str[3],16)
		if hex_str[2] == '-':
			exponent = -exponent
		exponent	=exponent-2
		return decimal * pow(10,exponent)


	def get_vacuum(self):
		vac0=self._read_vacuum('01')
		if self._get_decimal(vac0) < 1E-1:
			return self._read_vacuum('02')
		else:
			return vac0

