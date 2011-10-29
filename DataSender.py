__all__ = [
	'SerialGuard',
	'Send',
]

try:
	import serial
except ImportError, e:
	print 'Required: pySerial from http://pyserial.sourceforge.net/'
	raise e

SERIAL_BAUD_FILE = 'SerialBaud.h'
SERIAL_BAUD_NAME = 'SERIAL_BAUD'
TIMEOUT_DEFAULT = 0 # non-blocking read

class SerialGuard:
	"""
	A context guard to encapsulate opening (and closing) a USB serial
	connection. This depends on pySerial, and returns the serial
	object opened, which can then be written and read.
	
	This parses the serial baud from SerialBaud.h, which is
	used also by DataReceiver.
	"""
	def __init__(self, serialDevice, readTimeout=TIMEOUT_DEFAULT):
		"""
		@param serialDevice the full path of the serial device to open
		@param readTimeout a timeout number for reads, passed to the
			serial object; defaults to 0 for non-blocking reads
		"""
		self.__serialDevice = serialDevice
		self.__arduinoSerial = None
		self.__timeout = readTimeout

	def __enter__(self):
		with open(SERIAL_BAUD_FILE) as baudDefineFile:
			tokens = ''.join(baudDefineFile.readlines()).split()
			nameIndex = tokens.index(SERIAL_BAUD_NAME)
			serialBaud = int(tokens[nameIndex+1])
		self.__arduinoSerial = serial.Serial(SERIAL_DEVICE, serialBaud,
			timeout=self.__timeout)
		return self.__arduinoSerial

	def __exit__(self, excClass, excObj, tb):
		if self.__arduinoSerial is not None:
			self.__arduinoSerial.close()


def Format(**kwargs):
	"""
	Format a dictionary to send over serial to an Arduino which is listening
	with a DataReceiver object.
	"""
	return ''.join(['%s\t%s\n' % (k, v) for k, v in kwargs.iteritems()])


