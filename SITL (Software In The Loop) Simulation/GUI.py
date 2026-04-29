import sys
import socket
import json
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QLineEdit, QTextEdit
)
from PyQt5.QtCore import QTimer,Qt

# -----------------------------
# NETWORK CONFIG
# -----------------------------
GUI_RX_PORT = 9001
FIRMWARE_IP = "127.0.0.1"
FIRMWARE_PORT = 9000

sock = None
connected = False
last_telemetry = [0.0]*12


# -----------------------------
# NETWORK SETUP
# -----------------------------
def init_socket():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", GUI_RX_PORT))
    sock.setblocking(False)


def send_message(msg):
    sock.sendto(msg.encode(), (FIRMWARE_IP, FIRMWARE_PORT))


# -----------------------------
# HANDSHAKE
# -----------------------------
def process_incoming():
    global connected, last_telemetry

    try:
        data, _ = sock.recvfrom(4096)
        msg = data.decode()

        if msg == "ACK":
            connected = True
            return

        telemetry = json.loads(msg)
        if isinstance(telemetry, list) and len(telemetry) == 12:
            last_telemetry = telemetry

    except:
        pass


# -----------------------------
# COMMAND CORE
# -----------------------------

def get_current_pos():
    return last_telemetry[0], last_telemetry[1], last_telemetry[2]


def build_setpoint(r=None, p=None, y=None, x=None, yy=None, z=None):
    return [
        r if r is not None else "-",
        p if p is not None else "-",
        y if y is not None else "-",
        x if x is not None else "-",
        yy if yy is not None else "-",
        z if z is not None else "-"
    ]


def send_setpoint(sp):
    send_message(json.dumps({
        "type": "setpoint",
        "data": sp
    }))


def send_direct(cmd):
    send_message(cmd.upper())


# -----------------------------
# COMMAND PARSER
# -----------------------------

def handle_command(cmd_text):
    cmd_text = cmd_text.strip().lower()

    # =========================
    # DIRECT COMMANDS
    # =========================
    if cmd_text in ["arm", "disarm", "kill"]:
        send_direct(cmd_text)
        return f"[CMD] {cmd_text.upper()} sent"

    # =========================
    # GOTO
    # =========================
    if cmd_text.startswith("goto"):
        try:
            args = cmd_text[5:-1].split(",")

            cx, cy, cz = get_current_pos()

            if len(args) == 3:
                x, y, z = map(float, args)
            elif len(args) == 2:
                x, y = map(float, args)
                z = cz
            elif len(args) == 1:
                z = float(args[0])
                x, y = cx, cy
            else:
                return "[ERROR] Invalid goto args"

            sp = build_setpoint(x=x, yy=y, z=z)
            send_setpoint(sp)

            return f"[CMD] GOTO → ({x:.2f}, {y:.2f}, {z:.2f})"

        except:
            return "[ERROR] Invalid goto format"

    # =========================
    # POSHOLD
    # =========================
    if cmd_text == "poshold()":
        x, y, z = get_current_pos()
        sp = build_setpoint(x=x, yy=y, z=z)
        send_setpoint(sp)
        return "[CMD] Position hold"

    # =========================
    # ALTHOLD
    # =========================
    if cmd_text.startswith("althold"):
        try:
            args = cmd_text[8:-1]

            if args == "":
                _, _, z = get_current_pos()
            else:
                z = float(args)

            sp = build_setpoint(r=0, p=0, z=z)
            send_setpoint(sp)

            return f"[CMD] Altitude hold → {z:.2f}"

        except:
            return "[ERROR] Invalid althold format"

    # =========================
    # LAND
    # =========================
    if cmd_text == "land()":
        x, y, _ = get_current_pos()
        sp = build_setpoint(x=x, yy=y, z=0)
        send_setpoint(sp)
        return "[CMD] Landing"

    # =========================
    # RTL (SEQUENCE)
    # =========================
    if cmd_text == "rtl()":
        def rtl_sequence():
            import time

            # Step 1: go home
            sp = build_setpoint(x=0, yy=0, z=15)
            send_setpoint(sp)

            time.sleep(2)

            # Step 2: land
            sp = build_setpoint(x=0, yy=0, z=0)
            send_setpoint(sp)

        threading.Thread(target=rtl_sequence, daemon=True).start()
        return "[CMD] RTL initiated"

    # =========================
    # UNKNOWN
    # =========================
    return "[WARN] Unknown command"


