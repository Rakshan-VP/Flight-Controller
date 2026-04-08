import sys
import socket
import time
import os
import csv

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QHBoxLayout, QVBoxLayout, QLabel,
    QLineEdit, QGroupBox, QGridLayout, QSlider
)
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg

ESP_IP = "192.168.4.1"
ESP_PORT = 5000
MAX_POINTS = 2000


class PIDTestGUI(QWidget):

    def __init__(self):
        super().__init__()

        self.sock = None
        self.connected = False
        self.plotting = False
        self.active_axis = None
        self.buffer = ""

        self.roll_data = []
        self.pitch_data = []
        self.roll_ref_data = []
        self.pitch_ref_data = []
        self.m1_data = []
        self.m2_data = []
        self.m3_data = []
        self.m4_data = []
        self.time_data = []

        self.roll_ref = 0.0
        self.pitch_ref = 0.0

        self.start_time = 0
        self.logfile = None
        self.csvwriter = None

        os.makedirs("Basic Flight Tests/Dynamic Attitude Test/log", exist_ok=True)

        self.initUI()
        self.connectToDrone()

        self.timer = QTimer()
        self.timer.timeout.connect(self.receiveData)
        self.timer.start(10)

    # ---------------- UI ----------------
    def initUI(self):

        self.status_label = QLabel("Not Connected")
        self.base_pwm_input = QLineEdit("1100")

        # ---------- Roll Group ----------
        self.roll_group = QGroupBox("Roll Test")
        roll_layout = QGridLayout()

        self.roll_kp = QLineEdit("0.0")
        self.roll_ki = QLineEdit("0.0")
        self.roll_kd = QLineEdit("0.0")

        self.roll_start = QPushButton("Start")
        self.roll_stop = QPushButton("Stop")

        self.roll_start.clicked.connect(self.startRoll)
        self.roll_stop.clicked.connect(self.stopTest)

        roll_layout.addWidget(QLabel("Kp"), 0, 0)
        roll_layout.addWidget(self.roll_kp, 0, 1)
        roll_layout.addWidget(QLabel("Ki"), 1, 0)
        roll_layout.addWidget(self.roll_ki, 1, 1)
        roll_layout.addWidget(QLabel("Kd"), 2, 0)
        roll_layout.addWidget(self.roll_kd, 2, 1)
        roll_layout.addWidget(self.roll_start, 3, 0)
        roll_layout.addWidget(self.roll_stop, 3, 1)

        self.roll_group.setLayout(roll_layout)

        # ---------- Pitch Group ----------
        self.pitch_group = QGroupBox("Pitch Test")
        pitch_layout = QGridLayout()

        self.pitch_kp = QLineEdit("0.0")
        self.pitch_ki = QLineEdit("0.0")
        self.pitch_kd = QLineEdit("0.0")

        self.pitch_start = QPushButton("Start")
        self.pitch_stop = QPushButton("Stop")

        self.pitch_start.clicked.connect(self.startPitch)
        self.pitch_stop.clicked.connect(self.stopTest)

        pitch_layout.addWidget(QLabel("Kp"), 0, 0)
        pitch_layout.addWidget(self.pitch_kp, 0, 1)
        pitch_layout.addWidget(QLabel("Ki"), 1, 0)
        pitch_layout.addWidget(self.pitch_ki, 1, 1)
        pitch_layout.addWidget(QLabel("Kd"), 2, 0)
        pitch_layout.addWidget(self.pitch_kd, 2, 1)
        pitch_layout.addWidget(self.pitch_start, 3, 0)
        pitch_layout.addWidget(self.pitch_stop, 3, 1)

        self.pitch_group.setLayout(pitch_layout)

        # ---------- Sliders + Manual Inputs ----------
        self.roll_min = QLineEdit("-10")
        self.roll_max = QLineEdit("10")
        self.roll_input = QLineEdit("0")

        self.roll_slider = QSlider(Qt.Horizontal)
        self.roll_slider.setMinimum(-10)
        self.roll_slider.setMaximum(10)
        self.roll_slider.setValue(0)
        self.roll_slider.setSizePolicy(self.roll_slider.sizePolicy().Expanding, self.roll_slider.sizePolicy().Preferred)
        self.roll_slider.valueChanged.connect(self.updateRollRefSlider)

        self.roll_min.editingFinished.connect(self.applyRollSliderRange)
        self.roll_max.editingFinished.connect(self.applyRollSliderRange)

        self.pitch_min = QLineEdit("-10")
        self.pitch_max = QLineEdit("10")
        self.pitch_input = QLineEdit("0")

        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setMinimum(-10)
        self.pitch_slider.setMaximum(10)
        self.pitch_slider.setValue(0)
        self.pitch_slider.setSizePolicy(self.pitch_slider.sizePolicy().Expanding, self.pitch_slider.sizePolicy().Preferred)
        self.pitch_slider.valueChanged.connect(self.updatePitchRefSlider)

        self.pitch_min.editingFinished.connect(self.applyPitchSliderRange)
        self.pitch_max.editingFinished.connect(self.applyPitchSliderRange)

        self.roll_input.editingFinished.connect(self.updateRollRefBox)
        self.pitch_input.editingFinished.connect(self.updatePitchRefBox)

        slider_layout = QGridLayout()
        slider_layout.setColumnStretch(2, 5)

        slider_layout.addWidget(QLabel("Roll Min"), 0, 0)
        slider_layout.addWidget(self.roll_min, 0, 1)
        slider_layout.addWidget(self.roll_slider, 0, 2)
        slider_layout.addWidget(QLabel("Roll Max"), 0, 3)
        slider_layout.addWidget(self.roll_max, 0, 4)
        slider_layout.addWidget(QLabel("Ref"), 0, 5)
        slider_layout.addWidget(self.roll_input, 0, 6)

        slider_layout.addWidget(QLabel("Pitch Min"), 1, 0)
        slider_layout.addWidget(self.pitch_min, 1, 1)
        slider_layout.addWidget(self.pitch_slider, 1, 2)
        slider_layout.addWidget(QLabel("Pitch Max"), 1, 3)
        slider_layout.addWidget(self.pitch_max, 1, 4)
        slider_layout.addWidget(QLabel("Ref"), 1, 5)
        slider_layout.addWidget(self.pitch_input, 1, 6)

        # ---------- Roll Plot ----------
        self.roll_plot = pg.PlotWidget()
        self.roll_plot.addLegend()
        self.roll_plot.setLabel('left', 'Roll (deg)')
        self.roll_curve = self.roll_plot.plot(pen='r', name="Roll")
        self.roll_ref_curve = self.roll_plot.plot(pen='y', name="Ref")

        # ---------- Pitch Plot ----------
        self.pitch_plot = pg.PlotWidget()
        self.pitch_plot.addLegend()
        self.pitch_plot.setLabel('left', 'Pitch (deg)')
        self.pitch_curve = self.pitch_plot.plot(pen='b', name="Pitch")
        self.pitch_ref_curve = self.pitch_plot.plot(pen='y', name="Ref")

        # ---------- Motor Plot ----------
        self.motor_plot = pg.PlotWidget()
        self.motor_plot.addLegend()
        self.motor_plot.setLabel('left', 'PWM (µs)')

        self.m1_curve = self.motor_plot.plot(pen='y', name="M1")
        self.m2_curve = self.motor_plot.plot(pen='g', name="M2")
        self.m3_curve = self.motor_plot.plot(pen='m', name="M3")
        self.m4_curve = self.motor_plot.plot(pen='c', name="M4")

        # ---------- Layout ----------
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Base PWM"))
        top_bar.addWidget(self.base_pwm_input)
        top_bar.addWidget(self.status_label)

        columns = QHBoxLayout()
        columns.addWidget(self.roll_group)
        columns.addWidget(self.pitch_group)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_bar)
        main_layout.addLayout(columns)
        main_layout.addLayout(slider_layout)
        main_layout.addWidget(self.roll_plot)
        main_layout.addWidget(self.pitch_plot)
        main_layout.addWidget(self.motor_plot)

        self.setLayout(main_layout)
        self.setWindowTitle("1-DOF PID Test Bench (Dynamic)")
        self.resize(1100, 900)

    # ---------- Slider Range Update ----------
    def applyRollSliderRange(self):
        try:
            mn = int(float(self.roll_min.text()))
            mx = int(float(self.roll_max.text()))
            if mn < mx:
                self.roll_slider.setMinimum(mn)
                self.roll_slider.setMaximum(mx)
        except:
            pass

    def applyPitchSliderRange(self):
        try:
            mn = int(float(self.pitch_min.text()))
            mx = int(float(self.pitch_max.text()))
            if mn < mx:
                self.pitch_slider.setMinimum(mn)
                self.pitch_slider.setMaximum(mx)
        except:
            pass

    # ---------- Slider Sync ----------
    def updateRollRefSlider(self):
        self.roll_ref = float(self.roll_slider.value())
        self.roll_input.setText(str(self.roll_ref))
        # Send live setpoint update to ESP32
        if self.active_axis == "ROLL" and self.connected:
            self.send(f"SET_REF,{self.roll_ref}")

    def updatePitchRefSlider(self):
        self.pitch_ref = float(self.pitch_slider.value())
        self.pitch_input.setText(str(self.pitch_ref))
        # Send live setpoint update to ESP32
        if self.active_axis == "PITCH" and self.connected:
            self.send(f"SET_REF,{self.pitch_ref}")

    def updateRollRefBox(self):
        try:
            val = float(self.roll_input.text())
            # Clamp to slider range before setting
            val = max(self.roll_slider.minimum(), min(self.roll_slider.maximum(), int(val)))
            self.roll_slider.setValue(val)
            self.roll_ref = float(val)
            # Send live setpoint update to ESP32
            if self.active_axis == "ROLL" and self.connected:
                self.send(f"SET_REF,{self.roll_ref}")
        except:
            pass

    def updatePitchRefBox(self):
        try:
            val = float(self.pitch_input.text())
            val = max(self.pitch_slider.minimum(), min(self.pitch_slider.maximum(), int(val)))
            self.pitch_slider.setValue(val)
            self.pitch_ref = float(val)
            # Send live setpoint update to ESP32
            if self.active_axis == "PITCH" and self.connected:
                self.send(f"SET_REF,{self.pitch_ref}")
        except:
            pass

    # ---------------- Networking ----------------
    def connectToDrone(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ESP_IP, ESP_PORT))
            self.sock.setblocking(False)
            self.connected = True
            self.status_label.setText("Connected")
        except:
            self.status_label.setText("Not Connected")

    def send(self, msg):
        if self.connected:
            try:
                self.sock.sendall((msg + "\n").encode())
            except:
                self.connectionLost()

    def lockAll(self, lock):
        self.roll_kp.setDisabled(lock)
        self.roll_ki.setDisabled(lock)
        self.roll_kd.setDisabled(lock)
        self.pitch_kp.setDisabled(lock)
        self.pitch_ki.setDisabled(lock)
        self.pitch_kd.setDisabled(lock)
        self.base_pwm_input.setDisabled(lock)

    # ---------------- Control ----------------
    def startRoll(self):
        if self.active_axis:
            return
        self.active_axis = "ROLL"
        self.lockAll(True)
        self.send(f"SET_ROLL,{self.roll_kp.text()},{self.roll_ki.text()},{self.roll_kd.text()},{self.base_pwm_input.text()},{self.roll_ref}")
        self.send("START_ROLL")
        self.resetPlot()
        self.plotting = True

    def startPitch(self):
        if self.active_axis:
            return
        self.active_axis = "PITCH"
        self.lockAll(True)
        self.send(f"SET_PITCH,{self.pitch_kp.text()},{self.pitch_ki.text()},{self.pitch_kd.text()},{self.base_pwm_input.text()},{self.pitch_ref}")
        self.send("START_PITCH")
        self.resetPlot()
        self.plotting = True

    def stopTest(self):
        self.send("STOP")
        self.lockAll(False)
        self.active_axis = None
        self.plotting = False
        if self.logfile:
            self.logfile.close()
            self.logfile = None

    def resetPlot(self):
        self.roll_data.clear()
        self.pitch_data.clear()
        self.roll_ref_data.clear()
        self.pitch_ref_data.clear()
        self.m1_data.clear()
        self.m2_data.clear()
        self.m3_data.clear()
        self.m4_data.clear()
        self.time_data.clear()

        self.start_time = time.time()

        filename = time.strftime("Basic Flight Tests/Dynamic Attitude Test/log/%Y%m%d_%H%M%S.csv")
        self.logfile = open(filename, "w", newline="")
        self.csvwriter = csv.writer(self.logfile)

        self.csvwriter.writerow([
            "t", "roll", "roll_ref", "pitch", "pitch_ref", "m1", "m2", "m3", "m4"
        ])

    # ---------------- Telemetry ----------------
    def receiveData(self):

        if not self.connected or not self.plotting:
            return

        try:
            data = self.sock.recv(4096)
            if not data:
                self.connectionLost()
                return

            self.buffer += data.decode()

            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                parts = line.split(",")

                if len(parts) < 8:
                    continue

                try:
                    roll      = float(parts[0])
                    pitch     = float(parts[1])
                    roll_ref  = float(parts[2])
                    pitch_ref = float(parts[3])
                    m1        = float(parts[4])
                    m2        = float(parts[5])
                    m3        = float(parts[6])
                    m4        = float(parts[7])
                except:
                    continue

                t = time.time() - self.start_time

                self.time_data.append(t)
                self.roll_data.append(roll)
                self.pitch_data.append(pitch)
                self.roll_ref_data.append(roll_ref)
                self.pitch_ref_data.append(pitch_ref)
                self.m1_data.append(m1)
                self.m2_data.append(m2)
                self.m3_data.append(m3)
                self.m4_data.append(m4)

                # Log real reference echoed back from drone
                self.csvwriter.writerow([
                    t, roll, roll_ref, pitch, pitch_ref, m1, m2, m3, m4
                ])

            if len(self.time_data) > MAX_POINTS:
                self.time_data    = self.time_data[-MAX_POINTS:]
                self.roll_data    = self.roll_data[-MAX_POINTS:]
                self.pitch_data   = self.pitch_data[-MAX_POINTS:]
                self.roll_ref_data  = self.roll_ref_data[-MAX_POINTS:]
                self.pitch_ref_data = self.pitch_ref_data[-MAX_POINTS:]
                self.m1_data      = self.m1_data[-MAX_POINTS:]
                self.m2_data      = self.m2_data[-MAX_POINTS:]
                self.m3_data      = self.m3_data[-MAX_POINTS:]
                self.m4_data      = self.m4_data[-MAX_POINTS:]

            self.roll_curve.setData(self.time_data, self.roll_data)
            self.roll_ref_curve.setData(self.time_data, self.roll_ref_data)

            self.pitch_curve.setData(self.time_data, self.pitch_data)
            self.pitch_ref_curve.setData(self.time_data, self.pitch_ref_data)

            self.m1_curve.setData(self.time_data, self.m1_data)
            self.m2_curve.setData(self.time_data, self.m2_data)
            self.m3_curve.setData(self.time_data, self.m3_data)
            self.m4_curve.setData(self.time_data, self.m4_data)

        except BlockingIOError:
            pass
        except:
            self.connectionLost()

    def connectionLost(self):
        self.connected = False
        self.plotting = False
        self.active_axis = None
        self.lockAll(False)
        self.status_label.setText("Connection Lost")

        try:
            self.sock.close()
        except:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PIDTestGUI()
    window.show()
    sys.exit(app.exec_())