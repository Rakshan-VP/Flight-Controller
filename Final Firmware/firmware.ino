// ============================================================
// ======================== LIBRARIES ==========================
// ============================================================

#include <Wire.h>              // I2C (MPU6050, HMC5883L, BMP280)
#include <WiFi.h>              // ESP32 WiFi
#include <FastLED.h>           // WS2811 LED

#include <MPU6050.h>           // MPU6050 → Accelerometer + Gyroscope
#include <HMC5883L.h>          // HMC5883L → Magnetometer (Compass)
#include <Adafruit_BMP280.h>   // BMP280 → Pressure + Temperature (Altitude)
#include <Adafruit_Sensor.h>   // Required for BMP280

#include <TinyGPS++.h>         // NEO-6M → GPS parsing
#include <HardwareSerial.h>    // UART for GPS


// ============================================================
// ======================== CONNECTIONS ========================
// ============================================================


// -------- I2C BUS (Shared) --------
// MPU6050 + HMC5883L + BMP280
#define I2C_SDA 21
#define I2C_SCL 22


// -------- GPS (UART2) --------
// NEO-6M GPS Module
#define GPS_RX 16    // ESP32 RX2  ← GPS TX
#define GPS_TX 17    // ESP32 TX2  → GPS RX


// -------- MOTOR OUTPUTS (ESC PWM) --------
#define M1 25   // Front Right  (FR)
#define M2 26   // Back Right   (BR)
#define M3 32   // Front Left   (FL)
#define M4 33   // Back Left    (BL)


// -------- LED (STATUS) --------
// WS2811 Single LED
#define LED_PIN       23
#define NUM_LEDS      1
#define LED_TYPE      WS2811
#define COLOR_ORDER   GRB
#define BRIGHTNESS    120

CRGB leds[NUM_LEDS];


// -------- WIFI (GROUND LINK) --------
#define WIFI_SSID     "DRONE_ESP"
#define WIFI_PASS     "12345678"
#define WIFI_PORT     5000

WiFiServer server(WIFI_PORT);
WiFiClient client;

