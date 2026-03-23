
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

// -------- POTS --------
#define P1 32
#define P2 33
#define P3 34
#define P4 35

// -------- BUTTONS --------
#define B1 12
#define B2 14
#define B3 13
#define B4 27

// -------- SWITCHES --------
#define SW2 4
#define SWA1 25
#define SWA2 26
#define SWB 15

// -------- FUNCTIONS --------
int smoothRead(int pin) {
  long sum = 0;
  for (int i = 0; i < 5; i++) {
    sum += analogRead(pin);
  }
  return sum / 5;
}

// Reverse mapping (important)
int toPercentRev(int val) {
  return map(val, 0, 4095, 100, 0);
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

  // ===== ANALOG CHANNELS =====
  int throttle = toPercentRev(smoothRead(P2)); // CH1
  int yaw      = toPercentRev(smoothRead(P1)); // CH2
  int roll     = toPercentRev(smoothRead(P3)); // CH3
  int pitch    = toPercentRev(smoothRead(P4)); // CH4

  // ===== BUTTONS =====
  bool b1 = !digitalRead(B1);
  bool b2 = !digitalRead(B2);
  bool b3 = !digitalRead(B4); 
  bool b4 = !digitalRead(B3); 

  // ===== SWITCH CH5 =====
  String ch5 = digitalRead(SW2) ? "Mode 1" : "Mode 2";

  // ===== SWITCH CH6 (SWA) =====
  int s1 = digitalRead(SWA1);
  int s2 = digitalRead(SWA2);

  String ch6 = "Mode 2"; // mid default
  if (s1 == LOW && s2 == HIGH) ch6 = "Mode 1"; // A (up)
  else if (s1 == HIGH && s2 == LOW) ch6 = "Mode 3"; // B (down)

  // ===== SWITCH CH7 (SWB) =====
  String ch7 = digitalRead(SWB) ? "Mode 2" : "Mode 1";

  // ===== DISPLAY 1 (CHANNELS) =====
  display1.clearDisplay();
  display1.setTextSize(1);
  display1.setTextColor(SSD1306_WHITE);

  display1.setCursor(0, 0);
  display1.println("CH1 Throttle: " + String(throttle));
  display1.println("CH2 Yaw     : " + String(yaw));
  display1.println("CH3 Roll    : " + String(roll));
  display1.println("CH4 Pitch   : " + String(pitch));

  display1.display();

  // ===== DISPLAY 2 (BUTTONS + MODES) =====
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

  delay(120);
}