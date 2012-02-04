#!/usr/bin/env python

"""
Demonstrate sending a key/value pair to the Arduino.

Run this on a computer which is connected to an Arduino running echonoumber.pde.

Before running, change the SERIAL_DEVICE to match the device for your Arduino.
This can be found in the Arduino app, under Tools > Serial Port.
"""

SERIAL_DEVICE = '/dev/tty.usbmodemfa141'

import os, sys, time

# Set up the Python path to find DataSender.
sys.path.append(
	os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)),
	os.path.join('..', '..')))
)

import DataSender

if __name__ == '__main__':
	with DataSender.SerialGuard(SERIAL_DEVICE) as arduinoSerial:
		DataSender.WaitForReady(arduinoSerial)

		while True:
			textInput = raw_input('Enter a number: ')
			arduinoSerial.write(DataSender.Format(NUM=textInput))

			time.sleep(0.1)

			line = arduinoSerial.readline()
			while line:
				sys.stdout.write(line)
				sys.stdout.flush()
				line = arduinoSerial.readline()

