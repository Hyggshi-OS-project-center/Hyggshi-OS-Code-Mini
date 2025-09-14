"""
Syntax Checker Plugin for Hyggshi OS Code Mini
Checks syntax for various programming languages
"""

import os
import sys
import subprocess
import tempfile
from PyQt5.QtWidgets import QAction, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QComboBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor

try:
    from plugin_system import PluginInterface
except ImportError:
    # Fallback interface
    class PluginInterface:
        def __init__(self):
            self.name = "Syntax Checker"
            self.version = "1.0.0"
            self.description = "Syntax Checker Plugin"
            self.author = "Hyggshi OS"
            self.enabled = True
        def initialize(self, main_window):
            pass
        def cleanup(self):
            pass
        def get_menu_items(self):
            return []
        def get_toolbar_items(self):
            return []
        def get_settings_widget(self):
            return None

class SyntaxCheckerPlugin(PluginInterface):
    """Syntax Checker Plugin"""
    
    def __init__(self):
        super().__init__()
        self.name = "Syntax Checker"
        self.version = "1.0.0"
        self.description = "Real-time syntax checking for multiple programming languages"
        self.author = "Hyggshi OS Team"
        self.main_window = None
        self.checker_widget = None
        self.current_file = None
        
        # Supported languages and their checkers
        self.language_checkers = {
            'python': self.check_python_syntax,
            'javascript': self.check_javascript_syntax,
            'java': self.check_java_syntax,
            'cpp': self.check_cpp_syntax,
            'c': self.check_c_syntax,
        }
        
    def initialize(self, main_window):
        """Initialize the plugin"""
        self.main_window = main_window
        
        # Create syntax checker widget
        self.checker_widget = self.create_checker_widget()
        
        # Add to main window
        if hasattr(main_window, 'add_dock_widget'):
            main_window.add_dock_widget(self.checker_widget, "Syntax Checker", Qt.BottomDockWidgetArea)
        elif hasattr(main_window, 'add_sidebar_widget'):
            main_window.add_sidebar_widget(self.checker_widget, "Syntax Checker")
            
        # Connect to editor changes if possible
        self.connect_to_editor()
        
    def cleanup(self):
        """Cleanup when plugin is unloaded"""
        if self.checker_widget:
            try:
                self.checker_widget.close()
                self.checker_widget = None
            except Exception as e:
                print(f"Error cleaning up Syntax Checker plugin: {e}")
                
    def create_checker_widget(self):
        """Create the syntax checker widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header_layout = QVBoxLayout()
        
        title = QLabel("Syntax Checker")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #d4d4d4;")
        header_layout.addWidget(title)
        
        # Language selector
        self.language_combo = QComboBox()
        self.language_combo.addItems(['python', 'javascript', 'java', 'cpp', 'c'])
        self.language_combo.setStyleSheet("""
            QComboBox {
                background: #2d2d2d; color: #d4d4d4; border: 1px solid #333;
                border-radius: 4px; padding: 4px 8px;
            }
        """)
        header_layout.addWidget(self.language_combo)
        
        # Check button
        self.check_btn = QPushButton("Check Syntax")
        self.check_btn.setStyleSheet("""
            QPushButton {
                background: #28a745; color: white; border: none;
                border-radius: 4px; padding: 6px 12px; font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        self.check_btn.clicked.connect(self.check_current_syntax)
        header_layout.addWidget(self.check_btn)
        
        layout.addLayout(header_layout)
        
        # Results area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e; color: #d4d4d4; border: 1px solid #333;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.results_text)
        
        return widget
        
    def connect_to_editor(self):
        """Connect to editor changes for real-time checking"""
        try:
            if hasattr(self.main_window, 'editor'):
                editor = self.main_window.editor
                if hasattr(editor, 'textChanged'):
                    editor.textChanged.connect(self.on_text_changed)
        except Exception as e:
            print(f"Error connecting to editor: {e}")
            
    def on_text_changed(self):
        """Handle text changes in editor"""
        # Debounce the checking
        if hasattr(self, 'check_timer'):
            self.check_timer.stop()
        else:
            self.check_timer = QTimer()
            self.check_timer.timeout.connect(self.check_current_syntax)
            self.check_timer.setSingleShot(True)
            
        self.check_timer.start(1000)  # Check after 1 second of no changes
        
    def get_current_code(self):
        """Get current code from editor"""
        try:
            if hasattr(self.main_window, 'editor'):
                editor = self.main_window.editor
                if hasattr(editor, 'toPlainText'):
                    return editor.toPlainText()
                elif hasattr(editor, 'text'):
                    return editor.text()
        except Exception as e:
            print(f"Error getting current code: {e}")
        return ""
        
    def check_current_syntax(self):
        """Check syntax of current code"""
        code = self.get_current_code()
        if not code.strip():
            self.results_text.setText("No code to check")
            return
            
        language = self.language_combo.currentText()
        checker = self.language_checkers.get(language)
        
        if checker:
            result = checker(code)
            self.display_results(result)
        else:
            self.results_text.setText(f"Syntax checking not supported for {language}")
            
    def check_python_syntax(self, code):
        """Check Python syntax"""
        try:
            compile(code, '<string>', 'exec')
            return {"status": "success", "message": "Python syntax is valid"}
        except SyntaxError as e:
            return {
                "status": "error", 
                "message": f"Syntax Error: {e.msg} at line {e.lineno}, column {e.offset}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
            
    def check_javascript_syntax(self, code):
        """Check JavaScript syntax using Node.js"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
                
            # Run node --check
            result = subprocess.run(['node', '--check', temp_file], 
                                  capture_output=True, text=True, timeout=5)
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return {"status": "success", "message": "JavaScript syntax is valid"}
            else:
                return {"status": "error", "message": result.stderr}
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Syntax check timed out"}
        except FileNotFoundError:
            return {"status": "error", "message": "Node.js not found. Please install Node.js to check JavaScript syntax."}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
            
    def check_java_syntax(self, code):
        """Check Java syntax"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
                f.write(code)
                temp_file = f.name
                
            # Run javac -Xlint
            result = subprocess.run(['javac', '-Xlint', temp_file], 
                                  capture_output=True, text=True, timeout=10)
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return {"status": "success", "message": "Java syntax is valid"}
            else:
                return {"status": "error", "message": result.stderr}
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Syntax check timed out"}
        except FileNotFoundError:
            return {"status": "error", "message": "Java compiler not found. Please install JDK to check Java syntax."}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
            
    def check_cpp_syntax(self, code):
        """Check C++ syntax"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
                f.write(code)
                temp_file = f.name
                
            # Run g++ -fsyntax-only
            result = subprocess.run(['g++', '-fsyntax-only', temp_file], 
                                  capture_output=True, text=True, timeout=10)
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return {"status": "success", "message": "C++ syntax is valid"}
            else:
                return {"status": "error", "message": result.stderr}
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Syntax check timed out"}
        except FileNotFoundError:
            return {"status": "error", "message": "G++ compiler not found. Please install GCC to check C++ syntax."}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
            
    def check_c_syntax(self, code):
        """Check C syntax"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                f.write(code)
                temp_file = f.name
                
            # Run gcc -fsyntax-only
            result = subprocess.run(['gcc', '-fsyntax-only', temp_file], 
                                  capture_output=True, text=True, timeout=10)
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return {"status": "success", "message": "C syntax is valid"}
            else:
                return {"status": "error", "message": result.stderr}
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Syntax check timed out"}
        except FileNotFoundError:
            return {"status": "error", "message": "GCC compiler not found. Please install GCC to check C syntax."}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
            
    def display_results(self, result):
        """Display syntax check results"""
        status = result.get("status", "unknown")
        message = result.get("message", "No message")
        
        if status == "success":
            self.results_text.setStyleSheet("""
                QTextEdit {
                    background: #1e1e1e; color: #3fb950; border: 1px solid #3fb950;
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 12px;
                }
            """)
        else:
            self.results_text.setStyleSheet("""
                QTextEdit {
                    background: #1e1e1e; color: #f85149; border: 1px solid #f85149;
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 12px;
                }
            """)
            
        self.results_text.setText(f"[{status.upper()}] {message}")
        
    def get_menu_items(self):
        """Return menu items for this plugin"""
        menu_items = []
        
        # Syntax Check menu
        check_action = QAction("Check Syntax", self.main_window)
        check_action.setToolTip("Check syntax of current file")
        check_action.triggered.connect(self.check_current_syntax)
        menu_items.append(check_action)
        
        return menu_items
        
    def get_toolbar_items(self):
        """Return toolbar items for this plugin"""
        toolbar_items = []
        
        # Syntax Check button
        check_button = QPushButton("✓ Check")
        check_button.setToolTip("Check syntax")
        check_button.clicked.connect(self.check_current_syntax)
        check_button.setStyleSheet("""
            QPushButton {
                background: #28a745; color: white; border: none;
                border-radius: 4px; padding: 6px 12px; font-weight: bold;
            }
            QPushButton:hover { background: #218838; }
        """)
        toolbar_items.append(check_button)
        
        return toolbar_items
        
    def get_settings_widget(self):
        """Return settings widget for this plugin"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Plugin info
        info_label = QLabel(f"""
        <h3>{self.name}</h3>
        <p><b>Version:</b> {self.version}</p>
        <p><b>Author:</b> {self.author}</p>
        <p><b>Description:</b> {self.description}</p>
        <p><b>Supported Languages:</b> {', '.join(self.language_checkers.keys())}</p>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        return widget
        
    def get_supported_languages(self):
        """Return supported languages for syntax checking"""
        return {
            'Python': {'extension': '.py', 'plugin': 'syntax_checker'},
            'JavaScript': {'extension': '.js', 'plugin': 'syntax_checker'},
            'Java': {'extension': '.java', 'plugin': 'syntax_checker'},
            'C++': {'extension': '.cpp', 'plugin': 'syntax_checker'},
            'C': {'extension': '.c', 'plugin': 'syntax_checker'}
        }

# Plugin class that will be imported
Plugin = SyntaxCheckerPlugin
