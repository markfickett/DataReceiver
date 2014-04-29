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
#define NUMERIC_BYTE_LIMIT 255
#define END_OF_KEY 0
#define MAX_VALUE_SIZE 255
#define ACK_CHAR_VALUE 6
#define NACK_CHAR_VALUE 21
// The value which Python boolean True values are converted to, when sent.
#define TRUE_STRING "True"
