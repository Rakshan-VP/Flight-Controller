# Complementary Filter
![comp](https://github.com/user-attachments/assets/e3ab18e7-9403-4531-9f69-400684c896e2)

This module streams **real-time roll and pitch angles** from an **MPU6050 IMU** using an **ESP32** over WiFi to a **PyQt5 desktop GUI**.

The GUI plots the angles live to help test **IMU orientation, filtering, and frame alignment** before implementing drone flight control.

---

## System Overview

**Hardware**

- ESP32
- MPU6050 IMU
- PC running Python GUI

**Software**

- ESP32 firmware (Arduino)
- Python GUI (PyQt5 + PyQtGraph)
- WiFi TCP communication

```
Desktop GUI <--WiFi TCP--> ESP32 --> MPU6050
```

---

## WiFi Connection

ESP32 runs as a **WiFi Access Point**.

```
SSID: DRONE_ESP
Password: 12345678
IP: 192.168.4.1
Port: 5000
```

---

## Telemetry Format

ESP32 streams angles as CSV:

```
roll,pitch
```

Example:

```
-0.23,1.14
-0.21,1.09
-0.18,1.02
```

Streaming rate: **100 Hz**

---

## Sensor Fusion

Roll and pitch are computed using a **Complementary Filter** combining gyro and accelerometer data.

```
angle = α(angle + gyro * dt) + (1 - α)(acc_angle)
```

Where

```
α = 0.98
dt = 1 / IMU_frequency
```

This gives **fast response (gyro)** with **long-term stability (accelerometer)**.

---

## Angle Computation

**Roll**

```
roll = atan2(accY, accZ)
```

**Pitch**

```
pitch = atan2(-accX, sqrt(accY² + accZ²))
```

Angles are converted to degrees.

---

## Axis Mapping

IMU axes are remapped to the drone frame:

```
Drone X = -IMU Y
Drone Y = IMU X
Drone Z = IMU Z
```

---

## Offset Correction

Small mounting errors are corrected using calibration offsets.

```
correct_roll = roll - roll_offset
correct_pitch = pitch - pitch_offset
```

Example offsets

```
roll_offset = 2.65°
pitch_offset = -0.05°
```

---

## Data Rates

| Process | Frequency |
|-------|--------|
IMU update | 250 Hz |
Telemetry | 100 Hz |

---

## Running the System

1. Flash the ESP32 firmware
2. Connect PC to WiFi

```
DRONE_ESP
```

3. Run the GUI

```
python GUI.py
```

4. Press **Start Plotting**

Roll and pitch will appear in real time.

---

## Project Structure

```
Complementary Filter/
│
├── comp.ino
├── GUI.py
└── README.md
```

---

## Purpose

This tool helps verify:

- IMU orientation
- complementary filter performance
- frame alignment
- sensor stability before PID control

---

## License

Open source for **drone research and educational use**.
