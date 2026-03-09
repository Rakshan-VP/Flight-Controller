#include <WiFi.h>
#include <Wire.h>
#include <MPU6050.h>
#include <FastLED.h>

MPU6050 mpu;

// -------- Motor Pins --------
#define M1 25
#define M2 26
#define M3 32
#define M4 33

// -------- LED --------
#define LED_PIN     23
#define NUM_LEDS    1
#define LED_TYPE    WS2811
#define COLOR_ORDER GRB
#define BRIGHTNESS  120

CRGB leds[NUM_LEDS];

// -------- WiFi --------
const char* ssid = "DRONE_ESP";
const char* password = "12345678";

WiFiServer server(5000);
WiFiClient client;

// -------- ANGLE OFFSETS --------
const float roll_offset  = 2.65;
const float pitch_offset = -0.05;

// -------- Complementary Filter --------
float roll = 0.0;
float pitch = 0.0;
const float alpha = 0.98;

const float IMU_FREQ = 250.0;
const float TELEMETRY_FREQ = 100.0;

unsigned long lastIMU = 0;
unsigned long lastTelemetry = 0;

unsigned long armTimeout = 7500;

// -------- Raw IMU --------
float rawAccX=0, rawAccY=0, rawAccZ=0;
float rawGyroX=0, rawGyroY=0, rawGyroZ=0;

// -------- Drone Frame --------
float droneAccX=0, droneAccY=0, droneAccZ=0;
float droneGyroX=0, droneGyroY=0, droneGyroZ=0;

// -------- PID Gains --------
float Kpr=0, Kir=0, Kdr=0;
float Kpp=0, Kip=0, Kdp=0;

// -------- PID States --------
float error_r=0, integral_r=0;
float error_p=0, integral_p=0;

float basePWM = 1100;

// -------- System State --------
bool armed=false;
bool testRunning=false;
bool rampDown=false;

unsigned long armTime=0;
unsigned long lastBasePWMTime=0;
unsigned long lastRampStep=0;

// -------- Motor State --------
float m1_pwm=1000, m2_pwm=1000, m3_pwm=1000, m4_pwm=1000;

// -------- PWM --------
#define PWM_FREQ 400
#define PWM_RES 16

void setLED(CRGB color){
  leds[0] = color;
  FastLED.show();
}

void setupPWM(){
  ledcAttach(M1, PWM_FREQ, PWM_RES);
  ledcAttach(M2, PWM_FREQ, PWM_RES);
  ledcAttach(M3, PWM_FREQ, PWM_RES);
  ledcAttach(M4, PWM_FREQ, PWM_RES);
}

void setMotor(int pin, float pwm_us){
  pwm_us = constrain(pwm_us, 1000, 2000);
  uint32_t duty = (pwm_us / 20000.0) * ((1<<PWM_RES)-1);
  ledcWrite(pin, duty);

  if(pin==M1) m1_pwm=pwm_us;
  if(pin==M2) m2_pwm=pwm_us;
  if(pin==M3) m3_pwm=pwm_us;
  if(pin==M4) m4_pwm=pwm_us;
}

void stopMotors(){
  setMotor(M1,1000);
  setMotor(M2,1000);
  setMotor(M3,1000);
  setMotor(M4,1000);
}

void updateIMU(){

  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax,&ay,&az,&gx,&gy,&gz);

  rawAccX = ax / 16384.0;
  rawAccY = ay / 16384.0;
  rawAccZ = az / 16384.0;

  rawGyroX = gx / 131.0;
  rawGyroY = gy / 131.0;
  rawGyroZ = gz / 131.0;

  droneAccX = -rawAccY;
  droneAccY = rawAccX;
  droneAccZ = rawAccZ;

  droneGyroX = -rawGyroY;
  droneGyroY = rawGyroX;
  droneGyroZ = rawGyroZ;

  float dt = 1.0 / IMU_FREQ;

  float accRoll  = atan2(droneAccY, droneAccZ) * 180.0 / PI;
  float accPitch = atan2(-droneAccX, sqrt(droneAccY*droneAccY + droneAccZ*droneAccZ)) * 180.0 / PI;

  roll  = alpha * (roll  + droneGyroX * dt) + (1 - alpha) * accRoll;
  pitch = alpha * (pitch + droneGyroY * dt) + (1 - alpha) * accPitch;
}

