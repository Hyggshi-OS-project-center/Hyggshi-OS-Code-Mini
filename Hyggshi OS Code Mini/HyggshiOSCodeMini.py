import sys, os
import glob
import importlib.util 
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QTabWidget, QWidget, QVBoxLayout, QLineEdit, QShortcut,
    QDockWidget, QTreeView, QFileSystemModel, QFileIconProvider, QLabel, QScrollArea, QStatusBar, QMenu, QMessageBox,
    QDialog, QTextEdit, QPushButton, QToolBar, QAction, QActionGroup, QSplitter,
    QFrame, QGridLayout, QHBoxLayout, QComboBox, QCheckBox, QSpinBox, QSlider, QToolButton
)
from PyQt5.QtGui import QColor, QKeySequence, QPixmap, QWheelEvent, QMouseEvent, QTransform, QIcon, QFont, QPalette
from PyQt5.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal, QSize, QFileInfo
from PyQt5.Qsci import (
    QsciLexerPython, QsciLexerCPP, QsciLexerJavaScript,
    QsciLexerHTML, QsciLexerJava, QsciLexerJSON,
    QsciLexerLua, QsciScintilla, QsciScintillaBase,
    QsciLexerCSharp
)
from PyQt5.QtWidgets import QSlider, QHBoxLayout
import subprocess
import sys
import os
import tempfile
import json
import base64
import webbrowser
from module.ChatAI import ChatAIWidget
from module.markdown_highlight import apply_markdown_highlight
from module.Output_UI import OutputPanel
from module.Media.Musicview import MusicView
from module.Media.Videoview import VideoView
from module.Media.Photoview import PhotoView
from module.System.ShortcutManager import ShortcutManager
from module.System.QsciLexer import get_lexer
from module.System.Autocomplete import AutocompleteManager
from module.System.Notification import show_notification
from module.Custom_text_color.Swift_highlight import apply_swift_highlight
from module.Custom_text_color.css_highlight import apply_css_highlight
from module.Custom_text_color.Ruby_highlight import apply_ruby_highlight
from module.Custom_text_color.go_highlight import apply_go_highlight
from module.Custom_text_color.Kotlin_highlight import apply_kotlin_highlight
from module.Custom_text_color.Batch_highlight import apply_batch_highlight
from module.Custom_text_color.Hsi_highlight import apply_hsi_highlight
from module.Custom_text_color.typeScript_highlight import apply_typescript_highlight
from module.System.loading import show_loading_then_main
from module.System.check_update import check_and_update

# Dummy OutputPanel definition (replace with your actual implementation or import)
# from PyQt5.QtWidgets import QTextEdit
# class OutputPanel(QTextEdit):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setReadOnly(True)
#     def append_text(self, text):
#         self.append(text)

try:
    pass  # Add the code you want to try here
except Exception as e:
    print(f"An error occurred: {e}")
    from module.markdown_highlight import apply_markdown_highlight
except ImportError:
    def apply_markdown_highlight(editor):
        pass  # Dummy: Không làm gì nếu không có module

try:
    from module.unsaved_checker import check_unsaved_and_prompt
except ImportError:
    def check_unsaved_and_prompt(tab, parent):
        return True  # Dummy: Always allow closing

# Import plugin system and error handler
try:
    from module.plugin_system import PluginManager, set_plugin_manager
    from module.error_handler import error_handler
except ImportError:
    class PluginManager:
        def __init__(self, main_window):
            self.main_window = main_window
        def get_supported_languages(self):
            return {}
        def load_plugins(self):
            pass
        def load_all_plugins(self):
            pass
        def get_plugin_menu_items(self):
            return []
        def get_plugin_toolbar_items(self):
            return []
    def set_plugin_manager(manager):
        pass
    error_handler = None

try:
    from module.syntax_checker import (
        check_python_syntax,
        check_c_cpp_syntax,
        check_csharp_syntax,
        check_bat_syntax
    )
except ImportError:
    def check_python_syntax(code):
        return None
    def check_c_cpp_syntax(path):
        return None
    def check_csharp_syntax(path):
        return None
    def check_bat_syntax(path):
        return None

try:
    from module.check_Objective_C_syntax import check_objective_c_syntax  # type: ignore
except ImportError:
    def check_objective_c_syntax(path):
        return None

try:
    from module.Extensions import Extension
except ImportError:
    class Extension:
        display_name = "Dummy Extension"
        def __init__(self, *args, **kwargs):
            pass
        def on_load(self):
            pass
        def on_save(self):
            pass
        def on_close(self):
            pass

try:
    # from module.extension_loader import CppExtension
    pass
except ImportError:
    class CppExtension:
        def __init__(self, *args, **kwargs):
            pass

class EditorTab(QWidget):
    # Dummy extension: UppercaseOnSaveExtension
    class UppercaseOnSaveExtension(Extension):
        display_name = "Tự động chuyển chữ hoa khi lưu"
        def __init__(self, editor):
            self.editor = editor
        def on_save(self):
            text = self.editor.text()
            self.editor.setText(text.upper())

    AVAILABLE_EXTENSIONS = [
        ("Tự động chuyển chữ hoa khi lưu", UppercaseOnSaveExtension),
        # Thêm extension khác ở đây
    ]

    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.editor = QsciScintilla()
        self.modified = False  # Track changes
        self.editor.textChanged.connect(self.on_text_changed)

        self.set_language_from_extension(file_path)

        self.editor.setAutoIndent(True)
        self.editor.setIndentationGuides(True)
        self.editor.setMarginType(0, QsciScintilla.NumberMargin)
        self.editor.setMarginWidth(0, "00000")
        self.editor.setFolding(QsciScintilla.BoxedTreeFoldStyle)
        # Plugin manager is initialized later in __init__
        self.set_language("English")  # Default language

        self.set_dark_theme()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Tìm kiếm...")
        self.search_box.setStyleSheet("background-color: #333; color: white;")
        self.search_box.hide()
        layout.addWidget(self.search_box)

        self.setLayout(layout)

        self.last_search_text = ""
        self.last_search_pos = (0, 0)

        QShortcut(QKeySequence("Ctrl+F"), self, self.toggle_search_box)
        QShortcut(QKeySequence("Esc"), self, lambda: self.search_box.hide())
        QShortcut(QKeySequence("Return"), self.search_box, self.highlight_search)
        QShortcut(QKeySequence("Shift+Return"), self.search_box, self.highlight_search_backward)

        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save_file)
        self.auto_save_timer.start(10000)

        self.enabled_extensions = {}  # tên: đối tượng extension
        self.init_extensions()

        # OutputPanel and QDockWidget should be managed by the main window, not EditorTab.
        # self.output_panel = OutputPanel()
        # self.dock_output = QDockWidget("Output", self)
        # self.dock_output.setWidget(self.output_panel)
        # self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_output)
        # self.dock_output.hide()  # Ẩn mặc định, chỉ hiện khi gọi

    def init_extensions(self):
        # Nạp extension mặc định
        for name, ext_cls in self.AVAILABLE_EXTENSIONS:
            self.enabled_extensions[name] = None

        # Tự động nạp extension từ folder module/Extensions (trừ Extension.py)
        extension_folder = os.path.join(os.path.dirname(__file__), "module", "Extensions")
        for ext_file in glob.glob(os.path.join(extension_folder, "*.hsiext")):
            ext_name = os.path.basename(ext_file)
            if ext_name in ("Extension.py", "__init__.py"):
                continue
            module_name = f"module.Extensions.{ext_name[:-3]}"
            spec = importlib.util.spec_from_file_location(module_name, ext_file)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                # Tìm class kế thừa Extension
                for attr in dir(mod):
                    obj = getattr(mod, attr)
                    if isinstance(obj, type) and issubclass(obj, Extension) and obj is not Extension:
                        # Thêm vào danh sách extension khả dụng nếu chưa có
                        ext_display_name = getattr(obj, "display_name", obj.__name__)
                        if ext_display_name not in self.enabled_extensions:
                            self.enabled_extensions[ext_display_name] = None

    def enable_extension(self, name):
        if name in self.enabled_extensions and self.enabled_extensions[name] is None:
            ext = dict(self.AVAILABLE_EXTENSIONS)[name](self.editor)
            ext.on_load()
            self.enabled_extensions[name] = ext

    def disable_extension(self, name):
        if name in self.enabled_extensions and self.enabled_extensions[name]:
            self.enabled_extensions[name].on_close()
            self.enabled_extensions[name] = None

    def on_text_changed(self):
        self.modified = True


    def toggle_search_box(self):
        self.search_box.setVisible(not self.search_box.isVisible())
        if self.search_box.isVisible():
            self.search_box.setFocus()

    def highlight_search(self):
        text = self.search_box.text()
        if not text:
            return
        self.last_search_text = text
        line, index = self.editor.getCursorPosition()
        found = self.editor.findFirst(text, False, False, False, True, line, index)
        if found:
            self.last_search_pos = self.editor.getCursorPosition()
        else:
            self.editor.setCursorPosition(0, 0)

    def highlight_search_backward(self):
        text = self.search_box.text()
        if not text:
            return
        self.last_search_text = text
        line, index = self.editor.getCursorPosition()
        found = self.editor.findFirst(text, False, False, False, True, line, index, True)
        if found:
            self.last_search_pos = self.editor.getCursorPosition()
        else:
            self.editor.setCursorPosition(self.editor.lines() - 1, 0)

    def load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.editor.setText(f.read())
            self.file_path = path
            self.set_language_from_extension(path)
            return True
        except Exception as e:
            print("Error loading file:", e)
            return False

    def save_file(self):
        if not self.file_path:
            reply = QMessageBox.question(
                self, "Chưa có đường dẫn",
                "File này chưa có tên. Bạn có muốn lưu với tên mới không?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                return self.save_file_as()
            else:
                return False
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.text())
            self.modified = False
            for ext in self.enabled_extensions.values():
                if ext is not None:
                    if hasattr(ext, "on_save"):
                        ext.on_save()
                    elif hasattr(ext, "run"):
                        ext.run()
            return True
        except Exception as e:
            print("Error saving file:", e)
            return False

    def save_file_as(self):
        file_types = (
            "Markdown (*.md);;Python (*.py);;C++ (*.cpp *.h);;JavaScript (*.js);;"
            "HTML (*.html *.htm);;Lua (*.lua);;Java (*.java);;JSON (*.json);;"
            "C (*.c *.h);;Objective-C (*.m *.h);;Batch (*.bat);; (*.cmd);; (*.pdf);;"
            "PHP (*.php);;C# (*.cs);;Bash (*.sh);;Text (*.txt);;Ruby (*.rb);;"
            "Go (*.go);;Rust (*.rs);;Swift (*.swift);;Kotlin (*.kt);;Dart (*.dart);;"
            "SQL (*.sql);;YAML (*.yaml *.yml);;XML (*.xml);;All Files (*)"
        )
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", file_types)

        if file_path:
            self.file_path = file_path
            return self.save_file()
        return False

    def auto_save_file(self):
        if self.file_path:
            self.save_file()

    def set_dark_theme(self):
        self.editor.setCaretForegroundColor(QColor("#ffffff"))
        self.editor.setPaper(QColor("#000000"))
        self.editor.setColor(QColor("#d4d4d4"))
        self.editor.setMarginsBackgroundColor(QColor("#000000"))
        self.editor.setMarginsForegroundColor(QColor("#888888"))

    def set_light_theme(self):
        self.editor.setCaretForegroundColor(QColor("#000000"))
        self.editor.setPaper(QColor("#ffffff"))
        self.editor.setColor(QColor("#000000"))
        self.editor.setMarginsBackgroundColor(QColor("#dddddd"))
        self.editor.setMarginsForegroundColor(QColor("#555555"))

    def set_language(self, lang):
        if lang == "Python":
            self.editor.setLexer(QsciLexerPython())
        elif lang == "C++":
            self.editor.setLexer(QsciLexerCPP())
        elif lang == "C":
            try:
                self.editor.setLexer(QsciLexerCPP())
            except NameError:
                self.editor.setLexer(None)
        elif lang == "CSS":
            apply_css_highlight(self.editor)
        elif lang == "JavaScript":
            self.editor.setLexer(QsciLexerJavaScript())
        elif lang == "HTML":
            self.editor.setLexer(QsciLexerHTML())
        elif lang == "Java":
            self.editor.setLexer(QsciLexerJava())
        elif lang == "JSON":
            self.editor.setLexer(QsciLexerJSON())
        elif lang == "Lua":
            self.editor.setLexer(QsciLexerLua())
        elif lang == "Markdown":
            apply_markdown_highlight(self.editor)
        elif lang == "Ruby":
            apply_ruby_highlight(self.editor)
        elif lang == "Go":
            apply_go_highlight(self.editor)
        elif lang == "Kotlin":
            apply_kotlin_highlight(self.editor)
        elif lang == "Swift":
            apply_swift_highlight(self.editor)
        elif lang == "hsi":
            apply_hsi_highlight(self.editor)
        elif lang == "TypeScript":
            apply_typescript_highlight(self.editor)
        elif lang == "C#":
            try:
                self.editor.setLexer(QsciLexerCSharp())
            except NameError:
                self.editor.setLexer(None)
        elif lang == "Batch":
            apply_batch_highlight(self.editor)
        else:
            self.editor.setLexer(None)

    def set_language_from_extension(self, path):
        if not path:
            self.set_language("Plain Text")
            return
        ext = os.path.splitext(path)[1].lower()
        if ext == ".py":
            self.set_language("Python")
        elif ext in [".cpp", ".cxx", ".cc", ".h"]:
            self.set_language("C++")
        elif ext in [".js"]:
            self.set_language("JavaScript")
        elif ext in [".html", ".htm"]:
            self.set_language("HTML")
        elif ext in [".css"]:
            self.set_language("CSS")
        elif ext in [".java"]:
            self.set_language("Java")
        elif ext in [".c"]:
            self.set_language("C")
        elif ext in [".json"]:
            self.set_language("JSON")
        elif ext in [".lua"]:
            self.set_language("Lua")
        elif ext in [".md"]:
            self.set_language("Markdown")
        elif ext in [".rb"]:
            self.set_language("Ruby")
        elif ext in [".go"]:
            self.set_language("Go")
        elif ext in [".rs"]:
            self.set_language("Rust")
        elif ext in [".swift"]:
            self.set_language("Swift")
        elif ext in [".kt"]:
            self.set_language("Kotlin")
        elif ext in [".dart"]:
            self.set_language("Dart")
        elif ext in [".sql"]:
            self.set_language("SQL")
        elif ext in [".yaml", ".yml"]:
            self.set_language("YAML")
        elif ext in [".xml"]:
            self.set_language("XML")
        else:
            self.set_language("Plain Text")
        

