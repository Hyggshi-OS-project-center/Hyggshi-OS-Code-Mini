from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt


class WelcomeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Nền trong suốt
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent; color: #aaa;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Logo
        logo = QLabel()
        pix = QPixmap("Resources/IconFileSystem/icon.ico")
        logo.setPixmap(pix.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        layout.addSpacing(20)

        # Shortcut list container
        shortcut_container = QVBoxLayout()
        shortcut_container.setAlignment(Qt.AlignHCenter)

        shortcuts = [
            ("Show All Commands", "Ctrl + Shift + P"),
            ("Open File", "Ctrl + O"),
            ("Open Folder", "Ctrl + K Ctrl + O"),
            ("Open Recent", "Ctrl + R"),
            ("Open Chat", "Ctrl + Alt + I"),
        ]

        for desc, key in shortcuts:
            # Widget bao ngoài cho từng row
            row_widget = QWidget()
            row_widget.setStyleSheet("""
                background: rgba(50, 50, 50, 180);  /* nền xám trong suốt */
                border-radius: 6px;
            """)

            # Layout cho row
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(12, 6, 12, 6)  # padding trong box
            row.setAlignment(Qt.AlignHCenter)

            # Label mô tả
            label = QLabel(desc)
            label.setFont(QFont("Segoe UI", 13))
            label.setStyleSheet("color: #bbb;")
            row.addWidget(label)

            # Label phím tắt
            key_lbl = QLabel(key)
            key_lbl.setFont(QFont("Consolas", 13, QFont.Bold))
            key_lbl.setStyleSheet("""
                color: #fff;
                background: #333;
                border-radius: 4px;
                padding: 2px 8px;
                margin-left: 12px;
            """)
            row.addWidget(key_lbl)

            # Thêm vào container chính
            shortcut_container.addWidget(row_widget)
            shortcut_container.addSpacing(8)

        layout.addLayout(shortcut_container)
        layout.addStretch()
