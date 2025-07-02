import subprocess
import os

def check_c_cpp_syntax(path):
    """
    Kiểm tra cú pháp C/C++ bằng gcc/g++ (yêu cầu đã cài đặt MinGW hoặc tương tự).
    """
    ext = os.path.splitext(path)[1].lower()
    compiler = "gcc" if ext == ".c" else "g++"
    try:
        completed = subprocess.run(
            [compiler, "-fsyntax-only", path],
            capture_output=True, text=True, timeout=10
        )
        if completed.returncode != 0:
            return completed.stderr or completed.stdout or "Có lỗi khi kiểm tra cú pháp."
        return None
    except Exception as e:
        return f"Lỗi khi kiểm tra cú pháp: {e}"