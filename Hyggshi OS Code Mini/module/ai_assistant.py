"""
AI Assistant Plugin for Hyggshi OS Code Mini
Demonstrates how to create a plugin using the plugin system
"""

import os
import sys
from PyQt5.QtWidgets import QAction, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Add parent directory to path to import ChatAI
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from module.ChatAI import ChatAIWidget
    from module.plugin_system import PluginInterface
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    # Fallback interface
    class PluginInterface:
        def __init__(self):
            self.name = "AI Assistant"
            self.version = "1.0.0"
            self.description = "AI Assistant Plugin"
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

class AIAssistantPlugin(PluginInterface):
    """AI Assistant Plugin"""
    
    def __init__(self):
        super().__init__()
        self.name = "AI Assistant"
        self.version = "1.0.0"
        self.description = "AI-powered coding assistant with multiple model support"
        self.author = "Hyggshi OS Team"
        self.main_window = None
        self.chat_widget = None
        
    def initialize(self, main_window):
        """Initialize the plugin"""
        self.main_window = main_window
        
        # Create AI Assistant widget
        try:
            self.chat_widget = ChatAIWidget()
            
            # Add to main window if it has a method to add widgets
            if hasattr(main_window, 'add_dock_widget'):
                main_window.add_dock_widget(self.chat_widget, "AI Assistant", Qt.RightDockWidgetArea)
            elif hasattr(main_window, 'add_sidebar_widget'):
                main_window.add_sidebar_widget(self.chat_widget, "AI Assistant")
            else:
                # Fallback: try to add to a central widget or layout
                if hasattr(main_window, 'central_widget'):
                    layout = main_window.central_widget.layout()
                    if layout:
                        layout.addWidget(self.chat_widget)
                        
        except Exception as e:
            print(f"Error initializing AI Assistant plugin: {e}")
            
    def cleanup(self):
        """Cleanup when plugin is unloaded"""
        if self.chat_widget:
            try:
                self.chat_widget.close()
                self.chat_widget = None
            except Exception as e:
                print(f"Error cleaning up AI Assistant plugin: {e}")
                
    def get_menu_items(self):
        """Return menu items for this plugin"""
        menu_items = []
        
        # AI Assistant menu
        ai_action = QAction("AI Assistant", self.main_window)
        ai_action.setToolTip("Open AI Assistant")
        ai_action.triggered.connect(self.show_ai_assistant)
        menu_items.append(ai_action)
        
        # AI Settings menu
        settings_action = QAction("AI Settings", self.main_window)
        settings_action.setToolTip("Configure AI settings")
        settings_action.triggered.connect(self.show_ai_settings)
        menu_items.append(settings_action)
        
        return menu_items
        
    def get_toolbar_items(self):
        """Return toolbar items for this plugin"""
        toolbar_items = []
        
        # AI Assistant button
        ai_button = QPushButton("🤖 AI")
        ai_button.setToolTip("Open AI Assistant")
        ai_button.clicked.connect(self.show_ai_assistant)
        ai_button.setStyleSheet("""
            QPushButton {
                background: #007acc; color: white; border: none;
                border-radius: 4px; padding: 6px 12px; font-weight: bold;
            }
            QPushButton:hover { background: #005a9e; }
        """)
        toolbar_items.append(ai_button)
        
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
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Settings button
        settings_btn = QPushButton("Open AI Settings")
        settings_btn.clicked.connect(self.show_ai_settings)
        layout.addWidget(settings_btn)
        
        layout.addStretch()
        return widget
        
    def show_ai_assistant(self):
        """Show the AI Assistant widget"""
        if self.chat_widget:
            self.chat_widget.show()
            self.chat_widget.raise_()
            self.chat_widget.activateWindow()
        else:
            # Recreate if needed
            self.initialize(self.main_window)
            
    def show_ai_settings(self):
        """Show AI settings dialog"""
        if self.chat_widget and hasattr(self.chat_widget, 'open_settings_dialog'):
            self.chat_widget.open_settings_dialog()
        else:
            print("AI settings not available")

# Plugin class that will be imported
Plugin = AIAssistantPlugin
