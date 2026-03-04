#include <Wire.h>
#include <SPI.h>
#include <RF24.h>
#include <math.h>

#define MPU_ADDR 0x68
#define MAG_ADDR 0x1E

// I2C buses for MPU and Magnetometer
TwoWire Wire1(PB7, PB6);   // SDA, SCL for MPU
TwoWire Wire2(PB3, PB10);  // SDA, SCL for Mag

// nRF24L01 CE and CSN pins
#define CE_PIN PB0
#define CSN_PIN PA4

// Create RF24 radio object
RF24 radio(CE_PIN, CSN_PIN);

// Address to send data to
const byte address[6] = "node1";

struct RPY {
  float roll;
  float pitch;
  float yaw;
};

struct RPYData {
  float roll;
  float pitch;
  float yaw;
};

// Offsets for gyro and accel
int16_t gyro_x_offset = 0;
int16_t gyro_y_offset = 0;
int16_t gyro_z_offset = 0;
int16_t accel_x_offset = 0;
int16_t accel_y_offset = 0;
int16_t accel_z_offset = 0;

// Read MPU6050 data from Wire1 bus
void readMPU6050(int16_t* ax, int16_t* ay, int16_t* az, int16_t* gx, int16_t* gy, int16_t* gz) {
  Wire1.beginTransmission(MPU_ADDR);
  Wire1.write(0x3B);
  Wire1.endTransmission(false);
  Wire1.requestFrom(MPU_ADDR, 14, true);

  *ax = Wire1.read() << 8 | Wire1.read();
  *ay = Wire1.read() << 8 | Wire1.read();
  *az = Wire1.read() << 8 | Wire1.read();

  Wire1.read(); Wire1.read();  // skip temperature

  *gx = Wire1.read() << 8 | Wire1.read();
  *gy = Wire1.read() << 8 | Wire1.read();
  *gz = Wire1.read() << 8 | Wire1.read();

  // Apply offsets
  *gx -= gyro_x_offset;
  *gy -= gyro_y_offset;
  *gz -= gyro_z_offset;

  *ax -= accel_x_offset;
  *ay -= accel_y_offset;
  *az -= accel_z_offset;
}

// Read magnetometer data from Wire2 bus
void readMag(int16_t* mx, int16_t* my, int16_t* mz) {
  Wire2.beginTransmission(MAG_ADDR);
  Wire2.write(0x03);
  Wire2.endTransmission(false);
  Wire2.requestFrom(MAG_ADDR, 6, true);

  *mx = Wire2.read() << 8 | Wire2.read();
  *mz = Wire2.read() << 8 | Wire2.read();
  *my = Wire2.read() << 8 | Wire2.read();
}

// Calibration routine for gyro and accel
void calibrateIMU() {
  const int samples = 2000;
  long gx_sum = 0, gy_sum = 0, gz_sum = 0;
  long ax_sum = 0, ay_sum = 0, az_sum = 0;

  int16_t ax, ay, az, gx, gy, gz;

  for (int i = 0; i < samples; i++) {
    readMPU6050(&ax, &ay, &az, &gx, &gy, &gz);
    gx_sum += gx;
    gy_sum += gy;
    gz_sum += gz;
    ax_sum += ax;
    ay_sum += ay;
    az_sum += az;
    delay(3);  // Small delay between samples
  }

  gyro_x_offset = gx_sum / samples;
  gyro_y_offset = gy_sum / samples;
  gyro_z_offset = gz_sum / samples;

  accel_x_offset = ax_sum / samples;
  accel_y_offset = ay_sum / samples;
  accel_z_offset = (az_sum / samples) - 16384;  // Subtract gravity offset from accel Z
}

RPY computeRPY() {
  static float roll = 0.0, pitch = 0.0, yaw = 0.0;
  const float alpha = 0.5;
  const float dt = 0.01;

  int16_t ax_raw, ay_raw, az_raw;
  int16_t gx_raw, gy_raw, gz_raw;
  int16_t mx_raw, my_raw, mz_raw;

  readMPU6050(&ax_raw, &ay_raw, &az_raw, &gx_raw, &gy_raw, &gz_raw);
  readMag(&mx_raw, &my_raw, &mz_raw);

  // Normalize accelerometer
  float axf = ax_raw / 16384.0;
  float ayf = ay_raw / 16384.0;
  float azf = az_raw / 16384.0;

  float x_acc = -ayf;
  float y_acc = axf;
  float z_acc = azf;

  float roll_acc = atan2(y_acc, z_acc) * 180.0 / M_PI;
  float pitch_acc = atan2(-x_acc, sqrt(y_acc * y_acc + z_acc * z_acc)) * 180.0 / M_PI;

  // Gyro scale ±2000 dps → 16.4 LSB/deg/s
  float gx_deg = -gy_raw / 16.4;
  float gy_deg =  gx_raw / 16.4;
  float gz_deg =  gz_raw / 16.4;

  roll  = alpha * (roll  + gx_deg * dt) + (1.0 - alpha) * roll_acc;
  pitch = alpha * (pitch + gy_deg * dt) + (1.0 - alpha) * pitch_acc;

  // Magnetometer raw data, axis mapping
  float mag_x = -mx_raw;
  float mag_y = -my_raw;
  float mag_z = mz_raw;

  // Convert roll and pitch to radians for compensation
  float roll_rad = roll * M_PI / 180.0;
  float pitch_rad = pitch * M_PI / 180.0;

  // Tilt compensated magnetic sensor measurements
  float Xh = mag_x * cos(pitch_rad) + mag_y * sin(roll_rad) * sin(pitch_rad) + mag_z * cos(roll_rad) * sin(pitch_rad);
  float Yh = mag_y * cos(roll_rad) - mag_z * sin(roll_rad);

  // Compute compensated yaw angle
  float yaw_mag = atan2(Yh, Xh) * 180.0 / M_PI;

  if (yaw_mag > 180) yaw_mag -= 360;
  else if (yaw_mag < -180) yaw_mag += 360;

  // Complementary filter for yaw with gyro integration
  yaw = alpha * (yaw + gz_deg * dt) + (1.0 - alpha) * yaw_mag;

  if (yaw > 180) yaw -= 360;
  else if (yaw < -180) yaw += 360;

  return {roll, pitch, yaw};
}

void setup() {
  Serial.begin(115200);  // Added serial for calibration messages

  Wire1.begin();
  Wire2.begin();

  // Wake MPU6050
  Wire1.beginTransmission(MPU_ADDR);
  Wire1.write(0x6B);
  Wire1.write(0);
  Wire1.endTransmission();

  // Magnetometer continuous mode
  Wire2.beginTransmission(MAG_ADDR);
  Wire2.write(0x02);
  Wire2.write(0x00);
  Wire2.endTransmission();

  Serial.println("Calibrating IMU... Please keep device still.");
  calibrateIMU();
  Serial.println("Calibration done.");

  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_LOW);
  radio.stopListening();
}

void loop() {
  RPY rpy = computeRPY();

  RPYData dataToSend = {rpy.roll, rpy.pitch, rpy.yaw};
  radio.write(&dataToSend, sizeof(dataToSend));

  delay(10);
}