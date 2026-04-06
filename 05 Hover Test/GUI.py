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
from PyQt5.QtCore import QTimer, Qt, QSettings
import pyqtgraph as pg

ESP_IP = "192.168.4.1"
ESP_PORT = 5000
MAX_POINTS = 2000


class PIDTestGUI(QWidget):

    def __init__(self):
        super().__init__()
        
        self.settings = QSettings("DroneLab", "HoverPIDTest")
        self.sock = None
        self.connected = False
        self.plotting = False
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

        os.makedirs("4 Hover Test/log", exist_ok=True)

        self.initUI()
        self.connectToDrone()

        self.timer = QTimer()
        self.timer.timeout.connect(self.receiveData)
        self.timer.start(10)

        self.baseTimer = QTimer()
        self.baseTimer.timeout.connect(self.sendBasePWM)

    # ---------------- UI ----------------
    def initUI(self):

        self.status_label = QLabel("Not Connected")
        self.base_pwm_input = QLineEdit("1100")

        # -------- Max PWM --------
        self.max_pwm_input = QLineEdit("1400")

        # -------- Base PWM Slider --------
        self.base_slider = QSlider(Qt.Horizontal)
        self.base_slider.setMinimum(1000)
        self.base_slider.setMaximum(int(self.max_pwm_input.text()))
        self.base_slider.setValue(1100)
        self.base_slider.valueChanged.connect(self.sliderChanged)

        # ---------- Roll Group ----------
        self.roll_group = QGroupBox("Roll Gains")
        roll_layout = QGridLayout()

        self.roll_kp = QLineEdit("0.0")
        self.roll_ki = QLineEdit("0.0")
        self.roll_kd = QLineEdit("0.0")

        roll_layout.addWidget(QLabel("Kp"), 0, 0)
        roll_layout.addWidget(self.roll_kp, 0, 1)
        roll_layout.addWidget(QLabel("Ki"), 1, 0)
        roll_layout.addWidget(self.roll_ki, 1, 1)
        roll_layout.addWidget(QLabel("Kd"), 2, 0)
        roll_layout.addWidget(self.roll_kd, 2, 1)

        self.roll_group.setLayout(roll_layout)

        # ---------- Pitch Group ----------
        self.pitch_group = QGroupBox("Pitch Gains")
        pitch_layout = QGridLayout()

        self.pitch_kp = QLineEdit("0.0")
        self.pitch_ki = QLineEdit("0.0")
        self.pitch_kd = QLineEdit("0.0")

        pitch_layout.addWidget(QLabel("Kp"), 0, 0)
        pitch_layout.addWidget(self.pitch_kp, 0, 1)
        pitch_layout.addWidget(QLabel("Ki"), 1, 0)
        pitch_layout.addWidget(self.pitch_ki, 1, 1)
        pitch_layout.addWidget(QLabel("Kd"), 2, 0)
        pitch_layout.addWidget(self.pitch_kd, 2, 1)

        self.pitch_group.setLayout(pitch_layout)

        # ---------- Control Buttons ----------
        self.arm_button = QPushButton("ARM")
        self.start_button = QPushButton("Start Test")
        self.stop_button = QPushButton("Stop Test")
        self.disarm_button = QPushButton("DISARM")

        self.arm_button.clicked.connect(self.arm)
        self.start_button.clicked.connect(self.startTest)
        self.stop_button.clicked.connect(self.stopTest)
        self.disarm_button.clicked.connect(self.disarm)

        control_bar = QHBoxLayout()
        control_bar.addWidget(self.arm_button)
        control_bar.addWidget(self.start_button)
        control_bar.addWidget(self.stop_button)
        control_bar.addWidget(self.disarm_button)

        # ---------- TOP PLOT ----------
        self.rp_plot = pg.PlotWidget()
        self.rp_plot.addLegend()
        self.rp_plot.setLabel('left', 'Angle (deg)')
        self.rp_plot.setLabel('bottom', 'Time (s)')

        self.zero_line = pg.InfiniteLine(
            pos=0,
            angle=0,
            pen=pg.mkPen(color=(200, 200, 200), width=1, style=pg.QtCore.Qt.DashLine)
        )
        self.rp_plot.addItem(self.zero_line)

        self.roll_curve = self.rp_plot.plot(pen='r', name="Roll")
        self.pitch_curve = self.rp_plot.plot(pen='b', name="Pitch")

        # ---------- MOTOR PLOT ----------
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

        top_bar.addWidget(QLabel("Max PWM"))
        top_bar.addWidget(self.max_pwm_input)

        top_bar.addWidget(self.status_label)

        slider_layout = QVBoxLayout()
        slider_layout.addWidget(QLabel("Throttle Slider"))
        slider_layout.addWidget(self.base_slider)

        columns = QHBoxLayout()
        columns.addWidget(self.roll_group)
        columns.addWidget(self.pitch_group)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_bar)
        main_layout.addLayout(slider_layout)
        main_layout.addLayout(columns)
        main_layout.addLayout(control_bar)
        main_layout.addWidget(self.rp_plot)
        main_layout.addWidget(self.motor_plot)

        self.setLayout(main_layout)
        self.setWindowTitle("2-Axis PID Test Bench")
        self.resize(1000, 800)

        self.max_pwm_input.textChanged.connect(self.updateSliderMax)
        self.loadPIDValues()

    # ---------------- PID Persistence ----------------
    def savePIDValues(self):

        self.settings.setValue("roll_kp", self.roll_kp.text())
        self.settings.setValue("roll_ki", self.roll_ki.text())
        self.settings.setValue("roll_kd", self.roll_kd.text())

        self.settings.setValue("pitch_kp", self.pitch_kp.text())
        self.settings.setValue("pitch_ki", self.pitch_ki.text())
        self.settings.setValue("pitch_kd", self.pitch_kd.text())


    def loadPIDValues(self):

        self.roll_kp.setText(self.settings.value("roll_kp", "0.0"))
        self.roll_ki.setText(self.settings.value("roll_ki", "0.0"))
        self.roll_kd.setText(self.settings.value("roll_kd", "0.0"))

        self.pitch_kp.setText(self.settings.value("pitch_kp", "0.0"))
        self.pitch_ki.setText(self.settings.value("pitch_ki", "0.0"))
        self.pitch_kd.setText(self.settings.value("pitch_kd", "0.0"))

    # ---------------- Slider Logic ----------------
    def sliderChanged(self, value):
        self.base_pwm_input.setText(str(value))

    def updateSliderMax(self):
        try:
            max_pwm = int(self.max_pwm_input.text())

            # enforce limits
            if max_pwm < 1000:
                return
            if max_pwm > 2000:
                max_pwm = 2000
                self.max_pwm_input.setText("2000")

            current_val = self.base_slider.value()

            # update slider range
            self.base_slider.setMaximum(max_pwm)

            # clamp slider value
            if current_val > max_pwm:
                current_val = max_pwm
            if current_val < 1000:
                current_val = 1000

            self.base_slider.setValue(current_val)
            self.base_pwm_input.setText(str(current_val))

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

    # ---------------- Control ----------------
    def arm(self):
        self.send("ARM")

    def startTest(self):

        Kpr = self.roll_kp.text()
        Kir = self.roll_ki.text()
        Kdr = self.roll_kd.text()

        Kpp = self.pitch_kp.text()
        Kip = self.pitch_ki.text()
        Kdp = self.pitch_kd.text()

        self.savePIDValues()

        self.send(f"SET_PID,{Kpr},{Kir},{Kdr},{Kpp},{Kip},{Kdp}")

        base = self.base_pwm_input.text()
        self.send(f"SET_BASE,{base}")

        self.send("START_TEST")

        self.resetPlot()

        self.plotting = True
        self.baseTimer.start(200)

    def stopTest(self):

        self.baseTimer.stop()
        self.send("STOP_TEST")

        self.plotting = False

        if self.logfile:
            self.logfile.close()
            self.logfile = None

    def disarm(self):

        self.baseTimer.stop()
        self.send("DISARM")
        self.plotting = False

    def sendBasePWM(self):

        if not self.plotting:
            return

        base = self.base_pwm_input.text()
        self.send(f"SET_BASE,{base}")

    # ---------------- Plot Reset ----------------
    def resetPlot(self):

        self.roll_data.clear()
        self.pitch_data.clear()
        self.m1_data.clear()
        self.m2_data.clear()
        self.m3_data.clear()
        self.m4_data.clear()
        self.time_data.clear()

        self.start_time = time.time()

        Kpr = self.roll_kp.text()
        Kir = self.roll_ki.text()
        Kdr = self.roll_kd.text()

        Kpp = self.pitch_kp.text()
        Kip = self.pitch_ki.text()
        Kdp = self.pitch_kd.text()

        timestamp = time.strftime("%Y%m%d_%H%M%S")

        filename = f"4 Hover Test/log/{timestamp}_R({Kpr},{Kir},{Kdr})_P({Kpp},{Kip},{Kdp}).csv"
        self.logfile = open(filename, "w", newline="")
        self.csvwriter = csv.writer(self.logfile)

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

                if len(parts) < 6:
                    continue

                roll = float(parts[0])
                pitch = float(parts[1])
                m1 = float(parts[2])
                m2 = float(parts[3])
                m3 = float(parts[4])
                m4 = float(parts[5])

                t = time.time() - self.start_time

                self.time_data.append(t)
                self.roll_data.append(roll)
                self.pitch_data.append(pitch)

                self.m1_data.append(m1)
                self.m2_data.append(m2)
                self.m3_data.append(m3)
                self.m4_data.append(m4)

                if len(parts) == 18:

                    self.csvwriter.writerow([
                        t,roll,pitch,m1,m2,m3,m4,
                        parts[6],parts[7],parts[8],
                        parts[9],parts[10],parts[11],
                        parts[12],parts[13],parts[14],
                        parts[15],parts[16],parts[17]
                    ])

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