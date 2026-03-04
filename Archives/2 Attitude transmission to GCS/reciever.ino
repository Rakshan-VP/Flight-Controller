#include <SPI.h>
#include <RF24.h>

#define CE_PIN 6
#define CSN_PIN 7

RF24 radio(CE_PIN, CSN_PIN);
const byte address[6] = "node1";

struct RPYData {
  float roll;
  float pitch;
  float yaw;
};

void setup() {
  Serial.begin(115200);
  radio.begin();
  radio.openReadingPipe(0, address);
  radio.setPALevel(RF24_PA_LOW);
  radio.startListening();
}

void loop() {
  if (radio.available()) {
    RPYData receivedData;
    radio.read(&receivedData, sizeof(receivedData));

    Serial.print("Roll: ");
    Serial.print(receivedData.roll);
    Serial.print(", Pitch: ");
    Serial.print(receivedData.pitch);
    Serial.print(", Yaw: ");
    Serial.println(receivedData.yaw);
  }
}
