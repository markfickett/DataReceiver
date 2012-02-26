__all__ = [
	'SerialGuard',
	'DummySerialGuard',
	'GetSharedValues',
	'SendAndWait',
	'Format',
]

try:
	import serial
except ImportError, e:
	print 'Required: pySerial from http://pyserial.sourceforge.net/'
	raise e

import os, time, sys

SHARED_FILE = os.path.join(os.path.dirname(__file__), 'Shared.h')
SERIAL_BAUD_NAME = 'SERIAL_BAUD'
READY_STRING_NAME = 'READY_STRING'
NUMERIC_BYTE_LIMIT_NAME = 'NUMERIC_BYTE_LIMIT'
END_OF_KEY_NAME = 'END_OF_KEY'
MAX_VALUE_SIZE_NAME = 'MAX_VALUE_SIZE'
ACK_NAME = 'ACK_CHAR_VALUE'
NACK_NAME = 'NACK_CHAR_VALUE'
INT_VALUE_NAMES = (
	SERIAL_BAUD_NAME,
	NUMERIC_BYTE_LIMIT_NAME,
	END_OF_KEY_NAME,
	MAX_VALUE_SIZE_NAME,
	ACK_NAME,
	NACK_NAME,
)

def GetSharedValues(sharedFile, typeConversionMap={}):
	"""
	Read #define values from a (C/C++ header) file, facilitating sharing
	those values between C/C++ and Python.

	Limitations: Lines must start with '#define', and spaces must separate
	the '#define' from the name and the name from the value. The value
	continues to the end of the line; it may contain spaces. Name and value
	are stripped of padding whitespace. The exception is that names with no
	value are allowed, and assigned True. (This is unlikely to match parsing
	in C++ in many cases!)

	@param sharedFile an open file, supporting readlines(), to a (C/C++
		header) file from which to read
	@param typeConversionMap optional map of string names to functions which
		will convert their values to other types. For example, if the
		file contains '#define PI 3.14', a map with {'PI': float} will
		result in the returned dict containing {'PI': float('3.14')}
	@return a dict of {name: value}
	"""
	sharedValues = {}
	for line in sharedFile.readlines():
		if line.startswith('#define'):
			parts = line.split(' ', 2)
			if len(parts) == 2:
				poundDefine, name = parts
				value = True
			else:
				poundDefine, name, value = parts
				value = value.strip()
			name = name.strip()
			mapperFn = typeConversionMap.get(name)
			if mapperFn:
				value = mapperFn(value)
			sharedValues[name] = value
	return sharedValues


with open(SHARED_FILE) as sharedFile:
	typeConversionMap = {}
	for intName in INT_VALUE_NAMES:
		typeConversionMap[intName] = int
	SHARED_VALUES = GetSharedValues(sharedFile,
		typeConversionMap=typeConversionMap)

READY_STRING = SHARED_VALUES[READY_STRING_NAME].strip('"')
TIMEOUT_DEFAULT = 0 # non-blocking read

NUMERIC_BYTE_LIMIT = SHARED_VALUES[NUMERIC_BYTE_LIMIT_NAME]
END_OF_KEY = chr(SHARED_VALUES[END_OF_KEY_NAME])
MAX_VALUE_SIZE = SHARED_VALUES[MAX_VALUE_SIZE_NAME]

ACK = chr(SHARED_VALUES[ACK_NAME])
NACK = chr(SHARED_VALUES[NACK_NAME])

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
		serialBaud = SHARED_VALUES[SERIAL_BAUD_NAME]
		self.__arduinoSerial = serial.Serial(self.__serialDevice,
			serialBaud, timeout=self.__timeout)
		return self.__arduinoSerial

	def __exit__(self, excClass, excObj, tb):
		if self.__arduinoSerial is not None:
			self.__arduinoSerial.close()

QUIET_DELAY = 0.5
def WaitForReady(arduinoSerial):
	"""
	Wait until DataReceiver.sendReady() is called on the Arduino side.
	Wait until the ready string is sent, and nothing more is sent for
	half a second.
	"""
	print 'Waiting for "%s" from Arduino.' % READY_STRING
	text = ''
	quiet = 0
	lastTime = time.time()
	while (READY_STRING not in text) or (quiet < QUIET_DELAY):
		newText = arduinoSerial.readline()
		currentTime = time.time()
		if newText:
			text += newText
			sys.stdout.write(newText)
			sys.stdout.flush()
			lastTime = currentTime
		else:
			quiet = currentTime - lastTime
	print 'Done waiting.'


def __FormatSingle(key, value):
	"""
	Format a single key/value pair.
	The format is:
		<key characters>\0<byte count>\xFF<value bytes>
	for example,
		MESG\06\xFFHello!
	or
		LORUM\0\1\1\xFFLorem ipsum... 256 chars ...dolor sit amet.
	In the special case of a zero-length value, the format is trauncated:
		<key characters>\0\xFF
	Note that the byte count is effectively in base 255 (not 256), to allow
	reservation of 0xFF as the number-stop byte value.
	"""
	n = len(value)
	if n == 0:
		return '%s%s%s' % (key, END_OF_KEY, chr(NUMERIC_BYTE_LIMIT))
	elif n > MAX_VALUE_SIZE:
		raise ValueError(('Cannot send %dB value'
			' which is greater than %dB maximum: %s')
			% (n, MAX_VALUE_SIZE, value))

	packedSize = ''
	while n > 0:
		r = n % NUMERIC_BYTE_LIMIT
		packedSize = chr(r) + packedSize
		n = n / NUMERIC_BYTE_LIMIT
	return '%s%s%s%s%s' % (key, END_OF_KEY,
		packedSize, chr(NUMERIC_BYTE_LIMIT), value)


def Format(**kwargs):
	"""
	Format a dictionary to send over serial to an Arduino which is listening
	with a DataReceiver object. Data is given as key-value pairs, where
	the keys are specified as arbitrary keyword argument names, and values
	are strings (or any byte sequence).
	"""
	return ''.join([__FormatSingle(k, v) for k, v in kwargs.iteritems()])


def SendAndWait(arduinoSerial, **kwargs):
	"""
	Format and send the given key/value pairs over the given serial. Wait
	to hear positive or negative acknowledgement for each key. This works
	on the (tenuous) assumption that any synchronous response from the
	Arduino will not contain the acknowledgement (or negative ack) bytes.
	@return any output (or an empty string) which is not the acknowledgement
	"""
	numKeys = len(kwargs)
	numAcks = 0
	arduinoSerial.write(Format(**kwargs))
	output = ''
	while numAcks < numKeys:
		c = arduinoSerial.read()
		if not c:
			continue
		if c in (ACK, NACK):
			numAcks += 1
		else:
			output = output + c
	return output


class DummySerialGuard:
	"""
	Match SerialGuard, but print to stdout (or do not print at all).
	"""
	def __init__(self, serialDevice, readTimeout=TIMEOUT_DEFAULT,
			silent=False):
		self.__sentReady = False
		self.__silent = silent
	def __enter__(self):
		return self
	def __exit__(self, excClass, excObj, tb):
		pass
	def write(self, s):
		if not self.__silent:
			print s
	def flush(self):
		pass
	def readline(self):
		if not self.__sentReady:
			self.__sentReady = True
			return READY_STRING
		else:
			return ''

