import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QSlider, QPushButton,
    QHBoxLayout, QComboBox, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer
from dark_theme import dark_stylesheet

class Sender(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('RPY Control Panel')
        self.ser = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_and_receive)

        layout = QVBoxLayout()

        # COM Port Selector
        port_layout = QHBoxLayout()
        self.port_selector = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(QLabel("Select COM Port:"))
        port_layout.addWidget(self.port_selector)
        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_btn)
        layout.addLayout(port_layout)

        # Sliders for Roll, Pitch, Yaw
        self.sliders = {}
        self.desired_labels = {}
        for name in ['Roll', 'Pitch', 'Yaw']:
            lbl = QLabel(f"{name}: 0")
            sld = QSlider(Qt.Horizontal)
            sld.setRange(-90, 90)
            sld.setValue(0)
            sld.valueChanged.connect(lambda val, l=lbl, n=name: self.update_slider(val, l, n))
            layout.addWidget(lbl)
            layout.addWidget(sld)
            self.sliders[name] = sld
            self.desired_labels[name] = lbl

        # Status Indicators
        status_layout = QGridLayout()
        self.send_status = QLabel("Send: Waiting")
        self.recv_status = QLabel("Recv: Waiting")
        self.send_status.setStyleSheet("color: gray")
        self.recv_status.setStyleSheet("color: gray")
        status_layout.addWidget(self.send_status, 0, 0)
        status_layout.addWidget(self.recv_status, 0, 1)
        layout.addLayout(status_layout)

        # Current and Delta RPY Display
        self.current_rpy = QLabel("Current: Roll=0, Pitch=0, Yaw=0")
        self.delta_rpy = QLabel("Delta: Roll=0, Pitch=0, Yaw=0")
        layout.addWidget(self.current_rpy)
        layout.addWidget(self.delta_rpy)

        # Start and Stop Buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def refresh_ports(self):
        self.port_selector.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_selector.addItem(port.device)

    def update_slider(self, value, label, name):
        label.setText(f"{name}: {value}")

    def start(self):
        port = self.port_selector.currentText()
        if port:
            try:
                self.ser = serial.Serial(port, 9600, timeout=0.2)
                self.timer.start(100)
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.send_status.setText("Send: Waiting")
                self.send_status.setStyleSheet("color: gray")
                self.recv_status.setText("Recv: Waiting")
                self.recv_status.setStyleSheet("color: gray")
            except Exception as e:
                self.send_status.setText("Failed to open port ❌")
                self.send_status.setStyleSheet("color: red")
                print(f"Failed to open port {port}: {e}")

    def stop(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.timer.stop()
        self.ser = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.send_status.setText("Send: Stopped")
        self.send_status.setStyleSheet("color: gray")
        self.recv_status.setText("Recv: Stopped")
        self.recv_status.setStyleSheet("color: gray")

    def send_and_receive(self):
        if self.ser and self.ser.is_open:
            r = self.sliders['Roll'].value()
            p = self.sliders['Pitch'].value()
            y = self.sliders['Yaw'].value()
            msg = f"{r},{p},{y}\n"

            # Show sending status
            self.send_status.setText("Sending...")
            self.send_status.setStyleSheet("color: orange")

            try:
                self.ser.write(msg.encode())
                self.send_status.setText("Send Success ✅")
                self.send_status.setStyleSheet("color: green")
            except:
                self.send_status.setText("Send Failed ❌")
                self.send_status.setStyleSheet("color: red")
                return

            # Show receiving status
            self.recv_status.setText("Receiving...")
            self.recv_status.setStyleSheet("color: orange")

            try:
                line = self.ser.readline().decode().strip()
                parts = line.split(",")
                if len(parts) == 6:
                    cr, cp, cy, dr, dp, dy = parts
                    self.current_rpy.setText(f"Current: Roll={cr}, Pitch={cp}, Yaw={cy}")
                    self.delta_rpy.setText(f"Delta: Roll={dr}, Pitch={dp}, Yaw={dy}")
                    self.recv_status.setText("Receive Success ✅")
                    self.recv_status.setStyleSheet("color: green")
                else:
                    raise ValueError("Invalid response format")
            except:
                self.recv_status.setText("Receive Failed ❌")
                self.recv_status.setStyleSheet("color: red")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_stylesheet)
    win = Sender()
    win.show()
    sys.exit(app.exec_())
