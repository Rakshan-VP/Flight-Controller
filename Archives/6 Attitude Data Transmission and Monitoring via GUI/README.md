# Attitude Data Transmission and Monitoring via GUI

![Transciever](https://github.com/user-attachments/assets/4db8c453-5b46-430b-899f-d4f1960c4053)

This repo enables real-time transmission, visualization, and monitoring of drone **attitude (Roll, Pitch, Yaw)** data using RF communication between an **Arduino Nano-based Ground Control Station (GCS)** and an **STM32-based flight controller**, with a **PyQt5-based desktop GUI**.

---

## 🛠 Components

- **`fc.ino`** – Arduino Nano code for the **Flight Controller transmitter** (e.g., used in STM32 receiver side for testing).
- **`gcs.ino`** – Arduino Nano code for the **Ground Control Station** that:
  - Sends desired RPY to FC
  - Receives current and delta RPY back from FC
- **`Transciever_GUI.py`** – A PyQt5-based GUI to:
  - Send RPY commands using sliders
  - Display received current and delta RPY in real time
  - Show communication status (send/receive)
  - Serial port selector

---

## 📡 Communication

- **nRF24L01+** modules are used for wireless communication.
- RPY data is packed in a C-style struct and transmitted bi-directionally.
- Uses a simple `struct RPY { float roll; float pitch; float yaw; }` format.

---

## 🖥 GUI Features

- PyQt5 interface with sliders
- Serial port auto-refresh and connect/disconnect
- Sliders to set desired Roll, Pitch, Yaw (±90°)
- Displays:
  - ✅ Desired RPY
  - ✅ Current RPY from FC
  - ✅ Δ (delta) RPY
  - ✅ Communication status indicators

---

## 🔧 Requirements

### 🧠 Microcontrollers
- Arduino Nano (for GCS)
- STM32 (recommended: STM32F103C8T6 aka "Blue Pill") with Arduino Core

### 📦 Python Libraries
Install with:
```bash
pip install pyqt5 pyserial
```
---

## 📈 Serial Output (STM32)
STM32 prints the received desired RPY via Serial:
```
Received → Roll: -15.00 | Pitch: 20.00 | Yaw: 5.00
```
Use Arduino Serial Monitor, PuTTY, or similar tools at 115200 baud.

---

## 🧪 Getting Started
- Flash gcs.ino to Arduino Nano (connected to your PC).
- Flash fc.ino to another Nano or STM32.
- Connect nRF24L01 modules accordingly.
- Run Transciever_GUI.py:
```
python Transciever_GUI.py
```
- Select the correct COM port of GCS and hit Start.
- Move the sliders and observe serial + GUI feedback.






