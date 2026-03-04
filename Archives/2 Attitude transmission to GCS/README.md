# Attitude Transmission to GCS

This repo demonstrates how to read attitude (Roll, Pitch, Yaw) from an IMU and magnetometer using an STM32 microcontroller and transmit it wirelessly to a Ground Control Station (GCS) via nRF24L01+ modules.

## Overview

- Reads data from **MPU6050** (accelerometer + gyroscope) and **HMC5883L** (magnetometer).
- Calculates Roll, Pitch, and Yaw using a complementary filter.
- Sends the computed RPY values via **nRF24L01+**.
- A receiver (e.g., Arduino) prints the received RPY data to the Serial Monitor.

---

## Transmitter (STM32)

### Connections

<table>
<tr>
<td>


| Sensor / Module    | STM32 Pin     |
|--------------------|---------------|
| MPU6050 SDA/SCL    | PB7 / PB6     |
| HMC5883L SDA/SCL   | PB3 / PB10    |
| nRF24L01 CE/CSN    | PB0 / PA4     |

</td>
<td>

<img src="https://github.com/user-attachments/assets/42d3f858-76c1-4223-a5ae-192a9d05cda3" alt="Wiring Diagram" width="250"/>

</td>
</tr>
</table>

### How it works

- Initializes I2C communication on two buses.
- Reads sensor data and applies a complementary filter to estimate RPY.
- Transmits RPY data using RF24.

### Upload

Upload the `transmitter.ino` to STM32 using STM32CubeIDE or Arduino with STM32 board support.

---

## Receiver (Arduino)

### Connections

| nRF24L01 Pin | Arduino Pin |
|--------------|-------------|
| CE           | 6           |
| CSN          | 7           |

### How it works

- Listens for incoming RPY data.
- Prints Roll, Pitch, and Yaw to the Serial Monitor.

### Upload

Upload `receiver.ino` to your Arduino and open the Serial Monitor at **115200 baud**.

---

## Usage

1. Connect and power all modules properly.
2. Upload the respective codes to STM32 and Arduino.
3. Open the Serial Monitor on the Arduino side.
4. Observe real-time attitude values being received and displayed.

---

## Dependencies

- RF24 Library (for both STM32 and Arduino)
- Wire library (I2C communication)
- Math functions (for angle calculations)

---

## Notes

- Make sure both transmitter and receiver share the same RF24 address (`"node1"`).
- Use decoupling capacitors for nRF24L01+ if needed for stable operation.
- Orientation accuracy depends on sensor calibration and placement.

---




