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

        # Buttons
        self.calib_btn = QPushButton("Level Calibrate")
        self.start_btn = QPushButton("Start Accel Calibration")
        self.done_btn = QPushButton("Done (Capture)")

        self.status_label = QLabel("Not Connected")

        # Button actions
        self.calib_btn.clicked.connect(self.calibrate)
        self.start_btn.clicked.connect(self.startAccel)
        self.done_btn.clicked.connect(self.stepDone)

        # Top layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.calib_btn)
        top_layout.addWidget(self.start_btn)
        top_layout.addWidget(self.done_btn)
        top_layout.addWidget(self.status_label)

        # Calibration status
        self.calib_status = QLabel("Calibration: Not Started")

        # Step display
        self.step_label = QLabel("Step: -")

        # Offset display
        self.offset_label = QLabel(
            "Offsets:\n"
            "Roll: 0\nPitch: 0\n"
            "GX: 0\nGY: 0\nGZ: 0"
        )

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.calib_status)
        main_layout.addWidget(self.step_label)
        main_layout.addWidget(self.offset_label)

        self.setLayout(main_layout)
        self.setWindowTitle("Drone Calibration (ArduPilot Style)")
        self.resize(500, 300)

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

    def startAccel(self):
        if self.connected:
            try:
                self.sock.sendall(b"START_ACCEL\n")
            except:
                self.connectionLost()

    def stepDone(self):
        if self.connected:
            try:
                self.sock.sendall(b"STEP_DONE\n")
            except:
                self.connectionLost()

    # ---------------- RECEIVE ----------------
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

    # ---------------- PARSE ----------------
    def parseStatus(self, data):

        parts = data.split(",")

        # Expected:
        # STATUS,cal,accel_active,step,step_name,roll,pitch,gx,gy,gz
        if len(parts) < 10:
            return

        cal_flag = parts[1]
        accel_active = parts[2]
        step = int(parts[3])
        step_name = parts[4]

        roll = parts[5]
        pitch = parts[6]
        gx = parts[7]
        gy = parts[8]
        gz = parts[9]

        # ---- Calibration Status ----
        if accel_active == "1":
            self.calib_status.setText("Accel Calibration Running")
            self.step_label.setText(f"Step {step}/6 : {step_name}")
        else:
            if cal_flag == "1":
                self.calib_status.setText("Calibration: Completed")
                self.step_label.setText("Step: DONE")
            else:
                self.calib_status.setText("Calibration: Idle")
                self.step_label.setText("Step: -")

        # ---- Offset Display ----
        self.offset_label.setText(
            f"Offsets:\n"
            f"Roll: {roll}\nPitch: {pitch}\n"
            f"GX: {gx}\nGY: {gy}\nGZ: {gz}"
        )

    # ---------------- ERROR ----------------
    def connectionLost(self):
        self.connected = False
        self.status_label.setText("Connection Lost")
        try:
            self.sock.close()
        except:
            pass


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DroneGUI()
    window.show()
    sys.exit(app.exec_())