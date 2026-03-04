#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

#define CE_PIN PB0
#define CSN_PIN PA4

RF24 radio(CE_PIN, CSN_PIN);
const byte address[6] = "00001";

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
  radio.openReadingPipe(0, address);
  radio.startListening();  // Receiver mode
}

void loop() {
  if (radio.available()) {
    radio.read(&rpy, sizeof(rpy));

    Serial.print("Received: ");
    Serial.print(rpy.roll); Serial.print(", ");
    Serial.print(rpy.pitch); Serial.print(", ");
    Serial.println(rpy.yaw);
  }
}
