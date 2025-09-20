# Debugger.py
# Simple debugging utility for Hyggshi OS Code Mini

import traceback

def debug_log(message):
    """
    Ghi log thông báo debug ra console.
    """
    print(f"[DEBUG] {message}")

def debug_exception(e):
    """
    Ghi log ngoại lệ ra console với traceback.
    """
    print("[EXCEPTION]", str(e))
    traceback.print_exc()