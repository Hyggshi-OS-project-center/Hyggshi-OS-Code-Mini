import subprocess
import sys
import os

class TerminalOutput:
    def __init__(self):
        self.history = []  # List of (command, output, error, returncode)

    def run_command(self, command, cwd=None, timeout=30):
        """Chạy lệnh shell, lưu kết quả vào history, trả về (output, error, returncode)"""
        if cwd is None:
            cwd = os.getcwd()
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd, timeout=timeout)
            output = result.stdout
            error = result.stderr
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            output = ''
            error = 'Command timed out'
            returncode = -1
        except Exception as e:
            output = ''
            error = str(e)
            returncode = -1
        self.history.append((command, output, error, returncode))
        return output, error, returncode

    def get_history(self):
        """Trả về lịch sử các lệnh và output"""
        return self.history

    def clear_history(self):
        """Xóa lịch sử terminal"""
        self.history.clear()

    def append_output(self, output):
        """Thêm output vào history (không có lệnh)"""
        self.history.append((None, output, '', 0))
