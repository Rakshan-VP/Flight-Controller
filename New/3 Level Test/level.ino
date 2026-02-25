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
const char* ssid = "DRONE_ESP";
const char* password = "12345678";

WiFiServer server(5000);
WiFiClient client;

// -------- ANGLE OFFSETS ONLY --------
const float roll_offset  = 2.65;
const float pitch_offset = -0.05;

// -------- Filter --------
float roll = 0, pitch = 0;
const float alpha = 0.98;

const float IMU_FREQ = 250.0;
const float TELEMETRY_FREQ = 100.0;

unsigned long lastIMU = 0;
unsigned long lastTelemetry = 0;

// -------- PID --------
float Kp=0, Ki=0, Kd=0;
float basePWM = 1100;

float error=0, prevError=0;
float integral=0;

bool rollMode=false;
bool pitchMode=false;
bool testRunning=false;

// -------- Motor State --------
float m1_pwm=1000, m2_pwm=1000, m3_pwm=1000, m4_pwm=1000;

// -------- PWM --------
#define PWM_FREQ 400
#define PWM_RES 16

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

// -------- IMU --------
void updateIMU(){

  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax,&ay,&az,&gx,&gy,&gz);

  float imuX = ax/16384.0;
  float imuY = ay/16384.0;
  float imuZ = az/16384.0;

  float accX = -imuY;
  float accY =  imuX;
  float accZ =  imuZ;

  float gyroX = gx/131.0;
  float gyroY = gy/131.0;

  float drgyroX = -gyroY;
  float drgyroY =  gyroX;

  float dt = 1.0/IMU_FREQ;

  float accRoll  = atan2(accY, accZ)*180/PI;
  float accPitch = atan2(-accX, sqrt(accY*accY+accZ*accZ))*180/PI;

  roll  = alpha*(roll + drgyroX*dt) + (1-alpha)*accRoll;
  pitch = alpha*(pitch + drgyroY*dt) + (1-alpha)*accPitch;

  // Apply angle offsets only
  roll  -= roll_offset;
  pitch -= pitch_offset;
}

// -------- PID --------
float computePID(float measured){

  float dt = 1.0/IMU_FREQ;

  error = 0 - measured;
  integral += error * dt;
  integral = constrain(integral, -200, 200);

  float derivative = (error - prevError)/dt;
  prevError = error;

  return Kp*error + Ki*integral + Kd*derivative;
}

// -------- Motor Mixing --------
void applyMotor(float pidOut){

  if(rollMode){
    float right = basePWM - pidOut;
    float left  = basePWM + pidOut;

    setMotor(M1,right);
    setMotor(M2,right);
    setMotor(M3,left);
    setMotor(M4,left);
  }

  if(pitchMode){
    float front = basePWM - pidOut;
    float back  = basePWM + pidOut;

    setMotor(M1,front);
    setMotor(M3,front);
    setMotor(M2,back);
    setMotor(M4,back);
  }
}

// -------- Setup --------
void setup() {

  Serial.begin(115200);
  Wire.begin(21,22);
  mpu.initialize();
  setupPWM();

  WiFi.softAP(ssid, password);
  server.begin();

  lastIMU = micros();
  lastTelemetry = micros();
}

// -------- Loop --------
void loop() {

  if (!client || !client.connected()) {
    client = server.available();
    return;
  }

  while(client.available()){
    String cmd = client.readStringUntil('\n');
    cmd.trim();

    if(cmd.startsWith("SET_ROLL")){
      sscanf(cmd.c_str(),"SET_ROLL,%f,%f,%f,%f",&Kp,&Ki,&Kd,&basePWM);
      rollMode=true; pitchMode=false;
    }

    if(cmd.startsWith("SET_PITCH")){
      sscanf(cmd.c_str(),"SET_PITCH,%f,%f,%f,%f",&Kp,&Ki,&Kd,&basePWM);
      pitchMode=true; rollMode=false;
    }

    if(cmd=="START_ROLL" || cmd=="START_PITCH"){
      testRunning=true;
      integral=0;
      prevError=0;
    }

    if(cmd=="STOP"){
      testRunning=false;
      rollMode=false;
      pitchMode=false;
      stopMotors();
    }
  }

  if (micros() - lastIMU >= (1000000.0 / IMU_FREQ)) {
    lastIMU += (1000000.0 / IMU_FREQ);
    updateIMU();

    if(testRunning){
      float measured = rollMode ? roll : pitch;
      float pidOut = computePID(measured);
      applyMotor(pidOut);
    }
  }

  if (micros() - lastTelemetry >= (1000000.0 / TELEMETRY_FREQ)) {
    lastTelemetry += (1000000.0 / TELEMETRY_FREQ);

    client.print(roll); client.print(",");
    client.print(pitch); client.print(",");
    client.print(m1_pwm); client.print(",");
    client.print(m2_pwm); client.print(",");
    client.print(m3_pwm); client.print(",");
    client.println(m4_pwm);
  }
}