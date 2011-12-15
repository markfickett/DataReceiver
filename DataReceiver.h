#pragma once

#include "Shared.h"

#define MAX_KEYS		10
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
 * (See also, the example sketch.)
 */
class DataReceiver {
	private:
		int numListeners;
		struct Listener listeners[MAX_KEYS];

		char readBuffer[READ_BUFFER_SIZE];
		int readIndex;
		int valueIndex;

		void findAndCallCallback(const char* key, const char* value);

	public:
		DataReceiver();

		/**
		 * Initialize Serial. (The baud rate is defined in a header
		 * shared with the Python DataSender.)
		 */
		void setup();

		/**
		 * Once Arduino-side setup is complete, call this to send a
		 * message to the Python-side DataSender, signifying that this
		 * is ready to reaceive input.
		 */
		void sendReady();

		/**
		 * Register a callback. The number of callbacks which can be
		 * registered is determined by the MAX_KEYS symbolic constant.
		 */
		void addKey(const char* key, callbackPtr_t callbackPtr);

		/**
		 * Take input from Serial, parse for key/value pairs, and if
		 * a registered key is found call its callback with the value.
		 */
		void readAndUpdate();
};

