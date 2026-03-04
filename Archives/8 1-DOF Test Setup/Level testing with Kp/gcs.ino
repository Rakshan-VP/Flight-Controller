#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

#define CE_PIN 6
#define CSN_PIN 7
RF24 radio(CE_PIN, CSN_PIN);

struct __attribute__((packed)) Telemetry {
  float roll_error;
  float pitch_error;
  int16_t pwm1, pwm2, pwm3, pwm4;
};
Telemetry data;

const byte address[6] = "00001";

void setup() {
  Serial.begin(115200);
  radio.begin();
  radio.openReadingPipe(0, address);
  radio.setPALevel(RF24_PA_MIN);
  radio.startListening();
}

void loop() {
  if (radio.available()) {
    radio.read(&data, sizeof(data));
    Serial.print(data.roll_error); Serial.print(",");
    Serial.print(data.pitch_error); Serial.print(",");
    Serial.print(data.pwm1); Serial.print(",");
    Serial.print(data.pwm2); Serial.print(",");
    Serial.print(data.pwm3); Serial.print(",");
    Serial.println(data.pwm4);
  }
}
