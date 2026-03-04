# Level Testing for Roll & Pitch

This subfolder contains the necessary code and tools to perform level testing of a drone's roll and pitch control using an STM32F411 flight controller and an Arduino Nano GCS. The setup allows for communication via **nRF24L01** modules and provides a GUI for live plotting and logging of data.

---

## Folder Contents

- `fc.ino`  
  - Arduino code to be flashed to the **STM32F411 Flight Controller**.  
  - Implements level control for **roll and pitch** with `des_r = 0` and `des_p = 0`.

- `gcs.ino`  
  - Arduino code for the **Ground Control Station (GCS)** using an **Arduino Nano**.  
  - Communicates with the STM32 FC via **nRF24L01**.  

- `gui.py`  
  - PyQt5-based GUI for monitoring and controlling the test.  
  - Connects to the GCS via serial port.  
  - Provides live plotting of:
    - **Roll & Pitch Error**
    - **Motor PWM signals (M1–M4)**  
  - Allows starting and stopping the test.  
  - Saves logs as CSV files in the `log` folder with filename format:  
    ```
    drone_log_YYYYMMDD_HHMMSS.csv
    ```
  - Each log file contains columns:
    ```
    t, roll, pitch, M1, M2, M3, M4
    ```

- `log/`  
  - Folder where CSV logs are automatically saved.

---

## Requirements

- **Hardware**
  - STM32F411 Flight Controller
  - Arduino Nano (GCS)
  - nRF24L01 modules
  - 4 BLDC motors for testing

- **Software**
  - Arduino IDE for `fc.ino` and `gcs.ino`
  - Python 3.x
  - PyQt5 (`pip install pyqt5`)
  - pyqtgraph (`pip install pyqtgraph`)
  - pyserial (`pip install pyserial`)

---

## Setup Instructions

1. **Flash the code**
   - Upload `fc.ino` to the STM32F411 FC.
   - Upload `gcs.ino` to the Arduino Nano (GCS).

2. **Connect Hardware**
   - Connect nRF24L01 modules to both STM32 FC and Arduino Nano.
   - Connect motors to the flight controller.

3. **Run GUI**
   ```bash
   python gui.py
