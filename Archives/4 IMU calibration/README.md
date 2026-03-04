# 🔧 IMU Calibration

Before reliable roll, pitch, and yaw (RPY) values can be computed, the inertial sensors (MPU6050 accelerometer and gyroscope) must be calibrated.

---

## 🧪 What Is Calibrated?
- **Gyroscope Offsets:** Drift from zero when the sensor is still.
- **Accelerometer Offsets:** Especially the Z-axis, which measures gravity (~1g or 16384 in raw units).

### ⚙️ Calibration Routine

The function `calibrateIMU()` runs at startup:
```
const int samples = 2000;
```
It collects 2000 samples of raw accelerometer and gyroscope data.

Averages are computed for:
```
gx, gy, gz → Gyroscope offsets

ax, ay, az → Accelerometer offsets
```
Z-axis accelerometer offset is adjusted by subtracting 16384 (which corresponds to gravity).
```
accel_z_offset = (az_sum / samples) - 16384;
```
This ensures that the pitch and roll calculations based on gravity are accurate.

---

## 📌 Important Notes
Do not move the board during calibration!

Calibration takes ~6 seconds (2000 samples × 3 ms delay).

Offsets are applied on every IMU reading automatically.

---

## 🖥️ Serial Output
During calibration, messages are printed to the serial monitor:

```bash
Calibrating IMU... Please keep device still.
Calibration done.
```
This confirms when it is safe to begin using the RPY values.
