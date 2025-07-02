import subprocess
import os

def check_objective_c_syntax(path):
    """
    Kiểm tra cú pháp Objective-C bằng clang (yêu cầu đã cài đặt clang).
    """
    ext = os.path.splitext(path)[1].lower()
    if ext not in ('.m', '.mm'):
        return "Không phải file Objective-C (.m hoặc .mm)"
    try:
        completed = subprocess.run(
            ["clang", "-fsyntax-only", path],
            capture_output=True, text=True, timeout=10
        )
        if completed.returncode != 0:
            return completed.stderr or completed.stdout or "Có lỗi khi kiểm tra cú pháp."
        return None
    except Exception as e:
        return f"Lỗi khi kiểm tra cú pháp: {e}"