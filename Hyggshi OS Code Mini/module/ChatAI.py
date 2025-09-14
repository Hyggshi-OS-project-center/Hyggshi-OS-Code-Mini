from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
    QLabel, QDialog, QComboBox, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import threading
import json
import time
import traceback

# Import error handler
try:
    from .error_handler import error_handler, safe_call, handle_api_errors, timeout_handler
except ImportError:
    try:
        from error_handler import error_handler, safe_call, handle_api_errors, timeout_handler
    except ImportError:
        # Fallback if error_handler not available
        def safe_call(func):
            return func
        def handle_api_errors(api_name):
            def decorator(func):
                return func
            return decorator
        error_handler = None
        timeout_handler = None

try:
    import requests
except ImportError:
    requests = None

try:
    from requests.exceptions import RequestException, Timeout
except Exception:
    RequestException = Exception
    Timeout = Exception

try:
    from google import genai
except Exception:
    genai = None

from lupa import LuaRuntime
import os

# Initialize Lua runtime
lua = LuaRuntime(unpack_returned_tuples=True)
lua_path = os.path.join(os.path.dirname(__file__), "logicAI.lua")

# Load Lua script with proper error handling
logicAI = None
try:
    if os.path.exists(lua_path):
        with open(lua_path, "r", encoding="utf-8") as f:
            logicAI = lua.execute(f.read())
    else:
        print(f"Warning: Lua script 'logicAI.lua' not found at path: {lua_path}")
except Exception as e:
    print(f"Error loading Lua script: {e}")
    logicAI = None

# Import logging functions
try:
    from .log_AI import append_log, append_error
except ImportError:
    try:
        from log_AI import append_log, append_error
    except ImportError:
        # Fallback logging functions
        def append_log(sender, message):
            print(f"LOG [{sender}]: {message}")
        
        def append_error(error_msg, stacktrace=None):
            print(f"ERROR: {error_msg}")
            if stacktrace:
                print(stacktrace)

try:
    from .Gemini import call_gemini
except ImportError:
    try:
        from Gemini import call_gemini
    except ImportError:
        call_gemini = None


