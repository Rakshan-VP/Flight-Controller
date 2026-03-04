import sys
import socket
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QHBoxLayout, QVBoxLayout, QLabel, QCheckBox
)
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

ESP_IP = "192.168.4.1"
ESP_PORT = 5000

MAX_POINTS = 2000


class DronePlotGUI(QWidget):

    def __init__(self):
        super().__init__()

        self.sock = None
        self.connected = False
        self.plotting = False

        self.buffer = ""

        self.roll_data = []
        self.pitch_data = []
        self.time_data = []
        self.start_time = 0

        self.initUI()
        self.connectToDrone()

        self.timer = QTimer()
        self.timer.timeout.connect(self.receiveData)
        self.timer.start(10)   # 100 Hz polling

    # ---------------- UI ----------------
    def initUI(self):

        self.start_btn = QPushButton("Start Plotting")
        self.stop_btn = QPushButton("Stop Plotting")
        self.auto_scale_cb = QCheckBox("AutoScale")
        self.auto_scale_cb.setChecked(True)
        self.status_label = QLabel("Not Connected")

        self.start_btn.clicked.connect(self.startPlot)
        self.stop_btn.clicked.connect(self.stopPlot)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.start_btn)
        top_layout.addWidget(self.stop_btn)
        top_layout.addWidget(self.auto_scale_cb)
        top_layout.addWidget(self.status_label)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k')
        self.plot_widget.setLabel('left', 'Angle (deg)')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.addLegend()

        self.roll_curve = self.plot_widget.plot(pen='r', name="Roll")
        self.pitch_curve = self.plot_widget.plot(pen='b', name="Pitch")

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.plot_widget)

        self.setLayout(layout)
        self.setWindowTitle("Drone Attitude Monitor")
        self.resize(900, 500)

    # ---------------- NETWORK ----------------
    def connectToDrone(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2)
            self.sock.connect((ESP_IP, ESP_PORT))
            self.sock.setblocking(False)
            self.connected = True
            self.status_label.setText("Connected")
        except:
            self.connected = False
            self.status_label.setText("Not Connected")

    def startPlot(self):
        if not self.connected:
            self.connectToDrone()

        if self.connected:
            try:
                self.sock.sendall(b"START\n")
                self.plotting = True
                self.start_time = time.time()

                self.roll_data.clear()
                self.pitch_data.clear()
                self.time_data.clear()

            except:
                self.connectionLost()

    def stopPlot(self):
        if self.connected:
            try:
                self.sock.sendall(b"STOP\n")
            except:
                pass

        self.plotting = False

    def receiveData(self):

        if not self.connected or not self.plotting:
            return

        try:
            data = self.sock.recv(4096).decode()

            if not data:
                return

            self.buffer += data

            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)

                if "," in line:
                    try:
                        roll, pitch = map(float, line.split(","))
                    except:
                        continue

                    t = time.time() - self.start_time

                    self.time_data.append(t)
                    self.roll_data.append(roll)
                    self.pitch_data.append(pitch)

            # Limit stored points
            if len(self.time_data) > MAX_POINTS:
                self.time_data = self.time_data[-MAX_POINTS:]
                self.roll_data = self.roll_data[-MAX_POINTS:]
                self.pitch_data = self.pitch_data[-MAX_POINTS:]

            self.roll_curve.setData(self.time_data, self.roll_data)
            self.pitch_curve.setData(self.time_data, self.pitch_data)

            if self.auto_scale_cb.isChecked():
                self.plot_widget.enableAutoRange()

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
    window = DronePlotGUI()
    window.show()
    sys.exit(app.exec_())