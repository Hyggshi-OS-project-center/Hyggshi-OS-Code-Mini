from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QComboBox, QCheckBox, QSplitter, QTabWidget, QScrollArea,
    QLineEdit, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QProcess, QThread
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette
import datetime
import os
import subprocess
import sys
from module.Terminal_output import TerminalOutput

class OutputPanel(QWidget):
    # Signal emitted when new output is added
    output_added = pyqtSignal(str, str)  # level, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_styling()
        self.setup_connections()
        
        # Output categories
        self.output_categories = {
            "All": [],
            "Problems": [],
            "Output": [],
            "Debug": [],
            "Error": [],
            "Info": [],
            "Warning": [],
            "Ports": []
        }
        
        # Auto-scroll settings
        self.auto_scroll = True
        self.max_lines = 1000
        self.terminal_logic = TerminalOutput()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        from PyQt5.QtWidgets import QTextEdit
        test_tab = QTextEdit()
        self.tab_widget.addTab(test_tab, "TestTab")
        main_layout.addWidget(self.tab_widget)
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
    def create_output_widget(self, title):
        """Create a styled output widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e; color: #d4d4d4; border: none;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px; line-height: 1.4;
            }
            QScrollBar:vertical {
                background: #2d2d2d; width: 12px; border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555; border-radius: 6px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
        """)
        
        layout.addWidget(text_edit)
        return text_edit
        
    def create_debug_console(self):
        """Create debug console widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Debug console output
        self.debug_console_output = QTextEdit()
        self.debug_console_output.setReadOnly(True)
        self.debug_console_output.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e; color: #d4d4d4; border: none;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px; line-height: 1.4;
            }
            QScrollBar:vertical {
                background: #2d2d2d; width: 12px; border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555; border-radius: 6px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
        """)
        
        # Debug console input
        input_layout = QHBoxLayout()
        self.debug_input = QLineEdit()
        self.debug_input.setPlaceholderText("Enter debug command (e.g., print('Hello'), len([1,2,3]))")
        self.debug_input.setStyleSheet("""
            QLineEdit {
                background: #2d2d2d; color: #d4d4d4; border: 1px solid #333;
                border-radius: 4px; padding: 6px; font-family: monospace;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
        """)
        
        self.debug_execute_btn = QPushButton("Execute")
        self.debug_execute_btn.setStyleSheet("""
            QPushButton {
                background: #007acc; color: white; border: none;
                border-radius: 4px; padding: 6px 12px; font-weight: bold;
            }
            QPushButton:hover { background: #005a9e; }
        """)
        
        input_layout.addWidget(QLabel("Debug:"))
        input_layout.addWidget(self.debug_input, 1)
        input_layout.addWidget(self.debug_execute_btn)
        
        layout.addWidget(self.debug_console_output, 1)
        layout.addLayout(input_layout)
        
        # Connect signals
        self.debug_execute_btn.clicked.connect(self.execute_debug_command)
        self.debug_input.returnPressed.connect(self.execute_debug_command)
        
        return widget
        
    def create_terminal(self):
        """Create terminal widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Terminal output
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background: #0c0c0c; color: #00ff00; border: none;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px; line-height: 1.4;
            }
            QScrollBar:vertical {
                background: #2d2d2d; width: 12px; border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555; border-radius: 6px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
        """)
        
        # Terminal input
        input_layout = QHBoxLayout()
        self.terminal_prompt = QLabel("$")
        self.terminal_prompt.setStyleSheet("color: #00ff00; font-weight: bold; font-family: monospace;")
        self.terminal_prompt.setFixedWidth(20)
        
        self.terminal_input = QLineEdit()
        self.terminal_input.setStyleSheet("""
            QLineEdit {
                background: #0c0c0c; color: #00ff00; border: none;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 13px; padding: 4px;
            }
            QLineEdit:focus {
                border: 1px solid #00ff00;
            }
        """)
        
        input_layout.addWidget(self.terminal_prompt)
        input_layout.addWidget(self.terminal_input, 1)
        
        layout.addWidget(self.terminal_output, 1)
        layout.addLayout(input_layout)
        
        # Initialize terminal
        self.terminal_process = None
        self.current_directory = os.getcwd()
        self.terminal_output.append(f"Terminal initialized in: {self.current_directory}")
        self.terminal_output.append("Type 'help' for available commands or use standard shell commands.")
        self.terminal_output.append("")
        
        # Connect signals
        self.terminal_input.returnPressed.connect(self.execute_terminal_command)
        
        return widget
        
    def setup_styling(self):
        """Setup the overall styling"""
        self.setStyleSheet("""
            QWidget {
                background: #1e1e1e; color: #d4d4d4;
            }
        """)
        
    def setup_connections(self):
        """Setup signal connections"""
        if hasattr(self, 'clear_btn'):
            self.clear_btn.clicked.connect(self.clear_all)
        if hasattr(self, 'save_btn'):
            self.save_btn.clicked.connect(self.save_output)
        if hasattr(self, 'category_combo'):
            self.category_combo.currentTextChanged.connect(self.filter_output)
        if hasattr(self, 'auto_scroll_cb'):
            self.auto_scroll_cb.toggled.connect(self.toggle_auto_scroll)
        
    def append_text(self, text, level="Info", category="Output"):
        """Append text to the appropriate output widget"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_text = f"[{timestamp}] [{level}] {text}"
        
        # Add to category storage
        if category not in self.output_categories:
            category = "Output"
        self.output_categories[category].append(formatted_text)
        self.output_categories["All"].append(formatted_text)
        
        # Determine target widget using tab index
        target_widget = self.tab_widget.widget(0)  # Default to first tab
        if category == "Problems":
            target_widget = self.tab_widget.widget(0)  # Problems tab
        elif category == "Ports":
            target_widget = self.tab_widget.widget(4)  # Ports tab (index 4)
        elif category == "Debug":
            target_widget = self.tab_widget.widget(2)  # Debug Console tab
        elif category == "Error":
            target_widget = self.tab_widget.widget(0)  # Default to first tab
            
        # Apply color coding based on level
        color = self.get_level_color(level)
        colored_text = f'<span style="color: {color};">{formatted_text}</span>'
        
        # Append to widget
        if target_widget:
            cursor = target_widget.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertHtml(colored_text + '<br>')
            
            # Auto-scroll if enabled
            if self.auto_scroll:
                target_widget.verticalScrollBar().setValue(
                    target_widget.verticalScrollBar().maximum()
                )
                
            # Limit lines to prevent memory issues
            self.limit_lines(target_widget)
        
        # Update status
        self.status_label.setText(f"Last output: {timestamp} ({level})")
        
        # Emit signal
        self.output_added.emit(level, text)
        
    def get_level_color(self, level):
        """Get color for different log levels"""
        colors = {
            "Error": "#f85149",    # Red
            "Warning": "#d29922",  # Yellow
            "Info": "#58a6ff",     # Blue
            "Debug": "#7c3aed",    # Purple
            "Success": "#3fb950",  # Green
            "Build": "#f85149"     # Red for build errors
        }
        return colors.get(level, "#d4d4d4")
        
    def limit_lines(self, widget, max_lines=None):
        """Limit the number of lines in a widget"""
        if max_lines is None:
            max_lines = self.max_lines
            
        document = widget.document()
        if document.blockCount() > max_lines:
            cursor = widget.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 
                              document.blockCount() - max_lines)
            cursor.removeSelectedText()
            
    def clear_all(self):
        """Clear all output widgets"""
        if hasattr(self, 'problems_output') and self.problems_output:
            self.problems_output.clear()
        if hasattr(self, 'main_output') and self.main_output:
            self.main_output.clear()
        if hasattr(self, 'debug_console_output') and self.debug_console_output:
            self.debug_console_output.clear()
        if hasattr(self, 'terminal_output') and self.terminal_output:
            self.terminal_output.clear()
        if hasattr(self, 'ports_output') and self.ports_output:
            self.ports_output.clear()
        # Không gọi clear cho các widget không addTab hoặc không tồn tại
        if hasattr(self, 'build_output') and self.build_output:
            try:
                self.build_output.clear()
            except Exception:
                pass
        if hasattr(self, 'debug_output') and self.debug_output:
            try:
                self.debug_output.clear()
            except Exception:
                pass
        if hasattr(self, 'error_output') and self.error_output:
            try:
                self.error_output.clear()
            except Exception:
                pass
        if hasattr(self, 'terminal_logic') and self.terminal_logic:
            self.terminal_logic.clear_history()
        for category in self.output_categories:
            self.output_categories[category].clear()
        self.status_label.setText("Output cleared")
        
    def save_output(self):
        """Save current output to file"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output_{timestamp}.log"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Output Log - {datetime.datetime.now()}\n")
                f.write("=" * 50 + "\n\n")
                
                for category, messages in self.output_categories.items():
                    if messages:
                        f.write(f"\n[{category.upper()}]\n")
                        f.write("-" * 20 + "\n")
                        for message in messages:
                            f.write(message + "\n")
                            
            self.append_text(f"Output saved to {filename}", "Success")
            
        except Exception as e:
            self.append_text(f"Failed to save output: {str(e)}", "Error")
            
    def filter_output(self, category):
        """Filter output by category"""
        # This could be enhanced to show filtered view
        pass
        
    def toggle_auto_scroll(self, enabled):
        """Toggle auto-scroll functionality"""
        self.auto_scroll = enabled

    def clear(self):
        """Legacy method for compatibility"""
        self.clear_all()
        
    def append_build_output(self, text):
        """Append build-specific output"""
        self.append_text(text, "Build", "Build")
        
    def append_debug_output(self, text):
        """Append debug-specific output"""
        self.append_text(text, "Debug", "Debug")
        
    def append_error_output(self, text):
        """Append error-specific output"""
        self.append_text(text, "Error", "Error")
        
    def append_success_output(self, text):
        """Append success output"""
        self.append_text(text, "Success", "Main")
        
    def execute_debug_command(self):
        """Execute debug command in Python"""
        command = self.debug_input.text().strip()
        if not command:
            return
            
        # Clear input
        self.debug_input.clear()
        
        # Show command in output
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.debug_console_output.append(f'<span style="color: #569cd6;">[{timestamp}] > {command}</span>')
        
        try:
            # Execute the command
            result = eval(command)
            
            # Show result
            if result is not None:
                self.debug_console_output.append(f'<span style="color: #4ec9b0;">{repr(result)}</span>')
            else:
                self.debug_console_output.append('<span style="color: #888;">None</span>')
                
        except Exception as e:
            # Show error
            self.debug_console_output.append(f'<span style="color: #f85149;">Error: {str(e)}</span>')
            
        # Auto-scroll
        self.debug_console_output.verticalScrollBar().setValue(
            self.debug_console_output.verticalScrollBar().maximum()
        )
        
    def execute_terminal_command(self):
        """Execute terminal command"""
        command = self.terminal_input.text().strip()
        if not command:
            return
            
        # Clear input
        self.terminal_input.clear()
        
        # Show command in output
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.terminal_output.append(f'<span style="color: #00ff00;">[{timestamp}] $ {command}</span>')
        
        # Xử lý các lệnh đặc biệt (help, clear, pwd, cd, ls, ...)
        if command.lower() == 'help':
            self.terminal_output.append("Available commands:")
            self.terminal_output.append("  help - Show this help")
            self.terminal_output.append("  clear - Clear terminal")
            self.terminal_output.append("  pwd - Show current directory")
            self.terminal_output.append("  ls - List files")
            self.terminal_output.append("  cd <dir> - Change directory")
            self.terminal_output.append("  python <file> - Run Python file")
            self.terminal_output.append("  Any other shell command")
            self.terminal_output.append("")
            return
        if command.lower() == 'clear':
            self.terminal_output.clear()
            self.terminal_logic.clear_history()
            return
        if command.lower() == 'pwd':
            self.terminal_output.append(f'<span style="color: #00ff00;">{self.current_directory}</span>')
            self.terminal_output.append("")
            return
        if command.startswith('cd '):
            new_dir = command[3:].strip()
            try:
                if new_dir:
                    os.chdir(new_dir)
                    self.current_directory = os.getcwd()
                else:
                    os.chdir(os.path.expanduser("~"))
                    self.current_directory = os.getcwd()
                self.terminal_output.append(f'<span style="color: #00ff00;">Changed to: {self.current_directory}</span>')
            except Exception as e:
                self.terminal_output.append(f'<span style="color: #f85149;">Error: {str(e)}</span>')
            self.terminal_output.append("")
            return
        if command.lower() == 'ls' or command.lower() == 'dir':
            try:
                files = os.listdir(self.current_directory)
                for file in files:
                    file_path = os.path.join(self.current_directory, file)
                    if os.path.isdir(file_path):
                        self.terminal_output.append(f'<span style="color: #569cd6;">📁 {file}/</span>')
                    else:
                        self.terminal_output.append(f'<span style="color: #d4d4d4;">📄 {file}</span>')
            except Exception as e:
                self.terminal_output.append(f'<span style="color: #f85149;">Error: {str(e)}</span>')
            self.terminal_output.append("")
            return
        # Các lệnh còn lại dùng TerminalOutput
        output, error, returncode = self.terminal_logic.run_command(command, cwd=self.current_directory)
        if output:
            self.terminal_output.append(f'<span style="color: #d4d4d4;">{output}</span>')
        if error:
            self.terminal_output.append(f'<span style="color: #f85149;">{error}</span>')
        if returncode != 0:
            self.terminal_output.append(f'<span style="color: #f85149;">Process exited with code {returncode}</span>')
        self.terminal_output.append("")
        self.terminal_output.verticalScrollBar().setValue(self.terminal_output.verticalScrollBar().maximum())