"""
AI Chat Logging Module
Provides functions to log chat messages and errors to a text file.
"""

import os
import datetime
import threading

# Thread lock for file operations
_log_lock = threading.Lock()

# Log file path
LOG_FILE = os.path.join(os.path.dirname(__file__), "ai_chat_log.txt")

def ensure_log_file():
    try:
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"# AI Chat Log - Created {datetime.datetime.now().isoformat()}\n")
        return True
    except Exception as e:
        print(f"Warning: Could not create log file {LOG_FILE}: {e}")
        return False

def append_log(sender, message):
    if message is None:
        return
    try:
        with _log_lock:
            if ensure_log_file():
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    clean_message = str(message).replace('\r', '')
                    f.write(f"[{timestamp}] {sender}: {clean_message}\n")
                    f.flush()
    except Exception as e:
        print(f"Error writing to log file: {e}")

def append_error(error_msg, stacktrace=None):
    if not error_msg:
        return
    try:
        with _log_lock:
            if ensure_log_file():
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] ERROR: {error_msg}\n")
                    if stacktrace:
                        for line in str(stacktrace).splitlines():
                            if line.strip():
                                f.write(f"[{timestamp}] STACK: {line}\n")
                    f.write(f"[{timestamp}] --- End Error ---\n")
                    f.flush()
    except Exception as e:
        print(f"Error writing error to log file: {e}")

def clear_log():
    try:
        with _log_lock:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"# AI Chat Log - Cleared {datetime.datetime.now().isoformat()}\n")
        return True
    except Exception as e:
        print(f"Error clearing log file: {e}")
        return False

def read_log(lines=None):
    try:
        with _log_lock:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    if lines is None:
                        return f.read()
                    else:
                        all_lines = f.readlines()
                        return ''.join(all_lines[-lines:]) if all_lines else ""
            else:
                return "Log file does not exist"
    except Exception as e:
        return f"Error reading log file: {e}"

def get_log_stats():
    try:
        if not os.path.exists(LOG_FILE):
            return {"exists": False}
        stats = os.stat(LOG_FILE)
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return {
            "exists": True,
            "size_bytes": stats.st_size,
            "size_mb": round(stats.st_size / (1024 * 1024), 2),
            "line_count": len(lines),
            "modified": datetime.datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "path": LOG_FILE
        }
    except Exception as e:
        return {"exists": False, "error": str(e)}

# Initialize on import
ensure_log_file()

if __name__ == "__main__":
    # Test the logging functions
    print("Testing AI Chat Logging Module")
    print("=" * 40)
    
    # Test basic logging
    append_log("Test", "This is a test message")
    append_error("Test error", "Sample stacktrace\nLine 2 of stacktrace")
    
    # Show stats
    stats = get_log_stats()
    print(f"Log file stats: {stats}")
    
    # Read last few lines