# Level Test

This module is used to perform **1-DOF level testing and PID tuning** for the ESP32 drone using an **MPU6050 IMU** and a **Python GUI**.  
It allows testing **Roll and Pitch stabilization independently** while logging telemetry for analysis.

---

## Overview

The level test setup consists of two main components:

- **ESP32 Firmware (`level.ino`)**
- **Desktop GUI (`GUI.py`)**

The ESP32 performs IMU processing and motor control while the GUI sends PID parameters, visualizes telemetry, and logs data.

---

## level.ino

`level.ino` runs on the **ESP32 flight controller**.

### What it does
- Initializes **MPU6050**
- Reads **accelerometer and gyroscope data**
- Computes **roll and pitch angles**
- Runs **PID stabilization for Roll or Pitch**
- Controls **motor PWM outputs**
- Sends **real-time telemetry** to the GUI over WiFi

### Why some MPU functions are in `setup()`

Certain MPU configuration functions are placed in `setup()` to ensure the sensor starts in a **stable state before control begins**.

This prevents:
- sudden angle spikes
- unstable startup readings
- jumping values during the first few seconds

The IMU is configured once and then used continuously during the loop.

---

## GUI

The Python GUI is used to **run tests and visualize drone behavior in real time**.

Features:
- Connects to ESP32 via **WiFi TCP**
- Start / Stop **Roll or Pitch tests**
- Enter **PID gains (Kp, Ki, Kd)**
- Set **base motor PWM**
- Live plotting of:
  - Roll angle
  - Pitch angle
  - Motor outputs
- Automatic **CSV logging of telemetry**

Telemetry includes:
- roll
- pitch
- motor PWM values
- raw IMU data
- processed drone frame IMU data

See implementation: :contentReference[oaicite:0]{index=0}

---

## How to Execute

### 1. Upload Firmware
Upload `level.ino` to the ESP32.

The ESP32 creates a WiFi access point.

```
SSID: DRONE_ESP
Password: 12345678
```

---

### 2. Connect PC to Drone WiFi

Connect your computer to:

```
DRONE_ESP
```

---

### 3. Run the GUI

Install dependencies:

```
pip install pyqt5 pyqtgraph
```

Run:

```
python GUI.py
```

---

## Roll Test

The roll test evaluates **roll axis stabilization**.

Procedure:

1. Enter **Roll PID values**
2. Set **Base PWM**
3. Click **Start (Roll Test)**

The ESP32 will:
- stabilize roll angle
- send telemetry
- adjust **left vs right motors**

Observe:
- roll response
- oscillations
- motor correction behavior

All data is logged for analysis.

### Results
Kp = 2.0 Ki =0.1  Kd = 0.6
![roll](https://github.com/user-attachments/assets/a5d2cd71-7a6a-4dca-bf2c-2b53487e536a)

<img width="1536" height="807" alt="plot1" src="https://github.com/user-attachments/assets/a29d3056-557e-4057-b06a-2719bc8881d3" />

<img width="1536" height="807" alt="plot2" src="https://github.com/user-attachments/assets/b11cd145-7e94-4ee0-847f-0ceb53dd0d49" />

---

## Pitch Test

The pitch test evaluates **pitch axis stabilization**.

Procedure:

1. Enter **Pitch PID values**
2. Set **Base PWM**
3. Click **Start (Pitch Test)**

The ESP32 will:
- stabilize pitch angle
- adjust **front vs rear motors**

Observe:
- pitch stability
- response speed
- overshoot and oscillations

Telemetry is also recorded in the log file.

---

## Logs

All test runs are automatically stored as **CSV files**.

```
Level Test/log/
```

Each file contains:

- time
- roll
- pitch
- motor outputs
- raw IMU data
- processed IMU data

These logs can be used for:
- PID tuning
- control analysis
- plotting in MATLAB / Python.

---

## Purpose

This module helps with:

- PID tuning
- IMU validation
- motor response testing
- debugging control algorithms

before performing **full flight tests**.
