#pragma once

#include "WProgram.h"
#include "Shared.h"

#define STR_SIZE		20
#define READ_BUFFER_SIZE	255

typedef void(*callbackPtr_t)(const char*);

struct Listener {
	char key[STR_SIZE];
	callbackPtr_t callbackPtr;
};

/**
 * Call callbacks in response to text sent over Serial.
 *
 * Hold an array of string keys paired with callback function pointers.
 * Input (taken from Serial) should be formatted by the Python side DataSender,
 * and/but is simply "Key\tValue\n".
 *
 * The template argument MAX_KEYS determines the size of the listener array.
 *
 * (See also, the example sketch.)
 */
template<size_t MAX_KEYS>
class DataReceiver {
private:
	int numListeners;
	struct Listener listeners[MAX_KEYS];

	char readBuffer[READ_BUFFER_SIZE];
	int readIndex;
	int valueIndex;

	void findAndCallCallback(const char* key, const char* value) {
		for(int i = 0; i < numListeners; i++) {
			if (strcmp(key, listeners[i].key) == 0) {
				(*listeners[i].callbackPtr)(value);
				return;
			}
		}
		Serial.print(
			"Warning: DataReceiver found no handler for key \"");
		Serial.print(key);
		Serial.print("\" (sent with value \"");
		Serial.print(value);
		Serial.println("\", ignoring.");
	}


public:
	DataReceiver() : numListeners(0), readIndex(0), valueIndex(0)
	{ };

	/**
	 * Initialize Serial. (The baud rate is defined in a header
	 * shared with the Python DataSender.)
	 */
	void setup() {
		Serial.begin(SERIAL_BAUD);
	}

	/**
	 * Once Arduino-side setup is complete, call this to send a
	 * message to the Python-side DataSender, signifying that this
	 * is ready to reaceive input.
	 */
	void sendReady() {
		Serial.println(READY_STRING);
	}

	/**
	 * Register a callback. The number of callbacks which can be
	 * registered is determined by the MAX_KEYS template argument.
	 */
	void addKey(const char* key, callbackPtr_t callbackPtr) {
		if (numListeners >= MAX_KEYS) {
			Serial.print("Error: DataReceiver out of space,"
				" cannot register key \"");
			Serial.print(key);
			Serial.println("\".");
			return;
		}
		if (strlen(key) >= STR_SIZE+1) {
			Serial.print("Error: DataReceiver can't handle key \"");
			Serial.print(key);
			Serial.print("\" of length ");
			Serial.print(strlen(key));
			Serial.print(" which won't fit in a size ");
			Serial.print(STR_SIZE);
			Serial.println(" buffer.");
		}
		strcpy(listeners[numListeners].key, key);
		listeners[numListeners].callbackPtr = callbackPtr;
		numListeners++;
	}

	/**
	 * Take input from Serial, parse for key/value pairs, and if
	 * a registered key is found call its callback with the value.
	 */
	void readAndUpdate() {
		while (Serial.available() > 0) {
			int c = Serial.read();
			if (c == '\n' || readIndex+1 >= READ_BUFFER_SIZE) {
				readBuffer[readIndex] = '\0';

				findAndCallCallback(readBuffer,
					readBuffer + valueIndex);

				valueIndex = readIndex = 0;
				//Serial.flush();
				break;
			} else {
				if (c == '\t') {
					valueIndex = readIndex+1;
					c = '\0';
				}
				readBuffer[readIndex] = c;
				readIndex++;
			}
		}
	}
};


