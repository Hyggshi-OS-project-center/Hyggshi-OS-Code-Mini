from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QComboBox, QCheckBox, QSplitter, QTabWidget,
    QLineEdit, QProgressBar, QGroupBox, QGridLayout, 
    QListWidget, QListWidgetItem, QToolBar, QAction
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSettings, QDateTime
from PyQt5.QtGui import QFont, QColor, QKeySequence
import datetime
import os
import subprocess
import psutil
from collections import deque

class CompactSystemMonitor(QWidget):
    """Enhanced compact system monitoring widget with mini chart"""
    def __init__(self):
        super().__init__()
        self.cpu_history = deque(maxlen=20)
        self.ram_history = deque(maxlen=20)
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)  # Update every 2 seconds
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(3, 3, 3, 3)
        
        # CPU section
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU:"))
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximumHeight(12)
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setStyleSheet("""
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff00, stop:0.7 #ffff00, stop:1 #ff0000);
            }
        """)
        
        self.cpu_label = QLabel("0%")
        self.cpu_label.setMinimumWidth(35)
        
        cpu_layout.addWidget(self.cpu_progress, 1)
        cpu_layout.addWidget(self.cpu_label)
        
        # RAM section  
        ram_layout = QHBoxLayout()
        ram_layout.addWidget(QLabel("RAM:"))
        
        self.memory_progress = QProgressBar()
        self.memory_progress.setMaximumHeight(12)
        self.memory_progress.setRange(0, 100)
        self.memory_progress.setStyleSheet("""
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00ff00, stop:0.6 #ffff00, stop:1 #ff0000);
            }
        """)
        
        self.memory_label = QLabel("0%")
        self.memory_label.setMinimumWidth(35)
        
        ram_layout.addWidget(self.memory_progress, 1)
        ram_layout.addWidget(self.memory_label)
        
        # Mini chart area
        self.chart_label = QLabel()
        self.chart_label.setMaximumHeight(40)
        self.chart_label.setStyleSheet("border: 1px solid #333; background: #000;")
        
        layout.addLayout(cpu_layout)
        layout.addLayout(ram_layout)
        layout.addWidget(QLabel("History:"))
        layout.addWidget(self.chart_label)
        
    def update_stats(self):
        try:
            cpu_percent = psutil.cpu_percent()
            self.cpu_progress.setValue(int(cpu_percent))
            self.cpu_label.setText(f"{cpu_percent:.0f}%")
            
            memory = psutil.virtual_memory()
            self.memory_progress.setValue(int(memory.percent))
            self.memory_label.setText(f"{memory.percent:.0f}%")
            
            # Store history
            self.cpu_history.append(cpu_percent)
            self.ram_history.append(memory.percent)
            
            # Update mini chart
            self.update_mini_chart()
            
        except:
            pass
            
    def update_mini_chart(self):
        """Update mini chart display"""
        if len(self.cpu_history) < 2:
            return
            
        # Create simple ASCII-style chart
        chart_text = "CPU: "
        for val in list(self.cpu_history)[-10:]:
            if val < 30:
                chart_text += "▁"
            elif val < 60:
                chart_text += "▃" 
            else:
                chart_text += "▇"
                
        chart_text += "\nRAM: "
        for val in list(self.ram_history)[-10:]:
            if val < 30:
                chart_text += "▁"
            elif val < 60:
                chart_text += "▃"
            else:
                chart_text += "▇"
                
        self.chart_label.setText(chart_text)
        self.chart_label.setStyleSheet("""
            border: 1px solid #333; background: #000; color: #00ff00;
            font-family: monospace; font-size: 10px; padding: 2px;
        """)

