#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Servo.h>
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// ---- I2C buses ----
TwoWire Wire1(PB7, PB6);
TwoWire Wire2(PB3, PB10);

// ---- IMU objects ----
Adafruit_MPU6050 imu1;
Adafruit_MPU6050 imu2;

// ---- Motors ----
Servo M1, M2, M3, M4;
const int MOTOR_PIN_1 = PB4; //front right
const int MOTOR_PIN_2 = PA1; //front left
const int MOTOR_PIN_3 = PB5; //rear right
const int MOTOR_PIN_4 = PA0; //rear left

const int PWM_MIN  = 1100;
const int PWM_MAX  = 1300;
const int PWM_MID  = (PWM_MIN + PWM_MAX) / 2;

const float alpha = 0.98f;
float roll1=0, pitch1=0, roll2=0, pitch2=0;
float roll=0, pitch=0;
float Kp_roll, Kp_pitch;

unsigned long lastTime = 0;

// ---- RF24 ----
#define CE_PIN PB0
#define CSN_PIN PA4
RF24 radio(CE_PIN, CSN_PIN);

// Packed telemetry struct
struct __attribute__((packed)) Telemetry {
  float roll_error;
  float pitch_error;
  int16_t pwm1, pwm2, pwm3, pwm4;
};
Telemetry data;

const byte address[6] = "00001";

void setup() {
  Serial.begin(115200);

  Wire1.begin();
  Wire2.begin();

  if (! imu1.begin(MPU6050_I2CADDR_DEFAULT, &Wire1)) while (1);
  if (! imu2.begin(MPU6050_I2CADDR_DEFAULT, &Wire2)) while (1);
  imu1.setAccelerometerRange(MPU6050_RANGE_4_G);
  imu1.setGyroRange(MPU6050_RANGE_500_DEG);
  imu1.setFilterBandwidth(MPU6050_BAND_21_HZ);
  imu2.setAccelerometerRange(MPU6050_RANGE_4_G);
  imu2.setGyroRange(MPU6050_RANGE_500_DEG);
  imu2.setFilterBandwidth(MPU6050_BAND_21_HZ);

  M1.attach(MOTOR_PIN_1);
  M2.attach(MOTOR_PIN_2);
  M3.attach(MOTOR_PIN_3);
  M4.attach(MOTOR_PIN_4);

  Kp_roll  = float(PWM_MAX - PWM_MIN) / 30.0f;
  Kp_pitch = float(PWM_MAX - PWM_MIN) / 30.0f;

  M1.writeMicroseconds(1000);
  M2.writeMicroseconds(1000);
  M3.writeMicroseconds(1000);
  M4.writeMicroseconds(1000);

  delay(3000);

  // Setup radio
  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_MIN);
  radio.stopListening();

  lastTime = millis();
}

void fuseDroneAxes(const sensors_event_t &a, const sensors_event_t &g,
                   float &roll_est, float &pitch_est, float dt) {
  float ax=a.acceleration.x, ay=a.acceleration.y, az=a.acceleration.z;
  float gx=g.gyro.x, gy=g.gyro.y;

  float ax_d=ay, ay_d=-ax, az_d=az;
  float gx_d=gy, gy_d=-gx;

  float accRoll=atan2(ay_d, az_d)*180.0f/PI;
  float accPitch=atan2(-ax_d, sqrt(ay_d*ay_d+az_d*az_d))*180.0f/PI;
  float gyroRollRate=gx_d*180.0f/PI;
  float gyroPitchRate=gy_d*180.0f/PI;

  roll_est = alpha*(roll_est+gyroRollRate*dt)+(1-alpha)*accRoll;
  pitch_est= alpha*(pitch_est+gyroPitchRate*dt)+(1-alpha)*accPitch;
}

void loop() {
  unsigned long now=millis();
  float dt=(now-lastTime)/1000.0f;
  if(dt<=0) dt=0.001f;
  lastTime=now;

  sensors_event_t acc1, gyro1, t1;
  imu1.getEvent(&acc1, &gyro1, &t1);
  fuseDroneAxes(acc1, gyro1, roll1, pitch1, dt);

  sensors_event_t acc2, gyro2, t2;
  imu2.getEvent(&acc2, &gyro2, &t2);
  fuseDroneAxes(acc2, gyro2, roll2, pitch2, dt);

  roll=(roll1+roll2)*0.5f;
  pitch=(pitch1+pitch2)*0.5f;

  float roll_error=-roll;
  float pitch_error=-pitch;
  float roll_corr=Kp_roll*roll_error;
  float pitch_corr=Kp_pitch*pitch_error;

  int pwm1=int(PWM_MID-roll_corr-pitch_corr);
  int pwm2=int(PWM_MID+roll_corr-pitch_corr);
  int pwm3=int(PWM_MID-roll_corr+pitch_corr);
  int pwm4=int(PWM_MID+roll_corr+pitch_corr);

  pwm1=constrain(pwm1,PWM_MIN,PWM_MAX);
  pwm2=constrain(pwm2,PWM_MIN,PWM_MAX);
  pwm3=constrain(pwm3,PWM_MIN,PWM_MAX);
  pwm4=constrain(pwm4,PWM_MIN,PWM_MAX);

  M1.writeMicroseconds(pwm1);
  M2.writeMicroseconds(pwm2);
  M3.writeMicroseconds(pwm3);
  M4.writeMicroseconds(pwm4);

  // Pack telemetry
  data.roll_error=roll_error;
  data.pitch_error=pitch_error;
  data.pwm1=pwm1; data.pwm2=pwm2; data.pwm3=pwm3; data.pwm4=pwm4;

  radio.write(&data, sizeof(data));
  delay(50);
}
