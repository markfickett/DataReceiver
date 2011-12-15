/**
 * Demonstrate sending a key/value pair to the Arduino.
 *
 * Run this sketch on the Arduino, and echonumber.py on the connected computer.
 */

#include <DataReceiver.h>

#define PIN_LED_STATUS	13

DataReceiver receiver;

void numberSentCallback(const char* value) {
	digitalWrite(PIN_LED_STATUS, HIGH);

	float floatValue = atof(value);
	Serial.print("Got number: ");
	Serial.print(floatValue);
	Serial.print(" (parsed from \"");
	Serial.print(value);
	Serial.println("\")");

	digitalWrite(PIN_LED_STATUS, LOW);
}

void setup() {
	receiver.setup();
	receiver.addKey("NUM", &numberSentCallback);
	pinMode(PIN_LED_STATUS, OUTPUT);
	receiver.sendReady();
}

void loop() {
	receiver.readAndUpdate();
}
