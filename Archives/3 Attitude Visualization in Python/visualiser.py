import sys
import re
import serial
import serial.tools.list_ports
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QComboBox,
                             QHBoxLayout, QVBoxLayout, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from vispy import scene
from vispy.geometry import create_box
from vispy.visuals.transforms import MatrixTransform
from dark_theme import dark_stylesheet

# Regex to extract Roll, Pitch, Yaw
pattern = re.compile(r"Roll:\s*(-?\d+\.?\d*),\s*Pitch:\s*(-?\d+\.?\d*),\s*Yaw:\s*(-?\d+\.?\d*)")


class SerialReaderThread(QThread):
    data_received = pyqtSignal(float, float, float)
    error_occurred = pyqtSignal(str)

    def __init__(self, ser):
        super().__init__()
        self.ser = ser
        self.running = True

    def run(self):
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    match = pattern.search(line)
                    if match:
                        roll, pitch, yaw = map(float, match.groups())
                        self.data_received.emit(roll, pitch, yaw)
            except Exception as e:
                self.error_occurred.emit(str(e))
                break

    def stop(self):
        self.running = False
        self.wait()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attitude Visualiser")
        self.ser = None
        self.reader_thread = None
        self.latest_rpy = (0.0, 0.0, 0.0)  # Store latest RPY for throttled updates

        self.init_ui()
        self.init_vispy()
        self.init_timer()

    def init_ui(self):
        # Layouts
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        rpy_layout = QHBoxLayout()

        # COM port selection
        self.com_label = QLabel("COM:")
        self.com_box = QComboBox()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.com_box.addItems(ports)

        # Baud rate selection
        self.baud_label = QLabel("Baud:")
        self.baud_box = QComboBox()
        self.baud_box.addItems(['9600', '19200', '38400', '57600', '115200', '230400', '460800'])
        self.baud_box.setCurrentText('115200')

        # Status label
        self.status_label = QLabel("Not Connected")
        self.status_label.setStyleSheet("color: red; font-weight: bold")

        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)

        # Add widgets to top layout
        top_layout.addWidget(self.com_label)
        top_layout.addWidget(self.com_box)
        top_layout.addWidget(self.baud_label)
        top_layout.addWidget(self.baud_box)
        top_layout.addWidget(self.status_label)
        top_layout.addWidget(self.connect_btn)

        # RPY Display labels
        self.roll_label = QLabel("Roll:")
        self.roll_label.setStyleSheet("color: red; font-size: 16px;")
        self.roll_value = QLabel("--")
        self.roll_value.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")

        self.pitch_label = QLabel("Pitch:")
        self.pitch_label.setStyleSheet("color: blue; font-size: 16px;")
        self.pitch_value = QLabel("--")
        self.pitch_value.setStyleSheet("color: blue; font-weight: bold; font-size: 16px;")

        self.yaw_label = QLabel("Yaw:")
        self.yaw_label.setStyleSheet("color: green; font-size: 16px;")
        self.yaw_value = QLabel("--")
        self.yaw_value.setStyleSheet("color: green; font-weight: bold; font-size: 16px;")

        # Add RPY widgets to layout
        rpy_layout.addWidget(self.roll_label)
        rpy_layout.addWidget(self.roll_value)
        rpy_layout.addSpacing(20)
        rpy_layout.addWidget(self.pitch_label)
        rpy_layout.addWidget(self.pitch_value)
        rpy_layout.addSpacing(20)
        rpy_layout.addWidget(self.yaw_label)
        rpy_layout.addWidget(self.yaw_value)

        # Add all layouts to main layout
        main_layout.addLayout(top_layout)
        main_layout.addSpacing(10)
        main_layout.addLayout(rpy_layout)

        # VisPy canvas placeholder (will be added later)
        self.setLayout(main_layout)

    def init_vispy(self):
        from vispy import visuals

        # Create VisPy canvas and add as child widget to this window
        self.canvas = scene.SceneCanvas(keys='interactive', size=(600, 400))
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.TurntableCamera(fov=30, azimuth=135, elevation=30, distance=5)
        self.view.camera.interactive = False

        # Create cuboid
        vertices, faces, _ = create_box(width=1, height=0.4, depth=1)
        positions = vertices['position']
        self.cuboid = scene.visuals.Mesh(vertices=positions, faces=faces,
                                        color=(0.6, 1.0, 0.2, 1), shading='smooth',
                                        parent=self.view.scene)

        # Create a new parent node for local axes attached to cuboid
        self.local_axes = scene.Node(parent=self.cuboid)

        # Local axes arrows (rotate with cuboid)
        local_axes = {
            'X': ([0, 0, 0], [1, 0, 0], 'red', 'X'),
            'Y': ([0, 0, 0], [0, 1, 0], 'blue', 'Y'),
            'Z': ([0, 0, 0], [0, 0, 1], 'green', 'Z')
        }
        for start, end, color, label in local_axes.values():
            scene.visuals.Arrow(pos=np.array([start, end]), color=color,
                                arrow_size=10, arrow_type='stealth', width=2,
                                parent=self.local_axes)
            scene.visuals.Text(text=label, color=color, font_size=36,
                               pos=np.array(end) + 0.2, parent=self.local_axes,
                               anchor_x='center', anchor_y='bottom')

        # Set the transform of the cuboid mesh (and thus local axes)
        self.transform = MatrixTransform()
        self.cuboid.transform = self.transform

        # Add the VisPy canvas widget to the main layout below existing widgets
        self.layout().addWidget(self.canvas.native)

        # ----- Plot setup -----
        self.plot_data_length = 100  # max points to show
        self.time_data = []  # timestamps (simple index counter)
        self.roll_data = []
        self.pitch_data = []
        self.yaw_data = []

        # Create a separate canvas for the plots below cuboid
        self.plot_canvas = scene.SceneCanvas(keys='interactive', size=(600, 200), bgcolor='black')
        self.plot_view = self.plot_canvas.central_widget.add_view()

        # 2D camera for plots (pan/zoom)
        self.plot_view.camera = scene.PanZoomCamera(rect=[0, -180, self.plot_data_length, 360])
        self.plot_view.camera.flip = (False, True)  # Flip y-axis for natural orientation
        self.plot_view.camera.interactive = False

        # Create line visuals for Roll, Pitch, Yaw
        self.roll_line = scene.visuals.Line(color='red', parent=self.plot_view.scene)
        self.pitch_line = scene.visuals.Line(color='blue', parent=self.plot_view.scene)
        self.yaw_line = scene.visuals.Line(color='green', parent=self.plot_view.scene)

        # --- Add axis lines ---
        # X-axis line: from (0, 0) to (plot_data_length, 0)
        x_axis_pts = np.array([[0, 0], [self.plot_data_length, 0]])
        self.x_axis_line = scene.visuals.Line(pos=x_axis_pts, color='white', parent=self.plot_view.scene, width=1)

        # Y-axis line: vertical line at x=0 from y=-180 to y=180
        y_axis_pts = np.array([[0, -180], [0, 180]])
        self.y_axis_line = scene.visuals.Line(pos=y_axis_pts, color='white', parent=self.plot_view.scene, width=1)

        # Add plot canvas widget below main canvas
        self.layout().addWidget(self.plot_canvas.native)

        # Plot paused flag (start paused, only run when connected)
        self.plot_paused = True
        self.data_index = 0

    def init_timer(self):
        self.update_timer = QTimer()
        self.update_timer.setInterval(150)  
        self.update_timer.timeout.connect(self.update_vispy_and_labels)
        self.update_timer.start()

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port = self.com_box.currentText()
        try:
            baud = int(self.baud_box.currentText())
            self.ser = serial.Serial(port, baudrate=baud, timeout=1)
            self.reader_thread = SerialReaderThread(self.ser)
            self.reader_thread.data_received.connect(self.store_latest_rpy)
            self.reader_thread.error_occurred.connect(self.handle_error)
            self.reader_thread.start()
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; font-weight: bold")
            self.connect_btn.setText("Disconnect")
            self.plot_paused = False  # Resume plotting on connect
        except Exception as e:
            QMessageBox.critical(self, "Connection Failed", str(e))
            self.status_label.setText("Not Connected")
            self.status_label.setStyleSheet("color: red; font-weight: bold")
            self.plot_paused = True  # Pause plotting on failure

    def disconnect_serial(self):
        if self.reader_thread:
            self.reader_thread.stop()
            self.reader_thread = None
        if self.ser:
            self.ser.close()
            self.ser = None
        self.status_label.setText("Not Connected")
        self.status_label.setStyleSheet("color: red; font-weight: bold")
        self.connect_btn.setText("Connect")
        self.roll_value.setText("--")
        self.pitch_value.setText("--")
        self.yaw_value.setText("--")
        self.plot_paused = True  # Pause plotting on disconnect

    def store_latest_rpy(self, roll, pitch, yaw):
        self.latest_rpy = (roll, pitch, yaw)

    def update_vispy_and_labels(self):
        roll, pitch, yaw = self.latest_rpy

        # Update text labels
        self.roll_value.setText(f"{roll:.2f}")
        self.pitch_value.setText(f"{pitch:.2f}")
        self.yaw_value.setText(f"{yaw:.2f}")

        # Update cuboid rotation
        r, p, y = np.radians([roll, pitch, yaw])
        Rx = np.array([[1, 0, 0],
                       [0, np.cos(r), -np.sin(r)],
                       [0, np.sin(r), np.cos(r)]])
        Ry = np.array([[np.cos(p), 0, np.sin(p)],
                       [0, 1, 0],
                       [-np.sin(p), 0, np.cos(p)]])
        Rz = np.array([[np.cos(y), -np.sin(y), 0],
                       [np.sin(y), np.cos(y), 0],
                       [0, 0, 1]])
        R = Rz @ Ry @ Rx
        matrix = np.eye(4)
        matrix[:3, :3] = R
        self.transform.matrix = matrix
        self.canvas.update()

        if not self.plot_paused:
            self.data_index += 1
            self.time_data.append(self.data_index)
            self.roll_data.append(roll)
            self.pitch_data.append(pitch)
            self.yaw_data.append(yaw)

            if len(self.time_data) > self.plot_data_length:
                self.time_data.pop(0)
                self.roll_data.pop(0)
                self.pitch_data.pop(0)
                self.yaw_data.pop(0)

            roll_points = np.column_stack((self.time_data, self.roll_data))
            pitch_points = np.column_stack((self.time_data, self.pitch_data))
            yaw_points = np.column_stack((self.time_data, self.yaw_data))

            self.roll_line.set_data(roll_points)
            self.pitch_line.set_data(pitch_points)
            self.yaw_line.set_data(yaw_points)

            # Update camera rect for scrolling effect
            xmin = max(0, self.data_index - self.plot_data_length)
            self.plot_view.camera.rect = (xmin, -180, self.plot_data_length, 360)

            # Update axis lines positions to stay aligned with scrolling plot
            # X-axis line from xmin to xmin + plot_data_length
            self.x_axis_line.set_data(np.array([[xmin, 0], [xmin + self.plot_data_length, 0]]))
            # Y-axis line fixed at xmin (vertical)
            self.y_axis_line.set_data(np.array([[xmin, -180], [xmin, 180]]))

            self.plot_canvas.update()

    def handle_error(self, error_msg):
        QMessageBox.warning(self, "Read Error", error_msg)
        self.disconnect_serial()

    def closeEvent(self, event):
        self.disconnect_serial()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_stylesheet)
    window = MainWindow()
    window.resize(620, 650)  
    window.show()
    sys.exit(app.exec())
