#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>
#include <math.h>

// ---- I2C buses ----
TwoWire Wire1(PB7, PB6);
TwoWire Wire2(PB3, PB10);

// ---- IMU objects ----
Adafruit_MPU6050 imu1;
Adafruit_MPU6050 imu2;

// ---- Madgwick filter (manual) ----
float beta = 0.5f;
struct Quaternion { float w,x,y,z; };
Quaternion q1 = {1,0,0,0}, q2 = {1,0,0,0};

// ---- Complementary filter ----
const float alpha = 0.98f;
float roll1_cf=0, pitch1_cf=0, roll2_cf=0, pitch2_cf=0;
float roll_cf=0, pitch_cf=0;
float roll1_mad=0, pitch1_mad=0, roll2_mad=0, pitch2_mad=0;
float roll_mad=0, pitch_mad=0;

unsigned long lastTime = 0;

// ---- nRF24L01 ----
#define CE_PIN PB0
#define CSN_PIN PA4
RF24 radio(CE_PIN, CSN_PIN);
const byte address[6] = "00001";

// ---- telemetry struct ----
struct Telemetry {
  float roll_cf;
  float pitch_cf;
  float roll_mad;
  float pitch_mad;
};

// --- Madgwick AHRS update (IMU only) ---
void MadgwickAHRSupdateIMU(Quaternion &q, float gx, float gy, float gz,
                           float ax, float ay, float az, float dt) {
  float norm = sqrt(ax*ax + ay*ay + az*az);
  if(norm==0) return;
  ax/=norm; ay/=norm; az/=norm;

  float f1 = 2*(q.x*q.z - q.w*q.y) - ax;
  float f2 = 2*(q.w*q.x + q.y*q.z) - ay;
  float f3 = 2*(0.5 - q.x*q.x - q.y*q.y) - az;

  float J_11=-2*q.y; float J_12=2*q.z; float J_13=-2*q.w; float J_14=2*q.x;
  float J_21=2*q.x;  float J_22=2*q.w;  float J_23=2*q.z;  float J_24=2*q.y;
  float J_31=0;      float J_32=-4*q.x; float J_33=-4*q.y; float J_34=0;

  float qDot1 = 0.5f*(-q.x*gx - q.y*gy - q.z*gz) - beta*(J_11*f1 + J_21*f2 + J_31*f3);
  float qDot2 = 0.5f*( q.w*gx + q.y*gz - q.z*gy) - beta*(J_12*f1 + J_22*f2 + J_32*f3);
  float qDot3 = 0.5f*( q.w*gy - q.x*gz + q.z*gx) - beta*(J_13*f1 + J_23*f2 + J_33*f3);
  float qDot4 = 0.5f*( q.w*gz + q.x*gy - q.y*gx) - beta*(J_14*f1 + J_24*f2 + J_34*f3);

  q.w += qDot1*dt; q.x += qDot2*dt; q.y += qDot3*dt; q.z += qDot4*dt;

  norm = sqrt(q.w*q.w + q.x*q.x + q.y*q.y + q.z*q.z);
  q.w/=norm; q.x/=norm; q.y/=norm; q.z/=norm;
}

// --- quaternion to roll/pitch ---
void quaternionToEuler(const Quaternion &q, float &roll, float &pitch) {
  roll  = atan2(2*(q.w*q.x + q.y*q.z), 1 - 2*(q.x*q.x + q.y*q.y))*180.0/PI;
  pitch = asin(2*(q.w*q.y - q.z*q.x))*180.0/PI;
}

