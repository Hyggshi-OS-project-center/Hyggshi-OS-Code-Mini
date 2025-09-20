from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

def show_quick_window(title="Quick Window", message="Triển khai cửa sổ nhanh với Cython!"):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    win = QWidget()
    win.setWindowTitle(title)
    win.setFixedSize(340, 120)
    layout = QVBoxLayout(win)
    label = QLabel(message)
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)
    win.show()
    app.exec_()