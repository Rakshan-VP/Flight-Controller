#include <WiFi.h>
#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

// ---------------- WiFi ----------------
const char* ssid = "DRONE_ESP";
const char* password = "12345678";

WiFiServer server(5000);
WiFiClient client;

// ---------------- ANGLE OFFSETS ONLY ----------------
// From your calibration window
const float roll_offset  = 2.65;
const float pitch_offset = -0.05;

// ---------------- Complementary Filter ----------------
float roll = 0.0;
float pitch = 0.0;

const float alpha = 0.98;

const float IMU_FREQ = 250.0;        // 250 Hz
const float TELEMETRY_FREQ = 100.0;  // 100 Hz

unsigned long lastIMU = 0;
unsigned long lastTelemetry = 0;

bool plotting = false;

// ------------------------------------------------------

void setup() {

  Serial.begin(115200);
  Wire.begin(21, 22);

  mpu.initialize();

  WiFi.softAP(ssid, password);
  server.begin();

  lastIMU = micros();
  lastTelemetry = micros();

  Serial.println("ESP32 Ready - Angle Offset Mode");
}

// ------------------------------------------------------

void updateIMU() {

  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax,&ay,&az,&gx,&gy,&gz);

  // ----- Convert to physical units -----
  float imuX = ax / 16384.0;
  float imuY = ay / 16384.0;
  float imuZ = az / 16384.0;

  float gyroX = gx / 131.0;
  float gyroY = gy / 131.0;

  // ----- Axis Remapping -----
  // Drone X = IMU -Y
  // Drone Y = IMU X
  float accX = -imuY;
  float accY =  imuX;
  float accZ =  imuZ;

  float drgyroX = -gyroY;
  float drgyroY =  gyroX;

  float dt = 1.0 / IMU_FREQ;

  float accRoll  = atan2(accY, accZ) * 180.0 / PI;
  float accPitch = atan2(-accX, sqrt(accY*accY + accZ*accZ)) * 180.0 / PI;

  roll  = alpha * (roll  + drgyroX * dt) + (1 - alpha) * accRoll;
  pitch = alpha * (pitch + drgyroY * dt) + (1 - alpha) * accPitch;
}

// ------------------------------------------------------

void sendAngles() {

  // Apply ONLY angle offsets here
  float drone_roll  = roll  - roll_offset;
  float drone_pitch = pitch - pitch_offset;

  client.print(drone_roll);
  client.print(",");
  client.println(drone_pitch);
}

// ------------------------------------------------------

void loop() {

  if (!client || !client.connected()) {
    client = server.available();
    return;
  }

  while (client.available()) {
    String cmd = client.readStringUntil('\n');
    cmd.trim();

    if (cmd == "START") plotting = true;
    if (cmd == "STOP")  plotting = false;
  }

  // 250 Hz IMU update
  if (micros() - lastIMU >= (1000000.0 / IMU_FREQ)) {
    lastIMU += (1000000.0 / IMU_FREQ);
    updateIMU();
  }

  // 100 Hz telemetry
  if (plotting && (micros() - lastTelemetry >= (1000000.0 / TELEMETRY_FREQ))) {
    lastTelemetry += (1000000.0 / TELEMETRY_FREQ);
    sendAngles();
  }
}