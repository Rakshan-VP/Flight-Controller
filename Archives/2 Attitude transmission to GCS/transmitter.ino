#include <Wire.h>
#include <SPI.h>
#include <RF24.h>
#include <math.h>

#define MPU_ADDR 0x68
#define MAG_ADDR 0x1E

// I2C buses for MPU and Magnetometer
TwoWire Wire1(PB7, PB6);   // SDA, SCL for MPU (PB7=SDA, PB6=SCL)
TwoWire Wire2(PB3, PB10);  // SDA, SCL for Mag (PB3=SDA, PB10=SCL)

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
  Serial.begin(115200);

  // Start both I2C buses
  Wire1.begin();
  Wire2.begin();

  // Initialize MPU6050 - wake it up
  Wire1.beginTransmission(MPU_ADDR);
  Wire1.write(0x6B);  // Power management register
  Wire1.write(0);
  Wire1.endTransmission();

  // Initialize magnetometer (HMC5883L) in continuous mode
  Wire2.beginTransmission(MAG_ADDR);
  Wire2.write(0x02); // Mode register
  Wire2.write(0x00); // Continuous measurement mode
  Wire2.endTransmission();

  // Initialize nRF24L01 radio
  radio.begin();
  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_LOW);
  radio.stopListening();  // Set radio as transmitter
}

void loop() {
  RPY rpy = computeRPY();

  RPYData dataToSend = {rpy.roll, rpy.pitch, rpy.yaw};
  bool ok = radio.write(&dataToSend, sizeof(dataToSend));

  Serial.print("Roll: "); Serial.print(rpy.roll);
  Serial.print(", Pitch: "); Serial.print(rpy.pitch);
  Serial.print(", Yaw: "); Serial.print(rpy.yaw);
  Serial.print(" | RF Send: ");
  Serial.println(ok ? "Success" : "Fail");

  delay(10);
}
