from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QLinearGradient, QColor
import os
from PyQt5.QtWidgets import QMessageBox, QApplication
import sys

def show_notification(title, message):
    """
    Hiển thị thông báo popup (QMessageBox).
    """
    app = QApplication.instance()
    close_app = False
    if app is None:
        app = QApplication(sys.argv)
        close_app = True
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(QMessageBox.Information)
    msg.exec_()
    if close_app:
        app.quit()

def show_update_confirm(title, message):
    """
    Hiển thị hộp thoại xác nhận cập nhật với 2 nút: Đồng ý và Không đồng ý.
    Trả về True nếu người dùng chọn Đồng ý, False nếu chọn Không đồng ý.
    """
    app = QApplication.instance()
    close_app = False
    if app is None:
        app = QApplication(sys.argv)
        close_app = True
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(QMessageBox.Question)
    yes = msg.addButton("Đồng ý", QMessageBox.YesRole)
    no = msg.addButton("Không đồng ý", QMessageBox.NoRole)
    msg.exec_()
    result = msg.clickedButton() == yes
    if close_app:
        app.quit()
    return result

if __name__ == "__main__":
    # Test notification
    show_notification("Tiêu đề", "Nội dung thông báo!")
    # Test update confirm
    if show_update_confirm("Cập nhật", "Có bản cập nhật mới. Bạn có muốn cập nhật không?"):
        print("Đồng ý cập nhật!")
    else:
        print("Không cập nhật.")