class OutputPanel(QTextEdit):
    """Compact Output Panel with essential features"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        
        self.settings = QSettings("OutputPanel", "Settings")
        self.setup_ui()
        self.setup_styling()
        
        # Output storage
        self.output_categories = {
            "Problems": deque(maxlen=1000),
            "Output": deque(maxlen=1500),
            "Terminal": deque(maxlen=800)
        }
        
        self.auto_scroll = True
        self.max_lines = 1000
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Compact toolbar
        self.create_compact_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        
        # Create compact tabs
        self.create_compact_tabs()
        
        # Right: Compact sidebar
        sidebar = self.create_compact_sidebar()
        sidebar.setMaximumWidth(200)
        sidebar.setMinimumWidth(180)
        
        splitter.addWidget(self.tab_widget)
        splitter.addWidget(sidebar)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # Compact status bar
        self.status_label = QLabel("Ready")
        self.status_label.setMaximumHeight(20)
        main_layout.addWidget(self.status_label)
        
    def create_compact_toolbar(self):
        """Create compact toolbar with essential buttons"""
        self.toolbar = QToolBar()
        self.toolbar.setMaximumHeight(35)
        
        # Essential actions only
        clear_action = QAction("Clear", self)
        clear_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_action.triggered.connect(self.clear_all)
        self.toolbar.addAction(clear_action)
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_logs)
        self.toolbar.addAction(save_action)
        
        self.auto_scroll_action = QAction("Auto-scroll", self)
        self.auto_scroll_action.setCheckable(True)
        self.auto_scroll_action.setChecked(True)
        self.auto_scroll_action.triggered.connect(self.toggle_auto_scroll)
        self.toolbar.addAction(self.auto_scroll_action)
        
    def create_compact_tabs(self):
        """Create essential tabs only"""
        # Problems tab
        self.problems_widget = self.create_output_widget("Problems")
        self.tab_widget.addTab(self.problems_widget, "Problems")
        
        # Output tab
        self.output_widget = self.create_output_widget("Output")
        self.tab_widget.addTab(self.output_widget, "Output")
        
        # Terminal tab
        self.terminal_widget = self.create_terminal_widget()
        self.tab_widget.addTab(self.terminal_widget, "Terminal")
        
    def create_output_widget(self, category):
        """Create compact output widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Text edit
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setMaximumHeight(400)  # Limit height
        
        layout.addWidget(text_edit)
        
        # Store reference
        setattr(self, f"{category.lower()}_output", text_edit)
        
        return widget
        
    def create_terminal_widget(self):
        """Create compact terminal"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Terminal output
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setMaximumHeight(300)
        
        # Terminal input
        input_layout = QHBoxLayout()
        self.terminal_input = QLineEdit()
        self.terminal_input.setPlaceholderText("Enter command...")
        
        execute_btn = QPushButton("Run")
        execute_btn.setMaximumWidth(60)
        execute_btn.clicked.connect(self.execute_command)
        
        input_layout.addWidget(QLabel("$"))
        input_layout.addWidget(self.terminal_input)
        input_layout.addWidget(execute_btn)
        
        layout.addWidget(self.terminal_output)
        layout.addLayout(input_layout)
        
        # Connect enter key
        self.terminal_input.returnPressed.connect(self.execute_command)
        
        return widget
        
    def create_compact_sidebar(self):
        """Create compact sidebar"""
        sidebar = QWidget()
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(5)
        
        # Compact filters
        filter_group = QGroupBox("Filters")
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setSpacing(3)
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["All", "Error", "Warning", "Info"])
        self.level_combo.setMaximumHeight(25)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setMaximumHeight(25)
        
        filter_layout.addWidget(QLabel("Level:"))
        filter_layout.addWidget(self.level_combo)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input)
        
        # System monitor
        self.system_monitor = CompactSystemMonitor()
        
        # Compact stats
        stats_group = QGroupBox("Stats")
        stats_layout = QGridLayout(stats_group)
        
        self.message_count_label = QLabel("0")
        self.error_count_label = QLabel("0")
        
        stats_layout.addWidget(QLabel("Messages:"), 0, 0)
        stats_layout.addWidget(self.message_count_label, 0, 1)
        stats_layout.addWidget(QLabel("Errors:"), 1, 0)
        stats_layout.addWidget(self.error_count_label, 1, 1)
        
        layout.addWidget(filter_group)
        layout.addWidget(self.system_monitor)
        layout.addWidget(stats_group)
        layout.addStretch()
        
        return sidebar
        
    def setup_styling(self):
        """Compact dark theme styling"""
        self.setStyleSheet("""
            QWidget {
                background: #1e1e1e; color: #d4d4d4;
                font-family: 'Consolas', monospace; font-size: 14px;
            }
            QTabWidget::pane { border: 1px solid #333; }
            QTabBar::tab {
                background: #2d2d2d; color: #d4d4d4; 
                padding: 4px 8px; margin: 1px;
            }
            QTabBar::tab:selected { background: #007acc; }
            QTextEdit {
                background: #1e1e1e; color: #d4d4d4; border: 1px solid #333;
                font-family: monospace; font-size: 14px;
            }
            QLineEdit {
                background: #2d2d2d; color: #d4d4d4; border: 1px solid #333;
                padding: 3px; border-radius: 2px;
            }
            QPushButton {
                background: #007acc; color: white; border: none;
                padding: 4px 8px; border-radius: 2px;
            }
            QPushButton:hover { background: #005a9e; }
            QComboBox {
                background: #2d2d2d; color: #d4d4d4; border: 1px solid #333;
                padding: 2px; min-height: 20px;
            }
            QProgressBar {
                background: #333; border: 1px solid #555; border-radius: 2px;
            }
            QProgressBar::chunk { background: #007acc; }
            QGroupBox {
                border: 1px solid #333; margin-top: 5px; padding-top: 5px;
                font-weight: bold; font-size: 10px;
            }
            QToolBar {
                background: #2d2d2d; border: none; spacing: 2px;
            }
            QAction { padding: 3px 6px; }
        """)
        
    def append_text(self, text, level="Info", category="Output"):
        """Append text with standard log color classification and 'new engine' highlighting"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_text = f"[{timestamp}] {text}"
        
        # Store in category
        self.output_categories[category].append({
            'text': formatted_text, 'level': level
        })
        
        # Get target widget
        target_widget = getattr(self, f"{category.lower()}_output", None)
        if target_widget:
            # Standard log color classification
            color_map = {
                "Info": "#00ff00",      # Green for info
                "Warning": "#ffff00",   # Yellow for warning  
                "Error": "#ff0000"      # Red for error
            }
            color = color_map.get(level, "#d4d4d4")
            
            # Check for "new engine" highlight
            display_text = formatted_text
            if "new engine" in text.lower():
                # Highlight "new engine" with special styling
                display_text = formatted_text.replace(
                    "new engine", 
                    '<span style="background: #007acc; color: #ffffff; font-weight: bold; padding: 2px 4px; border-radius: 3px;">🚀 NEW ENGINE</span>'
                )
                display_text = f'<span style="color: {color}; font-weight: bold;">⭐ {display_text}</span>'
            else:
                display_text = f'<span style="color: {color};">{display_text}</span>'
            
            target_widget.append(display_text)
            
            # Auto-scroll
            if self.auto_scroll:
                scrollbar = target_widget.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
                
            # Limit lines
            if target_widget.document().blockCount() > self.max_lines:
                cursor = target_widget.textCursor()
                cursor.movePosition(cursor.Start)
                cursor.movePosition(cursor.Down, cursor.KeepAnchor, 100)
                cursor.removeSelectedText()
                
        self.update_stats()
        
    def execute_command(self):
        """Execute terminal command"""
        command = self.terminal_input.text().strip()
        if not command:
            return
            
        self.terminal_input.clear()
        
        # Show command
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.terminal_output.append(f'<span style="color: #00ff00;">[{timestamp}] $ {command}</span>')
        
        # Execute command
        try:
            if command == 'clear':
                self.terminal_output.clear()
                return
                
            result = subprocess.run(
                command, shell=True, capture_output=True, 
                text=True, timeout=10, cwd=os.getcwd()
            )
            
            if result.stdout:
                self.terminal_output.append(result.stdout.strip())
            if result.stderr:
                self.terminal_output.append(f'<span style="color: #f85149;">{result.stderr.strip()}</span>')
                
        except subprocess.TimeoutExpired:
            self.terminal_output.append('<span style="color: #f85149;">Command timed out</span>')
        except Exception as e:
            self.terminal_output.append(f'<span style="color: #f85149;">Error: {str(e)}</span>')
            
        # Auto-scroll
        if self.auto_scroll:
            scrollbar = self.terminal_output.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def update_stats(self):
        """Update statistics"""
        total = sum(len(msgs) for msgs in self.output_categories.values())
        errors = sum(1 for msgs in self.output_categories.values() 
                    for msg in msgs if msg.get('level') == 'Error')
        
        self.message_count_label.setText(str(total))
        self.error_count_label.setText(str(errors))
        
    def toggle_auto_scroll(self, enabled):
        """Toggle auto-scroll"""
        self.auto_scroll = enabled
        
    def save_logs(self):
        """Save logs to file"""
        try:
            filename = f"logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Compact Output Panel Logs\n")
                f.write("=" * 30 + "\n\n")
                
                for category, messages in self.output_categories.items():
                    if messages:
                        f.write(f"\n[{category}]\n")
                        for msg in messages:
                            f.write(f"{msg['text']}\n")
                            
            self.status_label.setText(f"Logs saved to {filename}")
            
        except Exception as e:
            self.status_label.setText(f"Save failed: {str(e)}")
            
    def clear_all(self):
        """Clear all outputs"""
        for attr_name in ['problems_output', 'output_output', 'terminal_output']:
            if hasattr(self, attr_name):
                getattr(self, attr_name).clear()
                
        for category in self.output_categories:
            self.output_categories[category].clear()
            
        self.status_label.setText("Cleared")

# Example usage
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    panel = OutputPanel()
    panel.setWindowTitle("Compact Output Panel")
    panel.resize(800, 500)  # Smaller default size
    panel.show()
    
    # Test with sample data
    panel.append_text("Application started", "Info", "Output")
    panel.append_text("Build completed successfully", "Info", "Output") 
    panel.append_text("Warning: Deprecated function used", "Warning", "Problems")
    panel.append_text("Error: File not found", "Error", "Problems")
    panel.append_text("Initializing new engine components", "Info", "Output")
    panel.append_text("New engine successfully loaded", "Info", "Output")
    
    sys.exit(app.exec_())