import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QSlider,
    QPushButton, QHBoxLayout, QComboBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from dark_theme import dark_stylesheet

class Sender(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('RPY Sender')
        self.ser = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_data)

        layout = QVBoxLayout()

        # COM port selector
        port_layout = QHBoxLayout()
        self.port_selector = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(QLabel("Select COM Port:"))
        port_layout.addWidget(self.port_selector)
        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_btn)
        layout.addLayout(port_layout)

        # RPY sliders
        self.sliders = {}
        for name in ['Roll', 'Pitch', 'Yaw']:
            lbl = QLabel(f"{name}: 0")
            sld = QSlider(Qt.Horizontal)
            sld.setMinimum(-90)
            sld.setMaximum(90)
            sld.setValue(0)
            sld.valueChanged.connect(lambda val, l=lbl, n=name: self.update_label(l, n, val))
            layout.addWidget(lbl)
            layout.addWidget(sld)
            self.sliders[name] = sld

        # Start/Stop buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_sending)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_sending)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Status Label
        self.status_label = QLabel("Status: Not started")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def refresh_ports(self):
        self.port_selector.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_selector.addItem(port.device)

    def update_label(self, label, name, value):
        label.setText(f"{name}: {value}")

    def start_sending(self):
        port = self.port_selector.currentText()
        if port:
            try:
                self.ser = serial.Serial(port, 9600)
                self.timer.start(100)  # send every 100 ms
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.status_label.setText("Status: Sending...")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                print(f"Started sending on {port}")
            except Exception as e:
                self.status_label.setText(f"Failed to open {port}")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                print(f"Failed to open {port}: {e}")

    def stop_sending(self):
        self.timer.stop()
        if self.ser:
            self.ser.close()
            self.ser = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        print("Stopped sending.")

    def send_data(self):
        if self.ser and self.ser.is_open:
            r = self.sliders['Roll'].value()
            p = self.sliders['Pitch'].value()
            y = self.sliders['Yaw'].value()
            msg = f"{r},{p},{y}\n"
            try:
                self.ser.write(msg.encode())
                self.status_label.setText("Status: Sending...")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            except Exception as e:
                self.status_label.setText("Status: Failed to send")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                print(f"Write error: {e}")
                self.stop_sending()

app = QApplication(sys.argv)
app.setStyleSheet(dark_stylesheet)
win = Sender()
win.show()
sys.exit(app.exec_())
