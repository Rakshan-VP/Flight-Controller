#include <WiFi.h>
#include <Wire.h>
#include <MPU6050.h>

// -------- Motor Pins (Dynamic.ino) --------
#define M1 25
#define M2 26
#define M3 32
#define M4 33

MPU6050 mpu;
WiFiServer server(8000); 
WiFiClient client;

// -------- Calibration & PWM --------
int yaw_min=262, yaw_mid=1815, yaw_max=3626;
int thr_min=302, thr_max=3647;
int roll_min=410, roll_mid=1940, roll_max=3835;
int pit_min=218, pit_mid=1801, pit_max=3603;

#define PWM_MIN 1050
#define PWM_MAX 1950
#define PWM_MID 1500
#define DEADZONE 20

// -------- PID & Sensors --------
float roll=0;
float roll_offset = 2.65;
float Kp=3.5, Ki=0.05, Kd=2.2;
float integral=0;
const float alpha = 0.98;

bool armed = false;
unsigned long lastCommandTime = 0;
float m1_pwm=1000, m2_pwm=1000, m3_pwm=1000, m4_pwm=1000;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  mpu.initialize();
  mpu.setDLPFMode(0x03); // 20Hz filter 

  ledcAttach(M1, 400, 16); // 400Hz PWM [cite: 11]
  ledcAttach(M2, 400, 16);
  ledcAttach(M3, 400, 16);
  ledcAttach(M4, 400, 16);

  WiFi.softAP("DRONE_ESP", "12345678");
  server.begin();
}

int processStick(int val, int minV, int midV, int maxV) {
  int out = (val < midV) ? map(val, minV, midV, PWM_MIN, PWM_MID) : map(val, midV, maxV, PWM_MID, PWM_MAX);
  out = (PWM_MAX + PWM_MIN) - out; // Reverse all axes [cite: 67, 70]
  if (abs(out - PWM_MID) < DEADZONE) out = PWM_MID;
  return constrain(out, PWM_MIN, PWM_MAX);
}

void setMotor(int pin, float pwm) {
  uint32_t duty = (constrain(pwm, 1000, 2000) / 20000.0) * 65535;
  ledcWrite(pin, duty);
}

void loop() {
  if (!client || !client.connected()) {
    client = server.available();
    return;
  }

  // --- IMU Update (Complementary Filter) ---
  int16_t ax, ay, az, gx, gy, gz;
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  float accRoll = atan2(-ax, az) * 180.0 / PI; // Adjusted for drone frame [cite: 20]
  roll = alpha * (roll + (gx/131.0) * 0.004) + (1-alpha) * accRoll;

  if (client.available()) {
    String cmd = client.readStringUntil('\n');
    int r_thr, r_yaw, r_roll, r_pit, ch5, ch6, ch7;
    sscanf(cmd.c_str(), "[%d,%d,%d,%d,%d,%d,%d]", &r_thr, &r_yaw, &r_roll, &r_pit, &ch5, &ch6, &ch7);
    
    int throttle = (PWM_MAX + PWM_MIN) - map(r_thr, thr_min, thr_max, PWM_MIN, PWM_MAX);
    int roll_stick = processStick(r_roll, roll_min, roll_mid, roll_max);

    // --- ARMING LOGIC (CH7) ---
    if (ch7 == 2 && throttle < 1100) armed = true;
    else if (ch7 == 1) armed = false;

    if (armed && (millis() - lastCommandTime > 7000)) armed = false;
    lastCommandTime = millis();

    // --- ROLL PID TEST ---
    if (armed && ch5 == 2) {
      float target = (roll_stick - 1500) / 10.0;
      float error = target - (roll - roll_offset);
      integral = constrain(integral + error * 0.004, -150, 150);
      float pidOut = Kp * error + Ki * integral - Kd * (gx/131.0);
      
      m1_pwm = 1200 - pidOut; m2_pwm = 1200 - pidOut;
      m3_pwm = 1200 + pidOut; m4_pwm = 1200 + pidOut;
    } else {
      m1_pwm = m2_pwm = m3_pwm = m4_pwm = 1000;
    }

    setMotor(M1, m1_pwm); setMotor(M2, m2_pwm); setMotor(M3, m3_pwm); setMotor(M4, m4_pwm);

    // --- Telemetry Response ---
    char buf[160];
    snprintf(buf, sizeof(buf), "[ack,%d,%d,%.1f,-,-,-,-,-,-,-,-,-,-,%.0f,%.0f,%.0f,%.0f]\n", 
             armed, ch5, roll, m1_pwm, m2_pwm, m3_pwm, m4_pwm);
    client.print(buf);
  }
}