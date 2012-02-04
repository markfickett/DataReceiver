#pragma once

#include "WProgram.h"
#include "Shared.h"

// maximum lengths for keys and values
// (for key, excluding \0 termination)
#define MAX_KEY_SIZE		20

/**
 * Callbacks are called with the size of, and a pointer to, a byte buffer
 * containing the value sent. There is always a '\0' after the last otherwise-
 * valid byte in the buffer, for convenience when the value is a string.
 */
typedef void(*callbackPtr_t)(size_t, const char*);

struct Listener {
	char key[MAX_KEY_SIZE+1];
	callbackPtr_t callbackPtr;
};

enum ReadingState {
	READING_KEY,
	READING_NUM,
	READING_VALUE,
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

	enum ReadingState state;
	size_t keyIndex, valueIndex, valueSize;
	char keyBuffer[MAX_KEY_SIZE+1];
	char valueBuffer[MAX_VALUE_SIZE+1];

	void findAndCallCallback(const char* key,
		size_t size, const char* value)
	{
		for(int i = 0; i < numListeners; i++) {
			if (strcmp(key, listeners[i].key) == 0) {
				(*listeners[i].callbackPtr)(size, value);
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

	void processChar(int c) {
		if (state == READING_KEY) {
			if (c == END_OF_KEY) {
				state = READING_NUM;
				valueSize = 0;
				keyBuffer[keyIndex] = '\0';
			} else if (keyIndex >= MAX_KEY_SIZE+1) {
				// Keys are sanitized on add, so error.
				keyBuffer[MAX_KEY_SIZE] = '\0';
				Serial.print("Choking on key which at ");
				Serial.print(keyIndex);
				Serial.print(" chars is invalid: \"");
				Serial.print(keyBuffer);
				Serial.println("\"");
				keyIndex = 0;
			} else {
				keyBuffer[keyIndex++] = c;
			}
		} else if (state == READING_NUM) {
			if (c >= NUMERIC_BYTE_LIMIT) {
				if (valueSize > 0) {
					state = READING_VALUE;
					valueIndex = 0;
				} else {
					valueBuffer[0] = '\0';
					findAndCallCallback(keyBuffer,
						valueSize, valueBuffer);
					state = READING_KEY;
					keyIndex = 0;
				}
			} else {
				valueSize *= NUMERIC_BYTE_LIMIT;
				valueSize += c;
			}
		} else /* state == READING_VALUE */ {
			valueBuffer[valueIndex++] = c;
			if (valueIndex >= valueSize
				|| valueIndex >= MAX_VALUE_SIZE)
			{
				valueBuffer[valueIndex] = '\0';
				findAndCallCallback(keyBuffer,
					valueSize, valueBuffer);
				if (valueSize > MAX_VALUE_SIZE) {
					Serial.print("Value size of ");
					Serial.print(valueSize);
					Serial.print("B was greater than ");
					Serial.print(MAX_VALUE_SIZE);
					Serial.print("B maximum. Will flush.");
					Serial.flush();
				}
				state = READING_KEY;
				keyIndex = 0;
			}
		}
	}


public:
	DataReceiver() : numListeners(0), keyIndex(0), valueIndex(0),
		state(READING_KEY), valueSize(0)
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
		if (strlen(key) > MAX_KEY_SIZE) {
			Serial.print("Error: DataReceiver can't handle key \"");
			Serial.print(key);
			Serial.print("\" of length ");
			Serial.print(strlen(key));
			Serial.print(" which won't fit in a size ");
			Serial.print(MAX_KEY_SIZE+1);
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
			processChar(Serial.read());
		}
	}
};


