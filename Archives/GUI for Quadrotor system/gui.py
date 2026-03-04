import sys
import socket
import time
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QLineEdit, QFrame
    , QGraphicsProxyWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon
import pyqtgraph as pg


## ----------------- STYLES -----------------

def red_border(widget, radius=10):
    widget.setStyleSheet(f"""
        QFrame {{
            background-color: black;
            border: 2px solid red;
            border-radius: {radius}px;
        }}
        QLabel {{
            color: white;
        }}
    """)


def top_button_style(btn):
    btn.setFixedHeight(45)
    btn.setFixedWidth(140)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #b00000;
            color: white;
            font-size: 15px;
            font-weight: bold;
            border-radius: 8px;
        }
        QPushButton:hover {
            background-color: #cc0000;
        }
    """)


def plot_style(plot, xlabel, ylabel):
    plot.setBackground('k')
    plot.showGrid(x=False, y=False)

    plot.setLabel('bottom', xlabel, color='white')
    plot.setLabel('left', ylabel, color='white')

    plot.getAxis('bottom').setPen('w')
    plot.getAxis('left').setPen('w')
    plot.getAxis('bottom').setTextPen('w')
    plot.getAxis('left').setTextPen('w')

    plot.getPlotItem().layout.setContentsMargins(10, 10, 10, 10)


def plot_border(plot):
    plot.setStyleSheet("""
        PlotWidget {
            background-color: black;
            border: 3px solid #b00000;
            border-radius: 7px;
        }
    """)

def add_autoscale_button(plot):
    btn = QPushButton("AUTO")
    btn.setCheckable(True)
    btn.setChecked(True)
    btn.setFixedSize(60, 22)

    btn.setStyleSheet("""
        QPushButton {
            background-color: #b00000;
            color: white;
            font-size: 10px;
            font-weight: bold;
            border-radius: 5px;
        }
        QPushButton:checked {
            background-color: #b00000;
        }
        QPushButton:!checked {
            background-color: #303030;
            color: #aaaaaa;
        }
    """)

    proxy = QGraphicsProxyWidget()
    proxy.setWidget(btn)
    plot.scene().addItem(proxy)

    # fixed top-left position inside plot
    proxy.setPos(8, 8)

    vb = plot.getViewBox()
    vb.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)

    def toggle_autoscale(state):
        if state:
            btn.setText("AUTO")
            vb.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)
        else:
            btn.setText("FIXED")
            vb.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=False)

    btn.toggled.connect(toggle_autoscale)

    return btn


# ----------------- HELPER FUNCTIONS -----------------

def start_esp32_connection_monitor(status_label, esp32_ip="192.168.4.1", interval_ms=1000):
    timer = QTimer()

    def check_connection():
        connected = False
        try:
            sock = socket.create_connection((esp32_ip, 80), timeout=0.5)
            sock.close()
            connected = True
        except Exception:
            connected = False

        if connected:
            status_label.setText("● CONNECTED")
            status_label.setStyleSheet(
                "color: #00ff66; font-weight: bold; padding-left: 20px;"
            )
        else:
            status_label.setText("● DISCONNECTED")
            status_label.setStyleSheet(
                "color: red; font-weight: bold; padding-left: 20px;"
            )

    timer.timeout.connect(check_connection)
    timer.start(interval_ms)

    return timer


# ----------------- TOP PANEL -----------------

def create_top_panel():
    frame = QWidget()
    layout = QHBoxLayout(frame)
    layout.setAlignment(Qt.AlignCenter)

    buttons = ["ARM", "DISARM", "CALIBRATE", "LAND", "RTL"]
    for b in buttons:
        btn = QPushButton(b)
        top_button_style(btn)
        layout.addWidget(btn)

    status = QLabel("● DISCONNECTED")
    status.setStyleSheet("color: red; font-weight: bold; padding-left: 20px;")
    layout.addWidget(status)

    return frame, status


# ----------------- MID PANEL -----------------

def create_mid_left():
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setSpacing(12)
    layout.setContentsMargins(6, 6, 6, 6)

    rp_plot = pg.PlotWidget()
    yaw_plot = pg.PlotWidget()

    rp_plot.setTitle("Roll & Pitch vs Time", color="w")
    yaw_plot.setTitle("Yaw vs Time", color="w")

    plot_style(rp_plot, "Time (s)", "Angle (deg)")
    plot_style(yaw_plot, "Time (s)", "Yaw (deg)")

    plot_border(rp_plot)
    plot_border(yaw_plot)

    # ---- Legend ----
    rp_plot.addLegend(offset=(10, 10))
    yaw_plot.addLegend(offset=(10, 10))

    # ---- Autoscale toggle ----
    add_autoscale_button(rp_plot)
    add_autoscale_button(yaw_plot)

    layout.addWidget(rp_plot)
    layout.addWidget(yaw_plot)

    return container, rp_plot, yaw_plot


def create_mid_map():
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(4, 4, 4, 4)

    map_plot = pg.PlotWidget()

    # --- Map behavior ---
    map_plot.setAspectLocked(True)
    vb = map_plot.getViewBox()
    vb.enableAutoRange(pg.ViewBox.XYAxes, True)
    vb.setMouseEnabled(x=True, y=True)

    # --- Labels ---
    map_plot.setLabel('bottom', "Longitude (deg)", color='white')
    map_plot.setLabel('left', "Latitude (deg)", color='white')

    # --- Enable full rectangular axes ---
    for ax in ('bottom', 'top', 'left', 'right'):
        axis = map_plot.getAxis(ax)
        axis.setVisible(True)
        axis.setPen(pg.mkPen("#9f9999", width=1))
        axis.setTextPen(pg.mkPen("#9f9999"))
        axis.setStyle(
            tickTextOffset=10,
            autoExpandTextSpace=True
        )

    # --- Hide numeric labels on top & right (ticks remain) ---
    map_plot.getAxis('top').setStyle(showValues=True)
    map_plot.getAxis('right').setStyle(showValues=True)

    # --- Remove widget border ---
    map_plot.setStyleSheet("""
        PlotWidget {
            background-color: black;
            border: none;
        }
    """)

    layout.addWidget(map_plot)
    return container, map_plot

def create_mid_right():
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setSpacing(12)
    layout.setContentsMargins(6, 6, 6, 6)

    pwm_plot = pg.PlotWidget()
    alt_plot = pg.PlotWidget()

    pwm_plot.setTitle("Motor PWM vs Time", color="w")
    alt_plot.setTitle("Altitude vs Time", color="w")

    plot_style(pwm_plot, "Time (s)", "PWM (µs)")
    plot_style(alt_plot, "Time (s)", "Altitude (m)")

    plot_border(pwm_plot)
    plot_border(alt_plot)

    pwm_plot.addLegend(offset=(10, 10))
    alt_plot.addLegend(offset=(10, 10))

    add_autoscale_button(pwm_plot)
    add_autoscale_button(alt_plot)

    layout.addWidget(pwm_plot)
    layout.addWidget(alt_plot)

    return container, pwm_plot, alt_plot

def create_mid_panel():
    frame = QWidget()
    layout = QHBoxLayout(frame)

    left, rp_plot, yaw_plot = create_mid_left()
    mid, map_plot = create_mid_map()
    right, pwm_plot, alt_plot = create_mid_right()

    layout.addWidget(left, 7)
    layout.addWidget(mid, 11)
    layout.addWidget(right, 7)

    return frame, rp_plot, yaw_plot, map_plot, pwm_plot, alt_plot


# ----------------- BOTTOM PANEL -----------------

def create_bottom_left():
    frame = QFrame()
    red_border(frame)

    layout = QVBoxLayout(frame)
    layout.setSpacing(10)
    layout.setContentsMargins(10, 10, 10, 10)

    # --- Row 1: Motors + Mode + Baro ---
    row1 = QLabel(
        "MOTORS & SYSTEM\n"
        "M1: ---   M2: ---   M3: ---   M4: ---\n"
        "Flight Mode: ---\n"
        "Baro Temp: --- °C    Pressure: --- Pa"
    )

    # --- Row 2: GPS + Altitude + Attitude ---
    row2 = QLabel(
        "NAVIGATION & ATTITUDE\n"
        "Lat: ---    Lon: ---\n"
        "GPS Alt: --- m    Baro Alt: --- m\n"
        "Roll: ---°   Pitch: ---°   Yaw: ---°"
    )

    # --- Styling (bigger, readable, oriented) ---
    common_style = """
        QLabel {
            color: white;
            font-size: 16px;
            font-family: Consolas, Courier, monospace;
            line-height: 1.4;
        }
    """
    row1.setStyleSheet(common_style)
    row2.setStyleSheet(common_style)

    layout.addWidget(row1)
    layout.addWidget(row2)

    return frame, row1, row2


def create_bottom_right():
    frame = QFrame()
    red_border(frame)

    main_layout = QHBoxLayout(frame)
    main_layout.setContentsMargins(8, 8, 8, 8)
    main_layout.setSpacing(8)

    # ================= LEFT: TERMINAL =================
    left_panel = QVBoxLayout()
    left_panel.setSpacing(8)

    output = QTextEdit()
    output.setReadOnly(True)
    output.setStyleSheet("""
        QTextEdit {
            background-color: black;
            color: #00ff66;
            border: none;
            font-family: Consolas, Courier, monospace;
            font-size: 12px;
        }
    """)
    output.setText("> Terminal ready...\n")

    cmd = QLineEdit()
    cmd.setPlaceholderText("command >")
    cmd.setStyleSheet("""
        QLineEdit {
            background-color: black;
            color: white;
            border: 1px solid #9f9999;
            border-radius: 4px;
            padding: 6px;
            font-family: Consolas, Courier, monospace;
            font-size: 12px;
        }
    """)

    exec_btn = QPushButton("EXECUTE")
    exec_btn.setFixedSize(90, 34)
    exec_btn.setStyleSheet("""
        QPushButton {
            background-color: #b00000;
            color: white;
            font-weight: bold;
            border-radius: 6px;
        }
        QPushButton:hover {
            background-color: #d00000;
        }
    """)

    cmd_bar = QHBoxLayout()
    cmd_bar.addWidget(cmd, 1)
    cmd_bar.addWidget(exec_btn)

    left_panel.addWidget(output, 1)
    left_panel.addLayout(cmd_bar)

    # ================= RIGHT: COMMAND PALETTE =================
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("border: none;")

    cmd_container = QWidget()
    cmd_layout = QVBoxLayout(cmd_container)
    cmd_layout.setSpacing(6)
    cmd_layout.setContentsMargins(4, 4, 4, 4)

    # Command templates (label → text inserted)
    command_templates = {
        "GOTO": "goto __m",
        "MOVE": "move x y z",

        "HOLD": "hold",
        "HOLD FOR": "hold __s",

        "STOP": "stop",

        "TAKEOFF": "takeoff __m",
        "LAND": "land",
        "EMERGENCY LAND": "eland",

        "ARM": "arm",
        "DISARM": "disarm",
        "STATUS": "status",

        "MISSION START": "mission start",
        "MISSION PAUSE": "mission pause",
        "MISSION RESUME": "mission resume",
        "MISSION ABORT": "mission abort",
    }

    def make_cmd_button(label, text):
        btn = QPushButton(label)
        btn.setFixedHeight(34)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #202020;
                color: white;
                border: 1px solid #9f9999;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #303030;
            }
        """)
        btn.clicked.connect(lambda: cmd.setText(text))
        return btn

    for label, text in command_templates.items():
        cmd_layout.addWidget(make_cmd_button(label, text))

    cmd_layout.addStretch()
    scroll.setWidget(cmd_container)
    scroll.setFixedWidth(140)

    # ================= ASSEMBLE =================
    main_layout.addLayout(left_panel, 1)
    main_layout.addWidget(scroll)

    return frame, output, cmd


