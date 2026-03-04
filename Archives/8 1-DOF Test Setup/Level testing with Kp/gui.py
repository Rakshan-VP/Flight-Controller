# gui.py
import sys, serial, threading, serial.tools.list_ports, csv, datetime, os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, QObject
import pyqtgraph as pg

# ---- Serial reader thread ----
class SerialReader(QObject):
    data_received = pyqtSignal(float, float, int, int, int, int)

    def __init__(self):
        super().__init__()
        self.ser = None
        self.running = False

    def start(self, port, baud):
        if self.running:
            self.stop()
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            self.running = True
            threading.Thread(target=self.read_loop, daemon=True).start()
        except:
            print("Failed to open serial port.")

    def read_loop(self):
        while self.running:
            try:
                line = self.ser.readline().decode().strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) == 6:
                    r, p, m1, m2, m3, m4 = parts
                    self.data_received.emit(float(r), float(p),
                                            int(m1), int(m2), int(m3), int(m4))
            except:
                pass

    def stop(self):
        self.running = False
        try:
            if self.ser:
                self.ser.close()
        except:
            pass

# ---- GUI ----
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone GCS GUI")

        self.layout = QVBoxLayout(self)

        # --- Serial controls ---
        serial_layout = QHBoxLayout()
        self.com_label = QLabel("COM:")
        self.com_selector = QComboBox()
        self.refresh_ports()
        self.baud_label = QLabel("Baud:")
        self.baud_selector = QComboBox()
        self.baud_selector.addItems(["9600","115200","230400"])
        serial_layout.addWidget(self.com_label)
        serial_layout.addWidget(self.com_selector)
        serial_layout.addWidget(self.baud_label)
        serial_layout.addWidget(self.baud_selector)
        self.layout.addLayout(serial_layout)

        # Roll/Pitch error plot
        self.error_plot = pg.PlotWidget(title="Roll & Pitch Error")
        self.error_plot.addLegend()
        self.curve_roll = self.error_plot.plot(pen='b', name="Roll error")
        self.curve_pitch = self.error_plot.plot(pen='g', name="Pitch error")
        self.stop_line_error = self.error_plot.addLine(y=0, pen=pg.mkPen('w', width=2))
        self.stop_line_error.setVisible(False)
        self.layout.addWidget(self.error_plot)

        # Motor PWM plot
        self.motor_plot = pg.PlotWidget(title="Motor PWMs")
        self.motor_plot.addLegend()
        self.curve_m1 = self.motor_plot.plot(pen='r', name="M1 [Front Right]")
        self.curve_m2 = self.motor_plot.plot(pen='g', name="M2 [Front Left]")
        self.curve_m3 = self.motor_plot.plot(pen='b', name="M3 [Rear Right]")
        self.curve_m4 = self.motor_plot.plot(pen='y', name="M4 [Rear Left]")
        self.stop_line_motor = self.motor_plot.addLine(y=0, pen=pg.mkPen('w', width=2))
        self.stop_line_motor.setVisible(False)
        self.layout.addWidget(self.motor_plot)

        # Buttons
        self.btn_start = QPushButton("START")
        self.btn_stop = QPushButton("STOP")
        self.layout.addWidget(self.btn_start)
        self.layout.addWidget(self.btn_stop)

        # Data buffers
        self.xdata, self.roll_err, self.pitch_err = [], [], []
        self.m1, self.m2, self.m3, self.m4 = [], [], [], []
        self.t = 0
        self.plotting = False

        # Serial reader
        self.reader = SerialReader()
        self.reader.data_received.connect(self.update_data)

        # Log folder and file setup
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_folder = os.path.join(script_dir, "log")
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        dt_string = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(log_folder, f"drone_log_{dt_string}.csv")
        self.log_file = open(log_path, "w", newline="")
        self.logger = csv.writer(self.log_file)
        self.logger.writerow(["t","roll","pitch","M1","M2","M3","M4"])

        # Connect buttons
        self.btn_start.clicked.connect(self.start_plotting)
        self.btn_stop.clicked.connect(self.stop_plotting)

    def refresh_ports(self):
        self.com_selector.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.com_selector.addItem(p.device)

    def start_plotting(self):
        port = self.com_selector.currentText()
        baud = int(self.baud_selector.currentText())
        self.reader.start(port, baud)
        self.plotting = True
        self.stop_line_error.setVisible(False)
        self.stop_line_motor.setVisible(False)

    def stop_plotting(self):
        self.plotting = False
        self.stop_line_error.setVisible(True)
        self.stop_line_motor.setVisible(True)
        # Log stop row
        self.t += 1
        self.logger.writerow([self.t,"STOP","","","","","",""])

    def update_data(self, r, p, m1, m2, m3, m4):
        MAX_POINTS = 200
        if not self.plotting:
            return

        self.t += 1
        self.xdata.append(self.t)
        self.roll_err.append(r)
        self.pitch_err.append(p)
        self.m1.append(m1)
        self.m2.append(m2)
        self.m3.append(m3)
        self.m4.append(m4)

        # log data
        self.logger.writerow([self.t,r,p,m1,m2,m3,m4])

        # keep only last MAX_POINTS points
        if len(self.xdata) > MAX_POINTS:
            self.xdata = self.xdata[-MAX_POINTS:]
            self.roll_err = self.roll_err[-MAX_POINTS:]
            self.pitch_err = self.pitch_err[-MAX_POINTS:]
            self.m1 = self.m1[-MAX_POINTS:]
            self.m2 = self.m2[-MAX_POINTS:]
            self.m3 = self.m3[-MAX_POINTS:]
            self.m4 = self.m4[-MAX_POINTS:]

        # update plots
        self.curve_roll.setData(self.xdata, self.roll_err)
        self.curve_pitch.setData(self.xdata, self.pitch_err)
        self.curve_m1.setData(self.xdata, self.m1)
        self.curve_m2.setData(self.xdata, self.m2)
        self.curve_m3.setData(self.xdata, self.m3)
        self.curve_m4.setData(self.xdata, self.m4)

    def closeEvent(self, e):
        self.reader.stop()
        self.log_file.close()
        e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
