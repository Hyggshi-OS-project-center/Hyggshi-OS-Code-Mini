import ast
import subprocess
import os

def check_python_syntax(code):
    """
    Trả về None nếu không có lỗi, hoặc chuỗi thông báo lỗi nếu có lỗi cú pháp.
    """
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        return f"Lỗi cú pháp tại dòng {e.lineno}: {e.msg}"

def check_bat_syntax(path):
    """
    Kiểm tra lỗi cú pháp file .bat bằng cách chạy thử với cmd /c.
    Chỉ nên dùng cho file test, KHÔNG dùng cho file có lệnh nguy hiểm!
    """
    try:
        completed = subprocess.run(
            ['cmd', '/c', 'call', path],
            capture_output=True, text=True, timeout=5
        )
        if completed.returncode != 0:
            return completed.stderr or completed.stdout or "Có lỗi khi chạy batch file."
        return None
    except Exception as e:
        return f"Lỗi khi kiểm tra batch: {e}"

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

def check_csharp_syntax(path):
    """
    Kiểm tra cú pháp C# bằng csc (yêu cầu đã cài đặt .NET SDK).
    """
    try:
        completed = subprocess.run(
            ["csc", "/nologo", "/t:library", "/parseonly", path],
            capture_output=True, text=True, timeout=10
        )
        if completed.returncode != 0:
            return completed.stderr or completed.stdout or "Có lỗi khi kiểm tra cú pháp."
        return None
    except Exception as e:
        return f"Lỗi khi kiểm tra cú pháp: {e}"
