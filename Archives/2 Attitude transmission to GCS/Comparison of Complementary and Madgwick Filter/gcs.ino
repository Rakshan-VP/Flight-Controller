#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// ---- nRF24L01 pins ----
#define CE_PIN 6
#define CSN_PIN 7
RF24 radio(CE_PIN, CSN_PIN);

// ---- Telemetry struct (matches sender) ----
struct __attribute__((packed)) Telemetry {
  float roll_cf;
  float pitch_cf;
  float roll_mad;
  float pitch_mad;
};

Telemetry data;

// ---- RF address ----
const byte address[6] = "00001";

// ---- Flag to print header once ----
bool headerPrinted = false;

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

    // --- Print header once ---
    if (!headerPrinted) {
      Serial.println("roll_cf,roll_mad,pitch_cf,pitch_mad");
      headerPrinted = true;
    }

    // --- Print all four values in one line ---
    Serial.print(data.roll_cf); Serial.print(",");
    Serial.print(data.roll_mad); Serial.print(",");
    Serial.print(data.pitch_cf); Serial.print(",");
    Serial.println(data.pitch_mad);
  }
}