# Ví dụ sử dụng trong HyggshiOSCodeMini.py:
def open_image(self, path):
    try:
        # ...code mở ảnh...
        show_notification("Đã mở ảnh thành công!", parent=self)
    except Exception as e:
        show_notification(f"Lỗi mở ảnh: {e}", parent=self)

# Ví dụ sử dụng trong EditorTab hoặc nơi khởi tạo QsciScintilla editor:
def set_editor_lexer(self, language):
    lexer = get_lexer(language, self.editor)
    if lexer:
        self.editor.setLexer(lexer)
    else:
        self.editor.setLexer(None)

class RunProcessThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
        self._process = None

    def run(self):
        import subprocess
        try:
            self._process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            try:
                stdout, stderr = self._process.communicate(timeout=300)
                output = stdout + ("\n" + stderr if stderr else "")
            except subprocess.TimeoutExpired:
                self._process.kill()
                output = "Lệnh bị dừng do quá thời gian."
        except Exception as e:
            output = f"Lỗi khi chạy file: {e}"
        self.finished.emit(output)

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.kill()

try:
    from module.save_settings import save_settings, load_settings
except ImportError:
    def save_settings(*args, **kwargs):
        pass
    def load_settings(*args, **kwargs):
        return {}


class CustomIconProvider(QFileIconProvider):
    def __init__(self):
        super().__init__()
        self.ext_map = {
            'py': 'icons/file-python.svg',
            'js': 'icons/file-javascript.png',
            'ts': 'icons/file-typescript.svg',
            'html': 'icons/file-html.svg',
            'css': 'icons/file-css.svg',
            'json': 'icons/file-json.svg',
            'md': 'icons/file-markdown.svg',
            'png': 'icons/file-image.svg',
            'jpg': 'icons/file-image.svg',
            'jpeg': 'icons/file-image.svg',
            'gif': 'icons/file-image.svg',
            'svg': 'icons/file-image.svg',
            'ico': 'icons/file-image.svg',
            'cpp': 'icons/file-cpp.svg',
            'c': 'icons/file-c.svg',
            'cc': 'icons/file-cpp.svg',
            'h': 'icons/file-cpp.svg',
            'java': 'icons/file-java.svg',
            'cs': 'icons/file-csharp.svg',
            'ru': 'icons/file-ruby.svg',
            'rb': 'icons/file-ruby.svg',
            'r': 'icons/file-r.svg',
            'go': 'icons/file-go.svg',
            'rs': 'icons/file-rust.svg',
            'sh': 'icons/file-batch.png',
            'bat': 'icons/file-batch.png',
            'php': 'icons/file-php.svg',
            'swift': 'icons/file-swift.svg',
            'kt': 'icons/file-kotlin.svg',
            'lua': 'icons/file-lua.svg',
            'batch': 'icons/file-batch.png',
            'cmd': 'icons/file-batch.png',
            'zsh': 'icons/file-shell.svg',
            'Powershell': 'icons/file-powershell.svg',
            'ps1': 'icons/file-powershell.svg',
            'sql': 'icons/file-sql.svg',
            'mm': 'icons/file-objectivec.svg',
            'm': 'icons/file-objectivec.svg',
            'swf': 'icons/file-swf.svg',
            'pdf': 'icons/file-pdf.svg',
            'mp4': 'icons/file-video.svg',
            'mkv': 'icons/file-video.svg',
            'avi': 'icons/file-video.svg',
            'mov': 'icons/file-video.svg',
            'flv': 'icons/file-video.svg',
            'wmv': 'icons/file-video.svg',
            'mp3': 'icons/file-audio.svg',
            'wav': 'icons/file-audio.svg',
            'ogg': 'icons/file-audio.svg',
            'flac': 'icons/file-audio.svg',
            'txt': 'icons/file-text.svg',
            'log': 'icons/file-log.svg',
            'blend': 'icons/file-blender.svg',
            'License': 'icons/file-license.svg',
            'doc': 'icons/file-word.png',
            'docx': 'icons/file-word.png',
            'rbxlx': 'icons/Roblox_Studio_icon1.png',
            'rbxl': 'icons/Roblox_Studio_icon.png',
            'luau': 'icons/file_type_luau.svg',
            'tsx': 'icons/file-typescript.svg',
            'hsi': 'icons/file-hsi.png',
            'hsiext': 'icons/file-hsiext.png',
            'gitlab-ci.yml': 'icons/file_type_gitlab.svg',
            'config': 'icons/file_type_config.svg',
            'exe': 'icons/file_type_Windows_exe.svg',
            'app': 'icons/file_type_mac_app.svg',
            'ini': 'icons/file-ini.svg',
            'temp': 'icons/file-temp.png',
            'tmp': 'icons/file-temp.png',
        }
        
        self.folder_icon = 'icons/default_folder.svg'
        self.folder_python_icon = 'icons/folder_type_python.svg'
        self.folder_python_open_icon = 'icons/folder_type_python_opened.svg'
        self.folder_open_icon = 'icons/default_folder_opened.svg'
        self.folder_type_log = 'icons/folder_type_log.svg'
        self.folder_type_log_opened = 'icons/folder_type_log_opened.svg'
        self.folder_type_json = 'icons/folder_type_json.svg'
        self.folder_type_js = 'icons/folder_type_js.svg'
        self.folder_type_images = 'icons/folder_type_images.svg'
        self.folder_type_css = 'icons/folder_type_css.svg'
        self.folder_type_vscode = 'icons/folder_type_vscode.svg'
        self.folder_type_video = 'icons/folder_type_video.svg'
        self.folder_type_audio = 'icons/folder_type_audio.svg'
        self.folder_type_temp = 'icons/folder_type_temp.svg'
        self.folder_type_src = 'icons/folder_type_src.svg'
        self.folder_type_plugins = 'icons/folder_type_plugins.svg'
        self.folder_type_php = 'icons/folder_type_php.svg'
        self.folder_type_package = 'icons/folder_type_package.svg'
        self.folder_type_typescript = 'icons/folder_type_typescript.svg'
        self.folder_type_Hyggshi = 'icons/folder_type_Hyggshi.png'
        self.folder_type_config = 'icons/folder_type_config.svg'
        self.folder_type_github = 'icons/folder_type_github.svg'
        self.folder_type_git = 'icons/folder_type_git.svg'
        self.folder_type_gitlab = 'icons/folder_type_gitlab.svg'
        self.folder_type_Roblox_Studio = 'icons/folder_type_Roblox_Studio.png'


    def icon(self, fileInfo: QFileInfo):
        try:
            if fileInfo.isDir():
                folder_path = fileInfo.absoluteFilePath()
                has_python = any(name.endswith('.py') for name in os.listdir(folder_path))
                has_log = any(name.endswith('.log') for name in os.listdir(folder_path))
                has_json = any(name.endswith('.json') for name in os.listdir(folder_path))
                has_js = any(name.endswith('.js') for name in os.listdir(folder_path))
                has_vscode = any(name == 'vscode' or name == '.vscode' for name in os.listdir(folder_path))
                has_css = any(name.endswith('.css') for name in os.listdir(folder_path))
                has_video = any(name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv')) for name in os.listdir(folder_path))
                has_audio = any(name.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')) for name in os.listdir(folder_path))
                has_temp = any(name.lower().endswith(('.tmp', '.temp')) for name in os.listdir(folder_path))
                has_src = any(name.lower() == 'src' for name in os.listdir(folder_path))
                has_plugins = any(name.lower() == 'plugins' for name in os.listdir(folder_path))
                has_php = any(name.endswith('.php') for name in os.listdir(folder_path))
                has_package = any(name.lower() in ('node_modules', 'vendor', 'packages') for name in os.listdir(folder_path))
                has_TSX = any(name.endswith('.tsx') for name in os.listdir(folder_path))
                has_TS = any(name.endswith('.ts') for name in os.listdir(folder_path))
                has_Batch = any(name.endswith(('.bat', '.cmd', '.hsi', '.hsiext')) for name in os.listdir(folder_path))
                has_Config = any(name.lower() in ('config', 'configs', 'configuration', 'settings') for name in os.listdir(folder_path))
                has_Roblox = any(name.endswith(('.rbxl', '.rbxlx')) for name in os.listdir(folder_path))
                has_Git = any(name.lower() == '.git' for name in os.listdir(folder_path))
                has_Gitlab = any(name.lower() == '.gitlab' for name in os.listdir(folder_path))

                folder_name = os.path.basename(folder_path).lower()
                # Sửa phát hiện .github
                has_github = folder_name == ".github"

                is_opened = self._is_folder_opened(folder_path)
                if has_python:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_python_open_icon if is_opened else self.folder_python_icon
                    )
                elif has_log:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_log_opened if is_opened else self.folder_type_log
                    )
                elif has_Config:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_config
                    )
                elif has_Gitlab:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_gitlab
                    )
                elif has_Git:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_git
                    )
                elif has_github:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_github
                  )
                elif has_plugins:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_plugins
                    )
                elif has_TSX:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_typescript
                    )
                elif has_Batch:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_Hyggshi
                    )
                elif has_TS:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_typescript
                    )
                elif has_audio:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_audio
                    )
                elif has_json:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_json
                    )
                elif has_Roblox:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_Roblox_Studio
                    )
                elif has_js:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_js
                    )
                elif has_package:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_package
                    )
                elif any(name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico')) for name in os.listdir(folder_path)):
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_images
                    )
                elif has_php:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_php
                    )
                elif has_src:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_src
                    )
                elif has_temp:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_temp
                    )
                elif any(name == 'vscode' or name == '.vscode' for name in os.listdir(folder_path)):
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_vscode
                    )
                elif any(name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv')) for name in os.listdir(folder_path)):
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_video
                    )
                elif any(name.endswith('.css') for name in os.listdir(folder_path)):
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_type_css
                    )
                else:
                    icon_path = os.path.join(
                        os.path.dirname(__file__),
                        self.folder_open_icon if is_opened else self.folder_icon
                    )
                if os.path.exists(icon_path):
                    return QIcon(icon_path)
                return super().icon(fileInfo)
            # Nếu là file, kiểm tra extension để lấy icon tương ứng
            suffix = fileInfo.suffix().lower()
            icon_rel = self.ext_map.get(suffix)
            if icon_rel:
                path = os.path.join(os.path.dirname(__file__), icon_rel)
                if os.path.exists(path):
                    return QIcon(path)
        except Exception:
            pass
        return super().icon(fileInfo)

    def _is_folder_opened(self, folder_path):
        try:
            mw = QApplication.activeWindow()
            if hasattr(mw, "tree") and hasattr(mw, "model"):
                idx = mw.tree.rootIndex()
                root_path = mw.model.filePath(idx)
                return os.path.normpath(root_path) == os.path.normpath(folder_path)
        except Exception:
            pass
        return False

    

