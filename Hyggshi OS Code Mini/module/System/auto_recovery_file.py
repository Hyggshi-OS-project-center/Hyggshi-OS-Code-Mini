# auto_recovery_file.py
# Tự động lưu và phục hồi file trong Hyggshi OS Code Mini

import os
import time
import json

RECOVERY_DIR = "auto_recovery"
RECOVERY_INTERVAL = 60  # giây
TEMP_JSON_PATH = os.path.join(RECOVERY_DIR, "File.json")

def ensure_recovery_dir():
    if not os.path.exists(RECOVERY_DIR):
        os.makedirs(RECOVERY_DIR)

def get_recovery_path(filename):
    ensure_recovery_dir()
    base = os.path.basename(filename)
    return os.path.join(RECOVERY_DIR, base + ".recovery")

def auto_save_file(filename, content):
    """
    Tự động lưu nội dung file vào thư mục recovery.
    """
    path = get_recovery_path(filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def auto_load_file(filename):
    """
    Phục hồi nội dung file từ thư mục recovery nếu có.
    """
    path = get_recovery_path(filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def remove_recovery_file(filename):
    """
    Xóa file recovery sau khi đã lưu chính thức.
    """
    path = get_recovery_path(filename)
    if os.path.exists(path):
        os.remove(path)

def list_recovery_files():
    """
    Liệt kê các file recovery còn tồn tại.
    """
    ensure_recovery_dir()
    return [f for f in os.listdir(RECOVERY_DIR) if f.endswith(".recovery")]

def auto_save_temp_file(content, temp_name="unsaved_temp"):
    """
    Lưu nội dung file chưa được lưu vào File.json trong thư mục auto_recovery.
    """
    if not os.path.exists(RECOVERY_DIR):
        os.makedirs(RECOVERY_DIR)
    data = {}
    if os.path.exists(TEMP_JSON_PATH):
        with open(TEMP_JSON_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    data[temp_name] = content
    with open(TEMP_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def auto_load_temp_file(temp_name="unsaved_temp"):
    """
    Phục hồi nội dung file tạm từ File.json nếu có.
    """
    if os.path.exists(TEMP_JSON_PATH):
        with open(TEMP_JSON_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get(temp_name)
            except Exception:
                return None
    return None

def remove_temp_file(temp_name="unsaved_temp"):
    """
    Xóa nội dung file tạm khỏi File.json sau khi đã lưu chính thức hoặc không cần nữa.
    """
    if os.path.exists(TEMP_JSON_PATH):
        with open(TEMP_JSON_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
        if temp_name in data:
            del data[temp_name]
            with open(TEMP_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

# Ví dụ sử dụng:
if __name__ == "__main__":
    test_file = "test.txt"
    test_content = "Nội dung thử nghiệm auto recovery"
    auto_save_file(test_file, test_content)
    print("Đã auto save.")
    print("Phục hồi:", auto_load_file(test_file))
    remove_recovery_file(test_file)
    print("Đã xóa file recovery.")

from module.System.auto_recovery_file import auto_save_file, remove_recovery_file, auto_save_temp_file, auto_load_temp_file

def on_text_changed(self, filename, content):
    auto_save_file(filename, content)

def save_file(self, filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    remove_recovery_file(filename)

def restore_unsaved_file_on_start(editor, temp_name="unsaved_temp"):
    content = auto_load_temp_file(temp_name)
    if content:
        editor.setText(content)
        # Có thể hiển thị thông báo: Đã phục hồi file chưa lưu!

# Khi bạn muốn lưu tạm nội dung chưa lưu:
auto_save_temp_file("Nội dung file chưa lưu", temp_name="untitled1")
# Giả sử editor là widget soạn thảo văn bản
# Thay thế editor bằng đối tượng editor thực tế của bạn
# Ví dụ:
# editor = MyEditorWidget()
# restore_unsaved_file_on_start(editor, temp_name="untitled1")