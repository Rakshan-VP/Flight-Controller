# IMU Calibration (ESP32 + MPU6050)
<img width="402" height="288" alt="image" src="https://github.com/user-attachments/assets/dbb5d79f-1dd9-4082-8d0d-1767e015b728" />

This module performs **IMU level calibration** for a drone using an **ESP32** and **MPU6050**.

The calibration procedure computes the **bias (offset) of roll and pitch** when the drone frame is physically level. These offsets are stored in **ESP32 flash memory** so they persist across power cycles.

A simple **PyQt5 desktop GUI** is included to trigger calibration and view stored offsets.

---

## Purpose

Even when a drone frame is perfectly level, the IMU often reports a small angle due to:

* Sensor manufacturing tolerances
* Board mounting misalignment
* Accelerometer bias

This calibration finds the **true level bias** so the flight controller can subtract it during operation.

```
correct_roll  = measured_roll  - roll_offset
correct_pitch = measured_pitch - pitch_offset
```

---

## System Overview

**Hardware**

* ESP32
* MPU6050 IMU
* WiFi connection (ESP32 SoftAP)

**Software**

* ESP32 firmware (Arduino framework)
* Python GUI using **PyQt5**
* TCP communication

```
Desktop GUI  <--WiFi TCP-->  ESP32  --> MPU6050
```

---

## Calibration Method

During calibration:

1. The drone is placed on a **perfectly level surface**
2. **1000 IMU samples** are collected
3. Accelerometer values are averaged
4. Axis mapping converts IMU axes to drone axes
5. Roll and pitch offsets are computed
6. Gyroscope bias is also measured
7. All values are saved to **ESP32 flash using Preferences**

### Axis Mapping

The IMU orientation may differ from the drone body frame.

Mapping used:

```
Drone X = IMU -Y
Drone Y = IMU  X
Drone Z = IMU  Z
```

### Roll Offset

```
roll_offset = atan2(ay, az)
```

### Pitch Offset

```
pitch_offset = atan2(-ax, sqrt(ay² + az²))
```

---

## Stored Calibration Values

The following parameters are stored in flash:

| Parameter | Description      |
| --------- | ---------------- |
| roll      | Roll angle bias  |
| pitch     | Pitch angle bias |
| gx        | Gyroscope X bias |
| gy        | Gyroscope Y bias |
| gz        | Gyroscope Z bias |
| cal       | Calibration flag |

---

## Communication Protocol

The ESP32 runs a **TCP server**.

**Port**

```
5000
```

### Commands

**Request status**

```
STATUS
```

**Start calibration**

```
CALIBRATE
```

### Response

```
STATUS,<calibrated>,<roll>,<pitch>,<gx>,<gy>,<gz>
```

Example

```
STATUS,1,-1.32,0.84,2.10,-0.33,0.11
```

---

## GUI

The included PyQt5 GUI allows you to:

* Connect to the ESP32
* Start calibration
* View calibration status
* Display stored offsets

### Controls

**Level Calibrate**

Starts the calibration routine on the ESP32.

**Status Display**

Shows:

* calibration state
* roll offset
* pitch offset
* gyro offsets

---

## Calibration Procedure

1. Power the ESP32
2. Connect your computer to WiFi:

```
SSID: DRONE_ESP
Password: 12345678
```

3. Launch the GUI
4. Press **Level Calibrate**
5. Keep the drone **completely still**
6. Calibration completes in ~3 seconds

Offsets are automatically saved.

---

## Why This Matters

Without level calibration:

* Drone may drift
* PID controller receives incorrect angles
* Hover becomes unstable

Proper bias removal significantly improves **attitude estimation accuracy**.

---

## Folder Contents

```
IMU Calibration/
│
├── mpu6050.ino     # ESP32 firmware
├── GUI.py        # PyQt5 GUI
└── README.md
```

---

## License

Open-source for educational and drone development purposes.
