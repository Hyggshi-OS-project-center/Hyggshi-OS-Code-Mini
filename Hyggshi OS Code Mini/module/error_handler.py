"""
Global Error Handler for Hyggshi OS Code Mini
Handles crashes, API errors, and UI freezing
"""

import sys
import traceback
import logging
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtGui import QFont
import datetime
import os

class ErrorHandler(QObject):
    """Global error handler with UI feedback"""
    
    # Signals
    error_occurred = pyqtSignal(str, str)  # error_type, message
    warning_occurred = pyqtSignal(str, str)
    info_occurred = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_logging()
        self.setup_exception_handler()
        self.error_count = 0
        self.max_errors_per_session = 10
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"error_{datetime.datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('HyggshiOS')
        
    def setup_exception_handler(self):
        """Setup global exception handler"""
        sys.excepthook = self.handle_exception
        
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        self.error_count += 1
        
        # Log the error
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.logger.error(f"Uncaught exception: {error_msg}")
        
        # Show user-friendly error message
        if self.error_count <= self.max_errors_per_session:
            self.show_error_dialog(
                "Application Error",
                f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}\n\n"
                f"Error #{self.error_count}. The application will continue running.\n"
                f"Check the log file for more details."
            )
        else:
            self.logger.critical("Too many errors, application may be unstable")
            
    def show_error_dialog(self, title, message, error_type="Error"):
        """Show error dialog to user"""
        try:
            msg_box = QMessageBox()
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Critical if error_type == "Error" else QMessageBox.Warning)
            msg_box.setStandardButtons(QMessageBox.Ok)
            
            # Style the dialog
            msg_box.setStyleSheet("""
                QMessageBox {
                    background: #1e1e1e; color: #d4d4d4;
                }
                QMessageBox QLabel {
                    color: #d4d4d4; font-size: 12px;
                }
                QMessageBox QPushButton {
                    background: #007acc; color: white; border: none;
                    border-radius: 4px; padding: 8px 16px; font-weight: bold;
                }
                QMessageBox QPushButton:hover {
                    background: #005a9e;
                }
            """)
            
            msg_box.exec_()
        except Exception as e:
            print(f"Failed to show error dialog: {e}")
            
    def handle_api_error(self, api_name, error, context=""):
        """Handle API-specific errors"""
        error_msg = f"API Error ({api_name}): {str(error)}"
        if context:
            error_msg += f"\nContext: {context}"
            
        self.logger.error(error_msg)
        
        # Emit signal for UI components to handle
        self.error_occurred.emit("API", error_msg)
        
        # Show user-friendly message
        self.show_error_dialog(
            "API Error",
            f"Failed to connect to {api_name}:\n\n{str(error)}\n\n"
            f"Please check your internet connection and API settings.",
            "Error"
        )
        
    def handle_ui_freeze(self, component_name):
        """Handle UI freezing issues"""
        self.logger.warning(f"UI freeze detected in {component_name}")
        
        # Emit signal to restart component
        self.warning_occurred.emit("UI", f"UI component {component_name} may be frozen")
        
    def safe_execute(self, func, *args, **kwargs):
        """Safely execute a function with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_exception(type(e), e, e.__traceback__)
            return None
            
    def safe_async_execute(self, func, *args, **kwargs):
        """Safely execute async function with error handling"""
        try:
            import asyncio
            return asyncio.run(func(*args, **kwargs))
        except Exception as e:
            self.handle_exception(type(e), e, e.__traceback__)
            return None

class TimeoutHandler:
    """Handle timeouts and prevent UI freezing"""
    
    def __init__(self, timeout_seconds=30):
        self.timeout_seconds = timeout_seconds
        self.timers = {}
        
    def start_timeout(self, operation_id, callback):
        """Start timeout for an operation"""
        timer = QTimer()
        timer.timeout.connect(lambda: self.handle_timeout(operation_id, callback))
        timer.setSingleShot(True)
        timer.start(self.timeout_seconds * 1000)
        self.timers[operation_id] = timer
        
    def cancel_timeout(self, operation_id):
        """Cancel timeout for an operation"""
        if operation_id in self.timers:
            self.timers[operation_id].stop()
            del self.timers[operation_id]
            
    def handle_timeout(self, operation_id, callback):
        """Handle timeout"""
        self.logger.warning(f"Operation {operation_id} timed out after {self.timeout_seconds}s")
        callback()
        self.cancel_timeout(operation_id)

class ResourceMonitor:
    """Monitor system resources and prevent crashes"""
    
    def __init__(self):
        self.memory_threshold = 500 * 1024 * 1024  # 500MB
        self.cpu_threshold = 80  # 80%
        
    def check_resources(self):
        """Check system resources"""
        try:
            import psutil
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                self.logger.warning(f"High memory usage: {memory.percent}%")
                
            # Check CPU usage
            cpu = psutil.cpu_percent(interval=1)
            if cpu > self.cpu_threshold:
                self.logger.warning(f"High CPU usage: {cpu}%")
                
            return {
                'memory_percent': memory.percent,
                'cpu_percent': cpu,
                'available_memory': memory.available
            }
        except ImportError:
            self.logger.warning("psutil not available for resource monitoring")
            return None
        except Exception as e:
            self.logger.error(f"Error monitoring resources: {e}")
            return None

# Global error handler instance
error_handler = ErrorHandler()
timeout_handler = TimeoutHandler()
resource_monitor = ResourceMonitor()

def safe_call(func, *args, **kwargs):
    """Decorator for safe function calls"""
    def wrapper(*args, **kwargs):
        return error_handler.safe_execute(func, *args, **kwargs)
    return wrapper

def handle_api_errors(api_name):
    """Decorator for API error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_api_error(api_name, e, f"Function: {func.__name__}")
                return None
        return wrapper
    return decorator
