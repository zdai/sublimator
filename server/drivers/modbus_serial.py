
from PyCRC.CRC16 import CRC16

class ModbusSerial(object):
	def __init__(self,port, echo=True, debug=True):
		self.port=port
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

	def _check_crc(self, src, tgt):
		check=self._calculate_crc(src)
		if self.debug:
			print("check crc: src=%s tgt=%s, check=%s"
				%(src.encode('hex'),tgt.encode('hex'),
				check.encode('hex')))

		if check != tgt:
			return False
		else:
			return True

	def _calculate_crc(self,src):
		crc16 	=CRC16(modbus_flag=True).calculate(src)
		crc_low	=chr(crc16&0xFF)
		crc_high=chr((crc16>>8)&0xFF)

		return crc_low+crc_high

	def open(self):
		pass

	def close(self):
		pass
