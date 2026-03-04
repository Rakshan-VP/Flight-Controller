#include <Wire.h>
#include <Adafruit_HMC5883_U.h>

Adafruit_HMC5883_Unified mag = Adafruit_HMC5883_Unified(12345);

void setup() {
  Serial.begin(115200);
  while (!Serial);  

  // Use PB3 as SDA and PB10 as SCL
  Wire.setSDA(PB3);
  Wire.setSCL(PB10);
  Wire.begin();

  Serial.println("HMC5883L Magnetometer Test");

  if (!mag.begin()) {
    Serial.println("Failed to detect HMC5883L. Check wiring!");
    while (1);
  }
}

void loop() {
  sensors_event_t event;
  mag.getEvent(&event);

  Serial.print("Mag X: "); Serial.print(event.magnetic.x); Serial.print(" μT, ");
  Serial.print("Y: "); Serial.print(event.magnetic.y); Serial.print(" μT, ");
  Serial.print("Z: "); Serial.print(event.magnetic.z); Serial.println(" μT");

  delay(500);
}
