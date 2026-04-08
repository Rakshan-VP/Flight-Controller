import sys
import serial
import json
import serial.tools.list_ports
import time
import os

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "params_db.json")


# ---------- SERIAL ----------
class SerialManager:
    def __init__(self):
        self.ser = None

    def connect(self, port):
        self.ser = serial.Serial(port, 115200, timeout=1)
        QThread.msleep(800)
        self.ser.reset_input_buffer()

    def disconnect(self):
        if self.ser:
            self.ser.close()
            self.ser = None

    def write_chunks(self, data, chunk_size=64):
        self.ser.reset_input_buffer()
        for i in range(0, len(data), chunk_size):
            self.ser.write(data[i:i + chunk_size])
            self.ser.flush()
            time.sleep(0.01)

    def read_line(self):
        return self.ser.readline().decode(errors="ignore").strip()

    def read_block(self, timeout=2):
        buffer = ""
        end_time = time.time() + timeout

        while time.time() < end_time:
            line = self.read_line()
            if line:
                buffer += line
                if "START" in buffer and "END" in buffer:
                    return buffer
        return None


# ---------- DB ----------
class DBManager:
    @staticmethod
    def load():
        if not os.path.exists(DB_FILE):
            return []
        with open(DB_FILE, "r") as f:
            return json.load(f)

    @staticmethod
    def save(data):
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=2)


