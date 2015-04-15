__all__ = [
  'Sender',
  'DummySender',

  'GetSharedValues',

  'Format',
  'SerialGuard',
  'DummySerialGuard',
  'TimeoutError',
]

try:
  import serial
except ImportError, e:
  print 'Required: pySerial from http://pyserial.sourceforge.net/'
  raise e

import os, time, sys, threading

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


def GetSharedValues(shared_file, type_conversion_map={}):
  """
  Reads #define values from a (C/C++ header) file, facilitating sharing
  those values between C/C++ and Python.

  Limitations: Lines must start with '#define', and spaces must separate
  the '#define' from the name and the name from the value. The value
  continues to the end of the line; it may contain spaces. Name and value
  are stripped of padding whitespace. The exception is that names with no
  value are allowed, and assigned True. (This is unlikely to match parsing
  in C++ in many cases!)

  Args:
    shared_file an open file, supporting readlines(), to a (C/C++
        header) file from which to read
    type_conversion_map optional map of string names to functions which
        will convert their values to other types. For example, if the
        file contains '#define PI 3.14', a map with {'PI': float} will
        result in the returned dict containing {'PI': float('3.14')}
  Returns:
    a dict of {name: value}
  """
  shared_values = {}
  for line in shared_file.readlines():
    if line.startswith('#define'):
      parts = line.split(' ', 2)
      if len(parts) == 2:
        pound_define, name = parts
        value = True
      else:
        pound_define, name, value = parts
        value = value.strip()
      name = name.strip()
      mapper_fn = type_conversion_map.get(name)
      if mapper_fn:
        value = mapper_fn(value)
      shared_values[name] = value
  return shared_values


with open(SHARED_FILE) as shared_file:
  type_conversion_map = {}
  for int_name in INT_VALUE_NAMES:
    type_conversion_map[int_name] = int
  SHARED_VALUES = GetSharedValues(shared_file,
    type_conversion_map=type_conversion_map)

READY_STRING = SHARED_VALUES[READY_STRING_NAME].strip('"')
TIMEOUT_DEFAULT = 0 # non-blocking read

NUMERIC_BYTE_LIMIT = SHARED_VALUES[NUMERIC_BYTE_LIMIT_NAME]
END_OF_KEY = chr(SHARED_VALUES[END_OF_KEY_NAME])
MAX_VALUE_SIZE = SHARED_VALUES[MAX_VALUE_SIZE_NAME]

ACK = chr(SHARED_VALUES[ACK_NAME])
NACK = chr(SHARED_VALUES[NACK_NAME])
ACK_TIMEOUT = 0.5


class SerialGuard:
  """
  A context guard to encapsulate opening (and closing) a USB serial
  connection. This depends on pySerial, and returns the serial
  object opened, which can then be written and read.

  This parses the serial baud from SerialBaud.h, which is
  used also by DataReceiver.
  """
  def __init__(self, serial_device, read_timeout=TIMEOUT_DEFAULT):
    """
    Args:
      serial_device the full path of the serial device to open
      read_timeout a timeout number for reads, passed to the
          serial object; defaults to 0 for non-blocking reads
    """
    self.__serial_device = serial_device
    self.__arduino_serial = None
    self.__timeout = read_timeout

  def __enter__(self):
    serialBaud = SHARED_VALUES[SERIAL_BAUD_NAME]
    self.__arduino_serial = serial.Serial(self.__serial_device,
      serialBaud, timeout=self.__timeout)
    return self.__arduino_serial

  def GetSerial(self):
    return self.__arduino_serial

  def __exit__(self, exc_class, exc_obj, tb):
    if self.__arduino_serial is not None:
      self.__arduino_serial.close()


class DummySerialGuard:
  """
  Match SerialGuard, but print to stdout (or do not print at all).
  """
  def __init__(self, serial_device, read_timeout=TIMEOUT_DEFAULT,
      silent=False):
    self.__sent_ready = False
    self.__silent = silent
  def __enter__(self):
    return self
  def __exit__(self, exc_class, exc_obj, tb):
    pass
  def GetSerial(self):
    return self
  def write(self, s):
    if not self.__silent:
      print s
  def flush(self):
    pass
  def read(self):
    return ACK
  def readline(self):
    if not self.__sent_ready:
      self.__sent_ready = True
      return READY_STRING
    else:
      return ''


def WaitForReady(arduino_serial, quiet_delay=0.5):
  """
  Waits until DataReceiver.sendReady() is called on the Arduino side.
  Waits until the ready string is sent, and nothing more is sent for
  half a second (or quiet_delay).
  """
  print 'Waiting for "%s" from Arduino.' % READY_STRING
  text = ''
  quiet = 0
  last_time = time.time()
  while (READY_STRING not in text) or (quiet < quiet_delay):
    new_text = arduino_serial.readline()
    current_time = time.time()
    if new_text:
      text += new_text
      sys.stdout.write(new_text)
      sys.stdout.flush()
      last_time = current_time
    else:
      quiet = current_time - last_time
  print 'Done waiting.'


