#include <WiFi.h>
#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

// -------- Motor Pins --------
#define M1 25
#define M2 26
#define M3 32
#define M4 33

// -------- WiFi --------
const char* ssid     = "DRONE_ESP";
const char* password = "12345678";

WiFiServer server(5000);
WiFiClient client;

// -------- Angle Offsets --------
const float roll_offset  =  2.65;
const float pitch_offset = -0.05;

// -------- Complementary Filter --------
float roll  = 0.0;
float pitch = 0.0;
const float alpha = 0.98;

const float IMU_FREQ       = 250.0;
const float TELEMETRY_FREQ = 100.0;

unsigned long lastIMU       = 0;
unsigned long lastTelemetry = 0;

// -------- Raw IMU --------
float rawAccX=0, rawAccY=0, rawAccZ=0;
float rawGyroX=0, rawGyroY=0, rawGyroZ=0;

// -------- Drone Frame --------
float droneAccX=0,  droneAccY=0,  droneAccZ=0;
float droneGyroX=0, droneGyroY=0, droneGyroZ=0;

// -------- PID --------
float Kp=0, Ki=0, Kd=0;
float basePWM = 1100;

float error=0, prevError=0;
float integral=0;

float roll_setpoint  = 0;
float pitch_setpoint = 0;

bool rollMode    = false;
bool pitchMode   = false;
bool testRunning = false;

// -------- Motor State --------
float m1_pwm=1000, m2_pwm=1000, m3_pwm=1000, m4_pwm=1000;

// -------- PWM --------
#define PWM_FREQ 400
#define PWM_RES  16

void setupPWM() {
  ledcAttach(M1, PWM_FREQ, PWM_RES);
  ledcAttach(M2, PWM_FREQ, PWM_RES);
  ledcAttach(M3, PWM_FREQ, PWM_RES);
  ledcAttach(M4, PWM_FREQ, PWM_RES);
}

void setMotor(int pin, float pwm_us) {
  pwm_us = constrain(pwm_us, 1000, 2000);
  uint32_t duty = (pwm_us / 20000.0) * ((1 << PWM_RES) - 1);
  ledcWrite(pin, duty);

  if (pin == M1) m1_pwm = pwm_us;
  if (pin == M2) m2_pwm = pwm_us;
  if (pin == M3) m3_pwm = pwm_us;
  if (pin == M4) m4_pwm = pwm_us;
}

void stopMotors() {
  setMotor(M1, 1000);
  setMotor(M2, 1000);
  setMotor(M3, 1000);
  setMotor(M4, 1000);
}

// -------- IMU --------
void updateIMU() {

  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  rawAccX  = ax / 16384.0;
  rawAccY  = ay / 16384.0;
  rawAccZ  = az / 16384.0;

  rawGyroX = gx / 131.0;
  rawGyroY = gy / 131.0;
  rawGyroZ = gz / 131.0;

  droneAccX  = -rawAccY;
  droneAccY  =  rawAccX;
  droneAccZ  =  rawAccZ;

  droneGyroX = -rawGyroY;
  droneGyroY =  rawGyroX;
  droneGyroZ =  rawGyroZ;

  float dt = 1.0 / IMU_FREQ;

  float accRoll  = atan2(droneAccY, droneAccZ) * 180.0 / PI;
  float accPitch = atan2(-droneAccX, sqrt(droneAccY * droneAccY + droneAccZ * droneAccZ)) * 180.0 / PI;

  roll  = alpha * (roll  + droneGyroX * dt) + (1 - alpha) * accRoll;
  pitch = alpha * (pitch + droneGyroY * dt) + (1 - alpha) * accPitch;
}

// -------- PID --------
float computePID(float measured) {

  float dt = 1.0 / IMU_FREQ;
  float sp  = rollMode ? roll_setpoint : pitch_setpoint;

  error = sp - measured;

  integral += error * dt;
  integral = constrain(integral, -200, 200);

  float derivative;
  if (rollMode)
    derivative = -droneGyroX;
  else
    derivative = -droneGyroY;

  return Kp * error + Ki * integral + Kd * derivative;
}

// -------- Motor Mixing --------
void applyMotor(float pidOut) {

  if (rollMode) {
    float right = basePWM - pidOut;
    float left  = basePWM + pidOut;

    setMotor(M1, right);
    setMotor(M2, right);
    setMotor(M3, left);
    setMotor(M4, left);
  }

  if (pitchMode) {
    float front = basePWM - pidOut;
    float back  = basePWM + pidOut;

    setMotor(M1, front);
    setMotor(M3, front);
    setMotor(M2, back);
    setMotor(M4, back);
  }
}

// -------- Setup --------
void setup() {

  Serial.begin(115200);
  Wire.begin(21, 22);
  mpu.initialize();
  mpu.setDLPFMode(MPU6050_DLPF_BW_20);
  mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_500);
  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_4);
  setupPWM();

  WiFi.softAP(ssid, password);
  server.begin();

  lastIMU       = micros();
  lastTelemetry = micros();
}

// -------- Loop --------
void loop() {

  // Accept new client if not connected
  if (!client || !client.connected()) {
    client = server.available();
    return;
  }

  // -------- Command Parsing --------
  while (client.available()) {
    String cmd = client.readStringUntil('\n');
    cmd.trim();

    // --- SET_ROLL: sets PID gains, base PWM, and initial setpoint ---
    if (cmd.startsWith("SET_ROLL")) {
      sscanf(cmd.c_str(), "SET_ROLL,%f,%f,%f,%f,%f",
             &Kp, &Ki, &Kd, &basePWM, &roll_setpoint);
      rollMode  = true;
      pitchMode = false;
    }

    // --- SET_PITCH: sets PID gains, base PWM, and initial setpoint ---
    if (cmd.startsWith("SET_PITCH")) {
      sscanf(cmd.c_str(), "SET_PITCH,%f,%f,%f,%f,%f",
             &Kp, &Ki, &Kd, &basePWM, &pitch_setpoint);
      pitchMode = true;
      rollMode  = false;
    }

    if (cmd.startsWith("SET_REF")) {
      float new_ref = 0;
      sscanf(cmd.c_str(), "SET_REF,%f", &new_ref);
      if (rollMode)  roll_setpoint  = new_ref;
      if (pitchMode) pitch_setpoint = new_ref;
    }

    if (cmd == "START_ROLL" || cmd == "START_PITCH") {
      testRunning = true;
      integral    = 0;
      prevError   = 0;
    }

    if (cmd == "STOP") {
      testRunning = false;
      rollMode    = false;
      pitchMode   = false;
      stopMotors();
    }
  }

  // -------- IMU + PID loop at IMU_FREQ --------
  if (micros() - lastIMU >= (1000000.0 / IMU_FREQ)) {
    lastIMU += (1000000.0 / IMU_FREQ);
    updateIMU();

    if (testRunning) {
      float measured = rollMode ? (roll  - roll_offset)
                                : (pitch - pitch_offset);
      float pidOut = computePID(measured);
      applyMotor(pidOut);
    }
  }

  // -------- Telemetry at TELEMETRY_FREQ --------
  if (micros() - lastTelemetry >= (1000000.0 / TELEMETRY_FREQ)) {
    lastTelemetry += (1000000.0 / TELEMETRY_FREQ);

    char buf[256];
    snprintf(buf, sizeof(buf),
      "%.3f,%.3f,%.3f,%.3f,%.1f,%.1f,%.1f,%.1f\n",
      roll,  pitch,
      roll_setpoint,  pitch_setpoint,
      m1_pwm, m2_pwm, m3_pwm, m4_pwm
    );

    client.print(buf);
  }
}
