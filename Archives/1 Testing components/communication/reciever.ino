#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// CE = 6, CSN = 7 for Arduino Nano
RF24 radio(6, 7); 
const uint64_t address = 0xF0F0F0F0E1LL;  // Same address as transmitter

void setup() {
  Serial.begin(9600);
  radio.begin();
  radio.openReadingPipe(0, address);  // Use same address
  radio.setPALevel(RF24_PA_MIN);      // Match transmitter power level
  radio.startListening();             // Set as receiver
}

void loop() {
  if (radio.available()) {
    char text[50] = {0};
    radio.read(&text, sizeof(text));
    Serial.print("Received: ");
    Serial.println(text);
  }
}
