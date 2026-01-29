#include <Wire.h>

const int motorPins[4]     = {25, 26, 32, 33};
const int motorChannels[4] = {0, 1, 2, 3};

const int pwmFreq = 50;
const int pwmResolution = 16;

#define MPU_ADDR 0x68

const float baseThrottle = 1300.0;
const float minThrottle  = 1170.0;
const float maxThrottle  = 1430.0;

float Kp = 15;
float Ki = 0.05;
float Kd = 0.7;

float roll = 0.0;
float lastError = 0.0;
unsigned long lastTime;

float leftPWM  = 1200.0;
float rightPWM = 1200.0;

float q0 = 1.0f, q1 = 0.0f, q2 = 0.0f, q3 = 0.0f;
float beta = 0.08f;

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

void readMPU(float &ax, float &ay, float &az,
             float &gx, float &gy, float &gz) {

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);

  int16_t axRaw = Wire.read() << 8 | Wire.read();
  int16_t ayRaw = Wire.read() << 8 | Wire.read();
  int16_t azRaw = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read();
  int16_t gxRaw = Wire.read() << 8 | Wire.read();
  int16_t gyRaw = Wire.read() << 8 | Wire.read();
  int16_t gzRaw = Wire.read() << 8 | Wire.read();

  ax = axRaw / 16384.0f;
  ay = ayRaw / 16384.0f;
  az = azRaw / 16384.0f;

  gx = gxRaw * DEG_TO_RAD / 131.0f;
  gy = gyRaw * DEG_TO_RAD / 131.0f;
  gz = gzRaw * DEG_TO_RAD / 131.0f;
}

void madgwickUpdate(float ax, float ay, float az,
                    float gx, float gy, float gz, float dt) {

  float recipNorm;
  float s0, s1, s2, s3;
  float qDot1, qDot2, qDot3, qDot4;

  qDot1 = 0.5f * (-q1 * gx - q2 * gy - q3 * gz);
  qDot2 = 0.5f * ( q0 * gx + q2 * gz - q3 * gy);
  qDot3 = 0.5f * ( q0 * gy - q1 * gz + q3 * gx);
  qDot4 = 0.5f * ( q0 * gz + q1 * gy - q2 * gx);

  if (!(ax == 0.0f && ay == 0.0f && az == 0.0f)) {

    recipNorm = 1.0f / sqrt(ax * ax + ay * ay + az * az);
    ax *= recipNorm;
    ay *= recipNorm;
    az *= recipNorm;

    s0 = 4.0f*q0*q2*q2 + 2.0f*q2*ax + 4.0f*q0*q1*q1 - 2.0f*q1*ay;
    s1 = 4.0f*q1*q3*q3 - 2.0f*q3*ax + 4.0f*q0*q0*q1 - 2.0f*q0*ay;
    s2 = 4.0f*q0*q0*q2 + 2.0f*q0*ax + 4.0f*q2*q3*q3 - 2.0f*q3*ay;
    s3 = 4.0f*q1*q1*q3 - 2.0f*q1*ax + 4.0f*q2*q2*q3 - 2.0f*q2*ay;

    recipNorm = 1.0f / sqrt(s0*s0 + s1*s1 + s2*s2 + s3*s3);
    s0 *= recipNorm;
    s1 *= recipNorm;
    s2 *= recipNorm;
    s3 *= recipNorm;

    qDot1 -= beta * s0;
    qDot2 -= beta * s1;
    qDot3 -= beta * s2;
    qDot4 -= beta * s3;
  }

  q0 += qDot1 * dt;
  q1 += qDot2 * dt;
  q2 += qDot3 * dt;
  q3 += qDot4 * dt;

  recipNorm = 1.0f / sqrt(q0*q0 + q1*q1 + q2*q2 + q3*q3);
  q0 *= recipNorm;
  q1 *= recipNorm;
  q2 *= recipNorm;
  q3 *= recipNorm;
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
  float ax, ay, az, gx, gy, gz;
  readMPU(ax, ay, az, gx, gy, gz);

  unsigned long now = micros();
  float dt = (now - lastTime) * 1e-6f;
  lastTime = now;

  madgwickUpdate(ax, ay, az, gx, gy, gz, dt);

  roll = atan2(2.0f * (q0*q1 + q2*q3),
               1.0f - 2.0f * (q1*q1 + q2*q2)) * RAD_TO_DEG;

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
