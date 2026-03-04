# Testing Components

This repository contains test scripts for verifying individual components used in a drone system. The **STM32** acts as the **Flight Controller (FC)** and the **Arduino Nano** is used as the **Ground Control Station (GCS)**. Components tested include sensors (IMU and magnetometer), PWM outputs, and wireless communication via nRF24L01 modules.

---

## 📁 Files Overview

### 🔧 Sensor Tests (STM32 FC)
- **`imu.ino`**  
  Reads and prints accelerometer and gyroscope data from the MPU6050 sensor.

- **`magnetometer.ino`**  
  Reads and prints magnetic field data from the HMC5883L sensor.

### ⚙️ PWM Output Test (STM32 FC)
- **`pwm_pins.ino`**  
  Outputs PWM signals on 6 pins to test servos by sweeping angles from 0° to 180° and back.

### 📡 Communication Test (STM32 ↔ Arduino Nano)
- **`communication/transmitter.ino`** *(STM32 FC)*  
  Sends test messages wirelessly using the nRF24L01 module.

- **`communication/receiver.ino`** *(Arduino Nano GCS)*  
  Receives and displays messages from the STM32 using another nRF24L01 module.

---

## ✅ How to Use

### 1. **IMU Test (`imu.ino`)**
- Upload to STM32.
- Connect MPU6050 via I2C (default: SDA = PB7, SCL = PB6).
- Open Serial Monitor at **115200 baud**.
- **Output:**
```
a/g: ax ay az gx gy gz
```

### 2. **Magnetometer Test (`magnetometer.ino`)**
- Upload to STM32.
- Connect HMC5883L via I2C (SDA = PB3, SCL = PB10).
- Open Serial Monitor at **115200 baud**.
- **Output:**
```
Mag X: __ μT, Y: __ μT, Z: __ μT
```

### 3. **PWM Output Test (`pwm_pins.ino`)**
- Upload to STM32.
- Connect servos to PB13, PB14, PB15, PA8, PA9, PA10.
- Open Serial Monitor at **115200 baud**.
- **Output:**
```
Angle: 0 → 180 → 0 (looping)
```

### 4. **Wireless Communication Test**
#### STM32 (Transmitter) → Arduino Nano (Receiver)
- Upload `transmitter.ino` to STM32.
- Upload `receiver.ino` to Arduino Nano.
- Connect nRF24L01 to both boards (use 3.3V regulated power).
- Open Serial Monitor on both at **9600 baud**.
- **Transmitter Output:**
```
Hello World 0
Hello World 1
```
- **Receiver Output:**
```
Received: Hello World 0
Received: Hello World 1
```
---

## 🛠️ Notes

- Make sure to power the nRF24L01 with **3.3V** (not 5V directly).
- Use a **level shifter** or **external 3.3V regulator** if needed.
- Confirm pin mappings match your board (especially for I2C and SPI).
- You can use **STM32CubeProgrammer** or **Arduino IDE (STM32 core)** for uploading to STM32.

---
