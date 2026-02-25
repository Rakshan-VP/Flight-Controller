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

// Angle offsets
float roll_off = 0;
float pitch_off = 0;

// Gyro offsets
float gx_off=0, gy_off=0, gz_off=0;

bool calibrated = false;

void setup() {
  Serial.begin(115200);
  Wire.begin(21,22);

  mpu.initialize();

  prefs.begin("drone", false);

  // Load saved values
  roll_off  = prefs.getFloat("roll",0);
  pitch_off = prefs.getFloat("pitch",0);
  gx_off = prefs.getFloat("gx",0);
  gy_off = prefs.getFloat("gy",0);
  gz_off = prefs.getFloat("gz",0);
  calibrated = prefs.getBool("cal", false);

  WiFi.softAP(ssid, password);
  server.begin();
}

// ----------------------------------------------------

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

  // Averages
  float ax_avg = ax_sum / samples;
  float ay_avg = ay_sum / samples;
  float az_avg = az_sum / samples;

  // -------- Axis Mapping --------
  // Drone X = IMU -Y
  // Drone Y = IMU X

  float drone_ax = -ay_avg;
  float drone_ay = ax_avg;
  float drone_az = az_avg;

  // -------- Compute Angle Offsets --------
  roll_off  = atan2(drone_ay, drone_az) * 180.0 / PI;
  pitch_off = atan2(-drone_ax, 
                    sqrt(drone_ay*drone_ay + drone_az*drone_az)) 
                    * 180.0 / PI;

  // -------- Gyro offsets (unchanged) --------
  gx_off = gx_sum / samples;
  gy_off = gy_sum / samples;
  gz_off = gz_sum / samples;

  // Save to flash
  prefs.putFloat("roll", roll_off);
  prefs.putFloat("pitch", pitch_off);
  prefs.putFloat("gx", gx_off);
  prefs.putFloat("gy", gy_off);
  prefs.putFloat("gz", gz_off);
  prefs.putBool("cal", true);

  calibrated = true;
}

// ----------------------------------------------------

void sendStatus(){
  client.print("STATUS,");
  client.print(calibrated ? "1" : "0");
  client.print(",");
  client.print(roll_off); client.print(",");
  client.print(pitch_off); client.print(",");
  client.print(gx_off); client.print(",");
  client.print(gy_off); client.print(",");
  client.println(gz_off);
}

// ----------------------------------------------------

void loop() {

  if (!client || !client.connected()) {
    client = server.available();
    return;
  }

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