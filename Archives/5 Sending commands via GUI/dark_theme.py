# dark_theme.py

dark_stylesheet = """
QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

QLabel {
    font-size: 16px;
}

QComboBox, QPushButton {
    background-color: #1e1e1e;
    border: 1px solid #333;
    padding: 5px 10px;
    color: #e0e0e0;
}

QComboBox:hover, QPushButton:hover {
    background-color: #333;
}

QPushButton:pressed {
    background-color: #555;
}

QComboBox QAbstractItemView {
    background-color: #1e1e1e;
    selection-background-color: #444;
    color: #e0e0e0;
}

QMessageBox {
    background-color: #1e1e1e;
    color: #e0e0e0;
}
"""
