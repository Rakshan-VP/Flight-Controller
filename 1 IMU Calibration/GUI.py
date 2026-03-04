import sys
import socket
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QHBoxLayout, QVBoxLayout, QLabel
)
from PyQt5.QtCore import QTimer

ESP_IP = "192.168.4.1"
ESP_PORT = 5000


class DroneGUI(QWidget):

    def __init__(self):
        super().__init__()

        self.sock = None
        self.connected = False

        self.initUI()
        self.connectToDrone()

        self.timer = QTimer()
        self.timer.timeout.connect(self.receiveData)
        self.timer.start(200)

    # ---------------- UI ----------------
    def initUI(self):

        self.calib_btn = QPushButton("Level Calibrate")
        self.status_label = QLabel("Not Connected")

        self.calib_btn.clicked.connect(self.calibrate)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.calib_btn)
        top_layout.addWidget(self.status_label)

        self.calib_status = QLabel("Calibration: Not Calibrated")

        self.offset_label = QLabel(
            "Offsets:\n"
            "Roll: 0\nPitch: 0\n"
            "GX: 0\nGY: 0\nGZ: 0"
        )

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.calib_status)
        main_layout.addWidget(self.offset_label)

        self.setLayout(main_layout)
        self.setWindowTitle("Drone Angle Calibration")
        self.resize(400, 250)

    # ---------------- NETWORK ----------------
    def connectToDrone(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2)
            self.sock.connect((ESP_IP, ESP_PORT))
            self.sock.setblocking(False)
            self.connected = True
            self.status_label.setText("Connected")
            self.requestStatus()
        except:
            self.connected = False
            self.status_label.setText("Not Connected")

    def requestStatus(self):
        if self.connected:
            try:
                self.sock.sendall(b"STATUS\n")
            except:
                self.connectionLost()

    def calibrate(self):
        if self.connected:
            try:
                self.sock.sendall(b"CALIBRATE\n")
            except:
                self.connectionLost()

    def receiveData(self):
        if not self.connected:
            return

        try:
            data = self.sock.recv(1024).decode().strip()
            if not data:
                return

            if data.startswith("STATUS"):
                self.parseStatus(data)

        except BlockingIOError:
            pass
        except:
            self.connectionLost()

    def parseStatus(self, data):
        parts = data.split(",")

        if len(parts) < 7:
            return

        cal_flag = parts[1]
        roll, pitch = parts[2], parts[3]
        gx, gy, gz = parts[4], parts[5], parts[6]

        if cal_flag == "1":
            self.calib_status.setText("Calibration: Calibrated")
        else:
            self.calib_status.setText("Calibration: Not Calibrated")

        self.offset_label.setText(
            f"Offsets:\n"
            f"Roll: {roll}\n"
            f"Pitch: {pitch}\n"
            f"GX: {gx}\n"
            f"GY: {gy}\n"
            f"GZ: {gz}"
        )

    def connectionLost(self):
        self.connected = False
        self.status_label.setText("Connection Lost")
        try:
            self.sock.close()
        except:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DroneGUI()
    window.show()
    sys.exit(app.exec_())