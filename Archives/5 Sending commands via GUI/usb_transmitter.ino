#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

#define CE_PIN 6
#define CSN_PIN 7

RF24 radio(CE_PIN, CSN_PIN);
const byte address[6] = "00001";

// Define struct to send RPY values
struct RPY {
  int16_t roll;
  int16_t pitch;
  int16_t yaw;
};

RPY rpy;

void setup() {
  Serial.begin(9600);
  radio.begin();
  radio.setPALevel(RF24_PA_LOW);
  radio.setDataRate(RF24_1MBPS);
  radio.openWritingPipe(address);
  radio.stopListening();  // Transmitter mode
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    int c1 = data.indexOf(',');
    int c2 = data.lastIndexOf(',');

    if (c1 > 0 && c2 > c1) {
      rpy.roll = data.substring(0, c1).toInt();
      rpy.pitch = data.substring(c1 + 1, c2).toInt();
      rpy.yaw = data.substring(c2 + 1).toInt();

      radio.write(&rpy, sizeof(rpy));
    }
  }
}