// --- Complementary filter ---
void fuseComplementary(const sensors_event_t &a, const sensors_event_t &g,
                       float &roll_est, float &pitch_est, float dt) {
  float ax_d = a.acceleration.y;
  float ay_d = -a.acceleration.x;
  float az_d = a.acceleration.z;

  float gx_d = g.gyro.y;
  float gy_d = -g.gyro.x;

  float accRoll  = atan2(ay_d, az_d)*180.0f/PI;
  float accPitch = atan2(-ax_d, sqrt(ay_d*ay_d + az_d*az_d))*180.0f/PI;
  float gyroRollRate  = gx_d*180.0f/PI;
  float gyroPitchRate = gy_d*180.0f/PI;

  roll_est  = alpha*(roll_est + gyroRollRate*dt) + (1-alpha)*accRoll;
  pitch_est = alpha*(pitch_est + gyroPitchRate*dt) + (1-alpha)*accPitch;
}

void setup() {
  Serial.begin(115200);

  Wire1.begin(); Wire2.begin();

  if(!imu1.begin(MPU6050_I2CADDR_DEFAULT, &Wire1)) while(1);
  if(!imu2.begin(MPU6050_I2CADDR_DEFAULT, &Wire2)) while(1);

  imu1.setAccelerometerRange(MPU6050_RANGE_4_G);
  imu1.setGyroRange(MPU6050_RANGE_500_DEG);
  imu1.setFilterBandwidth(MPU6050_BAND_21_HZ);

  imu2.setAccelerometerRange(MPU6050_RANGE_4_G);
  imu2.setGyroRange(MPU6050_RANGE_500_DEG);
  imu2.setFilterBandwidth(MPU6050_BAND_21_HZ);

  // --- nRF24L01 setup ---
  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_MIN);
  radio.stopListening();

  lastTime = millis();
}

void loop() {
  unsigned long now = millis();
  float dt = (now-lastTime)/1000.0f;
  if(dt<=0) dt = 0.001f;
  lastTime = now;

  sensors_event_t acc1, gyro1, temp1;
  imu1.getEvent(&acc1, &gyro1, &temp1);

  sensors_event_t acc2, gyro2, temp2;
  imu2.getEvent(&acc2, &gyro2, &temp2);

  // --- Complementary Filter ---
  fuseComplementary(acc1, gyro1, roll1_cf, pitch1_cf, dt);
  fuseComplementary(acc2, gyro2, roll2_cf, pitch2_cf, dt);
  roll_cf  = (roll1_cf + roll2_cf)/2.0f;
  pitch_cf = (pitch1_cf + pitch2_cf)/2.0f;

  // --- Madgwick Filter ---
  float ax1_d = acc1.acceleration.y; float ay1_d = -acc1.acceleration.x; float az1_d = acc1.acceleration.z;
  float gx1_d = gyro1.gyro.y*PI/180.0f; float gy1_d = -gyro1.gyro.x*PI/180.0f; float gz1_d = gyro1.gyro.z*PI/180.0f;
  MadgwickAHRSupdateIMU(q1, gx1_d, gy1_d, gz1_d, ax1_d, ay1_d, az1_d, dt);

  float ax2_d = acc2.acceleration.y; float ay2_d = -acc2.acceleration.x; float az2_d = acc2.acceleration.z;
  float gx2_d = gyro2.gyro.y*PI/180.0f; float gy2_d = -gyro2.gyro.x*PI/180.0f; float gz2_d = gyro2.gyro.z*PI/180.0f;
  MadgwickAHRSupdateIMU(q2, gx2_d, gy2_d, gz2_d, ax2_d, ay2_d, az2_d, dt);

  quaternionToEuler(q1, roll1_mad, pitch1_mad);
  quaternionToEuler(q2, roll2_mad, pitch2_mad);
  roll_mad  = (roll1_mad + roll2_mad)/2.0f;
  pitch_mad = (pitch1_mad + pitch2_mad)/2.0f;

  // --- Pack telemetry ---
  Telemetry data;
  data.roll_cf  = roll_cf;
  data.pitch_cf = pitch_cf;
  data.roll_mad = roll_mad;
  data.pitch_mad= pitch_mad;

  // --- Send via nRF24L01 ---
  radio.write(&data, sizeof(data));

  delay(20); // 50 Hz
}