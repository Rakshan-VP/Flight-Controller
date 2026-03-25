#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ================= PARAM SYSTEM =================
#include <Preferences.h>
#include <ArduinoJson.h>

Preferences param_prefs;
String paramJSON = "[]";
bool param_updated = false;

StaticJsonDocument<2048> param_doc;

void param_init() {
  param_prefs.begin("params", false);

  paramJSON = param_prefs.getString("params", "[]");

  if (deserializeJson(param_doc, paramJSON) || !param_doc.is<JsonArray>()) {
    paramJSON = "[]";
    param_prefs.putString("params", paramJSON);
    deserializeJson(param_doc, paramJSON);
  }
}

void param_save() {
  param_prefs.putString("params", paramJSON);
}

void param_sendAll() {
  Serial.println("START");
  Serial.println(paramJSON);
  Serial.println("END");
}

bool param_validate(JsonArray arr) {
  for (JsonObject obj : arr) {
    if (!obj.containsKey("n") ||
        !obj.containsKey("v") ||
        !obj.containsKey("u") ||
        !obj.containsKey("min") ||
        !obj.containsKey("max")) {
      return false;
    }

    float v = obj["v"];
    float mn = obj["min"];
    float mx = obj["max"];

    if (mn > mx) return false;
    if (v < mn || v > mx) return false;
  }
  return true;
}

void param_handle() {
  static String buffer = "";

  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {
      String cmd = buffer;
      buffer = "";
      cmd.trim();

      if (cmd == "GET") {
        param_sendAll();
      }
      else if (cmd.startsWith("SET_ALL|")) {
        String json = cmd.substring(8);

        StaticJsonDocument<2048> temp;

        if (deserializeJson(temp, json)) {
          Serial.println("ERR_JSON");
          return;
        }

        if (!temp.is<JsonArray>()) {
          Serial.println("ERR_FORMAT");
          return;
        }

        if (!param_validate(temp.as<JsonArray>())) {
          Serial.println("ERR_VALIDATION");
          return;
        }

        paramJSON = json;
        param_save();
        deserializeJson(param_doc, paramJSON);

        Serial.println("OK");
        param_updated = true;
      }
      else if (cmd == "CLEAR") {
        paramJSON = "[]";
        param_save();
        deserializeJson(param_doc, paramJSON);

        Serial.println("OK");
        param_updated = true;
      }
    } else {
      buffer += c;
    }
  }
}

float param_get(const char* name, float def = 0) {
  for (JsonObject obj : param_doc.as<JsonArray>()) {
    if (String((const char*)obj["n"]) == name) {
      return obj["v"];
    }
  }
  return def;
}

bool param_isUpdated() {
  if (param_updated) {
    param_updated = false;
    return true;
  }
  return false;
}
// =========================================================


// -------- OLED --------
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

// -------- CALIBRATION --------
int yaw_min, yaw_mid, yaw_max;
int thr_min, thr_max;
int roll_min, roll_mid, roll_max;
int pit_min, pit_mid, pit_max;

// -------- PWM --------
#define PWM_MIN 1050
#define PWM_MAX 1950
#define PWM_MID 1500
#define DEADZONE 20

void loadParamsToVars() {
  yaw_min = param_get("YAW_MIN", 262);
  yaw_mid = param_get("YAW_MID", 1815);
  yaw_max = param_get("YAW_MAX", 3626);

  thr_min = param_get("THROTTLE_MIN", 302);
  thr_max = param_get("THROTTLE_MAX", 3647);

  roll_min = param_get("ROLL_MIN", 410);
  roll_mid = param_get("ROLL_MID", 1940);
  roll_max = param_get("ROLL_MAX", 3835);

  pit_min = param_get("PITCH_MIN", 218);
  pit_mid = param_get("PITCH_MID", 1801);
  pit_max = param_get("PITCH_MAX", 3603);
}

// ---------- FUNCTIONS ----------
int smoothRead(int pin) {
  long sum = 0;
  for (int i = 0; i < 5; i++) sum += analogRead(pin);
  return sum / 5;
}

int mapCentered(int val, int minV, int midV, int maxV) {
  int out = (val < midV)
    ? map(val, minV, midV, PWM_MIN, PWM_MID)
    : map(val, midV, maxV, PWM_MID, PWM_MAX);

  if (abs(out - PWM_MID) < DEADZONE)
    out = PWM_MID;

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
  Serial.setRxBufferSize(2048);
  
  Serial.begin(115200);
  delay(500); // Give serial and power time to stabilize

  // 1. Initialize I2C FIRST
  I2C_1.begin(19, 18);
  I2C_2.begin(22, 21);
  delay(100); 

  // 2. Initialize Displays and SET TEXT CONFIG
  if(!display1.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 1 allocation failed"));
  }
  if(!display2.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 2 allocation failed"));
  }

  // Clear and set defaults
  display1.clearDisplay();
  display1.setTextSize(1);
  display1.setTextColor(SSD1306_WHITE);
  display1.display();

  display2.clearDisplay();
  display2.setTextSize(1);
  display2.setTextColor(SSD1306_WHITE);
  display2.display();

  // 3. Initialize Parameters
  param_init();
  loadParamsToVars();
  
  // Pin modes...
  pinMode(B1, INPUT_PULLUP);
  pinMode(B2, INPUT_PULLUP);
  pinMode(B3, INPUT_PULLUP);
  pinMode(B4, INPUT_PULLUP);
  pinMode(SW2, INPUT_PULLUP);
  pinMode(SWA1, INPUT_PULLUP);
  pinMode(SWA2, INPUT_PULLUP);
  pinMode(SWB, INPUT_PULLUP);
}

void loop() {
  param_handle();
  if (param_isUpdated()) {
    loadParamsToVars();
  }

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
  display1.setCursor(0, 0);
  display1.setTextSize(1);             // Ensure text size is set
  display1.setTextColor(SSD1306_WHITE); // Ensure color is set
  display1.println("CH1 Throttle: " + String(throttle));
  display1.println("CH2 Yaw     : " + String(yaw));
  display1.println("CH3 Roll    : " + String(roll));
  display1.println("CH4 Pitch   : " + String(pitch));
  display1.display();

  // ===== DISPLAY 2 =====
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