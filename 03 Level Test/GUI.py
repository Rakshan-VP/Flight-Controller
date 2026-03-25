import sys
import socket
import time
import os
import csv

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QHBoxLayout, QVBoxLayout, QLabel,
    QLineEdit, QGroupBox, QGridLayout
)
from PyQt5.QtCore import QTimer
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
        self.m1_data = []
        self.m2_data = []
        self.m3_data = []
        self.m4_data = []
        self.time_data = []

        self.start_time = 0
        self.logfile = None
        self.csvwriter = None

        os.makedirs("03 Level Test/log", exist_ok=True)

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

        # ---------- TOP PLOT (Roll & Pitch) ----------
        self.rp_plot = pg.PlotWidget()
        self.rp_plot.addLegend()
        self.rp_plot.setLabel('left', 'Angle (deg)')
        self.rp_plot.setLabel('bottom', 'Time (s)')
        # Zero reference line
        self.zero_line = pg.InfiniteLine(
            pos=0,
            angle=0,
            pen=pg.mkPen(color=(200, 200, 200), width=1, style=pg.QtCore.Qt.DashLine)
        )
        self.rp_plot.addItem(self.zero_line)

        self.roll_curve = self.rp_plot.plot(pen='r', name="Roll")
        self.pitch_curve = self.rp_plot.plot(pen='b', name="Pitch")

        # ---------- BOTTOM PLOT (Motors) ----------
        self.motor_plot = pg.PlotWidget()
        self.motor_plot.addLegend()
        self.motor_plot.setLabel('left', 'PWM (µs)')
        self.motor_plot.setLabel('bottom', 'Time (s)')

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
        main_layout.addWidget(self.rp_plot)
        main_layout.addWidget(self.motor_plot)

        self.setLayout(main_layout)
        self.setWindowTitle("1-DOF PID Test Bench")
        self.resize(1000, 800)

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

        kp = self.roll_kp.text()
        ki = self.roll_ki.text()
        kd = self.roll_kd.text()
        base = self.base_pwm_input.text()

        self.send(f"SET_ROLL,{kp},{ki},{kd},{base}")
        self.send("START_ROLL")

        self.resetPlot()
        self.plotting = True

    def startPitch(self):
        if self.active_axis:
            return

        self.active_axis = "PITCH"
        self.lockAll(True)

        kp = self.pitch_kp.text()
        ki = self.pitch_ki.text()
        kd = self.pitch_kd.text()
        base = self.base_pwm_input.text()

        self.send(f"SET_PITCH,{kp},{ki},{kd},{base}")
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
        self.m1_data.clear()
        self.m2_data.clear()
        self.m3_data.clear()
        self.m4_data.clear()
        self.time_data.clear()

        self.start_time = time.time()

        filename = time.strftime("03 Level Test/log/%Y%m%d_%H%M%S.csv")
        self.logfile = open(filename, "w", newline="")
        self.csvwriter = csv.writer(self.logfile)

        # Updated header (extra IMU values added)
        self.csvwriter.writerow([
            "t","roll","pitch","m1","m2","m3","m4",
            "accX_raw","accY_raw","accZ_raw",
            "gyroX_raw","gyroY_raw","gyroZ_raw",
            "accX_drone","accY_drone","accZ_drone",
            "gyroX_drone","gyroY_drone","gyroZ_drone"
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

                # Must have at least roll,pitch,m1,m2,m3,m4
                if len(parts) < 6:
                    continue

                try:
                    roll  = float(parts[0])
                    pitch = float(parts[1])
                    m1    = float(parts[2])
                    m2    = float(parts[3])
                    m3    = float(parts[4])
                    m4    = float(parts[5])
                except:
                    continue

                t = time.time() - self.start_time

                # ---- Plot (UNCHANGED) ----
                self.time_data.append(t)
                self.roll_data.append(roll)
                self.pitch_data.append(pitch)
                self.m1_data.append(m1)
                self.m2_data.append(m2)
                self.m3_data.append(m3)
                self.m4_data.append(m4)

                # ---- Extended Logging (only if full 18 values present) ----
                if len(parts) == 18:
                    try:
                        accX_raw  = float(parts[6])
                        accY_raw  = float(parts[7])
                        accZ_raw  = float(parts[8])
                        gyroX_raw = float(parts[9])
                        gyroY_raw = float(parts[10])
                        gyroZ_raw = float(parts[11])
                        accX_drone  = float(parts[12])
                        accY_drone  = float(parts[13])
                        accZ_drone  = float(parts[14])
                        gyroX_drone = float(parts[15])
                        gyroY_drone = float(parts[16])
                        gyroZ_drone = float(parts[17])
                    except:
                        continue

                    self.csvwriter.writerow([
                        t,roll,pitch,m1,m2,m3,m4,
                        accX_raw,accY_raw,accZ_raw,
                        gyroX_raw,gyroY_raw,gyroZ_raw,
                        accX_drone,accY_drone,accZ_drone,
                        gyroX_drone,gyroY_drone,gyroZ_drone
                    ])
                else:
                    # fallback logging if incomplete
                    self.csvwriter.writerow([t,roll,pitch,m1,m2,m3,m4])

            if len(self.time_data) > MAX_POINTS:
                self.time_data = self.time_data[-MAX_POINTS:]
                self.roll_data = self.roll_data[-MAX_POINTS:]
                self.pitch_data = self.pitch_data[-MAX_POINTS:]
                self.m1_data = self.m1_data[-MAX_POINTS:]
                self.m2_data = self.m2_data[-MAX_POINTS:]
                self.m3_data = self.m3_data[-MAX_POINTS:]
                self.m4_data = self.m4_data[-MAX_POINTS:]

            self.roll_curve.setData(self.time_data, self.roll_data)
            self.pitch_curve.setData(self.time_data, self.pitch_data)

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

#2.0,0.1,0.7 - Roll
#3.5,0.05,2.2 - Pitch