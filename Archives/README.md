# 🛩️ STM32 Flight Controller – GUI-Controlled Drone via PC (Arduino IDE, Windows)

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
[![Issues](https://img.shields.io/github/issues/Rakshan-VP/STM32-Flight-Controller)](https://github.com/Rakshan-VP/STM32-Flight-Controller/issues)
[![Last Commit](https://img.shields.io/github/last-commit/Rakshan-VP/STM32-Flight-Controller)](https://github.com/Rakshan-VP/STM32-Flight-Controller/commits/main)


A full-featured development project to create a **graphical user interface (GUI)** for controlling a drone using an **STM32-based flight controller** and **NRF24L01 communication module**. This setup uses the **Arduino IDE on Windows** and flashes firmware using **STM32CubeProgrammer or STM32duino bootloader**.

---

## 📦 Hardware Overview

<table>
  <tr>
    <td>

### ✈️ Drone Flight Controller

- **Board:** STM32F401 Blackpill  
- **IMU:** MPU6050 (Gyroscope + Accelerometer)  
- **Magnetometer:** HMC5883L  
- **GPS Module:** Neo 6M GPS  
- **Communication Module:** NRF24L01 (via SPI)  
- **PWM Outputs:** 6 (for ESCs or servos)  
- **Firmware Upload Mode:** USB (DFU or USB Serial via STM32duino)  

</td>
    <td>
      <img src="https://github.com/user-attachments/assets/b9ea3e52-a9c9-4f7d-bbfb-715b28fcec10" width="300"/>
    </td>
  </tr>
</table>

---

<table>
  <tr>
    <td>

### 🖥️ Ground Station Transceiver

- **Board:** Arduino Nano  
- **Communication Module:** NRF24L01  
- **Purpose:** Interface with PC over Serial for GUI ↔️ Drone communication  

</td>
    <td>
      <img src="https://github.com/user-attachments/assets/b35e7a9a-7ed1-4b73-9437-922d08681606" width="250"/>
    </td>
  </tr>
</table>


---

## 🛠️ Development Environment (Windows)

- **IDE:** [Arduino IDE](https://www.arduino.cc/en/software)
- **Board Support:** STM32 by STMicroelectronics via STM32duino
- **Driver Tool (for DFU mode):** [STM32CubeProgrammer](https://www.st.com/en/development-tools/stm32cubeprog.html)
- **Optional:** [Zadig](https://zadig.akeo.ie/) to install DFU drivers

---

## 🚀 Getting Started

### ✅ 1. Install Required Tools

1. Download and install the **Arduino IDE** (v1.8.x or v2.x)
2. Install **STM32CubeProgrammer**
3. If needed, use **Zadig** to install **WinUSB driver** for DFU mode


### 🧩 2. Add STM32 Board Support to Arduino IDE

1. Open **Arduino IDE**
2. Go to **File → Preferences**
3. In **"Additional Board Manager URLs"**, add:
```
https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json
```
4. Go to **Tools → Board → Boards Manager**
5. Search for **STM32** and install **STM32 MCU based boards** by STMicroelectronics


### 🔧 3. Configure Board Settings

In **Tools** menu:

- **Board:** "Generic STM32F4 series"
- **Board part number:** "BlackPill F401CC"
- **Upload method:** 
- If using STM32CubeProgrammer: `STM32CubeProgrammer (DFU)`
- If using USB Serial: `Serial`
- **Port:** (Auto-selected if using USB Serial)
- **USB support:** "CDC (generic 'Serial')"
- **Optimize:** "Smallest (default)"
- **Variant:** STM32F401CCU6


### 📄 4. Add the Source Code

1. Open the Arduino IDE
2. Create a new sketch or open the `.ino` file provided in this repo
3. Make sure all `.h` and `.cpp` files (if any) are in the same folder
4. Include all necessary libraries (e.g., `Wire`, `SPI`, `RF24`, `TinyGPS++`)

> If you're using `.cpp` and `.h` files: use `Sketch → Add File` to import them.

---
## ⬆️ Upload Firmware (via Arduino IDE + DFU Mode)

You can upload the firmware to the STM32F401 Blackpill directly from the **Arduino IDE** using **DFU (Device Firmware Upgrade) mode**, without needing any external programmer.


### 🔌 1. Enter DFU Mode

To put the board into DFU mode:

1. **Hold down the `BOOT0` button**
2. **Press and release the `RESET` button**
3. **Release the `BOOT0` button**

Your board should now be in DFU mode.

✅ To confirm:
- Open **Device Manager** (Windows)
- You should see:  
  **`STM Device in DFU Mode`** under *Universal Serial Bus devices*


### ⚙️ 2. Set Arduino IDE Settings

In **Tools** menu of Arduino IDE:

- **Board:** `Generic STM32F4 series`
- **Board part number:** `BlackPill F401CC`
- **Upload method:** `STM32CubeProgrammer (DFU)`
- **USB support:** `CDC (generic 'Serial')`
- **Optimize:** `Smallest (default)`
- **Variant:** `STM32F401CCU6`
- **Port:** *(Not needed for DFU mode)*


### 📥 3. Install STM32CubeProgrammer

If you haven’t already, install the official STM32CubeProgrammer:

🔗 [Download STM32CubeProgrammer](https://www.st.com/en/development-tools/stm32cubeprog.html)

Make sure it's added to your system **PATH** so Arduino IDE can call it.


### 📤 4. Upload the Firmware

1. Connect the STM32 board via USB
2. Put it in DFU mode (as shown above)
3. Open your `.ino` sketch in Arduino IDE
4. Click **Upload** (Ctrl + U)

The Arduino IDE will compile the sketch and upload it via **DFU using STM32CubeProgrammer**.


### 🖥️ 5. Open Serial Monitor (Optional)

After a successful upload:

1. Reset the board to exit DFU mode
2. The board will now appear as a COM port
3. Go to **Tools → Serial Monitor**
4. Set baud rate to **115200**
5. View logs or communicate with the flight controller

---
