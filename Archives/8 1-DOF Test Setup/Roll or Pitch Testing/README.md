# Roll/Pitch PID Testing – 1 DOF Test Rig

This project implements **PID-based roll or pitch testing** using a **1 DOF test rig** with a drone motor setup.  
It provides firmware for the **flight controller (FC)**, a **ground control station (GCS)** code for an Arduino with nRF24, and a **Python GUI** for real-time monitoring and logging.  

---

## 🎯 Objective

- Test **roll or pitch dynamics** in isolation on a 1 DOF test rig.  
- Send test commands from the **GUI → GCS → FC**.  
- Control motors based on **PID feedback** from IMU sensors.  
- Log and visualize roll/pitch errors and motor PWM outputs.  

---

## 📂 Files in This Folder

- **`fc.ino`**  
  Flight controller firmware (runs on STM32/Arduino).  
  - Reads dual IMUs.  
  - Computes roll/pitch estimates with complementary filter.  
  - Applies PID control for roll or pitch.  
  - Drives ESCs via PWM.  
  - Sends telemetry (error + motor PWMs) to GCS over nRF24.  

- **`gcs.ino`**  
  Ground control station firmware (runs on Arduino with nRF24).  
  - Receives telemetry from FC.  
  - Forwards it to PC via USB serial.  
  - Receives commands from Python GUI and sends them to FC.  

- **`gui.py`**  
  Python GUI for controlling and monitoring tests.  
  - Connects via serial to GCS.  
  - Allows selecting:
    - **Roll** or **Pitch** test.  
    - Desired angle.  
    - PID gains (`Kp`, `Ki`, `Kd`).  
  - Start/Stop button:
    - On **Start** → sends parameters, locks inputs, starts motors (ESC init delay: 4s).  
    - On **Stop** → unlocks inputs, stops motors, saves log file.  
  - Plots roll/pitch errors and motor PWM signals in real time.  
  - Logs data to CSV in a `log/` folder.  

---

## ⚙️ Requirements

### Hardware
- **1 DOF test rig** (allows rotation about roll or pitch).  
- STM32/Arduino microcontroller for flight controller.  
- nRF24L01 modules (FC ↔ GCS).  
- Arduino Nano/Uno for GCS.  
- 4 × Brushless motors + ESCs.  
- IMUs (MPU6050 × 2).  

### Software
- Arduino IDE / PlatformIO  
- Python 3.8+  
- Python dependencies:
  ```bash
  pip install pyqt5 pyqtgraph pyserial
  ```

## 🚀 How to Run

### 1. Flash the Codes
- Upload **fc.ino** to the STM32/Arduino on the 1 DOF test rig.  
- Upload **gcs.ino** to the Arduino connected to the PC with nRF24.  


### 2. Run the GUI
In the project folder, start the GUI with:
```bash
python gui.py
```

### 3. Testing Workflow

1. Connect the **GCS Arduino** to your PC via USB.  

2. Open the GUI and select:
   - **COM port**
   - **Baud rate** (e.g., `115200`)
   - **Roll** or **Pitch** test option  

3. Enter the following:
   - **Desired angle**
   - **PID gains** (`Kp`, `Ki`, `Kd`)  

4. Click **Start Program**:
   - Inputs lock  
   - ESCs initialize (**4 seconds delay**)  
   - Motors start running  
   - Real-time plots for **error** and **PWM signals** appear  

5. Click **Stop Program**:
   - Motors stop  
   - Inputs unlock  
   - Data log is saved automatically in:  
     ```
     log/drone_log_YYYYMMDD_HHMMSS.csv
     ```

