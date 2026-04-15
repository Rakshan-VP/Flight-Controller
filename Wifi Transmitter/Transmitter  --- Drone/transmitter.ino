#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// -------- Pin Mapping (Pwm_mapping.ino) --------
#define P1 32 // Yaw
#define P2 33 // Throttle
#define P3 34 // Roll
#define P4 35 // Pitch
#define SW2 4
#define SWA1 25
#define SWA2 26
#define SWB 15

TwoWire I2C_1 = TwoWire(0);
TwoWire I2C_2 = TwoWire(1);
Adafruit_SSD1306 d1(128, 64, &I2C_1, -1);
Adafruit_SSD1306 d2(128, 64, &I2C_2, -1);

WiFiClient client;
const char* host = "192.168.4.1";

void setup() {
  Serial.begin(115200);
  I2C_1.begin(19, 18); I2C_2.begin(22, 21);
  d1.begin(SSD1306_SWITCHCAPVCC, 0x3C); d2.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  
  pinMode(SW2, INPUT_PULLUP);
  pinMode(SWA1, INPUT_PULLUP);
  pinMode(SWA2, INPUT_PULLUP);
  pinMode(SWB, INPUT_PULLUP);

  WiFi.begin("DRONE_ESP", "12345678");
}

void loop() {
  if (!client.connected()) {
    client.connect(host, 8000);
    d1.clearDisplay();
    d1.setCursor(0,0); d1.setTextColor(1);
    d1.println("SEARCHING DRONE...");
    d1.display();
    delay(500);
    return;
  }

  // --- Read Raw Inputs ---
  int c1 = analogRead(P2); // Throttle
  int c2 = analogRead(P1); // Yaw
  int c3 = analogRead(P3); // Roll
  int c4 = analogRead(P4); // Pitch
  
  int ch5 = digitalRead(SW2) ? 1 : 2;
  int ch6 = (!digitalRead(SWA1) && digitalRead(SWA2)) ? 1 : (digitalRead(SWA1) && !digitalRead(SWA2) ? 3 : 2);
  int ch7 = digitalRead(SWB) ? 1 : 2; // Arm Switch

  // --- Send Data Packet ---
  client.printf("[%d,%d,%d,%d,%d,%d,%d]\n", c1, c2, c3, c4, ch5, ch6, ch7);

  // --- Receive and Split Telemetry ---
  if (client.available()) {
    String data = client.readStringUntil('\n');
    
    // Display 1: Status and Angles
    d1.clearDisplay();
    d1.setCursor(0,0); d1.setTextColor(1);
    d1.println("STATUS: CONNECTED");
    d1.println("---------------------");
    d1.printf("Mode: %d | Arm: %d\n", ch5, (data.indexOf(",1,") != -1));
    d1.display();

    // Display 2: Motor PWMs
    d2.clearDisplay();
    d2.setCursor(0,0); d2.setTextColor(1);
    d2.println("MOTOR TELEMETRY");
    d2.println(data.substring(data.lastIndexOf(",") - 20)); // Show M1-M4
    d2.display();
  }
  delay(100);
}