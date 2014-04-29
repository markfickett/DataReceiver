#!/usr/bin/env python

"""
Demonstrate sending a key/value pair to the Arduino.

Run this Python script on a computer which is connected to an Arduino running
echonoumber.pde.

Before running, change the SERIAL_DEVICE to match the device for your Arduino.
This can be found in the Arduino app, under Tools > Serial Port.
"""

SERIAL_DEVICE = '/dev/tty.usbmodem12341'

import os, sys, time

# Set up the Python path to find DataSender.
sys.path.append(
	os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)),
	os.path.join('..', '..')))
)

import DataSender

if __name__ == '__main__':
	# With USB communication (Teensey), pass readTimeout=0.05, startReady=True.
	# This is necessary because timeout=0 (normally non-blocking) does actually
	# block, and pyserial does not reset the microcontroller when it connects.
	sender = DataSender.Sender(SERIAL_DEVICE)
	with sender:

		# Calling waitForReady explicitly is optional, but keeps the first user
		# interaction snappy. It also provides the option to explicitly reset the
		# microcontroller program.
		sender.waitForReady()

		while True:
			textInput = raw_input('Enter a number: ')
			sender.send(NUM=textInput)

			sender.readAndPrint()

