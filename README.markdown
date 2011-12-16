DataReceiver
============

Arduino library to provide simple sending of key/value pairs from a computer to the Arduino. (For example: I have a CPU usage value on my desktop computer, and want to use an Arduino to control some lights in response to that. This gets the number to from desktop to Arduino.)

To match DataReceiver (the Arduino side) is DataSender in Python. It depends on [pySerial](http://pyserial.sourceforge.net/) for serial communication.

Example
-------

See examples/ for a quick introduction. Even more briefly:

Python:
	with DataSender.SerialGuard('/dev/usb.serialmodemfa141') as s:
		DataSender.WaitForReady(s)
		while True:
			... # generate a value
			s.write(DataSender.Format(KEY=value))
			... # maybe handle responses from the Arduino
Arduino:
	#include <DataReceiver.h>
	DataReceiver<1> receiver; // templated on # keys expected
	void callback(const char* value) {
		... // do something with value
	}
	void setup() {
		receiver.setup(); // Serial.begin
		receiver.sendReady(); // once ready to take Serial input
	}
	void loop() {
		receiver.readAndUpdate(); // read Serial, call callbacks
	}