def __FormatSingle(key, value):
  """
  Formats a single key/value pair.
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
    raise ValueError((
        'Cannot send %dB value which is greater than %dB maximum: %s')
        % (n, MAX_VALUE_SIZE, value))

  packed_size = ''
  while n > 0:
    r = n % NUMERIC_BYTE_LIMIT
    packed_size = chr(r) + packed_size
    n = n / NUMERIC_BYTE_LIMIT
  return '%s%s%s%s%s' % (key, END_OF_KEY,
    packed_size, chr(NUMERIC_BYTE_LIMIT), value)


def Format(**kwargs):
  """
  Formats a dictionary to send over serial to an Arduino which is listening
  with a DataReceiver object. Data is given as key-value pairs, where
  the keys are specified as arbitrary keyword argument names, and values
  are strings (or any byte sequence).
  """
  return ''.join(
    [__FormatSingle(k, str(v))
    for k, v in kwargs.iteritems()])


class TimeoutError(RuntimeError):
  pass


class _SenderMixin:
  __ACK_BYTES = (ACK, NACK)
  """
  Manage structured (mainly one-way) communication over Serial.
  This class is to extend a SerialGuard class (dummy or real).

  Args:
    start_ready: If True, do not wait for "Ready" from the Arduino before
        sending. Useful for devices such as the Teensey which use emulated
        Serial for communication.
  """
  def __init__(self, start_ready=False):
    self.__ready = bool(start_ready)
    self.__awaited_ack_count = 0
    self.__buffered_output = '' # stored while waiting for acks
    self.__lock = threading.Lock()

  def WaitForReady(self):
    """
    Waits for the Arduino to proclaim itself ready to receive data.
    (If not called explicitly, this is effectively called
    automatically before the first send or read.)
    """
    with self.__lock:
      if not self.__ready:
        self.__WaitForReady()

  def __WaitForReady(self):
    WaitForReady(self.GetSerial())
    self.__ready = True

  def Send(self, **kwargs):
    """
    Formats and sends the given key/value pairs over this Sender's
    Serial. Returns immediately. The Sender will wait for acks before
    doing any further sending, or when doing any other reading.

    This works on the (tenuous) assumption that any synchronous
    response from the Arduino will not contain the acknowledgement
    (or negative ack) bytes.

    Throws:
      TimeoutError if no ack is received after too long while preparing to send.
          Clients may want to catch this if they can resend or safely drop the
          previous message.
    """
    with self.__lock:
      if not self.__ready:
        self.__WaitForReady()
      self.__WaitForAcks()
      self.__awaited_ack_count += len(kwargs)

      self.GetSerial().write(Format(**kwargs))

  def __WaitForAcks(self):
    start_time = time.time()
    while self.__awaited_ack_count > 0:
      c = self.GetSerial().read()
      if not c:
        current_time = time.time()
        if current_time - start_time > ACK_TIMEOUT:
          # TODO Why does this occur? Hang on Arduino side? Serial issue?
          raise TimeoutError(
              'no data for ack for %.2fs ( > %.2fs), aborting'
              % (current_time - start_time, ACK_TIMEOUT))
        continue
      if c in self.__ACK_BYTES:
        self.__awaited_ack_count -= 1
      else:
        self.__buffered_output += c

  def Read(self):
    """
    Reads and return any buffered output. (This may block to wait
    for acks, but will not block for normal output.)

    Throws:
      TimeoutError as with Send.
    """
    with self.__lock:
      if not self.__ready:
        self.__WaitForReady()
      self.__WaitForAcks()
      output = self.__buffered_output
      self.__buffered_output = ''
      more_output = self.GetSerial().readline()
      while more_output:
        output += more_output
        more_output = self.GetSerial().readline()
    return output

  def ReadAndPrint(self):
    sys.stdout.write(self.Read())
    sys.stdout.flush()

class Sender(SerialGuard, _SenderMixin):
  def __init__(
      self,
      serial_device,
      read_timeout=TIMEOUT_DEFAULT,
      start_ready=False):
    SerialGuard.__init__(self, serial_device, read_timeout=read_timeout)
    _SenderMixin.__init__(self, start_ready=start_ready)

class DummySender(DummySerialGuard, _SenderMixin):
  def __init__(self, serial_device, silent=False):
    DummySerialGuard.__init__(self, serial_device, silent=silent)
    _SenderMixin.__init__(self)