def create_bottom_panel():
    frame = QWidget()
    layout = QHBoxLayout(frame)

    left, col1, col2 = create_bottom_left()
    right, output, cmd = create_bottom_right()

    layout.addWidget(left, 2)
    layout.addWidget(right, 3)

    return frame, col1, col2, output, cmd


# ----------------- MAIN -----------------

def main():
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("GCS")
    window.setWindowIcon(QIcon("GUI for Quadrotor system/logo.ico"))
    window.setStyleSheet("background-color: black;")

    layout = QVBoxLayout(window)

    top, status = create_top_panel()
    conn_timer = start_esp32_connection_monitor(status)
    
    mid, rp_plot, yaw_plot, map_plot, pwm_plot, alt_plot = create_mid_panel()
    bottom, col1, col2, output, cmd = create_bottom_panel()

    layout.addWidget(top, 1)
    layout.addWidget(mid, 7)
    layout.addWidget(bottom, 3)

    # ---- CURVES ----
    t = np.arange(200)

    roll_c = rp_plot.plot(pen='r')
    pitch_c = rp_plot.plot(pen='g')
    yaw_c = yaw_plot.plot(pen='b')

    pwm_c = [pwm_plot.plot(pen=pg.intColor(i)) for i in range(4)]
    alt_c = alt_plot.plot(pen='y')

    gps_c = map_plot.plot(pen='c', symbol='o')

    def update():
        roll = np.sin(t / 15) * 30
        pitch = np.cos(t / 20) * 20
        yaw = np.sin(t / 25) * 90

        roll_c.setData(t, roll)
        pitch_c.setData(t, pitch)
        yaw_c.setData(t, yaw)

        for i, c in enumerate(pwm_c):
            c.setData(t, 1200 + i * 50 + 100 * np.sin(t / 10))

        alt_c.setData(t, np.abs(np.sin(t / 30) * 60))

        lat = 12.0 + np.sin(t / 100) * 0.001
        lon = 77.0 + np.cos(t / 100) * 0.001
        gps_c.setData(lon, lat)
        map_plot.autoRange()

    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(100)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
