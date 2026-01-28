#include <Wire.h>

const int motorPins[4]     = {25, 26, 32, 33};
const int motorChannels[4] = {0, 1, 2, 3};

const int pwmFreq = 50;
const int pwmResolution = 16;

#define MPU_ADDR 0x68

const float baseThrottle = 1300.0;
const float minThrottle  = 1170.0;
const float maxThrottle  = 1430.0;

float Kp = 15.0;
float Ki = 0.05;
float Kd = 0.7;

const float alpha = 0.98;

float roll = 0.0;
float pidI = 0.0;
float lastError = 0.0;
unsigned long lastTime;

float leftPWM  = 1200.0;
float rightPWM = 1200.0;

uint32_t usToDuty(uint32_t us) {
  return (uint32_t)((us * 65535UL) / 20000UL);
}

void setMotor(int ch, float us) {
  us = constrain(us, minThrottle, maxThrottle);
  ledcWrite(ch, usToDuty((uint32_t)us));
}

void writeMotors(float left, float right) {
  leftPWM  = left;
  rightPWM = right;

  setMotor(0, left);
  setMotor(1, right);
  setMotor(2, right);
  setMotor(3, left);
}

void readMPU(float &accRoll, float &gyroRate) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);

  int16_t ax = Wire.read() << 8 | Wire.read();
  int16_t ay = Wire.read() << 8 | Wire.read();
  int16_t az = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read();
  int16_t gx = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read();
  Wire.read(); Wire.read();

  accRoll = atan2(ay, az) * 180.0 / PI;
  gyroRate = gx / 131.0;
}

void setup() {
  Serial.begin(115200);

  Wire.begin(21, 22);
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission();

  for (int i = 0; i < 4; i++) {
    ledcSetup(motorChannels[i], pwmFreq, pwmResolution);
    ledcAttachPin(motorPins[i], motorChannels[i]);
    ledcWrite(motorChannels[i], usToDuty(1000));
  }

  delay(4000);
  lastTime = micros();

  Serial.println("time_us,roll_deg,left_pwm_us,right_pwm_us");
}

void loop() {
  float accRoll, gyroRate;
  readMPU(accRoll, gyroRate);

  unsigned long now = micros();
  float dt = (now - lastTime) * 1e-6;
  lastTime = now;

  roll = alpha * (roll + gyroRate * dt) + (1 - alpha) * accRoll;

  float error = -roll;
  float pidP = Kp * error;
  float pidD = Kd * (error - lastError) / dt;
  lastError = error;

  float pidOutput = pidP + pidD;
  pidOutput = constrain(
    pidOutput,
    -(maxThrottle - baseThrottle),
     (maxThrottle - baseThrottle)
  );

  float left  = baseThrottle + pidOutput;
  float right = baseThrottle - pidOutput;

  writeMotors(left, right);

  Serial.print(now);
  Serial.print(",");
  Serial.print(roll, 3);
  Serial.print(",");
  Serial.print(leftPWM, 1);
  Serial.print(",");
  Serial.println(rightPWM, 1);

  delay(2);
}
