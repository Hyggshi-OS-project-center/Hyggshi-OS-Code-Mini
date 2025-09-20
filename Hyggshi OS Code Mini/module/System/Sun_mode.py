# Sun_mode.py
# Chế độ giao diện sáng cho Hyggshi OS Code Mini

from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtGui import QPalette, QColor

def apply_sun_mode(app=None):
    """
    Đặt giao diện sáng cho ứng dụng PyQt5.
    """
    if app is None:
        app = QApplication.instance()
    if app is not None:
        app.setStyle(QStyleFactory.create("Fusion"))
        light_palette = QPalette()
        light_palette.setColor(QPalette.Window,        QColor("#f5f5f5"))
        light_palette.setColor(QPalette.WindowText,    QColor("#23272e"))
        light_palette.setColor(QPalette.Base,          QColor("#ffffff"))  # Sidebar/file explorer background
        light_palette.setColor(QPalette.AlternateBase, QColor("#eaeaea"))
        light_palette.setColor(QPalette.Text,          QColor("#23272e"))  # Sidebar/file explorer text
        light_palette.setColor(QPalette.PlaceholderText, QColor("#888888"))  # Optional: placeholder text
        light_palette.setColor(QPalette.ToolTipBase,   QColor("#23272e"))
        light_palette.setColor(QPalette.ToolTipText,   QColor("#ffffff"))  # Make tooltip text white for contrast
        light_palette.setColor(QPalette.Button,        QColor("#eaeaea"))
        light_palette.setColor(QPalette.ButtonText,    QColor("#23272e"))
        light_palette.setColor(QPalette.BrightText,    QColor("#e53935"))
        light_palette.setColor(QPalette.Highlight,     QColor("#007acc"))
        light_palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        light_palette.setColor(QPalette.Link,          QColor("#0066cc"))  # Optional: link color
        light_palette.setColor(QPalette.LinkVisited,   QColor("#b2b2ff")) # Optional: visited link color
        app.setPalette(light_palette)