#!/usr/bin/env python

"""
Demonstrate sending a key/value pair to the Arduino.

Run this Python script on a computer which is connected to an Arduino running
echonoumber.pde.

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
	sender = DataSender.Sender(SERIAL_DEVICE)
	with sender:

		# Calling waitForReady explicitly is optional, but keeps the
		# first user interaction snappy.
		sender.waitForReady()

		while True:
			textInput = raw_input('Enter a number: ')
			sender.send(NUM=textInput)

			sender.readAndPrint()

