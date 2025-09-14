"""
Notification.py - Notification with two choice buttons for Hyggshi OS Code Mini
"""

import sys
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QApplication
from PyQt5.QtCore import Qt, QTimer
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from module.Media.Photoview import PhotoView
import subprocess
import os

def show_choice_notification(message, choice1="Python?", choice2="Web?", parent=None):
    """
    Hiển thị thông báo với hai nút lựa chọn.
    Trả về chuỗi lựa chọn của người dùng ("python" hoặc "web").
    """
    class ChoiceDialog(QDialog):
        def __init__(self, message, choice1, choice2, parent=None):
            super().__init__(parent)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setModal(True)
            self.setStyleSheet("""
                QDialog {
                    background: #111;
                    border-radius: 16px;
                }
                QLabel {
                    color: #fff;
                    font-size: 32px;
                    font-weight: bold;
                    padding: 24px 24px 8px 24px;
                }
                QPushButton {
                    background: #e0c6ff;
                    color: #222;
                    font-weight: bold;
                    font-size: 20px;
                    border-radius: 12px;
                    padding: 10px 32px;
                    margin: 16px 16px 24px 16px;
                }
                QPushButton:hover {
                    background: #d1b3ff;
                }
            """)
            vbox = QVBoxLayout(self)
            label = QLabel(message)
            label.setAlignment(Qt.AlignCenter)
            vbox.addWidget(label)
            hbox = QHBoxLayout()
            btn1 = QPushButton(choice1)
            btn2 = QPushButton(choice2)
            btn1.clicked.connect(lambda: self.done(1))
            btn2.clicked.connect(lambda: self.done(2))
            hbox.addWidget(btn1)
            hbox.addWidget(btn2)
            vbox.addLayout(hbox)
            self.setLayout(vbox)

    dlg = ChoiceDialog(message, choice1, choice2, parent)
    if parent:
        geo = parent.geometry()
        dlg.move(
            geo.x() + (geo.width() - dlg.sizeHint().width()) // 2,
            geo.y() + (geo.height() - dlg.sizeHint().height()) // 2
        )
    result = dlg.exec_()
    if result == 1:
        return "python"
    elif result == 2:
        return "web"
    return None

def show_notification(message, duration=3000, parent=None, button_text=None, button_callback=None):
    """
    Hiển thị thông báo đơn giản trong một thời gian ngắn, có thể thêm nút bấm.
    """
    class NotificationDialog(QDialog):
        def __init__(self, message, duration, parent=None, button_text=None, button_callback=None):
            super().__init__(parent)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setModal(False)
            self.setStyleSheet("""
                QDialog {
                    background: #111;
                    border-radius: 16px;
                }
                QLabel {
                    color: #fff;
                    font-size: 24px;
                    padding: 16px 24px;
                }
                QPushButton {
                    background: #e0c6ff;
                    color: #222;
                    font-weight: bold;
                    font-size: 16px;
                    border-radius: 8px;
                    padding: 8px 24px;
                    margin: 12px 0 16px 0;
                }
                QPushButton:hover {
                    background: #d1b3ff;
                }
            """)
            vbox = QVBoxLayout(self)
            label = QLabel(message)
            label.setAlignment(Qt.AlignCenter)
            vbox.addWidget(label)
            if button_text:
                btn = QPushButton(button_text)
                btn.clicked.connect(self.accept)
                if button_callback:
                    btn.clicked.connect(button_callback)
                vbox.addWidget(btn, alignment=Qt.AlignCenter)
            self.setLayout(vbox)
            QTimer.singleShot(duration, self.close)

    dlg = NotificationDialog(message, duration, parent, button_text, button_callback)
    if parent:
        geo = parent.geometry()
        dlg.move(
            geo.x() + (geo.width() - dlg.sizeHint().width()) // 2,
            geo.y() + (geo.height() - dlg.sizeHint().height()) // 2
        )
    dlg.show()
    QApplication.processEvents()  # Đảm bảo hiển thị ngay lập tức
    return dlg
    # Không chặn, tự động đóng sau duration

def open_image_with_choice(self, image_path):
    result = show_choice_notification("Mở bằng gì", "Python?", "Web?", parent=self)
    if result == "python":
        photo_view = PhotoView(image_path)
        photo_view.show()
    elif result == "web":
        js_path = os.path.abspath("module/Mediaweb/ImagePreviewer.js")
        subprocess.Popen(["electron", js_path, image_path])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Test notification with button
    def on_btn():
        print("Button clicked!")
    show_notification("Đây là thông báo có nút!", button_text="OK", button_callback=on_btn)
    # Test choice notification
    result = show_choice_notification("Mở bằng gì", "Python?", "Web?")
    print("Bạn chọn:", result)
    sys.exit(app.exec_())