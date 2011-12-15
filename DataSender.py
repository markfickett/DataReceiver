__all__ = [
	'SerialGuard',
	'Send',
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
SHARED_VALUES = {}
with open(SHARED_FILE) as sharedFile:
	for line in sharedFile.readlines():
		if line.startswith('#define'):
			poundDefine, name, value = line.split(' ', 2)
			value = value.strip()
			if name == SERIAL_BAUD_NAME:
				value = int(value)
			SHARED_VALUES[name] = value

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
	readyString = SHARED_VALUES[READY_STRING_NAME].strip('"')
	print 'Waiting for "%s" from Arduino.' % readyString
	text = ''
	quiet = 0
	lastTime = time.time()
	while (readyString not in text) or (quiet < QUIET_DELAY):
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


def Format(**kwargs):
	"""
	Format a dictionary to send over serial to an Arduino which is listening
	with a DataReceiver object.
	"""
	return ''.join(['%s\t%s\n' % (k, v) for k, v in kwargs.iteritems()])

