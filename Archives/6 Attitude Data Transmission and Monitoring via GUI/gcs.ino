#include <SPI.h>
#include <RF24.h>

#define CE_PIN 6
#define CSN_PIN 7

RF24 radio(CE_PIN, CSN_PIN);
const byte address[6] = "node1";

struct RPY {
  float roll;
  float pitch;
  float yaw;
};

RPY desiredRPY = {0, 0, 0};
RPY currentRPY = {0, 0, 0};

void setup() {
  Serial.begin(9600);
  radio.begin();
  radio.setPALevel(RF24_PA_LOW);
  radio.setDataRate(RF24_1MBPS);
  radio.openWritingPipe(address);
  radio.openReadingPipe(1, address);
  radio.stopListening();
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    int i1 = input.indexOf(',');
    int i2 = input.indexOf(',', i1 + 1);
    if (i1 > 0 && i2 > i1) {
      desiredRPY.roll = input.substring(0, i1).toFloat();
      desiredRPY.pitch = input.substring(i1 + 1, i2).toFloat();
      desiredRPY.yaw = input.substring(i2 + 1).toFloat();

      radio.stopListening();
      radio.write(&desiredRPY, sizeof(desiredRPY));
      delay(5);

      radio.startListening();
      unsigned long t0 = millis();
      while (!radio.available() && millis() - t0 < 50);

      if (radio.available()) {
        radio.read(&currentRPY, sizeof(currentRPY));
        float dr = desiredRPY.roll - currentRPY.roll;
        float dp = desiredRPY.pitch - currentRPY.pitch;
        float dy = desiredRPY.yaw - currentRPY.yaw;
        Serial.print(currentRPY.roll, 2); Serial.print(",");
        Serial.print(currentRPY.pitch, 2); Serial.print(",");
        Serial.print(currentRPY.yaw, 2); Serial.print(",");
        Serial.print(dr, 2); Serial.print(",");
        Serial.print(dp, 2); Serial.print(",");
        Serial.println(dy, 2);
      } else {
        Serial.println("0,0,0,0,0,0");
      }
    }
  }
}
