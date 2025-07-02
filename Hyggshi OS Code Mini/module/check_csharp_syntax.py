import subprocess

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