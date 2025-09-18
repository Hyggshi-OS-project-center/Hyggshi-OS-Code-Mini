# Dark_mode.py
# Chế độ giao diện tối cho Hyggshi OS Code Mini

from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtGui import QPalette, QColor

def apply_dark_mode(app=None):
    """
    Đặt giao diện tối cho ứng dụng PyQt5.
    """
    if app is None:
        app = QApplication.instance()
    if app is not None:
        app.setStyle(QStyleFactory.create("Fusion"))
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window,        QColor("#181a20"))
        dark_palette.setColor(QPalette.WindowText,    QColor("#e0e0e0"))
        dark_palette.setColor(QPalette.Base,          QColor("#23272e"))
        dark_palette.setColor(QPalette.AlternateBase, QColor("#20232a"))
        dark_palette.setColor(QPalette.ToolTipBase,   QColor("#e0e0e0"))
        dark_palette.setColor(QPalette.ToolTipText,   QColor("#23272e"))
        dark_palette.setColor(QPalette.Text,          QColor("#e0e0e0"))
        dark_palette.setColor(QPalette.Button,        QColor("#23272e"))
        dark_palette.setColor(QPalette.ButtonText,    QColor("#e0e0e0"))
        dark_palette.setColor(QPalette.BrightText,    QColor("#e53935"))
        dark_palette.setColor(QPalette.Highlight,     QColor("#569cd6"))
        dark_palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        app.setPalette(dark_palette)