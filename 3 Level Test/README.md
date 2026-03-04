# Level Test

This module is used to perform **1-DOF level testing and PID tuning** for the ESP32 drone using an **MPU6050 IMU** and a **Python GUI**.  
It allows testing **Roll and Pitch stabilization independently** while logging telemetry for analysis.

---

## Overview

The level test setup consists of two main components:

- **ESP32 Firmware (`level.ino`)**
- **Desktop GUI (`GUI.py`)**
- **Log Analysis Script (`logplotting.py`)**

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

---

## Log Plotting Script

The folder also includes **`logplotting.py`**, a small analysis script used to visualize the recorded telemetry logs.

This script reads a generated CSV log file and produces three plots:

1. **Roll and Pitch vs Time**
2. **Roll Error and Pitch Error vs Time**
3. **Motor PWM outputs (M1–M4) vs Time**

These plots help evaluate:

- stabilization performance
- PID response behavior
- motor correction activity during tests

### Running the Script

Update the file path if necessary and run:

```bash
python logplotting.py
```

Required libraries:

```bash
pip install pandas matplotlib
```

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

The following plot shows the response obtained during roll stabilization testing using:

```
Kp = 2.0
Ki = 0.05
Kd = 0.6
```

![roll](https://github.com/user-attachments/assets/658ec922-5a41-4d7e-be5e-f0418ec3342c)

All experiment data and corresponding plots are stored in the **Roll Test Results** folder.

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

### Results

The following plot shows the response obtained during pitch stabilization testing using:

```
Kp = 2.2
Ki = 0.05
Kd = 0.5
```

![pitch](https://github.com/user-attachments/assets/8daac9c7-aaf1-4f43-8ab0-a3de3e4a541f)

All experiment data and corresponding plots are stored in the **Pitch Test Results** folder.

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
