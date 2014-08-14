#pragma once

/**
 * Values shared with the Python DataSender.
 */

// define SERIAL_BAUD 4800
// define SERIAL_BAUD 9600
// define SERIAL_BAUD 14400
// define SERIAL_BAUD 19200
// define SERIAL_BAUD 28800
// define SERIAL_BAUD 38400
// define SERIAL_BAUD 57600
#define SERIAL_BAUD 115200

#define READY_STRING "Ready."
// The exclusive upper bound for data byte values, leaving room for special
// values (specifically, the end-of-value byte).
#define NUMERIC_BYTE_LIMIT 255
#define END_OF_KEY 0
// Arbitrary limit on number of bytes in a transmitted value. Used for buffer
// allocation on the Arduino.
#define MAX_VALUE_SIZE 512
#define ACK_CHAR_VALUE 6
#define NACK_CHAR_VALUE 21
// The value which Python boolean True values are converted to, when sent.
#define TRUE_STRING "True"
