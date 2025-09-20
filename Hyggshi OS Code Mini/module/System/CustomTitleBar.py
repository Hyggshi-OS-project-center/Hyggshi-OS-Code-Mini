from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy, QLineEdit
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(36)
        self.setStyleSheet("""
            background: #23272e;
            color: #e8f4f8;
            border-bottom: 1px solid #2d4263;
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)

        # App icon
        icon_label = QLabel()
        icon_label.setPixmap(QIcon("icon.ico").pixmap(24, 24))
        layout.addWidget(icon_label)

        # App name
        title = QLabel("Hyggshi OS Code Mini")
        title.setStyleSheet("font-weight: bold; font-size: 15px;")
        layout.addWidget(title)

        # Spacer
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Search bar (optional)
        search = QLineEdit()
        search.setPlaceholderText("Search Hyggshi OS Code Mini")
        search.setFixedWidth(260)
        search.setStyleSheet("""
            background: #1a2332;
            border-radius: 6px;
            padding: 4px 10px;
            color: #e8f4f8;
            border: 1px solid #2d4263;
        """)
        layout.addWidget(search)

        # Window control buttons
        btn_min = QPushButton("–")
        btn_min.setFixedSize(28, 28)
        btn_min.clicked.connect(self.minimize)
        btn_min.setStyleSheet("background: none; font-size: 18px;")
        layout.addWidget(btn_min)

        btn_max = QPushButton("□")
        btn_max.setFixedSize(28, 28)
        btn_max.clicked.connect(self.maximize_restore)
        btn_max.setStyleSheet("background: none; font-size: 14px;")
        layout.addWidget(btn_max)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.clicked.connect(self.close_window)
        btn_close.setStyleSheet("background: none; color: #ef4444; font-size: 16px;")
        layout.addWidget(btn_close)

        self.start = QPoint(0, 0)
        self.pressing = False

    def mousePressEvent(self, event):
        self.start = self.mapToGlobal(event.pos())
        self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing and self.parent:
            self.parent.move(self.mapToGlobal(event.pos()) - self.start + self.parent.pos())

    def mouseReleaseEvent(self, event):
        self.pressing = False

    def minimize(self):
        if self.parent:
            self.parent.showMinimized()

    def maximize_restore(self):
        if self.parent:
            if self.parent.isMaximized():
                self.parent.showNormal()
            else:
                self.parent.showMaximized()

    def close_window(self):
        if self.parent:
            self.parent.close()