void computePID(float &rollPID, float &pitchPID){

  float dt = 1.0/IMU_FREQ;

  float measuredRoll  = roll  - roll_offset;
  float measuredPitch = pitch - pitch_offset;

  error_r = -measuredRoll;
  integral_r += error_r * dt;
  integral_r = constrain(integral_r,-200,200);

  float derivative_r = -droneGyroX;
  rollPID = Kpr*error_r + Kir*integral_r + Kdr*derivative_r;

  error_p = -measuredPitch;
  integral_p += error_p * dt;
  integral_p = constrain(integral_p,-200,200);

  float derivative_p = -droneGyroY;
  pitchPID = Kpp*error_p + Kip*integral_p + Kdp*derivative_p;
}

void applyMotor(float rollPID, float pitchPID){

  float m1 = basePWM - pitchPID - rollPID;
  float m2 = basePWM + pitchPID - rollPID;
  float m3 = basePWM - pitchPID + rollPID;
  float m4 = basePWM + pitchPID + rollPID;

  setMotor(M1,m1);
  setMotor(M2,m2);
  setMotor(M3,m3);
  setMotor(M4,m4);
}

void setup() {

  Serial.begin(115200);
  Wire.begin(21,22);
  mpu.initialize();

  mpu.setDLPFMode(MPU6050_DLPF_BW_20);
  mpu.setFullScaleGyroRange(MPU6050_GYRO_FS_500);
  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_4);

  setupPWM();

  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  setLED(CRGB::Red);

  WiFi.softAP(ssid, password);
  server.begin();

  lastIMU = micros();
  lastTelemetry = micros();
}

void loop() {

  if (!client || !client.connected())
      client = server.available();

  if (client && client.connected()) {
    while(client.available()){

      String cmd = client.readStringUntil('\n');
      cmd.trim();

      if(cmd.startsWith("SET_PID")){
        sscanf(cmd.c_str(),"SET_PID,%f,%f,%f,%f,%f,%f",
        &Kpr,&Kir,&Kdr,&Kpp,&Kip,&Kdp);
      }

      if(cmd.startsWith("SET_BASE")){
        sscanf(cmd.c_str(),"SET_BASE,%f",&basePWM);
        lastBasePWMTime = millis();
      }

      if(cmd=="ARM"){
        armed=true;
        armTime=millis();

        setMotor(M1,1100);
        setMotor(M2,1100);
        setMotor(M3,1100);
        setMotor(M4,1100);

        setLED(CRGB::Green);
      }

      if(cmd=="START_TEST" && armed){
        testRunning=true;
        rampDown=false;

        integral_r=0;
        integral_p=0;

        lastBasePWMTime = millis();

        setLED(CRGB::Blue);
      }

      if(cmd=="STOP_TEST"){
        testRunning=false;
        rampDown=true;
        lastRampStep=millis();

        setLED(CRGB::Yellow);
      }

      if(cmd=="DISARM"){
        rampDown=false;
        testRunning=false;
        armed=false;
        stopMotors();
        setLED(CRGB::Red);
      }
    }
  }

  if(rampDown && millis()-lastRampStep >= 40){

      basePWM -= 2;
      lastRampStep = millis();

      setMotor(M1, basePWM);
      setMotor(M2, basePWM);
      setMotor(M3, basePWM);
      setMotor(M4, basePWM);

      if(basePWM <= 1100){
          basePWM = 1100;
          rampDown=false;
          armed=false;

          stopMotors();
          setLED(CRGB::Red);
      }
  }

  if(armed && !testRunning && !rampDown){
    if(millis()-armTime > armTimeout){
      stopMotors();
      armed=false;
      setLED(CRGB::Red);
    }
  }

  if(testRunning){
    if(millis() - lastBasePWMTime > 5000){
      rampDown=true;
      testRunning=false;
    }
  }

  if (micros() - lastIMU >= (1000000.0 / IMU_FREQ)) {

    lastIMU += (1000000.0 / IMU_FREQ);
    updateIMU();

    if(armed && testRunning){

      float rollPID,pitchPID;
      computePID(rollPID,pitchPID);
      applyMotor(rollPID,pitchPID);
    }
  }

  if (micros() - lastTelemetry >= (1000000.0 / TELEMETRY_FREQ)) {

    lastTelemetry += (1000000.0 / TELEMETRY_FREQ);

    char buffer[256];

    snprintf(buffer, sizeof(buffer),
      "%.3f,%.3f,%.1f,%.1f,%.1f,%.1f,"
      "%.3f,%.3f,%.3f,"
      "%.3f,%.3f,%.3f,"
      "%.3f,%.3f,%.3f,"
      "%.3f,%.3f,%.3f\n",
      roll, pitch,
      m1_pwm, m2_pwm, m3_pwm, m4_pwm,
      rawAccX, rawAccY, rawAccZ,
      rawGyroX, rawGyroY, rawGyroZ,
      droneAccX, droneAccY, droneAccZ,
      droneGyroX, droneGyroY, droneGyroZ
    );

    client.print(buffer);
  }
}