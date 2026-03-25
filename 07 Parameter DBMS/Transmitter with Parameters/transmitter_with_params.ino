#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "paramSystem.h" 

// -------- OLED CONFIG --------
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

TwoWire I2C_1 = TwoWire(0);
TwoWire I2C_2 = TwoWire(1);

Adafruit_SSD1306 display1(SCREEN_WIDTH, SCREEN_HEIGHT, &I2C_1, -1);
Adafruit_SSD1306 display2(SCREEN_WIDTH, SCREEN_HEIGHT, &I2C_2, -1);

// -------- PINS --------
#define P1 32
#define P2 33
#define P3 34
#define P4 35

#define B1 12
#define B2 14
#define B3 13
#define B4 27

#define SW2 4
#define SWA1 25
#define SWA2 26
#define SWB 15

// -------- CALIBRATION VARS --------
int yaw_min, yaw_mid, yaw_max;
int thr_min, thr_max;
int roll_min, roll_mid, roll_max;
int pit_min, pit_mid, pit_max;

// -------- PWM SETTINGS --------
#define PWM_MIN 1050
#define PWM_MAX 1950
#define PWM_MID 1500
#define DEADZONE 20

// ---------- LOAD PARAMS FROM HEADER ----------
void loadParamsToVars() {
  yaw_min  = param_get("YAW_MIN", 262);
  yaw_mid  = param_get("YAW_MID", 1815);
  yaw_max  = param_get("YAW_MAX", 3626);

  thr_min  = param_get("THROTTLE_MIN", 302);
  thr_max  = param_get("THROTTLE_MAX", 3647);

  roll_min = param_get("ROLL_MIN", 410);
  roll_mid = param_get("ROLL_MID", 1940);
  roll_max = param_get("ROLL_MAX", 3835);

  pit_min  = param_get("PITCH_MIN", 218);
  pit_mid  = param_get("PITCH_MID", 1801);
  pit_max  = param_get("PITCH_MAX", 3603);
}

// ---------- HELPER FUNCTIONS ----------
int smoothRead(int pin) {
  long sum = 0;
  for (int i = 0; i < 5; i++) sum += analogRead(pin);
  return sum / 5;
}

int mapCentered(int val, int minV, int midV, int maxV) {
  int out = (val < midV)
    ? map(val, minV, midV, PWM_MIN, PWM_MID)
    : map(val, midV, maxV, PWM_MID, PWM_MAX);

  if (abs(out - PWM_MID) < DEADZONE) out = PWM_MID;
  return constrain(out, PWM_MIN, PWM_MAX);
}

int mapThrottle(int val) {
  int out = map(val, thr_min, thr_max, PWM_MIN, PWM_MAX);
  if (out < 1120) out = PWM_MIN;
  return constrain(out, PWM_MIN, PWM_MAX);
}

int reversePWM(int val) {
  return (PWM_MAX + PWM_MIN) - val;
}

// ---------- SETUP ----------
void setup() {
  Serial.begin(115200);
  delay(500); 

  // 1. Initialize I2C
  I2C_1.begin(19, 18);
  I2C_2.begin(22, 21);
  delay(100); 

  // 2. Initialize Displays
  display1.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display2.begin(SSD1306_SWITCHCAPVCC, 0x3C);

  // 3. Initialize Param System
  param_init();
  loadParamsToVars();
  
  // 4. Pin setup
  pinMode(B1, INPUT_PULLUP);
  pinMode(B2, INPUT_PULLUP);
  pinMode(B3, INPUT_PULLUP);
  pinMode(B4, INPUT_PULLUP);
  pinMode(SW2, INPUT_PULLUP);
  pinMode(SWA1, INPUT_PULLUP);
  pinMode(SWA2, INPUT_PULLUP);
  pinMode(SWB, INPUT_PULLUP);
}

// ---------- LOOP ----------
void loop() {
  // Check for Serial commands and updates
  param_handle();
  if (param_isUpdated()) {
    loadParamsToVars();
  }

  // --- Logic ---
  int throttle = reversePWM(mapThrottle(smoothRead(P2)));
  int yaw      = reversePWM(mapCentered(smoothRead(P1), yaw_min, yaw_mid, yaw_max));
  int roll     = reversePWM(mapCentered(smoothRead(P3), roll_min, roll_mid, roll_max));
  int pitch    = reversePWM(mapCentered(smoothRead(P4), pit_min, pit_mid, pit_max));

  bool b1 = !digitalRead(B1);
  bool b2 = !digitalRead(B2);
  bool b3 = !digitalRead(B4);
  bool b4 = !digitalRead(B3);

  String ch5 = digitalRead(SW2) ? "Mode 1" : "Mode 2";
  int s1 = digitalRead(SWA1);
  int s2 = digitalRead(SWA2);
  String ch6 = (s1 == LOW && s2 == HIGH) ? "Mode 1" : (s1 == HIGH && s2 == LOW) ? "Mode 3" : "Mode 2";
  String ch7 = digitalRead(SWB) ? "Mode 2" : "Mode 1";

  // --- Display 1 ---
  display1.clearDisplay();
  display1.setCursor(0, 0);
  display1.setTextSize(1);
  display1.setTextColor(SSD1306_WHITE);
  display1.println("CH1 Throttle: " + String(throttle));
  display1.println("CH2 Yaw     : " + String(yaw));
  display1.println("CH3 Roll    : " + String(roll));
  display1.println("CH4 Pitch   : " + String(pitch));
  display1.display();

  // --- Display 2 ---
  display2.clearDisplay();
  display2.setCursor(0, 0);
  display2.setTextSize(1);
  display2.setTextColor(SSD1306_WHITE);
  display2.println("B1 : " + String(b1));
  display2.println("B2 : " + String(b2));
  display2.println("B3 : " + String(b3));
  display2.println("B4 : " + String(b4));
  display2.println("CH5: " + ch5);
  display2.println("CH6: " + ch6);
  display2.println("CH7: " + ch7);
  display2.display();

  delay(20);
}