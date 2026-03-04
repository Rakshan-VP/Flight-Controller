# 🛩️ Attitude Visualization in Python

This project visualizes Roll, Pitch, and Yaw data from a flight controller in real-time using a PyQt5 GUI and VisPy 3D graphics.

---

## 🚀 Getting Started

### 📡 Upload the Arduino sketches

- Upload `transmitter.ino` to your **flight controller**.
- Upload `receiver.ino` to your **ground control station (GCS)**.

### 🖥️ Run the Visualizer

- Run `visualiser.py` using Python 3.
- You will see a GUI window like this:

 ![AttitudeVisualiser](https://github.com/user-attachments/assets/73fab404-0e93-4207-b8ba-e94ed6644dd7)

- Change the orientation of flight controller accordingly and check the results.

### ⚙️ Using the GUI

1. Select the correct **COM port** and **baud rate** for your serial connection.
2. Click **Connect** ▶️ to start receiving and visualizing data.
3. The GUI displays:
   - Real-time **Roll**, **Pitch**, and **Yaw** numeric values.
   - A 3D cuboid representing attitude 🎛️.
   - Plots of Roll, Pitch, and Yaw values over time 📈.


---

## 📋 Requirements

- Python 3.x 🐍
- PyQt5
- VisPy
- pyserial
- numpy

Install dependencies using:

```bash
pip install pyqt5 vispy pyserial numpy
