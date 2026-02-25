#include <WiFi.h>
#include <Preferences.h>
#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;
Preferences prefs;

const char* ssid = "DRONE_ESP";
const char* password = "12345678";

WiFiServer server(5000);
WiFiClient client;

float ax_off=0, ay_off=0, az_off=0;
float gx_off=0, gy_off=0, gz_off=0;

bool calibrated = false;

void setup() {
  Serial.begin(115200);
  Wire.begin(21,22);

  mpu.initialize();

  prefs.begin("drone", false);

  ax_off = prefs.getFloat("ax",0);
  ay_off = prefs.getFloat("ay",0);
  az_off = prefs.getFloat("az",0);
  gx_off = prefs.getFloat("gx",0);
  gy_off = prefs.getFloat("gy",0);
  gz_off = prefs.getFloat("gz",0);
  calibrated = prefs.getBool("cal", false);

  WiFi.softAP(ssid, password);
  server.begin();
}

void calibrateSensors() {

  const int samples = 1000;

  long ax_sum=0, ay_sum=0, az_sum=0;
  long gx_sum=0, gy_sum=0, gz_sum=0;

  for(int i=0;i<samples;i++){
    int16_t ax, ay, az, gx, gy, gz;
    mpu.getMotion6(&ax,&ay,&az,&gx,&gy,&gz);

    ax_sum += ax;
    ay_sum += ay;
    az_sum += az;
    gx_sum += gx;
    gy_sum += gy;
    gz_sum += gz;

    delay(3);
  }

  ax_off = ax_sum / samples;
  ay_off = ay_sum / samples;
  az_off = (az_sum / samples) - 16384; // remove gravity
  gx_off = gx_sum / samples;
  gy_off = gy_sum / samples;
  gz_off = gz_sum / samples;

  prefs.putFloat("ax", ax_off);
  prefs.putFloat("ay", ay_off);
  prefs.putFloat("az", az_off);
  prefs.putFloat("gx", gx_off);
  prefs.putFloat("gy", gy_off);
  prefs.putFloat("gz", gz_off);
  prefs.putBool("cal", true);

  calibrated = true;
}

void sendStatus(){
  client.print("STATUS,");
  client.print(calibrated ? "1" : "0");
  client.print(",");
  client.print(ax_off); client.print(",");
  client.print(ay_off); client.print(",");
  client.print(az_off); client.print(",");
  client.print(gx_off); client.print(",");
  client.print(gy_off); client.print(",");
  client.println(gz_off);
}

void loop() {

  if (!client || !client.connected()) {
    client = server.available();
    return;
  }

  // Handle commands
  while (client.available()) {
    String cmd = client.readStringUntil('\n');
    cmd.trim();

    if (cmd == "CALIBRATE") {
      calibrateSensors();
      sendStatus();
    }

    if (cmd == "STATUS") {
      sendStatus();
    }
  }
}