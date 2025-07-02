from PyQt5.QtWidgets import QMessageBox

def check_unsaved_and_prompt(tab, parent_widget):
    if hasattr(tab, 'modified') and tab.modified:
        reply = QMessageBox.question(
            parent_widget, "Chưa lưu file",
            "Bạn chưa lưu file này. Bạn có muốn lưu trước khi đóng?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        if reply == QMessageBox.Cancel:
            return False
        elif reply == QMessageBox.Yes:
            if not tab.save_file():
                return False
    return True
