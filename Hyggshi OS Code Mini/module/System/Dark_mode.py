"""
Dark_mode.py - Simple dark mode toggle for PyQt5 applications
"""

from PyQt5.QtWidgets import QApplication

DARK_STYLESHEET = """
QWidget {
    background-color: #232629;
    color: #e0e0e0;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2b2b2b;
    color: #e0e0e0;
    border: 1px solid #444;
}
QPushButton {
    background-color: #353535;
    color: #e0e0e0;
    border: 1px solid #444;
    padding: 4px 8px;
}
QPushButton:hover {
    background-color: #444;
}
QMenuBar, QMenu, QToolBar {
    background-color: #232629;
    color: #e0e0e0;
}
QTabWidget::pane {
    border: 1px solid #444;
}
QTabBar::tab {
    background: #2b2b2b;
    color: #e0e0e0;
    padding: 6px;
}
QTabBar::tab:selected {
    background: #353535;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background: #232629;
    border: 1px solid #444;
}
"""

def enable_dark_mode(app: QApplication):
    """Apply dark mode stylesheet to the given QApplication."""
    app.setStyleSheet(DARK_STYLESHEET)

def disable_dark_mode(app: QApplication):
    """Remove custom stylesheet (restore default)."""