# ---------- GUI ----------
class GUI(QWidget):
    def __init__(self):
        super().__init__()

        self.serial = SerialManager()
        self.connected = False
        self.groups = set()

        self.init_ui()
        self.apply_theme()
        self.set_controls_enabled(False)

    # ---------- UI ----------
    def init_ui(self):
        self.setWindowTitle("Parameter Manager")
        self.resize(1000, 650)

        layout = QVBoxLayout()

        # Top bar
        self.portBox = QComboBox()
        self.refreshBtn = QPushButton("Refresh")
        self.connectBtn = QPushButton("Connect")
        self.statusLabel = QLabel("🔴 Disconnected")

        self.refreshBtn.clicked.connect(self.refresh_ports)
        self.connectBtn.clicked.connect(self.toggle_connection)

        top = QHBoxLayout()
        for w in [self.portBox, self.refreshBtn, self.connectBtn, self.statusLabel]:
            top.addWidget(w)
        layout.addLayout(top)

        # Search
        self.searchBox = QLineEdit()
        self.searchBox.setPlaceholderText("Search by parameter name...")
        self.searchBox.textChanged.connect(self.filter_table)
        layout.addWidget(self.searchBox)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Group", "Name", "Value", "Default", "Description"]
        )
        self.setup_table()
        layout.addWidget(self.table)

        # Buttons
        self.loadBtn = QPushButton("Load")
        self.addBtn = QPushButton("Add")
        self.delBtn = QPushButton("Delete")
        self.writeBtn = QPushButton("WRITE")

        self.loadBtn.clicked.connect(self.load)
        self.addBtn.clicked.connect(self.add_row)
        self.delBtn.clicked.connect(self.delete_row)
        self.writeBtn.clicked.connect(self.write)

        btns = QHBoxLayout()
        for b in [self.loadBtn, self.addBtn, self.delBtn, self.writeBtn]:
            btns.addWidget(b)
        layout.addLayout(btns)

        # Log
        self.logBox = QTextEdit()
        self.logBox.setReadOnly(True)
        layout.addWidget(self.logBox)

        self.setLayout(layout)
        self.refresh_ports()

    def setup_table(self):
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)

    # ---------- HELPERS ----------
    def log(self, text):
        self.logBox.append(text)

    def set_controls_enabled(self, state):
        for w in [self.loadBtn, self.addBtn, self.delBtn, self.writeBtn]:
            w.setEnabled(state)

    # ---------- GROUP SYSTEM ----------
    def _create_group_combo(self, value=""):
        combo = QComboBox()
        combo.setEditable(True)

        combo.addItems(sorted(self.groups))

        if value and value not in self.groups:
            combo.addItem(value)

        combo.setCurrentText(value)

        combo.lineEdit().editingFinished.connect(
            lambda: self._register_group(combo.currentText())
        )

        return combo

    def _register_group(self, group):
        if group and group not in self.groups:
            self.groups.add(group)
            self._refresh_group_dropdowns()

    def _refresh_group_dropdowns(self):
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if isinstance(widget, QComboBox):
                current = widget.currentText()

                widget.blockSignals(True)
                widget.clear()
                widget.addItems(sorted(self.groups))
                widget.setCurrentText(current)
                widget.blockSignals(False)

    # ---------- TABLE ----------
    def _get_table_row(self, row):
        combo = self.table.cellWidget(row, 0)

        return {
            "g": combo.currentText() if combo else "",
            "n": self.table.item(row, 1).text(),
            "v": float(self.table.item(row, 2).text()),
            "d": float(self.table.item(row, 3).text()),
            "desc": self.table.item(row, 4).text()
        }

    def _set_table_row(self, row, p):
        combo = self._create_group_combo(p["g"])
        self.table.setCellWidget(row, 0, combo)

        self._register_group(p["g"])

        self.table.setItem(row, 1, QTableWidgetItem(p["n"]))
        self.table.setItem(row, 2, QTableWidgetItem(str(p["v"])))
        self.table.setItem(row, 3, QTableWidgetItem(str(p["d"])))
        self.table.setItem(row, 4, QTableWidgetItem(p["desc"]))

    # ---------- PORTS ----------
    def refresh_ports(self):
        self.portBox.clear()
        for port in serial.tools.list_ports.comports():
            self.portBox.addItem(port.device)

    # ---------- CONNECTION ----------
    def toggle_connection(self):
        if not self.connected:
            try:
                self.serial.connect(self.portBox.currentText())
                self.connected = True
                self.statusLabel.setText("🟢 Connected")
                self.connectBtn.setText("Disconnect")
                self.set_controls_enabled(True)
                QTimer.singleShot(300, self.load)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            self.serial.disconnect()
            self.connected = False
            self.statusLabel.setText("🔴 Disconnected")
            self.connectBtn.setText("Connect")
            self.set_controls_enabled(False)
            self.table.setRowCount(0)
            self.log("Disconnected")

    # ---------- SEARCH ----------
    def filter_table(self):
        text = self.searchBox.text().lower()
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 1).text().lower()
            self.table.setRowHidden(row, text not in name)

    # ---------- LOAD ----------
    def load(self):
        if not self.connected:
            QMessageBox.warning(self, "Error", "Not connected")
            return

        self.table.setRowCount(0)

        self.serial.ser.write(b"GET\n")
        self.log(">> GET")

        buffer = self.serial.read_block()
        if not buffer:
            QMessageBox.warning(self, "Error", "Timeout")
            return

        try:
            data = buffer.split("START")[1].split("END")[0]
            esp = json.loads(data)
        except:
            QMessageBox.warning(self, "Error", "Invalid data")
            return

        db = DBManager.load()
        self.groups = {p["g"] for p in db if p.get("g")}
        db_map = {p["n"]: p for p in db}

        for p in esp:
            merged = db_map.get(p["n"], {"g": "", "n": p["n"], "d": 0, "desc": ""})
            merged["v"] = p["v"]

            r = self.table.rowCount()
            self.table.insertRow(r)
            self._set_table_row(r, merged)

    # ---------- ADD / DELETE ----------
    def add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        self._set_table_row(r, {"g": "", "n": "", "v": 0, "d": 0, "desc": ""})

    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    # ---------- WRITE ----------
    def write(self):
        if QMessageBox.question(
                self, "Confirm", "Overwrite ALL parameters?",
                QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return

        try:
            esp_params = [
                {"n": self.table.item(r, 1).text(),
                 "v": float(self.table.item(r, 2).text())}
                for r in range(self.table.rowCount())
            ]
        except:
            QMessageBox.warning(self, "Error", "Invalid table data")
            return

        cmd = f"SET_ALL|{json.dumps(esp_params)}\n"
        self.log(">> " + cmd[:80] + "...")

        self.serial.write_chunks(cmd.encode())

        resp = self.wait_for_ack()

        if resp == "OK":
            DBManager.save([
                {
                    "g": self._get_table_row(r)["g"],
                    "n": self._get_table_row(r)["n"],
                    "d": self._get_table_row(r)["d"],
                    "desc": self._get_table_row(r)["desc"]
                }
                for r in range(self.table.rowCount())
            ])
            QMessageBox.information(self, "Success", "Saved")
        else:
            QMessageBox.critical(self, "Error", resp)

    # ---------- ACK ----------
    def wait_for_ack(self, timeout=2):
        buffer = ""
        end = time.time() + timeout

        while time.time() < end:
            line = self.serial.read_line()
            if not line:
                continue

            self.log("<< " + line)
            buffer += line

            if "OK" in buffer:
                return "OK"

        return "TIMEOUT"

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


# ---------- MAIN ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = GUI()
    w.show()
    sys.exit(app.exec_())