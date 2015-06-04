

import serial,sys,time,random
from drivers.modbus_serial import *
from PyCRC.CRC16 import CRC16

class DummyTcSerial(ModbusSerial):
	def __init__(self,port,echo,debug):
		super(DummyTcSerial,self).__init__(port,echo,debug)

	def read(self,cnt):
		if self.debug: # generate random number for debugging
			prec 	='010302'.decode('hex')
			high	=chr(random.randint(0,9))
		 	low		=chr(random.randint(0,255))
			crc		=self._calculate_crc(prec+high+low)

			if self.echo:
				return self.wbuf+prec+high+low+crc
			else:
				return prec+high+low+crc
		else:
			return 0.0

class TempController(object):
	def __init__(self,port,baud=9600,timeout=1,echo=True,debug=True):
		try:
			self.serial_interface =serial.Serial(
				port=port,baudrate=baud,timeout=timeout,
				parity=serial.PARITY_EVEN,stopbits=serial.STOPBITS_ONE,
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

	def _read_register(self,dev_addr,reg_addr):
		self.err_code	='ER00'
		self.retry =0
		while (self.err_code != "OK00") and (self.retry < self.max_retry):
			self.cmd = (dev_addr+'03'+reg_addr+'0001').decode('hex')
			crc=self._calculate_crc(self.cmd)
			self.cmd=self.cmd+crc
			self.serial_interface.write(self.cmd)
			self._recv_response(dev_addr,reg_addr)
			self.retry+=1

	def _serial_read(self):
		rspn=''
		try:
			rspn  =self.serial_interface.read(100) #waiting for time out
		except:
			print(self.serial_interface)
			print(sys.exc_info())
			rspn = ''
		return rspn

	def _recv_response(self,dev_arr,reg_addr):
		self.rsp_dat  =0.0
		rspn =self._serial_read()

		if self.echo:
			expected =15
		else:
			expected =7

		if len(rspn) < expected:
			self.err_code ='ERR00'
			print("TC %s reg %s ERR00: rspn('%s') is shorter than expected"%(dev_addr,reg_addr,rspn.encode('hex')))
			return

		if not self._check_crc(rspn[expected-7:expected-2],rspn[expected-2:]):
			self.err_code ='ERR01'
			print("TC %s reg %s ERR01: CRC check failed! rspn=%s" %(dev_addr,reg_addr,rspn.encode('hex')))
			return

		self.err_code ='OK00'
		self.rsp_dat  =int(rspn[expected-4:expected-2].encode('hex'),16)

	def read_register(self,dev,reg):
		self._read_register(dev,reg)
		return self.rsp_dat

	def _check_crc(self, src, tgt):
		check=self._calculate_crc(src)

		if check != tgt:
			return False
		else:
			return True

	def _calculate_crc(self,src):
		crc16 	=CRC16(modbus_flag=True).calculate(src)
		crc_low	=chr(crc16&0xFF)
		crc_high=chr((crc16>>8)&0xFF)

		return crc_low+crc_high

