from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class OutputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def append_text(self, text):
        self.text_edit.append(text)

    def clear(self):
        self.text_edit.clear()