# -----------------------------
# GUI BUILD
# -----------------------------
def build_gui():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Drone GCS")

    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(0,0,0,0)
    main_layout.setSpacing(0)

    # =============================
    # TOP PANEL (LIGHT TELEMETRY)
    # =============================
    top_widget = QWidget()
    top_widget.setStyleSheet("""
        background-color: #F5F5F5;
        color: #111111;
        font-family: Consolas, monospace;
        font-size: 13px;
    """)

    top_layout = QHBoxLayout()
    top_layout.setContentsMargins(10,10,10,10)

    # -------- TELEMETRY (LEFT) --------
    telemetry_layout = QVBoxLayout()

    COLORS = [
        "#007ACC","#007ACC","#007ACC",   # position
        "#B58900","#B58900","#B58900",   # velocity
        "#D33682","#D33682","#D33682",   # rotation
        "#6C71C4","#6C71C4","#6C71C4"    # angular velocity
    ]

    NAMES = [
        "x","y","z",
        "vx","vy","vz",
        "r","p","y",
        "wx","wy","wz"
    ]

    state_labels = []

    for i in range(12):
        lbl = QLabel(f"{NAMES[i]}: 0.00")
        lbl.setStyleSheet(f"color:{COLORS[i]}; font-weight:bold;")
        state_labels.append(lbl)

    def make_row(start, end):
        row = QHBoxLayout()
        for i in range(start, end):
            row.addWidget(state_labels[i])
        row.addStretch()
        return row

    telemetry_layout.addLayout(make_row(0,6))
    telemetry_layout.addLayout(make_row(6,12))

    # -------- CONNECTION (RIGHT) --------
    conn_label = QLabel("● DISCONNECTED")
    conn_label.setStyleSheet("color:#FF4444; font-weight:bold;")
    conn_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

    # Layout split
    top_layout.addLayout(telemetry_layout, 4)
    top_layout.addWidget(conn_label, 1)

    top_widget.setLayout(top_layout)

    # =============================
    # BOTTOM PANEL (TERMINAL)
    # =============================
    bottom_widget = QWidget()
    bottom_widget.setStyleSheet("""
        background-color: #1E1E1E;
        color: #00FF00;
        font-family: Consolas, monospace;
        font-size: 13px;
    """)

    bottom_layout = QVBoxLayout()
    bottom_layout.setContentsMargins(10,10,10,10)

    from PyQt5.QtWidgets import QTextEdit
    terminal = QTextEdit()
    terminal.setReadOnly(True)
    terminal.setStyleSheet("background-color:#1E1E1E; border:none;")

    def log(msg, level="info"):
        color_map = {
            "info": "#00FF00",
            "cmd": "#FFFFFF",
            "warn": "#FFA500",
            "error": "#FF5555",
            "sys": "#4FC3F7"
        }
        color = color_map.get(level, "#00FF00")

        terminal.append(f'<span style="color:{color}">{msg}</span>')
        terminal.verticalScrollBar().setValue(
            terminal.verticalScrollBar().maximum()
        )

    # -------- COMMAND INPUT --------
    cmd_layout = QHBoxLayout()
    prompt = QLabel(">>>")
    prompt.setStyleSheet("color:#AAAAAA;")

    cmd_input = QLineEdit()
    cmd_input.setStyleSheet("""
        background-color:#1E1E1E;
        border:none;
        color:#FFFFFF;
    """)

    cmd_layout.addWidget(prompt)
    cmd_layout.addWidget(cmd_input)

    def on_enter():
        cmd = cmd_input.text()
        if not cmd:
            return

        log(f">>> {cmd}", "cmd")

        response = handle_command(cmd)
        log(response, "sys")

        cmd_input.clear()

    cmd_input.returnPressed.connect(on_enter)

    bottom_layout.addWidget(terminal)
    bottom_layout.addLayout(cmd_layout)

    bottom_widget.setLayout(bottom_layout)

    # =============================
    # UPDATE LOOP
    # =============================
    def update_gui():
        prev = conn_label.text()

        process_incoming()

        if connected:
            conn_label.setText("● CONNECTED")
            conn_label.setStyleSheet("color:#00AA00; font-weight:bold;")
        else:
            conn_label.setText("● DISCONNECTED")
            conn_label.setStyleSheet("color:#FF4444; font-weight:bold;")

        if prev != conn_label.text():
            log(f"[SYSTEM] {conn_label.text()}", "sys")

        for i in range(12):
            state_labels[i].setText(f"{NAMES[i]}: {last_telemetry[i]:.2f}")

    timer = QTimer()
    timer.timeout.connect(update_gui)
    timer.start(50)

    # =============================
    # HANDSHAKE LOOP
    # =============================
    def handshake_loop():
        import time
        while True:
            if not connected:
                send_message("HELLO")
            time.sleep(1)

    threading.Thread(target=handshake_loop, daemon=True).start()

    # =============================
    # FINAL LAYOUT
    # =============================
    main_layout.addWidget(top_widget)
    main_layout.addWidget(bottom_widget)

    window.setLayout(main_layout)

    log("[SYSTEM] GUI started", "sys")
    log("[SYSTEM] Waiting for firmware...", "sys")

    window.show()
    sys.exit(app.exec_())

    # -----------------------------
    # TERMINAL
    # -----------------------------
    terminal = QTextEdit()
    terminal.setReadOnly(True)

    def log(msg, level="info"):
        color_map = {
            "info": "#00FF00",
            "cmd": "#FFFFFF",
            "warn": "#FFA500",
            "error": "#FF4444",
            "sys": "#00BFFF"
        }
        color = color_map.get(level, "#00FF00")

        terminal.append(f'<span style="color:{color}">{msg}</span>')
        terminal.verticalScrollBar().setValue(
            terminal.verticalScrollBar().maximum()
        )

    # -----------------------------
    # COMMAND INPUT
    # -----------------------------
    cmd_layout = QHBoxLayout()
    prompt = QLabel(">>>")
    cmd_input = QLineEdit()

    cmd_layout.addWidget(prompt)
    cmd_layout.addWidget(cmd_input)

    # -----------------------------
    # COMMAND ENTER
    # -----------------------------
    def on_enter():
        cmd = cmd_input.text()
        if not cmd:
            return

        log(f">>> {cmd}", "cmd")

        response = handle_command(cmd)
        log(response, "sys")

        cmd_input.clear()

    cmd_input.returnPressed.connect(on_enter)

    # -----------------------------
    # UPDATE LOOP
    # -----------------------------
    def update_gui():
        prev = conn_label.text()

        process_incoming()

        if connected:
            conn_label.setText("● CONNECTED")
            conn_label.setStyleSheet("color:#00FF00; font-weight:bold;")
        else:
            conn_label.setText("● DISCONNECTED")
            conn_label.setStyleSheet("color:#FF4444; font-weight:bold;")

        if prev != conn_label.text():
            log(f"[SYSTEM] {conn_label.text()}", "sys")

        for i in range(12):
            state_labels[i].setText(f"{NAMES[i]}: {last_telemetry[i]:.2f}")

    timer = QTimer()
    timer.timeout.connect(update_gui)
    timer.start(50)

    # -----------------------------
    # HANDSHAKE LOOP
    # -----------------------------
    def handshake_loop():
        import time
        while True:
            if not connected:
                send_message("HELLO")
            time.sleep(1)

    threading.Thread(target=handshake_loop, daemon=True).start()

    # -----------------------------
    # STARTUP LOGS
    # -----------------------------
    log("[SYSTEM] GUI started", "sys")
    log("[SYSTEM] Waiting for firmware...", "sys")

    main_layout.addLayout(top_layout)
    main_layout.addWidget(terminal)
    main_layout.addLayout(cmd_layout)

    window.setLayout(main_layout)
    window.show()
    sys.exit(app.exec_())


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    init_socket()
    build_gui()