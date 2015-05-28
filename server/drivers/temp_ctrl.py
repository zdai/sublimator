

import serial,sys,time,random
from drivers.dummy_serial import *


class DummyTcSerial(DummySerial):
	def __init__(self,port,echo,debug):
		super(DummyTcSerial,self).__init__(port,echo,debug)

	def read(self,cnt):
		if self.debug: # generate random number for debugging
			temp=random.random()
			temp*=100
			return str(temp)
		else:
			return ''


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
			self.serial_interface =DummyTcSerial(port,echo,debug)
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
		self.err_code	='ER00'
		self.retry =0
		while (self.err_code != "OK00") and (self.retry < self.max_retry):
			self.cmd = '0103'+reg_addr
			self.serial_interface.write(self.cmd.decode('hex'))
			self._recv_response(reg_addr)
			self.retry+=1

	def _serial_read(self):
		rspn  =self.serial_interface.read(100) #waiting for time out
		return rspn

	def _recv_response(self,reg_addr):
		rspn =self._serial_read()

		self.err_code ='OK00'
		self.rsp_dat  =float(rspn)

	def get_temp_pv(self):
		self._read_register('1000')
		return self.rsp_dat

	def get_temp_sv(self):
		self._read_register('1001')
		return self.rsp_dat
