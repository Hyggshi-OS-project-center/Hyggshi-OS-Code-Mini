class Extension:
    """
    Lớp cơ sở cho extension/plugin Python.
    """
    def __init__(self, editor):
        self.editor = editor

    def on_load(self):
        pass

    def on_save(self):
        pass

    def on_close(self):
        pass

# Ví dụ extension: tự động chuyển chữ thường thành chữ hoa khi lưu
class UppercaseOnSaveExtension(Extension):
    def on_save(self):
        text = self.editor.text()
        self.editor.setText(text.upper())

# Để sử dụng:
# ext = UppercaseOnSaveExtension(editor)
# ext.on_save()