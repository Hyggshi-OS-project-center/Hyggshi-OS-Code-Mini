# Debugger.py
# Simple debugging utility for Hyggshi OS Code Mini

import sys
import traceback

def debug_log(message):
    """
    Ghi log thông báo debug ra console, hỗ trợ Unicode.
    """
    try:
        print(f"[DEBUG] {message}")
    except UnicodeEncodeError:
        sys.stdout.buffer.write(f"[DEBUG] {message}\n".encode("utf-8"))
        sys.stdout.flush()

def debug_exception(e):
    """
    Ghi log ngoại lệ ra console với traceback.
    """
    try:
        print("[EXCEPTION]", str(e))
        traceback.print_exc()
    except UnicodeEncodeError:
        sys.stdout.buffer.write(f"[EXCEPTION] {str(e)}\n".encode("utf-8"))
        sys.stdout.flush()
        traceback.print_exc()