import sys
import serial
import json
import serial.tools.list_ports
import time

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class GUI(QWidget):
    def __init__(self):
        super().__init__()

        self.ser = None
        self.connected = False

        self.setWindowTitle("Parameter Manager")
        self.resize(900, 600)

        layout = QVBoxLayout()

        # ---------- TOP BAR ----------
        self.portBox = QComboBox()
        self.refresh_ports()

        self.refreshBtn = QPushButton("⟳")
        self.refreshBtn.clicked.connect(self.refresh_ports)

        self.connectBtn = QPushButton("Connect")
        self.connectBtn.clicked.connect(self.toggle_connection)

        self.statusLabel = QLabel("🔴 Disconnected")

        top = QHBoxLayout()
        top.addWidget(self.portBox)
        top.addWidget(self.refreshBtn)
        top.addWidget(self.connectBtn)
        top.addWidget(self.statusLabel)

        layout.addLayout(top)

        # ---------- TABLE ----------
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Units", "Min", "Max"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.table)

        # ---------- BUTTONS ----------
        btns = QHBoxLayout()

        self.loadBtn = QPushButton("Load")
        self.loadBtn.clicked.connect(self.load)

        self.addBtn = QPushButton("Add")
        self.addBtn.clicked.connect(self.add_row)

        self.delBtn = QPushButton("Delete")
        self.delBtn.clicked.connect(self.delete_row)

        self.writeBtn = QPushButton("WRITE")
        self.writeBtn.clicked.connect(self.write)

        btns.addWidget(self.loadBtn)
        btns.addWidget(self.addBtn)
        btns.addWidget(self.delBtn)
        btns.addWidget(self.writeBtn)

        layout.addLayout(btns)

        # ---------- SERIAL LOG ----------
        self.logBox = QTextEdit()
        self.logBox.setReadOnly(True)
        layout.addWidget(self.logBox)

        self.setLayout(layout)

        self.set_controls_enabled(False)
        self.apply_theme()

    # ---------- LOG ----------
    def log(self, text):
        self.logBox.append(text)

    # ---------- ENABLE/DISABLE ----------
    def set_controls_enabled(self, state):
        self.loadBtn.setEnabled(state)
        self.addBtn.setEnabled(state)
        self.delBtn.setEnabled(state)
        self.writeBtn.setEnabled(state)

    # ---------- PORTS ----------
    def refresh_ports(self):
        self.portBox.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.portBox.addItem(port.device)

    # ---------- CONNECT ----------
    def toggle_connection(self):
        if not self.connected:
            self.connect_serial()
        else:
            self.disconnect_serial()

    def connect_serial(self):
        try:
            port = self.portBox.currentText()
            self.ser = serial.Serial(port, 115200, timeout=1)

            # 🔥 Give ESP32 time to boot
            QThread.msleep(800)

            # 🔥 Flush ALL garbage
            self.ser.reset_input_buffer()

            # 🔥 Optional: small delay after flush
            QThread.msleep(100)

            self.connected = True
            self.statusLabel.setText("🟢 Connected")
            self.connectBtn.setText("Disconnect")
            self.set_controls_enabled(True)

            # 🔥 Delay before auto load (CRITICAL)
            QTimer.singleShot(300, self.load)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.ser = None

    def disconnect_serial(self):
        if self.ser:
            self.ser.close()

        self.connected = False
        self.statusLabel.setText("🔴 Disconnected")
        self.connectBtn.setText("Connect")
        self.set_controls_enabled(False)
        self.table.setRowCount(0)

    # ---------- SERIAL HELPERS ----------
    def wait_for(self, keyword, timeout=2):
        start = time.time()

        while time.time() - start < timeout:
            line = self.ser.readline().decode(errors="ignore").strip()
            if line:
                self.log("<< " + line)
            if keyword in line:
                return True
        return False

    def wait_for_ack(self, timeout=2):
        start = time.time()

        while time.time() - start < timeout:
            line = self.ser.readline().decode(errors="ignore").strip()

            if not line:
                continue

            self.log("<< " + line)

            if line in ["START", "END"]:
                continue

            if line in ["OK", "ERR_JSON", "ERR_FORMAT", "ERR_VALIDATION"]:
                return line

        return "TIMEOUT"

    # ---------- LOAD ----------
    def load(self):
        self.table.setRowCount(0)

        self.ser.reset_input_buffer()
        self.ser.write(b"GET\n")
        self.log(">> GET")

        buffer = ""
        timeout = time.time() + 2

        while time.time() < timeout:
            line = self.ser.readline().decode(errors="ignore")

            if not line:
                continue

            line = line.strip()
            self.log("<< " + line)

            buffer += line

            # 🔥 detect full frame anywhere
            if "START" in buffer and "END" in buffer:
                break

        # 🔥 Extract JSON safely
        try:
            start_idx = buffer.index("START") + len("START")
            end_idx = buffer.index("END")

            data = buffer[start_idx:end_idx].strip()
        except:
            QMessageBox.warning(self, "Error", "Invalid frame received")
            return

        if not data:
            QMessageBox.warning(self, "Error", "Empty JSON received")
            return

        try:
            params = json.loads(data)
        except Exception as e:
            QMessageBox.critical(self, "JSON Error", str(e))
            return

        for p in params:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(p["n"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(p["v"])))
            self.table.setItem(row, 2, QTableWidgetItem(p["u"]))
            self.table.setItem(row, 3, QTableWidgetItem(str(p["min"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(p["max"])))

    # ---------- ADD ----------
    def add_row(self):
        self.table.insertRow(self.table.rowCount())

    # ---------- DELETE ----------
    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    # ---------- WRITE ----------
    def write(self):
        reply = QMessageBox.question(
            self,
            "Confirm Write",
            "Overwrite ALL parameters?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        params = []

        for row in range(self.table.rowCount()):
            try:
                n = self.table.item(row, 0).text()
                v = float(self.table.item(row, 1).text())
                u = self.table.item(row, 2).text()
                mn = float(self.table.item(row, 3).text())
                mx = float(self.table.item(row, 4).text())

                if mn > mx or not (mn <= v <= mx):
                    raise ValueError

                params.append({"n": n, "v": v, "u": u, "min": mn, "max": mx})

            except:
                QMessageBox.warning(self, "Error", f"Invalid row {row}")
                return

        json_data = json.dumps(params)

        self.ser.reset_input_buffer()

        cmd = f"SET_ALL|{json_data}\n"
        self.log(">> " + cmd.strip())
        encoded_cmd = cmd.encode()
        for i in range(0, len(encoded_cmd), 64):  # Send in 64-byte chunks
            self.ser.write(encoded_cmd[i:i+64])
            self.ser.flush() # Ensure it's sent
            time.sleep(0.01) # 10ms delay between chunks

        resp = self.wait_for_ack()

        if resp == "OK":
            QMessageBox.information(self, "Success", "Saved")
        elif resp == "TIMEOUT":
            QMessageBox.critical(self, "Error", "No response from ESP32")
        else:
            QMessageBox.critical(self, "Error", resp)

    # ---------- THEME ----------
    def apply_theme(self):
        self.setStyleSheet("""
            QWidget { background-color: #0d0d0d; color: white; }
            QTableWidget { background-color: #121212; }
            QHeaderView::section { background-color: #1f7a1f; color: white; }
            QPushButton {
                background-color: #1f7a1f;
                color: white;
                padding: 6px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #2ecc71; }
            QComboBox { background-color: #1a1a1a; border: 1px solid #2ecc71; }
            QTextEdit { background-color: black; color: #00ffcc; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = GUI()
    w.show()
    sys.exit(app.exec_())