# Try to use keyring for secure API key storage; fallback to file storage
try:
    import keyring  # pyright: ignore[reportMissingImports]
    HAS_KEYRING = True
except Exception:
    keyring = None
    HAS_KEYRING = False

class HyggshiOSCodeMini(QMainWindow):

    def __init__(self):
        super().__init__()
        # Thêm dòng này ngay sau super().__init__()
        self._translate = lambda k, **kw: k
        self.setWindowTitle("Hyggshi OS Code Mini")
        self.setWindowIcon(QIcon("icon.png"))  # Ensure you have an icon file named 'icon.png'
        self.resize(1200, 800)

        # Initialize theme system
        self.current_theme = "dark"  # Default to dark theme
        
        # Create main splitter for modern layout
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.main_splitter)

        # Activity bar (VS Code-like) on the far left
        self.activity_bar = QFrame()
        self.activity_bar.setFixedWidth(52)
        self.activity_bar.setObjectName("activity_bar")
        act_layout = QVBoxLayout(self.activity_bar)
        act_layout.setContentsMargins(6, 6, 6, 6)
        act_layout.setSpacing(8)

        def make_tool_button(text, tooltip, slot):
            btn = QToolButton()
            btn.setText(text)
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setFixedSize(40, 40)
            btn.setToolTip(tooltip)
            btn.clicked.connect(slot)
            return btn

        # Minimal icons/text for the activity bar
        self.explorer_btn = make_tool_button("📁", "Explorer", lambda: self.toggle_explorer())
        self.search_btn = make_tool_button("🔎", "Search", lambda: self.toggle_search_panel())
        self.scm_btn = make_tool_button("🔀", "Source Control", lambda: self.toggle_scm_panel())
        self.run_btn = make_tool_button("▶️", "Run", self.toggle_output_panel)
        self.ext_btn = make_tool_button("🔌", "Extensions", lambda: self.toggle_extensions_panel())

        act_layout.addWidget(self.explorer_btn)
        act_layout.addWidget(self.search_btn)
        act_layout.addWidget(self.scm_btn)
        act_layout.addStretch()
        act_layout.addWidget(self.run_btn)
        act_layout.addWidget(self.ext_btn)

        # Create left panel for sidebar (holds explorer dock)
        self.left_panel = QWidget()
        self.left_panel.setMaximumWidth(300)
        self.left_panel.setMinimumWidth(200)
        
        # Create center panel for editor
        self.center_panel = QWidget()
        
        # Add widgets to splitter (activity bar, sidebar, center)
        self.main_splitter.addWidget(self.activity_bar)
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.center_panel)
        self.main_splitter.setSizes([52, 250, 898])  # Set initial sizes

        # Setup center panel with tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(True)
        
        center_layout = QVBoxLayout(self.center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(self.tabs)
        
        # Now setup theme after tabs are created
        self.setup_theme()

        self.project_path = "."

        # Initialize plugin system
        self.plugin_manager = PluginManager(self)
        set_plugin_manager(self.plugin_manager)
        
        # Initialize error handler
        if error_handler:
            error_handler.error_occurred.connect(self.handle_error)
            error_handler.warning_occurred.connect(self.handle_warning)

        self.setup_sidebar()
        self.setup_modern_toolbar()
        self.setup_modern_statusbar()

        self.interface_language = "English"  # Default language
        self.setup_menu()
        
        # Load plugins after UI is set up
        self.load_plugins()

        QShortcut(QKeySequence("Ctrl+N"), self, self.new_file)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, self.toggle_theme)

        self.output_panel = OutputPanel()
        self.dock_output = QDockWidget("Output", self)
        self.dock_output.setWidget(self.output_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_output)
        self.dock_output.hide()  # Ẩn mặc định

        QShortcut(QKeySequence("Ctrl+Shift+O"), self, self.toggle_output_panel)

        # Thêm vào menu
        output_menu = self.menuBar().addMenu("Output")
        output_menu.addAction("Show/Hide Output (Ctrl+Shift+O)", self.toggle_output_panel)

        # Thêm vào toolbar
        toolbar = self.addToolBar("MainToolbar")
        output_action = toolbar.addAction("Output")
        output_action.triggered.connect(self.toggle_output_panel)
        run_action = toolbar.addAction("Run")
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.run_current_file)
        stop_action = toolbar.addAction("Stop")
        stop_action.setShortcut("Ctrl+F5")
        stop_action.triggered.connect(self.stop_running_process)

        # --- Add AI Assistant button ---
        chat_ai_action = toolbar.addAction("AI Assistant")
        chat_ai_action.triggered.connect(self.toggle_chat_ai_panel)

        settings_action = toolbar.addAction("⚙️ Settings")
        settings_action.triggered.connect(self.open_settings_dialog)

        restart_action = toolbar.addAction("🔁 Restart")
        restart_action.triggered.connect(self.restart_running_process)

        clear_action = toolbar.addAction("🧹 Clear")
        clear_action.triggered.connect(self.clear_output_panel)
        
        # Add plugin toolbar items
        self.add_plugin_toolbar_items(toolbar)

        self.extensions = []
        self.load_extensions()

        self.settings = load_settings()
        # Ví dụ: đọc trạng thái extension đã bật
        self.enabled_extensions = self.settings.get("enabled_extensions", [])
        self.log_color = self.settings.get("log_color", "#FFFFFF")
        self.timeout = self.settings.get("timeout", 60)
        # Load language helper
        self.current_language = self.settings.get("language", "en_US")
        # Try to sync with native language engine if available
        try:
            from module import language_engine
            native = language_engine.get_current_language()
            if native:
                self.current_language = native
        except Exception:
            pass
        self.load_language()

        # Shortcut manager example: Add Ctrl+S to save file
        self.shortcut_manager = ShortcutManager(self)
        self.shortcut_manager.add_shortcut("Ctrl+S", self.save_current_file, name="save_file")

        self.apply_vscode_style()

        import threading
        def check_update_on_start():
            try:
                from module.System.check_update import check_and_update
                threading.Thread(target=check_and_update, daemon=True).start()
            except Exception as e:
                print("Không thể kiểm tra cập nhật:", e)

        # Gọi khi khởi động ứng dụng:
        check_update_on_start()

    def load_extensions(self):
        # Nạp extension Python
        # self.extensions.append(MyPythonExtension(self.editor))
        # Nạp extension C++ (giả sử đã biên dịch thành .dll/.so)
        cpp_ext_path = os.path.join(os.path.dirname(__file__), "module", "Extensions_World.dll")  # hoặc .so
        if os.path.exists(cpp_ext_path):
            self.extensions.append(CppExtension(cpp_ext_path))

    def setup_sidebar(self):
        self.dock = QDockWidget("Explorer", self)
        self.dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

        self.model = QFileSystemModel()
        self.model.setRootPath(self.project_path)
        try:
            provider = CustomIconProvider()
            self.model.setIconProvider(provider)
        except Exception:
            pass

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.project_path))
        self.tree.doubleClicked.connect(self.tree_item_clicked)
        try:
            self.tree.setHeaderHidden(True)
            self.tree.setIndentation(12)
            self.tree.setRootIsDecorated(False)
            self.tree.setIconSize(QSize(32, 32))  # Phóng to icon explorer
            # XÓA CÁC CỘT NGÀY THÁNG NĂM VÀ DUNG LƯỢNG
            self.tree.setColumnHidden(1, True)  # Hide Size column
            self.tree.setColumnHidden(2, True)  # Hide Type column
            self.tree.setColumnHidden(3, True)  # Hide Date Modified column
        except Exception:
            pass

        self.dock.setWidget(self.tree)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.addWidget(self.dock)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        try:
            from module.context_ui import create_tree_context_menu
            self.tree.customContextMenuRequested.connect(lambda pos: self._on_tree_context_menu_ext(pos, create_tree_context_menu))
        except Exception:
            self.tree.customContextMenuRequested.connect(self.on_tree_context_menu)

    def load_language(self):
        """Load translation helper for current_language into `self._translate`."""
        try:
            # Try module package like en_US.en_US or vi_VN.vi_VN
            mod = None
            try:
                mod = importlib.import_module(f"{self.current_language}.{self.current_language}")
            except Exception:
                try:
                    mod = importlib.import_module(self.current_language)
                except Exception:
                    mod = None
            if mod and hasattr(mod, 't'):
                self._translate = getattr(mod, 't')
                return
        except Exception:
            pass
        # fallback to en_US
        try:
            from en_US.en_US import t as _t  # pyright: ignore[reportMissingImports]
            self._translate = _t
        except Exception:
            self._translate = lambda k, **kw: k

    def on_tree_context_menu(self, pos):
        idx = self.tree.indexAt(pos)
        path = self.model.filePath(idx) if idx.isValid() else None
        menu = QMenu()
        if path and os.path.isfile(path):
            menu.addAction("Open", lambda: self.add_new_tab(path))
            menu.addAction("Open Containing Folder", lambda: os.startfile(os.path.dirname(path)))
            menu.addSeparator()
            menu.addAction("Rename", lambda: QMessageBox.information(self, "Explorer", "Rename not implemented"))
            menu.addAction("Delete", lambda: QMessageBox.information(self, "Explorer", "Delete not implemented"))
        elif path and os.path.isdir(path):
            menu.addAction("Open Folder", lambda: self.open_folder())
            menu.addAction("New File", lambda: self.new_file())
        else:
            menu.addAction("Refresh", lambda: self.model.refresh())
        menu.exec_(self.tree.viewport().mapToGlobal(pos))

    def _on_tree_context_menu_ext(self, pos, helper_func):
        idx = self.tree.indexAt(pos)
        path = self.model.filePath(idx) if idx.isValid() else None
        try:
            menu = helper_func(self, path)
            if isinstance(menu, QMenu):
                menu.exec_(self.tree.viewport().mapToGlobal(pos))
        except Exception:
            # fallback
            self.on_tree_context_menu(pos)

    # Editor context menu (right click inside editor)
    def setup_editor_context(self, editor: QsciScintilla):
        try:
            editor.setContextMenuPolicy(Qt.CustomContextMenu)
            # Prefer external helper
            try:
                from module.context_ui import create_editor_context_menu
                editor.customContextMenuRequested.connect(lambda pos, ed=editor: self._on_editor_context_menu_ext(ed, pos, create_editor_context_menu))
            except Exception:
                editor.customContextMenuRequested.connect(lambda pos, ed=editor: self.on_editor_context_menu(ed, pos))
        except Exception:
            pass

    def on_editor_context_menu(self, editor, pos):
        menu = QMenu()
        menu.addAction("Cut", editor.cut)
        menu.addAction("Copy", editor.copy)
        menu.addAction("Paste", editor.paste)
        menu.addSeparator()
        menu.addAction("Format/Indent", lambda: QMessageBox.information(self, "Editor", "Format not implemented"))
        menu.exec_(editor.mapToGlobal(pos))

    def _on_editor_context_menu_ext(self, editor, pos, helper_func):
        try:
            menu = helper_func(editor, self)
            if isinstance(menu, QMenu):
                menu.exec_(editor.mapToGlobal(pos))
        except Exception:
            self.on_editor_context_menu(editor, pos)

        # --- Chat AI Sidebar ---
        self.chat_ai_dock = QDockWidget("AI Assistant", self)
        self.chat_ai_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.chat_ai_widget = ChatAIWidget(self)
        self.chat_ai_dock.setWidget(self.chat_ai_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.chat_ai_dock)
        self.chat_ai_dock.hide()  # Hide by default
        # Ensure welcome message setting respects user preference
        try:
            # load setting from app settings if present
            show_welcome = self.settings.get('ai_show_welcome', False) if hasattr(self, 'settings') else False
            self.chat_ai_widget.show_welcome_on_open = bool(show_welcome)
        except Exception:
            pass

    def tree_item_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self.add_new_tab(path)

    def setup_theme(self):
        """Setup modern theme system"""
        if self.current_theme == "dark":
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
    
    def apply_dark_theme(self):
        """Apply modern dark theme"""
        dark_palette = QPalette()
        
        # Window colors
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
        
        # Base colors (for input fields, text areas)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(35, 35, 35))
        
        # Text colors
        dark_palette.setColor(QPalette.Text, QColor(220, 220, 220))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        
        # Button colors
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))
        
        # Highlight colors
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Link colors
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.LinkVisited, QColor(130, 42, 218))
        
        # Tooltip colors
        dark_palette.setColor(QPalette.ToolTipBase, QColor(50, 50, 50))
        dark_palette.setColor(QPalette.ToolTipText, QColor(220, 220, 220))
        
        self.setPalette(dark_palette)
        
        # Apply dark theme to tabs
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
                border-bottom: 2px solid #2a82da;
            }
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
            QTabBar::close-button {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDRMNCAxMk00IDEyTDEyIDQiIHN0cm9rZT0iI2NjY2NjYyIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K);
                width: 16px;
                height: 16px;
                margin-right: 8px;
                margin-left: 4px;
            }
            QTabBar::close-button:hover {
                background-color: #e74c3c;
                border-radius: 8px;
            }
        """)
    
    def apply_light_theme(self):
        """Apply modern light theme"""
        light_palette = QPalette()
        
        # Window colors
        light_palette.setColor(QPalette.Window, QColor(255, 255, 255))
        light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        
        # Base colors
        light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
        light_palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
        
        # Text colors
        light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
        light_palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        
        # Button colors
        light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        
        # Highlight colors
        light_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Link colors
        light_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        light_palette.setColor(QPalette.LinkVisited, QColor(130, 42, 218))
        
        # Tooltip colors
        light_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        
        self.setPalette(light_palette)
        
        # Apply light theme to tabs
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #333333;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #000000;
                border-bottom: 2px solid #2a82da;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
            QTabBar::close-button {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1zbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDRMNCAxMk00IDEyTDEyIDQiIHN0cm9rZT0iIzMzMzMzMyIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K);
                width: 16px;
                height: 16px;
                margin-right: 8px;
                margin-left: 4px;
            }
            QTabBar::close-button:hover {
                background-color: #e74c3c;
                border-radius: 8px;
            }
        """)
    
    def set_theme(self, theme_name):
        """Set specific theme"""
        self.current_theme = theme_name
        self.setup_theme()
        if hasattr(self, 'theme_label'):
            self.theme_label.setText(f"🎨 {theme_name.title()} Theme")
        self.status.showMessage(f"Switched to {theme_name} theme", 2000)
    
    def toggle_theme(self):
        """Toggle between dark and light theme"""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.setup_theme()
        if hasattr(self, 'theme_label'):
            self.theme_label.setText(f"🎨 {self.current_theme.title()} Theme")
        self.status.showMessage(f"Switched to {self.current_theme} theme", 2000)
    
    def setup_modern_toolbar(self):
        """Setup modern toolbar with icons"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(self.toolbar)
        
        # File actions
        new_action = QAction(f"📄 {self._translate('new')}", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        self.toolbar.addAction(new_action)
        
        open_action = QAction(f"📂 {self._translate('open')}", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        self.toolbar.addAction(open_action)
        
        save_action = QAction(f"💾 {self._translate('save')}", self)
        # Không setShortcut ở đây nếu đã có QShortcut hoặc ShortcutManager cho Ctrl+S
        save_action.triggered.connect(self.save_file)
        self.toolbar.addAction(save_action)
        
        self.toolbar.addSeparator()
        
        # Edit actions
        undo_action = QAction(f"↶ {self._translate('undo')}", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        self.toolbar.addAction(undo_action)
        
        redo_action = QAction(f"↷ {self._translate('redo')}", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)
        self.toolbar.addAction(redo_action)
        
        self.toolbar.addSeparator()
        
        # Theme toggle
        theme_action = QAction(f"🌙 {self._translate('theme')}", self)
        theme_action.setShortcut("Ctrl+Shift+T")
        theme_action.triggered.connect(self.toggle_theme)
        self.toolbar.addAction(theme_action)
        
        # Output toggle
        output_action = QAction(f"📊 {self._translate('output')}", self)
        output_action.setShortcut("Ctrl+Shift+O")
        output_action.triggered.connect(self.toggle_output_panel)
        self.toolbar.addAction(output_action)
        
        self.toolbar.addSeparator()
        
        # AI Assistant
        ai_action = QAction(f"🤖 {self._translate('ai')}", self)
        ai_action.triggered.connect(self.toggle_ai_assistant)
        self.toolbar.addAction(ai_action)
        
        # Syntax Check
        syntax_action = QAction(f"✅ {self._translate('syntax')}", self)
        syntax_action.triggered.connect(self.check_current_syntax)
        self.toolbar.addAction(syntax_action)
    
    def setup_modern_statusbar(self):
        """Setup modern status bar with information panels"""
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        
        # Theme indicator
        self.theme_label = QLabel(f"🎨 {self.current_theme.title()} Theme")
        self.status.addPermanentWidget(self.theme_label)
        
        # Language indicator
        self.language_label = QLabel("💻 No Language")
        self.status.addPermanentWidget(self.language_label)
        
        # File info
        self.file_info_label = QLabel("📄 No File")
        self.status.addPermanentWidget(self.file_info_label)
        
        # Welcome message
        self.status.showMessage("Welcome to Hyggshi OS Code Mini", 3000)

    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("📁 File")
        file_menu.addAction("📄 New File", self.new_file)
        file_menu.addAction("📂 Open File", self.open_file)
        file_menu.addAction("📁 Open Folder", self.open_folder)
        file_menu.addSeparator()
        file_menu.addAction("💾 Save File", self.save_file)
        file_menu.addAction("💾 Save File As", self.save_file_as)
        file_menu.addSeparator()
        file_menu.addAction("❌ Exit", self.close)

        theme_menu = menubar.addMenu("🎨 Theme")
        dark_action = theme_menu.addAction("🌙 Dark Theme")
        dark_action.triggered.connect(lambda: self.set_theme("dark"))
        light_action = theme_menu.addAction("☀️ Light Theme")
        light_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addSeparator()
        toggle_action = theme_menu.addAction("🔄 Toggle Theme (Ctrl+Shift+T)")
        toggle_action.triggered.connect(self.toggle_theme)

        lang_menu = menubar.addMenu("💻 Language")

        default_langs = [
            "Plain Text", "Python", "C++", "JavaScript", "HTML", "CSS", "Java", 
            "JSON", "Lua", "Markdown", "C#", "Ruby", "Go", "Rust", "Swift", 
            "Kotlin", "Dart", "SQL", "YAML", "XML", "PHP", "Bash", "Batch", 
            "PowerShell", "TypeScript", "Scala", "Perl", "Haskell", "Clojure", 
            "Erlang", "Elixir", "F#", "OCaml", "Pascal", "Fortran", "Assembly", 
            "VHDL", "Verilog", "Tcl", "VBScript", "AutoHotkey", "Ini", "TOML", 
            "Dockerfile", "Makefile", "CMake", "Gradle", "Nginx", "Apache", "Log",
            "hsi",
            "Text"
        ]
        for lang in default_langs:
            act = lang_menu.addAction(
            f"🐍 {lang}" if lang == "Python"
            else f"⚡ {lang}" if lang == "JavaScript"
            else f"🔧 {lang}" if lang == "C++"
            else f"🌐 {lang}" if lang == "HTML"
            else f"🧱 {lang}" if lang == "CSS"
            else f"☕ {lang}" if lang == "Java"
            else f"📄 {lang}" if lang == "Markdown"
            else f"🔷 {lang}" if lang == "C#"
            else f"💎 {lang}" if lang == "Ruby"
            else f"🐹 {lang}" if lang == "Go"
            else f"🦀 {lang}" if lang == "Rust"
            else f"🍎 {lang}" if lang == "Swift"
            else f"📱 {lang}" if lang == "Kotlin"
            else f"🎯 {lang}" if lang == "Dart"
            else f"🗄️ {lang}" if lang == "SQL"
            else f"📜 {lang}" if lang == "YAML"
            else f"📂 {lang}" if lang == "XML"
            else f"🐘 {lang}" if lang == "PHP"
            else f"🐚 {lang}" if lang == "Bash"
            else f"📑 {lang}" if lang == "Batch"
            else f"⚡ {lang}" if lang == "PowerShell"
            else f"🌀 {lang}" if lang == "TypeScript"
            else f"🔮 {lang}" if lang == "Scala"
            else f"🧬 {lang}" if lang == "Perl"
            else f"🔗 {lang}" if lang == "Haskell"
            else f"🌿 {lang}" if lang == "Clojure"
            else f"📡 {lang}" if lang == "Erlang"
            else f"✨ {lang}" if lang == "Elixir"
            else f"📘 {lang}" if lang == "F#"
            else f"🦉 {lang}" if lang == "OCaml"
            else f"📜 {lang}" if lang == "Pascal"
            else f"📐 {lang}" if lang == "Fortran"
            else f"⚙️ {lang}" if lang == "Assembly"
            else f"🔌 {lang}" if lang == "VHDL"
            else f"🔧 {lang}" if lang == "Verilog"
            else f"🔤 {lang}" if lang == "Tcl"
            else f"📄 {lang}" if lang == "VBScript"
            else f"⌨️ {lang}" if lang == "AutoHotkey"
            else f"⚙️ {lang}" if lang == "Ini"
            else f"📋 {lang}" if lang == "TOML"
            else f"🐳 {lang}" if lang == "Dockerfile"
            else f"🔨 {lang}" if lang == "Makefile"
            else f"🛠️ {lang}" if lang == "CMake"
            else f"📦 {lang}" if lang == "Gradle"
            else f"🌐 {lang}" if lang == "Nginx"
            else f"🌍 {lang}" if lang == "Apache"
            else f"📜 {lang}" if lang == "Log"
            else f"👾 {lang}" if lang == "hsi"
            else f"📝 {lang}"
            )
            act.triggered.connect(lambda _, l=lang: self.set_language_for_current_tab(l))
            
            act.triggered.connect(lambda _, l=lang: self.set_language_for_current_tab(l))

        if hasattr(self.plugin_manager, "get_supported_languages"):
            for lang in self.plugin_manager.get_supported_languages().keys():
                act = lang_menu.addAction(f"🔌 [Plugin] {lang}")
                act.triggered.connect(lambda _, l=lang: self.set_language_for_current_tab(l))

        plugin_menu = menubar.addMenu("🔌 Plugins")
        plugin_menu.addAction("🔄 Reload Plugins", self.reload_plugins)
        plugin_menu.addAction("📋 List Supported Languages", self.show_plugin_languages)

        tool_menu = menubar.addMenu("🛠️ Tools")
        tool_menu.addAction("✅ Check Syntax", self.check_current_syntax)
        tool_menu.addAction("🔽 Download Icon Pack", self.download_icons_from_web)
        tool_menu.addAction("▶️ Run Current File", self.run_current_file)
        tool_menu.addSeparator()
        tool_menu.addAction("⚙️ Settings", self.open_settings_dialog)
        tool_menu.addAction("🔁 Restart", self.restart_running_process)
        tool_menu.addAction("🧹 Clear", self.clear_output_panel)

        extension_menu = menubar.addMenu("Extensions")
        for name, _ in EditorTab.AVAILABLE_EXTENSIONS:
            action = extension_menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(False)
            action.toggled.connect(lambda checked, n=name: self.toggle_extension_for_current_tab(n, checked))

        # Thêm nút "Add Extension"
        extension_menu.addSeparator()
        extension_menu.addAction("Add Extension...", self.add_extension_dialog)
        extension_menu.addSeparator()
        extension_menu.addAction("Check Extensions...", self.check_extensions_status)

    def add_extension_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file extension", "", "HSI Extension (*.hsiext)")
        if path:
            import shutil
            ext_folder = os.path.join(os.path.dirname(__file__), "module", "Extensions")
            os.makedirs(ext_folder, exist_ok=True)
            dest = os.path.join(ext_folder, os.path.basename(path))
            try:
                shutil.copy2(path, dest)
                QMessageBox.information(self, "Extension", "Đã thêm extension mới. Vui lòng khởi động lại phần mềm để sử dụng.")
            except PermissionError:
                QMessageBox.critical(self, "Extension", "Không thể ghi đè file extension vì file đang được sử dụng. Hãy đóng mọi chương trình đang mở file này rồi thử lại.")
            except Exception as e:
                QMessageBox.critical(self, "Extension", f"Lỗi khi thêm extension: {e}")

    def toggle_extension_for_current_tab(self, name, checked):
        tab = self.current_editor_tab()
        if not isinstance(tab, EditorTab):
            return
        if checked:
            tab.enable_extension(name)
            if name not in self.enabled_extensions:
                self.enabled_extensions.append(name)
        else:
            tab.disable_extension(name)
            if name in self.enabled_extensions:
                self.enabled_extensions.remove(name)
        # Lưu lại trạng thái extension
        self.settings["enabled_extensions"] = self.enabled_extensions
        save_settings(self.settings)

    def new_file(self):
        self.add_new_tab()

    def open_file(self):
        file_types = (
    "All Files (*)"
)
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", file_types)
        if path:
            self.add_new_tab(path)

    def open_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Open Folder", "")
        if path:
            self.project_path = path
            self.model.setRootPath(path)
            self.tree.setRootIndex(self.model.index(path))

    def save_file(self):
        tab = self.current_editor_tab()
        if isinstance(tab, EditorTab):
            if not tab.save_file():
                tab.save_file_as()
            # mark tab title clean
            try:
                idx = self.tabs.indexOf(tab)
                if idx >= 0:
                    title = self.tabs.tabText(idx)
                    if title.endswith('*'):
                        self.tabs.setTabText(idx, title.rstrip('*'))
            except Exception:
                pass

    def save_file_as(self):
        tab = self.current_editor_tab()
        if isinstance(tab, EditorTab):
            tab.save_file_as()

    def add_new_tab(self, path=None):
        image_exts = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".ico", ".avif"]
        txt_exts = [".txt"]
        video_exts = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg", ".3gp", ".ts", ".ogv"]
        music_exts = [".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".wma", ".opus", ".aiff", ".alac"]

        if path and os.path.splitext(path)[1].lower() in image_exts:
            tab = PhotoView(path)
            icon_path = "icons/image.png"
            icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        elif path and os.path.splitext(path)[1].lower() in txt_exts:
            tab = EditorTab(path)
            tab.load_file(path)
            icon_path = "icons/text.png"
            icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        elif path and os.path.splitext(path)[1].lower() in video_exts:
            tab = VideoView()
            tab.video_path = path
            tab.cap = None
            tab.open_btn.setEnabled(False)
            tab.play_btn.setEnabled(True)
            tab.stop_btn.setEnabled(True)
            # Tự động mở video khi tab được tạo
            try:
                import cv2
                tab.cap = cv2.VideoCapture(path)
                if not tab.cap.isOpened():
                    tab.frame_label.setText("Failed to open video.")
                    tab.cap = None
                else:
                    tab.show_frame()
            except Exception as e:
                tab.frame_label.setText(f"OpenCV error: {e}")
            icon_path = "icons/video.png"
            icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        elif path and os.path.splitext(path)[1].lower() in music_exts:
            tab = MusicView()
            tab.music_path = path
            tab.label.setText(f"Loaded: {path}")
            tab.play_btn.setEnabled(True)
            tab.pause_btn.setEnabled(False)
            tab.stop_btn.setEnabled(False)
            try:
                if hasattr(tab, "open_music") and callable(tab.open_music):
                    import pygame
                    if pygame:
                        pygame.mixer.music.load(path)
            except Exception as e:
                tab.label.setText(f"Error loading music: {e}")
            icon_path = "icons/music.png"
            icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        else:
            tab = EditorTab(path)
            if path and not tab.load_file(path):
                return
            icon_path = "icons/code.png"
            icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        title = os.path.basename(path) if path else "Untitled"
        # Attach editor context menu hook
        if isinstance(tab, EditorTab):
            try:
                self.setup_editor_context(tab.editor)
            except Exception:
                pass
            tab.modified = False
            try:
                tab.editor.textChanged.connect(lambda t=tab: self._on_tab_modified(t))
            except Exception:
                pass
        self.tabs.addTab(tab, icon, title)
        self.tabs.setCurrentWidget(tab)

    # def close_tab(self, index):
    #     self.tabs.removeTab(index)

    def current_editor_tab(self):
        return self.tabs.currentWidget()

    def set_language(self, lang):
        tab = self.current_editor_tab()
        if not isinstance(tab, EditorTab):
            return
        plugin_langs = self.plugin_manager.get_supported_languages()
        if lang in plugin_langs:
            tab.editor.setLexer(plugin_langs[lang]["lexer"])
            return

    def apply_dark_theme(self):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, EditorTab):
                tab.set_dark_theme()

    def apply_light_theme(self):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, EditorTab):
                tab.set_light_theme()
    
    def close_tab(self, index):
        tab = self.tabs.widget(index)
        if isinstance(tab, EditorTab):
            if not check_unsaved_and_prompt(tab, self):
                return
        self.tabs.removeTab(index)

    def closeEvent(self, event):
        for i in range(self.tabs.count() - 1, -1, -1):
            if not check_unsaved_and_prompt(self.tabs.widget(i), self):
                event.ignore()
                return
        super().closeEvent(event)

    def set_language_for_current_tab(self, lang):
        tab = self.current_editor_tab()
        if not isinstance(tab, EditorTab):
            return

        # Ưu tiên: nếu ngôn ngữ nằm trong plugin
        plugin_langs = self.plugin_manager.get_supported_languages()
        if lang in plugin_langs:
            tab.editor.setLexer(plugin_langs[lang]["lexer"])
            return

        # Nếu không thì dùng ngôn ngữ mặc định
        tab.set_language(lang)

    def _on_tab_modified(self, tab):
        try:
            idx = self.tabs.indexOf(tab)
            if idx >= 0:
                title = self.tabs.tabText(idx)
                if not title.endswith('*'):
                    self.tabs.setTabText(idx, title + '*')
        except Exception:
            pass

    def reload_plugins(self):
        self.plugin_manager.load_all_plugins()
        QMessageBox.information(self, "Plugins", "Plugins đã được tải lại.")

    def show_plugin_languages(self):
        # Get languages from loaded plugins
        plugin_langs = self.plugin_manager.get_supported_languages()
        
        # Built-in supported languages
        builtin_langs = {
            "Python": {"extension": ".py", "plugin": "builtin"},
            "JavaScript": {"extension": ".js", "plugin": "builtin"},
            "TypeScript": {"extension": ".ts", "plugin": "builtin"},
            "HTML": {"extension": ".html", "plugin": "builtin"},
            "CSS": {"extension": ".css", "plugin": "builtin"},
            "JSON": {"extension": ".json", "plugin": "builtin"},
            "Markdown": {"extension": ".md", "plugin": "builtin"},
            "XML": {"extension": ".xml", "plugin": "builtin"},
            "YAML": {"extension": ".yml", "plugin": "builtin"},
            "SQL": {"extension": ".sql", "plugin": "builtin"},
            "Bash": {"extension": ".sh", "plugin": "builtin"},
            "Batch": {"extension": ".bat", "plugin": "builtin"},
            "PowerShell": {"extension": ".ps1", "plugin": "builtin"},
            "Lua": {"extension": ".lua", "plugin": "builtin"},
            "Rust": {"extension": ".rs", "plugin": "builtin"},
            "Go": {"extension": ".go", "plugin": "builtin"},
            "PHP": {"extension": ".php", "plugin": "builtin"},
            "Ruby": {"extension": ".rb", "plugin": "builtin"},
            "Swift": {"extension": ".swift", "plugin": "builtin"},
            "Kotlin": {"extension": ".kt", "plugin": "builtin"},
            "Scala": {"extension": ".scala", "plugin": "builtin"},
            "Dart": {"extension": ".dart", "plugin": "builtin"},
            "R": {"extension": ".r", "plugin": "builtin"},
            "MATLAB": {"extension": ".m", "plugin": "builtin"},
            "Perl": {"extension": ".pl", "plugin": "builtin"},
            "Haskell": {"extension": ".hs", "plugin": "builtin"},
            "Clojure": {"extension": ".clj", "plugin": "builtin"},
            "Erlang": {"extension": ".erl", "plugin": "builtin"},
            "Elixir": {"extension": ".ex", "plugin": "builtin"},
            "F#": {"extension": ".fs", "plugin": "builtin"},
            "OCaml": {"extension": ".ml", "plugin": "builtin"},
            "Pascal": {"extension": ".pas", "plugin": "builtin"},
            "Fortran": {"extension": ".f90", "plugin": "builtin"},
            "Assembly": {"extension": ".asm", "plugin": "builtin"},
            "VHDL": {"extension": ".vhd", "plugin": "builtin"},
            "Verilog": {"extension": ".v", "plugin": "builtin"},
            "Tcl": {"extension": ".tcl", "plugin": "builtin"},
            "VBScript": {"extension": ".vbs", "plugin": "builtin"},
            "AutoHotkey": {"extension": ".ahk", "plugin": "builtin"},
            "Ini": {"extension": ".ini", "plugin": "builtin"},
            "TOML": {"extension": ".toml", "plugin": "builtin"},
            "Dockerfile": {"extension": "Dockerfile", "plugin": "builtin"},
            "Makefile": {"extension": "Makefile", "plugin": "builtin"},
            "CMake": {"extension": ".cmake", "plugin": "builtin"},
            "Gradle": {"extension": ".gradle", "plugin": "builtin"},
            "Maven": {"extension": ".pom", "plugin": "builtin"},
            "Ant": {"extension": ".xml", "plugin": "builtin"},
            "Nginx": {"extension": ".conf", "plugin": "builtin"},
            "Apache": {"extension": ".htaccess", "plugin": "builtin"},
            "Log": {"extension": ".log", "plugin": "builtin"},
            "Text": {"extension": ".txt", "plugin": "builtin"}
        }
        
        # Combine built-in and plugin languages
        all_langs = {**builtin_langs, **plugin_langs}
        
        if not all_langs:
            QMessageBox.information(self, "Supported Languages", "Không có ngôn ngữ nào được hỗ trợ.")
        else:
            # Sort languages alphabetically
            sorted_langs = sorted(all_langs.items())
            
            # Create detailed message
            msg_lines = ["🎯 **DANH SÁCH NGÔN NGỮ LẬP TRÌNH ĐƯỢC HỖ TRỢ**\n"]
            msg_lines.append(f"📊 **Tổng cộng: {len(all_langs)} ngôn ngữ**\n")
            
            # Group by plugin type
            builtin_count = 0
            plugin_count = 0
            
            msg_lines.append("🔧 **Built-in Languages:**")
            for name, info in sorted_langs:
                if info.get('plugin') == 'builtin':
                    msg_lines.append(f"  • {name} ({info['extension']})")
                    builtin_count += 1
            
            if plugin_langs:
                msg_lines.append(f"\n🔌 **Plugin Languages ({len(plugin_langs)}):**")
                for name, info in sorted_langs:
                    if info.get('plugin') != 'builtin':
                        plugin_source = info.get('plugin', 'unknown')
                        msg_lines.append(f"  • {name} ({info['extension']}) - {plugin_source}")
                        plugin_count += 1
            
            msg_lines.append(f"\n📈 **Thống kê:**")
            msg_lines.append(f"  • Built-in: {builtin_count} ngôn ngữ")
            msg_lines.append(f"  • Plugin: {plugin_count} ngôn ngữ")
            msg_lines.append(f"  • Tổng cộng: {len(all_langs)} ngôn ngữ")
            
            msg = "\n".join(msg_lines)
            
            # Create a custom dialog with scrollable text
            dialog = QDialog(self)
            dialog.setWindowTitle("🎯 Supported Programming Languages")
            dialog.setModal(True)
            dialog.resize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Text area
            text_area = QTextEdit()
            text_area.setPlainText(msg)
            text_area.setReadOnly(True)
            text_area.setFont(QFont("Consolas", 9))
            layout.addWidget(text_area)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec_()

    def check_current_syntax(self):
        tab = self.current_editor_tab()
        if not tab or not hasattr(tab, "editor"):
            QMessageBox.warning(self, "Syntax Checker", "Không có file nào đang mở.")
            return

        file_path = getattr(tab, "file_path", None)
        code = tab.editor.text()
        ext = os.path.splitext(file_path)[1].lower() if file_path else ""

        # Detect language and call appropriate checker
        if ext == ".py":
            error = check_python_syntax(code)
            lang_name = "Python"
        elif ext in [".cpp", ".c", ".cxx", ".cc", ".h"]:
            if file_path:
                error = check_c_cpp_syntax(file_path)
            else:
                error = "Không thể kiểm tra cú pháp C/C++ vì file chưa được lưu."
            lang_name = "C/C++"
        elif ext == ".cs":
            if file_path:
                error = check_csharp_syntax(file_path)
            else:
                error = "Không thể kiểm tra cú pháp C# vì file chưa được lưu."
            lang_name = "C#"
        elif ext == ".bat":
            if file_path:
                error = check_bat_syntax(file_path)
            else:
                error = "Không thể kiểm tra cú pháp batch vì file chưa được lưu."
            lang_name = "Batch"
        elif ext == ".m":
            if file_path:
                error = check_objective_c_syntax(file_path)
            else:
                error = "Không thể kiểm tra cú pháp Objective-C vì file chưa được lưu."
            lang_name = "Objective-C"
        else:
            QMessageBox.information(self, "Syntax Checker", "Không hỗ trợ kiểm tra cú pháp cho định dạng này.")
            return

        if error:
            QMessageBox.critical(self, f"Lỗi cú pháp {lang_name}", error)
        else:
            QMessageBox.information(self, "Syntax Checker", f"Không phát hiện lỗi cú pháp {lang_name}.")

    def toggle_output_panel(self):
        if self.dock_output.isVisible():
            self.dock_output.hide()
        else:
            self.dock_output.show()
    
    def toggle_explorer(self):
        """Toggle the Explorer dock visibility"""
        if hasattr(self, 'dock'):
            try:
                if self.dock.isVisible():
                    self.dock.hide()
                else:
                    self.dock.show()
            except Exception:
                pass

    def toggle_search_panel(self):
        """Show a simple Search dock (placeholder)"""
        if not hasattr(self, 'search_dock'):
            self.search_dock = QDockWidget("Search", self)
            w = QWidget()
            layout = QVBoxLayout(w)
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search in files...")
            layout.addWidget(self.search_input)
            self.search_results = QTextEdit()
            self.search_results.setReadOnly(True)
            layout.addWidget(self.search_results)
            self.search_dock.setWidget(w)
            self.addDockWidget(Qt.RightDockWidgetArea, self.search_dock)
            self.search_dock.hide()
        if self.search_dock.isVisible():
            self.search_dock.hide()
        else:
            self.search_dock.show()

    def toggle_scm_panel(self):
        """Show a placeholder Source Control dock"""
        if not hasattr(self, 'scm_dock'):
            self.scm_dock = QDockWidget("Source Control", self)
            widget = QLabel("Source Control (placeholder)")
            widget.setAlignment(Qt.AlignCenter)
            self.scm_dock.setWidget(widget)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.scm_dock)
            self.scm_dock.hide()
        if self.scm_dock.isVisible():
            self.scm_dock.hide()
        else:
            self.scm_dock.show()

    def toggle_extensions_panel(self):
        """Show extensions list dock"""
        if not hasattr(self, 'extensions_dock'):
            self.extensions_dock = QDockWidget("Extensions", self)
            widget = QTextEdit()
            widget.setReadOnly(True)
            # List available extensions
            ex_list = '\n'.join([name for name, _ in EditorTab.AVAILABLE_EXTENSIONS])
            widget.setPlainText(ex_list or "No extensions")
            self.extensions_dock.setWidget(widget)
            self.addDockWidget(Qt.RightDockWidgetArea, self.extensions_dock)
            self.extensions_dock.hide()
       

        if self.extensions_dock.isVisible():
            self.extensions_dock.hide()
        else:
            self.extensions_dock.show()
    
    def toggle_ai_assistant(self):
        """Toggle AI Assistant panel"""
        if hasattr(self, 'chat_ai_dock'):
            if self.chat_ai_dock.isVisible():
                self.chat_ai_dock.hide()
            else:
                self.chat_ai_dock.show()
    
    def undo(self):
        """Undo last action in current editor"""
        tab = self.current_editor_tab()
        if tab and hasattr(tab, "editor"):
            tab.editor.undo()
    
    def redo(self):
        """Redo last undone action in current editor"""
        tab = self.current_editor_tab()
        if tab and hasattr(tab, "editor"):
            tab.editor.redo()

    def run_current_file(self):
        tab = self.current_editor_tab()
        if not tab or not hasattr(tab, "editor"):
            QMessageBox.warning(self, "Run", "Không có file nào đang mở.")
            return

        ext = os.path.splitext(getattr(tab, "file_path", "") or "")[1].lower()
        code = tab.editor.text()

        if ext == ".py" or not tab.file_path:
            try:
                if tab.file_path and ext == ".py":
                    run_path = tab.file_path
                    is_temp = False
                else:
                    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
                        tmp.write(code)
                        run_path = tmp.name
                    is_temp = True

                # Tạo thread để chạy subprocess
                self.run_thread = RunProcessThread([sys.executable, run_path])
                self.run_thread.finished.connect(lambda output, rp=run_path, temp=is_temp: self.on_run_finished(output, rp, temp))
                self.output_panel.append_text(f"--- Đang chạy {run_path} ---\n")
                self.dock_output.show()
                self.run_thread.start()
            except Exception as e:
                self.output_panel.append_text(f"Lỗi khi chạy file: {e}")
                self.dock_output.show()
        else:
            QMessageBox.information(self, "Run", "Chỉ hỗ trợ chạy file Python trực tiếp.")

    def on_run_finished(self, output, run_path, is_temp):
        self.output_panel.append_text(output)
        self.dock_output.show()
        if is_temp:
            try:
                os.unlink(run_path)
            except Exception:
                pass

    def run_cpp_extension(self):
        for ext in self.extensions:
            if hasattr(ext, "run"):
                ext.run()
                self.output_panel.append_text("Đã chạy extension C++!\n")
                self.dock_output.show()
                return
        QMessageBox.information(self, "Extension", "Không tìm thấy extension C++ nào để chạy.")

    def check_extensions_status(self):
        error_msgs = []
        extension_folder = os.path.join(os.path.dirname(__file__), "module", "Extensions")
        for ext_file in glob.glob(os.path.join(extension_folder, "*.hsiext")):
            ext_name = os.path.basename(ext_file)
            if ext_name in ("Extension.py", "__init__.py"):
                continue
            module_name = f"module.Extensions.{ext_name[:-3]}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, ext_file)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
            except Exception as e:
                error_msgs.append(f"{ext_name}: {e}")
        if error_msgs:
            QMessageBox.critical(self, "Extension Errors", "\n".join(error_msgs))
        else:
            QMessageBox.information(self, "Extension Check", "Tất cả extension đều nạp thành công!")

    def stop_running_process(self):
        if hasattr(self, "run_thread") and self.run_thread.isRunning():
            self.run_thread.stop()
            self.output_panel.append_text("--- Đã dừng tiến trình đang chạy ---\n")
            self.dock_output.show()
        else:
            QMessageBox.information(self, "Stop", "Không có tiến trình nào đang chạy.")

    def open_settings_dialog(self):
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
            QCheckBox, QLineEdit, QPushButton, QFileDialog
        )

        class SettingsDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Settings")
                self.setMinimumWidth(400)
                layout = QVBoxLayout(self)

                # ⏱️ Timeout script
                timeout_layout = QHBoxLayout()
                timeout_label = QLabel("⏱️ Timeout script (seconds):")
                self.timeout_spin = QSpinBox()
                self.timeout_spin.setRange(1, 600)
                self.timeout_spin.setValue(getattr(self, "timeout_script", 60))
                timeout_layout.addWidget(timeout_label)
                timeout_layout.addWidget(self.timeout_spin)
                layout.addLayout(timeout_layout)

                # 🌈 Giao diện
                theme_layout = QHBoxLayout()
                theme_label = QLabel("🌈 Output background:")
                self.theme_combo = QComboBox()
                self.theme_combo.addItems(["Dark", "Light", "Custom"])
                self.theme_combo.setCurrentText(getattr(self, "output_theme", "Dark"))
                theme_layout.addWidget(theme_label)
                theme_layout.addWidget(self.theme_combo)
                layout.addLayout(theme_layout)

                # 🌐 Language (scan Language/ folder for available languages)
                lang_layout = QHBoxLayout()
                lang_label = QLabel("🌐 Language:")
                self.lang_combo = QComboBox()

                lang_folder = os.path.join(os.path.dirname(__file__), 'Language')
                discovered = {}
                try:
                    for name in sorted(os.listdir(lang_folder)):
                        sub = os.path.join(lang_folder, name)
                        if os.path.isdir(sub):
                            # guess display name
                            if name == 'en_US':
                                display = 'English'
                            elif name == 'vi_VN':
                                display = 'Tiếng Việt'
                            else:
                                display = name
                            discovered[display] = name
                except Exception:
                    # fallback to defaults
                    discovered = {'English': 'en_US', 'Tiếng Việt': 'vi_VN'}

                self.available_languages = discovered
                self.lang_combo.addItems(list(self.available_languages.keys()))

                # set current language (read from parent window settings if available)
                if parent and hasattr(parent, 'current_language'):
                    curr = getattr(parent, 'current_language')
                elif parent and hasattr(parent, 'settings'):
                    curr = parent.settings.get('language', 'en_US')
                else:
                    curr = 'en_US'

                sel_display = None
                for disp, mod in self.available_languages.items():
                    if mod == curr:
                        sel_display = disp
                        break
                if sel_display:
                    idx = self.lang_combo.findText(sel_display)
                    if idx >= 0:
                        self.lang_combo.setCurrentIndex(idx)

                lang_layout.addWidget(lang_label)
                lang_layout.addWidget(self.lang_combo)
                layout.addLayout(lang_layout)

                # 🔊 Hiện thông báo khi chạy xong
                self.notify_checkbox = QCheckBox("🔊 Show notification when finished")
                self.notify_checkbox.setChecked(getattr(self, "notify_on_finish", True))
                layout.addWidget(self.notify_checkbox)

                # 📁 Đường dẫn plugin
                plugin_layout = QHBoxLayout()
                plugin_label = QLabel("📁 Plugin folder:")
                self.plugin_path_edit = QLineEdit(getattr(self, "plugin_folder", "module/Extensions"))
                plugin_btn = QPushButton("Browse")
                def browse_folder():
                    folder = QFileDialog.getExistingDirectory(self, "Select Plugin Folder", self.plugin_path_edit.text())
                    if folder:
                        self.plugin_path_edit.setText(folder)
                plugin_btn.clicked.connect(browse_folder)
                plugin_layout.addWidget(plugin_label)
                plugin_layout.addWidget(self.plugin_path_edit)
                plugin_layout.addWidget(plugin_btn)
                layout.addLayout(plugin_layout)

                # --- API Keys management ---
                api_label = QLabel("🔐 API Keys")
                api_label.setStyleSheet("font-weight: bold; margin-top:8px")
                layout.addWidget(api_label)

                self.api_info_label = QLabel("Using keyring for secure storage." if HAS_KEYRING else "Keyring not available — keys stored (base64) in user_settings.json")
                layout.addWidget(self.api_info_label)

                api_form = QHBoxLayout()
                self.api_service = QLineEdit()
                self.api_service.setPlaceholderText("Service (e.g., openai)")
                self.api_key_name = QLineEdit()
                self.api_key_name.setPlaceholderText("Key name (e.g., default)")
                api_form.addWidget(self.api_service)
                api_form.addWidget(self.api_key_name)
                layout.addLayout(api_form)

                self.api_key_input = QLineEdit()
                self.api_key_input.setPlaceholderText("API Key (hidden)")
                self.api_key_input.setEchoMode(QLineEdit.Password)
                layout.addWidget(self.api_key_input)

                api_btn_layout = QHBoxLayout()
                add_api_btn = QPushButton("Add/Update API Key")
                del_api_btn = QPushButton("Delete API Key")
                api_btn_layout.addWidget(add_api_btn)
                api_btn_layout.addWidget(del_api_btn)
                layout.addLayout(api_btn_layout)

                self.api_list = QTextEdit()
                self.api_list.setReadOnly(True)
                layout.addWidget(self.api_list)

                def refresh_api_list():
                    parent_win = self.parent()
                    if parent_win and hasattr(parent_win, '_parent_read_all_api_keys'):
                        keys = parent_win._parent_read_all_api_keys()
                    else:
                                               keys = {}
                    lines = []
                    for svc, entries in keys.items():
                        for name in entries.keys():
                            lines.append(f"{svc} / {name}")
                    self.api_list.setPlainText("\n".join(lines) if lines else "No API keys saved.")

                def on_add_api():
                    svc = self.api_service.text().strip()
                    name = self.api_key_name.text().strip()
                    key = self.api_key_input.text().strip()
                    if not svc or not name or not key:
                        QMessageBox.warning(self, "API Keys", "Please provide service, key name and key value.")
                        return
                    parent_win = self.parent()
                    if not parent_win or not hasattr(parent_win, '_parent_set_api_key'):
                        QMessageBox.critical(self, "API Keys", "Parent window helper not available.")
                        return
                    try:
                        parent_win._parent_set_api_key(svc, name, key)
                        QMessageBox.information(self, "API Keys", "API key saved.")
                        self.api_key_input.clear()
                        refresh_api_list()
                    except Exception as e:
                        QMessageBox.critical(self, "API Keys", f"Error saving API key: {e}")

                def on_del_api():
                    svc = self.api_service.text().strip()
                    name = self.api_key_name.text().strip()
                    if not svc or not name:
                        QMessageBox.warning(self, "API Keys", "Please provide service and key name to delete.")
                        return
                    parent_win = self.parent()
                    if not parent_win or not hasattr(parent_win, '_parent_delete_api_key'):
                        QMessageBox.critical(self, "API Keys", "Parent window helper not available.")
                        return
                    try:
                        parent_win._parent_delete_api_key(svc, name)
                        QMessageBox.information(self, "API Keys", "API key deleted.")
                        refresh_api_list()
                    except Exception as e:
                        QMessageBox.critical(self, "API Keys", f"Error deleting API key: {e}")

                add_api_btn.clicked.connect(on_add_api)
                del_api_btn.clicked.connect(on_del_api)
                # expose parent helper methods via closure
                refresh_api_list()

                # 🧪 Chế độ developer
                self.dev_checkbox = QCheckBox("🧪 Developer mode (show debug/log)")
                self.dev_checkbox.setChecked(getattr(self, "developer_mode", False))
                layout.addWidget(self.dev_checkbox)

                # 🛑 Dừng plugin tự động khi treo
                self.timeout_check = QCheckBox("🛑 Auto-stop plugin if hang (timeout)")
                self.timeout_check.setChecked(getattr(self, "auto_stop_plugin", True))
                layout.addWidget(self.timeout_check)

                # Buttons
                btn_layout = QHBoxLayout()
                ok_btn = QPushButton("OK")
                cancel_btn = QPushButton("Cancel")
                ok_btn.clicked.connect(self.accept)
                cancel_btn.clicked.connect(self.reject)
                btn_layout.addStretch()
                btn_layout.addWidget(ok_btn)
                btn_layout.addWidget(cancel_btn)
                layout.addLayout(btn_layout)

            def get_settings(self):
                return {
                    "timeout_script": self.timeout_spin.value(),
                    "output_theme": self.theme_combo.currentText(),
                    "language": self.available_languages.get(self.lang_combo.currentText(), "en_US"),
                    "notify_on_finish": self.notify_checkbox.isChecked(),
                    "plugin_folder": self.plugin_path_edit.text(),
                    "developer_mode": self.dev_checkbox.isChecked(),
                    "auto_stop_plugin": self.timeout_check.isChecked()
                }

        dlg = SettingsDialog(self)
        if dlg.exec_():
            settings = dlg.get_settings()
            self.timeout_script = settings["timeout_script"]
            self.output_theme = settings["output_theme"]
            # language apply
            self.current_language = settings.get("language", self.current_language)
            try:
                self.load_language()
            except Exception:
                pass
            self.notify_on_finish = settings["notify_on_finish"]
            self.plugin_folder = settings["plugin_folder"]
            self.developer_mode = settings["developer_mode"]
            self.auto_stop_plugin = settings["auto_stop_plugin"]
            # persist settings
            try:
                self.settings.update(settings)
                save_settings(self.settings)
            except Exception:
                pass
            
    def load_plugins(self):
        """Load all available plugins"""
        try:
            self.plugin_manager.load_all_plugins()
            
            # Add plugin menu items
            self.add_plugin_menu_items()
            
        except Exception as e:
            if error_handler:
                error_handler.handle_api_error("Plugin System", e, "Loading plugins")
            else:
                print(f"Error loading plugins: {e}")
                
    # ----------------- API key helpers -----------------
    def _api_keys_file_path(self):
        # Use module folder or workspace user_settings.json
        candidate = os.path.join(os.path.dirname(__file__), 'user_settings.json')
        if os.path.exists(candidate):
            return candidate
        return os.path.join(os.path.dirname(__file__), 'module', 'user_settings.json')

    def _read_api_file(self):
        p = self._api_keys_file_path()
        try:
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_api_file(self, data):
        p = self._api_keys_file_path()
        try:
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            raise

    def set_api_key(self, service, name, key):
        """Public wrapper to set an API key (uses keyring if available)"""
        if HAS_KEYRING and keyring:
            keyring.set_password(service, name, key)
            return True
        # fallback: store base64 encoded in user settings JSON under "api_keys"
        data = self._read_api_file()
        api_keys = data.get('api_keys', {})
        svc = api_keys.get(service, {})
        svc[name] = base64.b64encode(key.encode('utf-8')).decode('ascii')
        api_keys[service] = svc
        data['api_keys'] = api_keys
        self._write_api_file(data)
        return True

    def get_api_key(self, service, name):
        """Retrieve API key from keyring or file. Returns None if not found."""
        if HAS_KEYRING and keyring:
            try:
                return keyring.get_password(service, name)
            except Exception:
                return None
        data = self._read_api_file()
        api_keys = data.get('api_keys', {})
        svc = api_keys.get(service, {})
        val = svc.get(name)
        if not val:
            return None
        try:
            return base64.b64decode(val.encode('ascii')).decode('utf-8')
        except Exception:
            return None

    def delete_api_key(self, service, name):
        if HAS_KEYRING and keyring:
            try:
                keyring.delete_password(service, name)
                return True
            except Exception:
                return False
        data = self._read_api_file()
        api_keys = data.get('api_keys', {})
        svc = api_keys.get(service, {})
        if name in svc:
            del svc[name]
            api_keys[service] = svc
            data['api_keys'] = api_keys
            self._write_api_file(data)
            return True
        return False

    # Adapter methods used by SettingsDialog closures
    def _parent_set_api_key(self, service, name, key):
        return self.set_api_key(service, name, key)

    def _parent_delete_api_key(self, service, name):
        return self.delete_api_key(service, name)

    def _parent_read_all_api_keys(self):
        data = self._read_api_file()
        api_keys = data.get('api_keys', {})
        # Do not return secret values here for safety, just metadata
        out = {}
        for svc, entries in api_keys.items():
            out[svc] = {name: True for name in entries.keys()}
        return out
    
    def _download_icon_pack(self, url: str = None):
        """Download an icons zip from a URL (raw GitHub link recommended) and extract to ./icons/"""
        import urllib.request, zipfile, io
        icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
        os.makedirs(icons_dir, exist_ok=True)
        # Default URL points to a lightweight icon pack (user can override)
        default_url = 'https://github.com/PKief/vscode-material-icon-theme/raw/main/icons.zip'
        download_url = url or default_url
        try:
            with urllib.request.urlopen(download_url) as resp:
                data = resp.read()
            z = zipfile.ZipFile(io.BytesIO(data))
            z.extractall(icons_dir)
            return True, 'Icons downloaded and extracted.'
        except Exception as e:
            return False, str(e)

    def download_icons_from_web(self):
        # Ask user for URL (simple input dialog) or use default
        from PyQt5.QtWidgets import QInputDialog
        url, ok = QInputDialog.getText(self, 'Download Icons', 'Icon pack URL (leave empty for default):')
        if not ok:
            return
        url = url.strip() or None
        ok, msg = self._download_icon_pack(url)
        if ok:
            QMessageBox.information(self, 'Icons', msg)
            # refresh icon provider
            try:
                provider = CustomIconProvider()
                self.model.setIconProvider(provider)
                # force a view refresh
                self.tree.reset()
            except Exception:
                pass
        else:
            QMessageBox.critical(self, 'Icons', f'Failed to download icons: {msg}')
    def add_plugin_menu_items(self):
        """Add plugin menu items to the menu bar"""
        try:
            plugin_items = self.plugin_manager.get_plugin_menu_items()
            if plugin_items:
                # Create Plugins menu
                plugins_menu = self.menuBar().addMenu("Plugins")
                for item in plugin_items:
                    plugins_menu.addAction(item)
        except Exception as e:
            print(f"Error adding plugin menu items: {e}")
            
    def add_plugin_toolbar_items(self, toolbar):
        """Add plugin toolbar items to the toolbar"""
        try:
            plugin_items = self.plugin_manager.get_plugin_toolbar_items()
            for item in plugin_items:
                if hasattr(item, 'clicked'):
                    toolbar.addWidget(item)
                else:
                    toolbar.addAction(item)
        except Exception as e:
            print(f"Error adding plugin toolbar items: {e}")
            
    def add_dock_widget(self, widget, title, area):
        """Add a dock widget to the main window"""
        dock = QDockWidget(title, self)
        dock.setWidget(widget)
        self.addDockWidget(area, dock)
        return dock
        
    def add_sidebar_widget(self, widget, title):
        """Add a widget to the sidebar"""
        # This is a placeholder - implement based on your sidebar structure
        pass
        
    def handle_error(self, error_type, message):
        """Handle errors from error handler"""
        self.output_panel.append_text(f"[ERROR] {error_type}: {message}")
        
    def handle_warning(self, warning_type, message):
        """Handle warnings from error handler"""
        self.output_panel.append_text(f"[WARNING] {warning_type}: {message}")

    def restart_running_process(self):
        self.stop_running_process()
        self.run_current_file()

    def clear_output_panel(self):
        self.output_panel.clear()

    def toggle_chat_ai_panel(self):
        # Ensure dock exists
        if not hasattr(self, 'chat_ai_dock') or self.chat_ai_dock is None:
            try:
                self.chat_ai_dock = QDockWidget("AI Assistant", self)
                self.chat_ai_widget = ChatAIWidget(self)
                self.chat_ai_dock.setWidget(self.chat_ai_widget)
                self.addDockWidget(Qt.RightDockWidgetArea, self.chat_ai_dock)
                self.chat_ai_dock.hide()
            except Exception:
                return

        if self.chat_ai_dock.isVisible():
            self.chat_ai_dock.hide()
        else:
            self.chat_ai_dock.show()

    def save_current_file(self):
        # Hàm này sẽ được gọi khi nhấn Ctrl+S
        current_tab = self.tabs.currentWidget()
        if hasattr(current_tab, "save_file"):
            current_tab.save_file()
        else:
            # Hiển thị thông báo hoặc xử lý khác nếu tab không hỗ trợ lưu
            pass

    def apply_vscode_style(self):
        self.setStyleSheet("""
        QMainWindow {
            background: #1e1e1e;
        }
        QTabWidget::pane {
            border: none;
            background: #1e1e1e;
        }
        QTabBar::tab {
            background: #2d2d2d;
            color: #cccccc;
            padding: 8px 32px 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-family: 'Consolas', 'Fira Code', 'JetBrains Mono', monospace;
            font-size: 13px;
            min-width: 120px;
            height: 32px;
        }
        QTabBar::tab:selected {
            background: #1e1e1e;
            color: #ffffff;
            border-bottom: 2px solid #007acc;
        }
        QTabBar::tab:hover {
            background: #252526;
        }
        QTabBar::close-button {
            width: 16px;
            height: 16px;
            image: (data:Resource/close.png);
        }
        QTabBar::close-button:hover {
            background: #e06c75;
            border-radius: 8px;
            image: (data:Resource/close.png);
        }
        QToolBar {
            background: #2c2c32;
            border: none;
            spacing: 8px;
            padding: 4px;
        }
        QToolButton {
            background: transparent;
            color: #cccccc;
            border: none;
            font-size: 15px;
            padding: 6px 10px;
        }
        QToolButton:hover {
            background: #333337;
            color: #ffffff;
        }
        QFrame#activity_bar {
            background: #2c2c32;
            border-right: 1px solid #222;
        }
        QDockWidget {
            background: #23272e;
            color: #fff;
            font-size: 15px;
            font-weight: bold;
        }
        QDockWidget::title {
            background: #23272e;
            color: #fff;
            font-size: 15px;
            font-weight: bold;
            padding-left: 8px;
        }
        QTreeView, QListView {
            background: #23272e;
            color: #cccccc;
            font-size: 13px;
            border: none;
        }
        QTreeView::item:selected {
            background: #094771;
            color: #fff;
        }
        QScrollBar:vertical, QScrollBar:horizontal {
            background: #23272e;
            border: none;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background: #444950;
            border-radius: 5px;
            min-height: 20px;
        }
        QStatusBar {
            background: #007acc;
            color: #fff;
            font-size: 12px;
        }
        QMenuBar {
            background: #23272e;
            color: #cccccc;
        }
        QMenuBar::item:selected {
            background: #094771;
            color: #fff;
        }
        QMenu {
            background: #23272e;
            color: #cccccc;
            border: 1px solid #222;
        }
        QMenu::item:selected {
            background: #094771;
            color: #fff;
        }
        QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox, QPushButton {
            font-family: 'Consolas', 'Fira Code', 'JetBrains Mono', monospace;
            font-size: 13px;
        }
        QPushButton {
            background: #2d2d2d;
            color: #cccccc;
            border: 1px solid #444;
            border-radius: 4px;
            padding: 4px 12px;
        }
        QPushButton:hover {
            background: #3d3d3d;
            color: #fff;
            border: 1px solid #007acc;
        }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background: #23272e;
            color: #cccccc;
            border: 1px solid #444;
            border-radius: 4px;
        }
        """)

    def setup_autocomplete(self):
        # Tùy vào ngôn ngữ, bạn có thể truyền vào danh sách từ khóa phù hợp
        keywords = [
            "def", "class", "import", "from", "for", "while", "if", "else", "elif", "return",
            "print", "self", "True", "False", "None", "with", "as", "try", "except", "finally",
            "break", "continue", "pass", "yield", "lambda", "global", "nonlocal", "assert", "raise"
        ]
        self.autocomplete_manager = AutocompleteManager(self.editor, api_words=keywords)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Example usage with custom screen size
    show_loading_then_main(
        HyggshiOSCodeMini,
        image_path="Resources/Image.png", 
        img_width=1090, 
        img_height=615,
        image_size=(1090, 615),  # Custom loading screen size
        print_info=True
    )