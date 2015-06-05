

import serial,sys,time,random
from drivers.modbus_serial import *

class VacuumOpenError(Exception):
	pass

class VacuumMaxRetryError(Exception):
	pass

class DummyVacuumSerial(ModbusSerial):
	def __init__(self,port,echo,debug):
		super(DummyVacuumSerial,self).__init__(port,echo,debug)

	def read(self,cnt):
		if self.debug:
			prec ='010304'.decode('hex')
			rint =chr(48+random.randint(0,9))
			rdec =chr(48+random.randint(0,9))
			rsig =random.choice('-----')
			rexp =chr(48+random.randint(0,6))
			crc  ='00'
			if self.echo:
				return self.wbuf+prec+rint+rdec+rsig+rexp+crc
			else:
				return prec+rint+rdec+rsig+rexp+crc
		else:
			return ''

class VacuumReader(object):
	def __init__(self,port,timeout,debug=True,echo=True):
		self.debug 		=debug
		try:
			self.serial_interface =serial.Serial(
				port=port,baudrate=9600,timeout=timeout,
				parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,
				bytesize=serial.EIGHTBITS)
			self.dummy=False
		except:
			print("unable to connect to the vacuum reader through port\
			 %s! Err message %s" % (port,sys.exc_info()))
			self.serial_interface =DummyVacuumSerial(port,echo,debug)
			self.dummy=True
			if not self.debug:
				raise VacuumOpenError

		self.echo		=echo
		self.rsp_dat	='0000'
		self.err_code	='ER00'
		self.max_retry  =3
		self.retry  	=0

		if not self.dummy:
			self.serial_interface.flushInput()
			self.serial_interface.flushOutput()
			self.serial_interface.flush()

	def _read_vacuum(self,dev_addr):
		self.err_code	='ER00'
		self.retry =0
		while (self.err_code != "OK00") and (self.retry < self.max_retry):
			self.cmd = dev_addr+'03006B0002'
			self.serial_interface.write(self.cmd.decode('hex'))
			self._recv_response(dev_addr)
			self.retry+=1

		if self.retry == self.max_retry:
			raise VacuumMaxRetryError

		return self._convert_to_decimal(self.rsp_dat)

	def _serial_read(self):
		rspn  =self.serial_interface.read(100) #waiting for time out
		return rspn

	def _recv_response(self,dev_addr):
		self.rsp_dat  ='0000'
		rspn =self._serial_read()

		if self.debug:
			print("return from vacuum " + rspn.encode('hex'))

		if self.echo:
			expected =15
		else:
			expected =9

		if len(rspn) < expected:
			self.err_code ='ERR00'
			return

		self.err_code ='OK00'
		self.rsp_dat  =rspn[expected-6:expected-2]

	def _convert_to_decimal(self,hex_str):
		decimal	=(int(hex_str[0],16)*10) + int(hex_str[1],16)
		temp	=float(decimal)/10.0
		exponent=int(hex_str[3],16)
		if hex_str[2] == '-':
			exponent = -exponent
		return temp*pow(10,exponent)

	def get_vacuum(self):
		vac=self._read_vacuum('01')
		if vac <= 0.1:
			vac=self._read_vacuum('02')

		return vac

