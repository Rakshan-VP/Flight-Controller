#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// -------- OLED --------
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

TwoWire I2C_1 = TwoWire(0);
TwoWire I2C_2 = TwoWire(1);

Adafruit_SSD1306 display1(SCREEN_WIDTH, SCREEN_HEIGHT, &I2C_1, -1);
Adafruit_SSD1306 display2(SCREEN_WIDTH, SCREEN_HEIGHT, &I2C_2, -1);

// -------- PINS --------
#define P1 32  // Yaw
#define P2 33  // Throttle
#define P3 34  // Roll
#define P4 35  // Pitch

#define B1 12
#define B2 14
#define B3 13
#define B4 27

#define SW2 4
#define SWA1 25
#define SWA2 26
#define SWB 15

// -------- CALIBRATION --------
int yaw_min=262, yaw_mid=1815, yaw_max=3626;
int thr_min=302, thr_max=3647;
int roll_min=410, roll_mid=1940, roll_max=3835;
int pit_min=218, pit_mid=1801, pit_max=3603;

// -------- PWM SETTINGS --------
#define PWM_MIN 1050
#define PWM_MAX 1950
#define PWM_MID 1500
#define DEADZONE 20

// -------- FUNCTIONS --------
int smoothRead(int pin) {
  long sum = 0;
  for (int i = 0; i < 5; i++) {
    sum += analogRead(pin);
  }
  return sum / 5;
}

// Centered mapping
int mapCentered(int val, int minV, int midV, int maxV) {
  int out;

  if (val < midV)
    out = map(val, minV, midV, PWM_MIN, PWM_MID);
  else
    out = map(val, midV, maxV, PWM_MID, PWM_MAX);

  // Deadzone
  if (abs(out - PWM_MID) < DEADZONE)
    out = PWM_MID;

  return constrain(out, PWM_MIN, PWM_MAX);
}

// Throttle mapping
int mapThrottle(int val) {
  int out = map(val, thr_min, thr_max, PWM_MIN, PWM_MAX);

  // Safety floor
  if (out < 1120) out = PWM_MIN;

  return constrain(out, PWM_MIN, PWM_MAX);
}

// Reverse helper
int reversePWM(int val) {
  return (PWM_MAX + PWM_MIN) - val;
}

// -------- SETUP --------
void setup() {
  Serial.begin(115200);

  I2C_1.begin(19, 18);
  I2C_2.begin(22, 21);

  display1.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display2.begin(SSD1306_SWITCHCAPVCC, 0x3C);

  pinMode(B1, INPUT_PULLUP);
  pinMode(B2, INPUT_PULLUP);
  pinMode(B3, INPUT_PULLUP);
  pinMode(B4, INPUT_PULLUP);

  pinMode(SW2, INPUT_PULLUP);
  pinMode(SWA1, INPUT_PULLUP);
  pinMode(SWA2, INPUT_PULLUP);
  pinMode(SWB, INPUT_PULLUP);
}

// -------- LOOP --------
void loop() {

  // ===== ANALOG → PWM =====
  int throttle = reversePWM(mapThrottle(smoothRead(P2)));  // CH1
  int yaw      = reversePWM(mapCentered(smoothRead(P1), yaw_min, yaw_mid, yaw_max)); // CH2
  int roll     = reversePWM(mapCentered(smoothRead(P3), roll_min, roll_mid, roll_max)); // CH3
  int pitch    = reversePWM(mapCentered(smoothRead(P4), pit_min, pit_mid, pit_max)); // CH4

  // ===== BUTTONS =====
  bool b1 = !digitalRead(B1);
  bool b2 = !digitalRead(B2);
  bool b3 = !digitalRead(B4); // swapped
  bool b4 = !digitalRead(B3); // swapped

  // ===== SWITCHES =====
  String ch5 = digitalRead(SW2) ? "Mode 1" : "Mode 2";

  int s1 = digitalRead(SWA1);
  int s2 = digitalRead(SWA2);

  String ch6 = "Mode 2";
  if (s1 == LOW && s2 == HIGH) ch6 = "Mode 1";
  else if (s1 == HIGH && s2 == LOW) ch6 = "Mode 3";

  String ch7 = digitalRead(SWB) ? "Mode 2" : "Mode 1";

  // ===== DISPLAY 1 =====
  display1.clearDisplay();
  display1.setTextSize(1);
  display1.setTextColor(SSD1306_WHITE);

  display1.setCursor(0, 0);
  display1.println("CH1 Throttle: " + String(throttle));
  display1.println("CH2 Yaw     : " + String(yaw));
  display1.println("CH3 Roll    : " + String(roll));
  display1.println("CH4 Pitch   : " + String(pitch));

  display1.display();

  // ===== DISPLAY 2 =====
  display2.clearDisplay();
  display2.setTextSize(1);
  display2.setTextColor(SSD1306_WHITE);

  display2.setCursor(0, 0);

  display2.println("B1 : " + String(b1));
  display2.println("B2 : " + String(b2));
  display2.println("B3 : " + String(b3));
  display2.println("B4 : " + String(b4));

  display2.println("CH5: " + ch5);
  display2.println("CH6: " + ch6);
  display2.println("CH7: " + ch7);

  display2.display();

  delay(100);
}