class ChatAIWidget(QWidget):
    append_message_signal = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Assistant")
        self.setMinimumWidth(350)
        self.setMaximumWidth(500)
        self.setStyleSheet("background: #1e1e1e; color: #d4d4d4;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # Title + Settings button
        title_layout = QHBoxLayout()
        title = QLabel("AI Assistant")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-weight: bold; font-size: 18px; padding: 8px 0; "
            "background: #252526; border-radius: 6px;"
        )
        title_layout.addWidget(title, 1)
        
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFixedWidth(32)
        self.settings_btn.setStyleSheet(
            "background: #23272e; color: #d4d4d4; border: none; font-size: 16px;"
        )
        self.settings_btn.clicked.connect(self.open_settings_dialog)
        title_layout.addWidget(self.settings_btn)
        main_layout.addLayout(title_layout)

        # Scrollable dialog area
        self.dialog_area = QTextEdit()
        self.dialog_area.setReadOnly(True)
        self.dialog_area.setStyleSheet(
            "background: #23272e; color: #d4d4d4; border: none; "
            "font-size: 14px; border-radius: 6px;"
        )
        self.dialog_area.setMinimumHeight(300)
        # Enable HTML formatting
        self.dialog_area.setAcceptRichText(True)
        main_layout.addWidget(self.dialog_area, 1)

        # Input + Send + Insert
        input_layout = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Enter question or use /explain, /fix, /test ...")
        self.input_box.setStyleSheet(
            "background: #1e1e1e; color: #d4d4d4; border: 1px solid #333; "
            "border-radius: 4px; padding: 6px;"
        )
        input_layout.addWidget(self.input_box, 1)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet(
            "background: #007acc; color: white; border-radius: 4px; padding: 6px 16px;"
        )
        input_layout.addWidget(self.send_btn)
        
        self.insert_btn = QPushButton("Insert Code")
        self.insert_btn.setStyleSheet(
            "background: #28a745; color: white; border-radius: 4px; padding: 6px 12px;"
        )
        self.insert_btn.setEnabled(False)
        self.insert_btn.clicked.connect(self.insert_code_to_editor)
        input_layout.addWidget(self.insert_btn)
        
        self.markdown_btn = QPushButton("📝")
        self.markdown_btn.setStyleSheet(
            "background: #6c757d; color: white; border-radius: 4px; padding: 6px 8px; font-size: 14px;"
        )
        self.markdown_btn.setToolTip("Toggle Markdown Preview")
        self.markdown_btn.setCheckable(True)
        self.markdown_btn.setChecked(True)
        self.markdown_btn.clicked.connect(self.toggle_markdown)
        input_layout.addWidget(self.markdown_btn)
        
        main_layout.addLayout(input_layout)

        # Initialize state variables
        self.api_company = None
        self.api_key = None
        self.api_model = None
        self.show_debug = False
        # Control whether to show the welcome message when the widget is created
        # Default: False to avoid noisy repeated welcome messages
        self.show_welcome_on_open = False
        self._last_raw_response = None
        self._api_watch_timer = None
        self.chat_history = []  # For OpenAI-style context
        self._is_processing = False
        self._pending_reply = None
        self._last_code_response = None  # Store last code response for insertion
        self._markdown_enabled = True  # Enable markdown by default

        # Connect signals
        self.send_btn.clicked.connect(self.on_send)
        self.input_box.returnPressed.connect(self.on_send)
        self.append_message_signal.connect(self.append_message)
        
        # Update UI state
        self.update_send_enabled()

        # Load chat history
        self.load_chat_history()
        
        # Add welcome message if no history and setting enabled
        if not self.chat_history and getattr(self, 'show_welcome_on_open', False):
            self.append_message("AI", "Welcome! Configure your API key in settings ⚙️ to get started.")

    def append_message(self, sender, message):
        print(f"[append_message] Called with sender={sender}, message={repr(message)}")
        """Add a message to the dialog area with proper formatting"""
        try:
            # Use QTextDocument for better formatting
            from PyQt5.QtGui import QTextDocument, QTextCursor
            from PyQt5.QtCore import Qt
            
            # Create formatted text
            if self._markdown_enabled:
                formatted_text = f'<div style="margin: 12px 0; padding: 8px; border-radius: 6px; background: rgba(255,255,255,0.02);"><b style="color:#569CD6; font-size: 14px;">{sender}:</b><br/>'
                formatted_text += self._format_message(message)
                formatted_text += '</div>'
            else:
                # Plain text mode
                formatted_text = f'<div style="margin: 8px 0;"><b style="color:#569CD6">{sender}:</b><br/><span style="color:#d4d4d4; font-family: monospace;">{message}</span></div>'
            
            # Insert HTML content
            cursor = self.dialog_area.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertHtml(formatted_text + '<br/>')
            
            # Scroll to bottom
            self.dialog_area.verticalScrollBar().setValue(
                self.dialog_area.verticalScrollBar().maximum()
            )
            
            # Log the message
            append_log(sender, message)
            
            # Save to chat history
            self.save_chat_history()
            
            # Try to write to output panel if it exists
            self._write_to_output_panel(sender, message)
        except Exception as e:
            print(f"Error appending message: {e}")
            # Fallback: try to append directly (no formatting)
            try:
                self.dialog_area.append(f"{sender}: {message}")
            except Exception as e2:
                print(f"[append_message fallback] Error: {e2}")

    def _format_message(self, message):
        """Format message for better display in chat with enhanced markdown support"""
        if not message:
            return ""
        
        import re
        formatted = str(message)
        
        # Enhanced markdown formatting
        
        # 1. Code blocks first (to avoid conflicts)
        formatted = re.sub(r'```(\w+)?\n?(.*?)```', 
                          r'<div style="background:#1e1e1e;border:1px solid #333;border-radius:6px;margin:8px 0;overflow-x:auto;"><div style="background:#2d2d2d;padding:8px 12px;color:#569cd6;font-size:12px;border-bottom:1px solid #333;">\1</div><pre style="margin:0;padding:12px;color:#d4d4d4;font-family:\'Consolas\',\'Monaco\',\'Courier New\',monospace;font-size:13px;line-height:1.4;white-space:pre-wrap;">\2</pre></div>', 
                          formatted, flags=re.DOTALL)
        
        # 2. Inline code
        formatted = re.sub(r'`([^`]+)`', 
                          r'<code style="background:#2d2d2d;color:#d4d4d4;padding:2px 6px;border-radius:3px;font-family:\'Consolas\',\'Monaco\',\'Courier New\',monospace;font-size:12px;border:1px solid #444;">\1</code>', 
                          formatted)
        
        # 3. Bold text: **text** -> <b>text</b>
        formatted = re.sub(r'\*\*(.*?)\*\*', r'<b style="color:#ffffff;font-weight:bold;">\1</b>', formatted)
        
        # 4. Italic text: *text* -> <i>text</i> (avoid conflicts with bold)
        formatted = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i style="color:#d4d4d4;font-style:italic;">\1</i>', formatted)
        
        # 5. Headers: # Header -> <h3>Header</h3>
        formatted = re.sub(r'^### (.*?)$', r'<h3 style="color:#569cd6;margin:12px 0 8px 0;font-size:16px;font-weight:bold;">\1</h3>', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^## (.*?)$', r'<h2 style="color:#4ec9b0;margin:16px 0 10px 0;font-size:18px;font-weight:bold;">\1</h2>', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^# (.*?)$', r'<h1 style="color:#4ec9b0;margin:20px 0 12px 0;font-size:20px;font-weight:bold;">\1</h1>', formatted, flags=re.MULTILINE)
        
        # 6. Lists: - item or * item -> <li>item</li>
        formatted = re.sub(r'^[\s]*[-*] (.*?)$', r'<li style="color:#d4d4d4;margin:4px 0;">\1</li>', formatted, flags=re.MULTILINE)
        
        # 7. Numbered lists: 1. item -> <li>item</li>
        formatted = re.sub(r'^[\s]*\d+\. (.*?)$', r'<li style="color:#d4d4d4;margin:4px 0;">\1</li>', formatted, flags=re.MULTILINE)
        
        # 8. Links: [text](url) -> <a>text</a>
        formatted = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" style="color:#569cd6;text-decoration:underline;">\1</a>', formatted)
        
        # 9. Blockquotes: > text -> <blockquote>text</blockquote>
        formatted = re.sub(r'^> (.*?)$', r'<blockquote style="border-left:4px solid #569cd6;margin:8px 0;padding:8px 12px;background:#2d2d2d;color:#d4d4d4;font-style:italic;">\1</blockquote>', formatted, flags=re.MULTILINE)
        
        # 10. Horizontal rules: --- -> <hr>
        formatted = re.sub(r'^---$', r'<hr style="border:none;border-top:1px solid #333;margin:16px 0;">', formatted, flags=re.MULTILINE)
        
        # 11. Line breaks and paragraphs
        formatted = formatted.replace('\n\n', '</p><p style="margin:8px 0;color:#d4d4d4;">')
        formatted = formatted.replace('\n', '<br/>')
        
        # Wrap in paragraph if not already wrapped
        if not formatted.startswith('<'):
            formatted = f'<p style="margin:8px 0;color:#d4d4d4;">{formatted}</p>'
        
        return formatted

    def _write_to_output_panel(self, sender, message):
        """Write message to parent's output panel if it exists"""
        try:
            win = self.window()
            if win and hasattr(win, 'output_panel'):
                out = getattr(win, 'output_panel')
                if out is not None and hasattr(out, 'append_text'):
                    out.append_text(f"{sender}: {message}")
        except Exception:
            pass

    def open_settings_dialog(self):
        """Open the settings dialog for API configuration"""
        dlg = QDialog(self)
        dlg.setWindowTitle("AI API Settings")
        dlg.setMinimumWidth(350)
        layout = QVBoxLayout(dlg)

        # Company selection
        company_label = QLabel("Select API Company:")
        layout.addWidget(company_label)
        company_combo = QComboBox()
        company_combo.addItems(["", "OpenAI", "Google", "Anthropic", "Cohere", "Ollama", "LM Studio", "XAI", "Microsoft"])
        if self.api_company:
            idx = company_combo.findText(self.api_company)
            if idx >= 0:
                company_combo.setCurrentIndex(idx)
        layout.addWidget(company_combo)

        # Model selection
        model_label = QLabel("Select Model:")
        layout.addWidget(model_label)
        model_combo = QComboBox()
        layout.addWidget(model_combo)

        model_options = {
    "OpenAI": [
        "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-5", "gpt-5-turbo",
    ],
    "Google": [
        "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro",
        "gemini-1.0-pro", "gemini-pro-vision"
    ],
    "Anthropic": [
        "claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-2.1", "claude-2.0", "claude-instant-1"
    ],
    "Cohere": [
        "command-r", "command-r-plus", "command", "command-light", "command-nightly"
    ],
    "Ollama": [
        "llama3.1", "llama2", "codellama", "mistral", "phi3", "gemma2", "mixtral", "dolphin-mixtral", "starcoder2"
    ],
    "LM Studio": [
        "local-model", "custom-model", "phi3", "llama3", "mistral", "deepseek-coder"
    ],
    "XAI": [
        "grok-4-latest", "grok-3", "grok-3-mini"
    ],
    "Microsoft": [
        "phi-3", "phi-2", "orca-2", "dolphin-2.6", "llama-2", "microsoft-gpt-4", "microsoft-gpt-35-turbo"
    ]
}

        def update_model_options():
            selected_company = company_combo.currentText()
            model_combo.clear()
            opts = model_options.get(selected_company, [])
            if opts:
                model_combo.addItems(opts)
                if self.api_model and self.api_model in opts:
                    idx = model_combo.findText(self.api_model)
                    if idx >= 0:
                        model_combo.setCurrentIndex(idx)
            else:
                model_combo.addItem("Default")

        company_combo.currentTextChanged.connect(lambda: update_model_options())
        update_model_options()

        # Debug checkbox
        debug_chk = QCheckBox("Show debug API responses")
        debug_chk.setChecked(self.show_debug)
        layout.addWidget(debug_chk)

        # API key input
        key_label = QLabel("Enter API Key:")
        layout.addWidget(key_label)
        key_edit = QLineEdit()
        key_edit.setPlaceholderText("Paste your API key here...")
        key_edit.setEchoMode(QLineEdit.Password)
        if self.api_key:
            key_edit.setText(self.api_key)
        layout.addWidget(key_edit)

        # Save button
        save_btn = QPushButton("Save")
        layout.addWidget(save_btn)

        def save():
            company = company_combo.currentText().strip()
            key = key_edit.text().strip()
            model = model_combo.currentText().strip()
            
            if not company:
                QMessageBox.warning(dlg, "Missing Company", 
                                  "Please select the company/service for your API key.")
                return
            
            if not key or len(key) < 10:
                if company not in ["Ollama", "LM Studio"]:
                    QMessageBox.warning(dlg, "Invalid Key", 
                                       "Please enter a valid API key.")
                    return
            # Validate API key format
            if company == "OpenAI" and not key.startswith("sk-"):
                QMessageBox.warning(dlg, "Invalid OpenAI Key", 
                                  "OpenAI API keys should start with 'sk-'.")
                return
            
            if company == "Google" and not (key.startswith("AIza") or len(key) >= 30):
                QMessageBox.warning(dlg, "Invalid Google Key", 
                                  "Please check your Google API key format.")
                return
            
            if company in ["Ollama", "LM Studio"]:
                # For local models, key can be empty or localhost URL
                if key and not (key.startswith("http://") or key.startswith("https://")):
                    key = f"http://localhost:11434" if company == "Ollama" else f"http://localhost:1234"
                
            self.api_company = company
            self.api_key = key
            self.api_model = model if model and model != "Default" else None
            self.show_debug = debug_chk.isChecked()
            self.chat_history.clear()  # Reset chat history when changing settings
            
            QMessageBox.information(dlg, "Saved", f"API key for {company} saved.")
            dlg.accept()
            self.update_send_enabled()

        save_btn.clicked.connect(save)
        dlg.exec_()

    def update_send_enabled(self):
        """Update the enabled state of send button and input box"""
        enabled = bool(self.api_company and self.api_key) and not self._is_processing
        self.send_btn.setEnabled(enabled)
        self.input_box.setEnabled(enabled)
        
        if self._is_processing:
            self.input_box.setPlaceholderText("Processing...")
        elif not self.api_company or not self.api_key:
            self.input_box.setPlaceholderText("Configure API key in settings ⚙️")
        else:
            self.input_box.setPlaceholderText("Enter question ...")

    def on_send(self):
        """Handle send button click"""
        user_msg = self.input_box.text().strip()
        if not user_msg or self._is_processing:
            return

        # Process slash commands
        processed_msg = self._process_slash_commands(user_msg)

        self.append_message("User", user_msg)
        self.input_box.clear()

        # Always use API if configured
        if self.api_company and self.api_key:
            # Add user message to chat history first
            self.chat_history.append({"role": "user", "content": processed_msg})
            self._is_processing = True
            self.update_send_enabled()
            threading.Thread(target=lambda: self._call_ai_api(processed_msg), daemon=True).start()
        else:
            # Fallback to Lua/local logic
            try:
                if logicAI and hasattr(logicAI, 'on_user_message'):
                    reply = logicAI.on_user_message(processed_msg)
                    if not reply:
                        reply = "Xin lỗi, tôi không thể tạo phản hồi."
                else:
                    reply = "Vui lòng cấu hình API key trong settings để sử dụng tính năng AI."
                self.append_message("AI", reply)
            except Exception as e:
                self.append_message("AI", f"Lỗi: {str(e)}")

    def _process_slash_commands(self, message):
        """Process slash commands and return modified message"""
        if message.startswith('/explain'):
            return f"Giải thích chi tiết: {message[8:].strip()}"
        elif message.startswith('/fix'):
            return f"Sửa lỗi code: {message[4:].strip()}"
        elif message.startswith('/test'):
            return f"Viết test case cho: {message[5:].strip()}"
        elif message.startswith('/code'):
            return f"Viết code: {message[5:].strip()}"
        else:
            return message

    def _call_ai_api(self, user_msg):
        """Call AI API in background thread with error handling"""
        operation_id = f"api_call_{int(time.time())}"
        
        # Start timeout
        if timeout_handler:
            timeout_handler.start_timeout(operation_id, lambda: self._handle_timeout())
        
        try:
            if self.api_company == "OpenAI":
                reply = self._call_openai_api()
            elif self.api_company == "Google":
                reply = self._call_google_gemini_api()
            elif self.api_company == "Anthropic":
                reply = self._call_anthropic_api()
            elif self.api_company == "Cohere":
                reply = self._call_cohere_api()
            elif self.api_company == "Ollama":
                reply = self._call_ollama_api()
            elif self.api_company == "LM Studio":
                reply = self._call_lm_studio_api()
            else:
                reply = f"API integration for {self.api_company} is not implemented yet."
                
            # Cancel timeout on success
            if timeout_handler:
                timeout_handler.cancel_timeout(operation_id)
                
        except Exception as e:
            reply = f"API error: {str(e)}"
            if error_handler:
                error_handler.handle_api_error(self.api_company or "Unknown", e, f"User message: {user_msg[:50]}...")
            else:
                append_error(f"API error: {str(e)}", traceback.format_exc())

        # Store reply and use QTimer to update UI on main thread
        self._pending_reply = reply
        QTimer.singleShot(0, self._handle_api_response)
        
    def _handle_timeout(self):
        """Handle API timeout"""
        self._pending_reply = "Request timed out. Please try again or check your connection."
        QTimer.singleShot(0, self._handle_api_response)

    def _handle_api_response(self):
        """Handle API response in main thread"""
        try:
            reply = getattr(self, '_pending_reply', None)
            print(f"[ChatAI] Handling API response: {repr(reply)}")
            final_reply = reply if reply and str(reply).strip() else "(No response received from AI)"
            
            # Check if response contains code and enable insert button
            self._check_for_code(final_reply)
            
            # Direct UI update - force immediate display
            print(f"[ChatAI] About to append: AI: {final_reply}")
            self.dialog_area.append(f'<b style="color:#569CD6">AI:</b> {final_reply}')
            self.dialog_area.verticalScrollBar().setValue(self.dialog_area.verticalScrollBar().maximum())
            self.dialog_area.repaint()  # Force repaint
            
            # Also log it
            append_log("AI", final_reply)
            
            if self.show_debug and self._last_raw_response is not None:
                try:
                    if isinstance(self._last_raw_response, dict):
                        raw_text = json.dumps(self._last_raw_response, ensure_ascii=False, indent=2)
                    else:
                        raw_text = str(self._last_raw_response)
                    self.dialog_area.append(f'<b style="color:#FFA500">Debug:</b> {raw_text}')
                except Exception:
                    self.dialog_area.append(f'<b style="color:#FFA500">Debug:</b> {str(self._last_raw_response)}')
        finally:
            self._is_processing = False
            self.update_send_enabled()

    def _check_for_code(self, response):
        """Check if response contains code and enable insert button"""
        import re
        # Look for code blocks or code patterns
        code_patterns = [
            r'```[\s\S]*?```',  # Code blocks
            r'`[^`]+`',         # Inline code
            r'(def |class |function |import |from |#include)',  # Common code keywords
        ]
        
        has_code = any(re.search(pattern, response, re.IGNORECASE) for pattern in code_patterns)
        
        if has_code:
            self._last_code_response = response
            self.insert_btn.setEnabled(True)
            self.insert_btn.setText("Insert Code")
        else:
            self.insert_btn.setEnabled(False)
            self.insert_btn.setText("Insert Code")

    def insert_code_to_editor(self):
        """Insert the last code response into the editor"""
        if not self._last_code_response:
            return
            
        try:
            # Extract code from response
            import re
            code_blocks = re.findall(r'```(?:python|py|javascript|js|java|cpp|c\+\+|c|html|css|sql)?\n?(.*?)```', 
                                   self._last_code_response, re.DOTALL | re.IGNORECASE)
            
            if code_blocks:
                code = code_blocks[0].strip()
            else:
                # Try to extract inline code or other patterns
                inline_code = re.findall(r'`([^`]+)`', self._last_code_response)
                if inline_code:
                    code = inline_code[0]
                else:
                    # Use the whole response if no code blocks found
                    code = self._last_code_response
            
            # Try to insert into parent window's editor
            self._insert_into_parent_editor(code)
            
        except Exception as e:
            print(f"Error inserting code: {e}")
            self.append_message("System", f"Lỗi khi chèn code: {e}")

    def _insert_into_parent_editor(self, code):
        """Insert code into the parent window's editor"""
        try:
            # Get the main window
            main_window = self.window()
            if main_window and hasattr(main_window, 'editor'):
                editor = main_window.editor
                if editor and hasattr(editor, 'insert_text'):
                    editor.insert_text(code)
                    self.append_message("System", "Code đã được chèn vào editor!")
                else:
                    self.append_message("System", "Không tìm thấy editor để chèn code.")
            else:
                self.append_message("System", "Không thể truy cập editor. Vui lòng copy code thủ công.")
        except Exception as e:
            print(f"Error accessing parent editor: {e}")
            self.append_message("System", f"Lỗi truy cập editor: {e}")

    def load_chat_history(self):
        """Load chat history from ai_chat_log.txt"""
        try:
            log_path = os.path.join(os.path.dirname(__file__), "ai_chat_log.txt")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                # Parse log entries and rebuild chat history
                for line in lines:
                    if "User:" in line:
                        # Extract user message
                        parts = line.split("User:", 1)
                        if len(parts) > 1:
                            message = parts[1].strip()
                            self.chat_history.append({"role": "user", "content": message})
                    elif "AI:" in line:
                        # Extract AI message
                        parts = line.split("AI:", 1)
                        if len(parts) > 1:
                            message = parts[1].strip()
                            self.chat_history.append({"role": "assistant", "content": message})
                
                # Display loaded history in UI
                for msg in self.chat_history[-20:]:  # Show last 20 messages
                    role = msg["role"]
                    content = msg["content"]
                    if role == "user":
                        self.append_message("User", content)
                    elif role == "assistant":
                        self.append_message("AI", content)
                        
        except Exception as e:
            print(f"Error loading chat history: {e}")

    def save_chat_history(self):
        """Save current chat history to ai_chat_log.txt"""
        try:
            log_path = os.path.join(os.path.dirname(__file__), "ai_chat_log.txt")
            
            # Write chat history in a structured format
            with open(log_path, "w", encoding="utf-8") as f:
                for msg in self.chat_history:
                    role = msg["role"]
                    content = msg["content"]
                    f.write(f"{role.title()}: {content}\n")
                    
        except Exception as e:
            print(f"Error saving chat history: {e}")

    def toggle_markdown(self):
        """Toggle markdown formatting on/off"""
        self._markdown_enabled = self.markdown_btn.isChecked()
        
        if self._markdown_enabled:
            self.markdown_btn.setText("📝")
            self.markdown_btn.setToolTip("Markdown Preview: ON")
            self.markdown_btn.setStyleSheet(
                "background: #28a745; color: white; border-radius: 4px; padding: 6px 8px; font-size: 14px;"
            )
        else:
            self.markdown_btn.setText("📄")
            self.markdown_btn.setToolTip("Markdown Preview: OFF")
            self.markdown_btn.setStyleSheet(
                "background: #6c757d; color: white; border-radius: 4px; padding: 6px 8px; font-size: 14px;"
            )
        
        # Refresh the chat display
        self.refresh_chat_display()

    def refresh_chat_display(self):
        """Refresh the entire chat display with current markdown setting"""
        try:
            # Clear the dialog area
            self.dialog_area.clear()
            
            # Re-display all messages with current formatting
            for msg in self.chat_history[-50:]:  # Show last 50 messages
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    self.append_message("User", content)
                elif role == "assistant":
                    self.append_message("AI", content)
                    
        except Exception as e:
            print(f"Error refreshing chat display: {e}")

    def _call_openai_api(self):
        """Call OpenAI API"""
        if requests is None:
            raise Exception("The 'requests' library is not installed. Please install it with 'pip install requests'.")
        
        model = self.api_model or 'gpt-3.5-turbo'
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": self.chat_history[-10:],  # Keep last 10 messages for context
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            result = resp.json()
            self._last_raw_response = result
            
            if resp.status_code == 200:
                ai_msg = result["choices"][0]["message"]["content"].strip()
                self.chat_history.append({"role": "assistant", "content": ai_msg})
                return ai_msg
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                raise Exception(f"OpenAI API error: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected response format: {str(e)}")

    def _call_google_gemini_api(self):
        """Call Google Gemini API using the shared Gemini module"""
        if call_gemini is None:
            print("[ChatAI] Gemini API function not found.")
            raise Exception("Gemini API function not found. Please check module.Gemini.py.")
        if not self.api_key:
            print("[ChatAI] No API key provided for Gemini API.")
            raise Exception("No API key provided for Gemini API.")
        model = self.api_model or 'gemini-2.0-flash'
        try:
            # Get the latest user message
            latest_user_msg = self.chat_history[-1]["content"] if self.chat_history else "Hello"
            print(f"[ChatAI] Calling Gemini with model={model}, message='{latest_user_msg}'...")
            
            # Add user message to chat history if not already there
            if not self.chat_history or self.chat_history[-1]["role"] != "user":
                self.chat_history.append({"role": "user", "content": latest_user_msg})
            
            ai_msg = call_gemini(self.api_key, model, latest_user_msg, chat_history=self.chat_history)
            print(f"[ChatAI] Gemini response: {repr(ai_msg)}")
            
            if not ai_msg or not str(ai_msg).strip():
                ai_msg = "Xin lỗi, tôi không thể tạo phản hồi. Vui lòng thử lại."
            
            # Add AI response to chat history
            self.chat_history.append({"role": "assistant", "content": ai_msg})
            return ai_msg
        except Exception as e:
            print(f"[ChatAI] Gemini API error: {e}")
            return f"Lỗi API Gemini: {e}"

    def _call_anthropic_api(self):
        """Call Anthropic Claude API"""
        if requests is None:
            raise Exception("The 'requests' library is not installed.")
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Get the latest user message
        latest_message = self.chat_history[-1]["content"] if self.chat_history else "Hello"
        
        data = {
            "model": self.api_model or "claude-3-sonnet-20240229",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": latest_message}]
        }
        
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            result = resp.json()
            self._last_raw_response = result
            
            if resp.status_code == 200:
                ai_msg = result["content"][0]["text"].strip()
                self.chat_history.append({"role": "assistant", "content": ai_msg})
                return ai_msg
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                raise Exception(f"Anthropic API error: {error_msg}")
        except Exception as e:
            raise Exception(f"Anthropic API call failed: {str(e)}")

    def _call_cohere_api(self):
        """Call Cohere API"""
        return "Cohere API integration not implemented yet. Please use OpenAI or Google."

    def _call_ollama_api(self):
        """Call Ollama local API"""
        if requests is None:
            raise Exception("The 'requests' library is not installed.")
        
        model = self.api_model or 'llama3.1'
        url = f"{self.api_key or 'http://localhost:11434'}/api/generate"
        
        # Get the latest user message
        latest_message = self.chat_history[-1]["content"] if self.chat_history else "Hello"
        
        data = {
            "model": model,
            "prompt": latest_message,
            "stream": False
        }
        
        try:
            resp = requests.post(url, json=data, timeout=60)
            result = resp.json()
            self._last_raw_response = result
            
            if resp.status_code == 200:
                ai_msg = result.get("response", "").strip()
                self.chat_history.append({"role": "assistant", "content": ai_msg})
                return ai_msg
            else:
                error_msg = result.get("error", "Unknown error")
                raise Exception(f"Ollama API error: {error_msg}")
        except Exception as e:
            raise Exception(f"Ollama API call failed: {str(e)}")

    def _call_lm_studio_api(self):
        """Call LM Studio local API"""
        if requests is None:
            raise Exception("The 'requests' library is not installed.")
        
        model = self.api_model or 'local-model'
        url = f"{self.api_key or 'http://localhost:1234'}/v1/chat/completions"
        
        # Convert chat history to OpenAI format
        messages = []
        for msg in self.chat_history[-10:]:  # Keep last 10 messages
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            resp = requests.post(url, json=data, timeout=60)
            result = resp.json()
            self._last_raw_response = result
            
            if resp.status_code == 200:
                ai_msg = result["choices"][0]["message"]["content"].strip()
                self.chat_history.append({"role": "assistant", "content": ai_msg})
                return ai_msg
            else:
                error_msg = result.get("error", {}).get("message", "Unknown error")
                raise Exception(f"LM Studio API error: {error_msg}")
        except Exception as e:
            raise Exception(f"LM Studio API call failed: {str(e)}")

    def call_gemini_google_ai_studio(api_key, model, prompt):
        """
        Call Gemini Google AI Studio API (now uses shared Gemini module)
        """
        if call_gemini is None:
            return "Gemini API function not found."
        try:
            return call_gemini(api_key, model, prompt)
        except Exception as e:
            return f"Gemini API error: {e}"


def main():
    """Main function for testing the widget"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    widget = ChatAIWidget()
    widget.show()
    sys.exit(app.exec_())
