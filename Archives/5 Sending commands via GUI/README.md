# Sending Commands via GUI

![USB Communication](https://github.com/user-attachments/assets/fb787c53-2b16-43e4-a326-cba6f28c340a)


This repo allows you to **send Roll, Pitch, and Yaw (RPY) commands from a Python GUI** to an **STM32 flight controller using nRF24L01 wireless modules**, with an **Arduino Nano acting as the transmitter**.

---

## 💡 What This Repo Does

- Provides a simple **PyQt5-based GUI** to send RPY values via serial.
- Uses **Arduino Nano + nRF24L01** to transmit commands wirelessly.
- An **STM32 board with nRF24L01** receives commands and prints them to its serial monitor (e.g., COM5).
- Displays **live status feedback** (green for success, red for failure) in the GUI.

![flow](https://github.com/user-attachments/assets/7cbc5e6f-f98e-42e8-b842-1e4297c10c65)

---

## 🚀 How to Use

1. **Upload Arduino Code**
   - Open `nano_tx.ino` in Arduino IDE.
   - Flash it to your **Arduino Nano**.
   - This reads RPY from serial and sends it via nRF24L01.

2. **Upload STM32 Code**
   - Use `stm32_rx.ino` (or `.cpp`, depending on your environment).
   - Flash it to your **STM32** board using STM32CubeIDE or STM32 core in Arduino IDE.
   - This receives RPY via nRF24L01 and sends it over serial (COM5).

3. **Connect the STM32 to Your Laptop**
   - Verify it appears on **COM5** (or update the COM port in the GUI if different).
   - Open the **serial monitor** (115200 or 9600 baud) to see incoming RPY values.

4. **Run the GUI**
   - From your terminal:
     ```bash
     python GUI.py
     ```
   - GUI features:
     - Select the COM port of the GCS (eg., COM12).
     - `Start` and `Stop` buttons.
     - Roll, Pitch, Yaw sliders.
     - Status label (green = sending, red = failed).

5. **Observe the Output**
   - Adjust sliders.
   - View RPY values printed in the STM32’s serial monitor (eg., COM5).
   - Click `Stop` when you're done.

---

## 🛠 Dependencies

- Python 3.x
- PyQt5 
- pyserial
- Arduino IDE
- STM32CubeIDE or STM32 core (if using Arduino for STM32)

---

## ⚠️ Notes

- Only one application can use a COM port at a time.
  - Close the serial monitor before starting the GUI.
- If you see inconsistent nRF24L01 behavior, power it with a separate 3.3V regulator.
- Make sure CE and CSN pin definitions in the code match your hardware wiring.

