# Communication Protocol

## Overview

This system uses a **centralized communication architecture** where the **Drone (ESP32)** acts as a WiFi Access Point (SoftAP), and both the **Transmitter (ESP32)** and **GCS (Laptop)** connect as clients.

- **Drone IP:** `192.168.4.1`
- **Protocol:** UDP
- **Ports:**
  - `8000` → Transmitter ↔ Drone
  - `9000` → Drone → GCS
  - `9001` → GCS → Drone

---

## Architecture

<p align="center">
  <img width="461" height="181" alt="Connections" src="https://github.com/user-attachments/assets/718cc696-45b1-4028-8854-cf742d138960" />
</p>

- Drone runs in **WiFi SoftAP mode**
- Transmitter and GCS connect to the drone network
- Drone acts as the **central communication hub**

---

## Communication Flow

<p align="center">
  <img width="621" height="101" alt="one" src="https://github.com/user-attachments/assets/45e0219f-f749-417a-a4bb-1803fcf11bcf" />
</p>

### 1. Transmitter → Drone (Port 8000)

Sends real-time control inputs:

```
[ch1, ch2, ch3, ch4, ch5, ch6, ch7]
```

- `ch1–ch4` → analog controls (throttle, roll, pitch, yaw)
- `ch5–ch7` → switches / modes

---

### 2. Drone → Transmitter (Port 8000)

Sends basic telemetry for display:

```
[ack, armed, mode, roll, pitch, yaw, baro_alt, gps_alt, x, y, temp]
```

Used for:
- status display
- basic flight feedback

---

<p align="center">
  <img width="811" height="121" alt="two" src="https://github.com/user-attachments/assets/c044844a-9832-4937-bd5d-0d298d675220" />
</p>

### 3. Drone → GCS (Port 9001)

Sends full telemetry:

```
[ack, armed, mode, roll, pitch, yaw, baro_alt, gps_alt, x, y, gps_fix, sats, hdop, temp, m1, m2, m3, m4]
```

Includes:
- attitude (roll, pitch, yaw)
- altitude and position (baro_alt, gps_alt, x, y)
- GPS quality (gps_fix, satellites, hdop)
- motor outputs (m1–m4)

---

### 4. GCS → Drone (Port 9000)

Sends high-level commands:

```
HIGH LEVEL / SCRIPT BASED COMMANDS
```

Examples:
- flight mode changes
- mission commands
- parameter updates

---

## Design Notes

- Drone is the **central node**
- Communication uses **fixed-size structured data**
- No complex protocol → **low latency**
- Clear separation:
  - Transmitter → control inputs
  - GCS → monitoring + commands

---

## Summary

- WiFi SoftAP based system  
- UDP communication with dedicated ports  
- Lightweight and real-time  
- Scalable and easy to extend  

---
