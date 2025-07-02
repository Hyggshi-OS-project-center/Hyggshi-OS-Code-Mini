import sys, os
import glob
import importlib.util 
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QTabWidget, QWidget, QVBoxLayout, QLineEdit, QShortcut,
    QDockWidget, QTreeView, QFileSystemModel, QLabel, QScrollArea, QStatusBar, QMenu, QMessageBox
)
from PyQt5.QtGui import QColor, QKeySequence, QPixmap, QWheelEvent, QMouseEvent, QTransform, QIcon
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.Qsci import (
    QsciLexerPython, QsciLexerCPP, QsciLexerJavaScript,
    QsciLexerHTML, QsciLexerJava, QsciLexerJSON,
    QsciLexerLua, QsciScintilla, QsciScintillaBase,
)
from PyQt5.QtWidgets import QSlider, QHBoxLayout
import subprocess
import tempfile

# Dummy OutputPanel definition (replace with your actual implementation or import)
from PyQt5.QtWidgets import QTextEdit
class OutputPanel(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
    def append_text(self, text):
        self.append(text)

try:
    from module.markdown_highlight import apply_markdown_highlight
except ImportError:
    def apply_markdown_highlight(editor):
        pass  # Dummy: No highlighting

try:
    from module.unsaved_checker import check_unsaved_and_prompt
except ImportError:
    def check_unsaved_and_prompt(tab, parent):
        return True  # Dummy: Always allow closing

try:
    from module.plugins import PluginManager
except ImportError:
    class PluginManager:
        def get_supported_languages(self):
            return {}
        def load_plugins(self):
            pass
        def get_interface_language(self):
            return "English"

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

from module.Extensions import Extension
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
        self.plugins = PluginManager()
        self.set_language(self.plugins.get_interface_language())

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
            "PHP (*.php);;C# (*.cs);;Bash (*.sh);;Text (*.txt);;All Files (*)"
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
        elif ext in [".json"]:
            self.set_language("JSON")
        elif ext in [".lua"]:
            self.set_language("Lua")
        elif ext in [".md"]:
            self.set_language("Markdown")
        else:
            self.set_language("Plain Text")  
        


class ImageTab(QWidget):
    def __init__(self, image_path, status_bar):
        super().__init__()
        self.image_path = image_path
        self.status_bar = status_bar
        self.zoom = 1.0
        self.rotation = 0
        self.flipped = False
        self.last_pos = QPoint()
        self.dragging = False


        self.layout = QVBoxLayout(self)
        self.scroll = QScrollArea(self)
        self.label = QLabel()
        self.pixmap = QPixmap(image_path)

        self.label.setAlignment(Qt.AlignCenter)
        self.label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.label.customContextMenuRequested.connect(self.show_context_menu)
        self.scroll.setWidget(self.label)
        self.scroll.setWidgetResizable(True)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(10)
        self.slider.setMaximum(1000)
        self.slider.setValue(100)
        self.slider.valueChanged.connect(self.slider_zoom_changed)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("padding-left: 6px; color: gray")

        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(self.slider)
        zoom_layout.addWidget(self.zoom_label)

        self.layout.addWidget(self.scroll)
        self.layout.addLayout(zoom_layout)
        self.setLayout(self.layout)

        self.update_image()


        QShortcut(QKeySequence("Ctrl+0"), self, self.reset_zoom)

    def slider_zoom_changed(self, value):
        self.zoom = value / 100.0
        self.update_image()

    def wheelEvent(self, event: QWheelEvent):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            angle = event.angleDelta().y()
            factor = 1.1 if angle > 0 else 0.9
            self.zoom *= factor
            self.zoom = max(0.1, min(10.0, self.zoom))
            self.update_image()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.last_pos = event.pos()
            self.dragging = True

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging:
            delta = event.pos() - self.last_pos
            self.scroll.horizontalScrollBar().setValue(
                self.scroll.horizontalScrollBar().value() - delta.x())
            self.scroll.verticalScrollBar().setValue(
                self.scroll.verticalScrollBar().value() - delta.y())
            self.last_pos = event.pos()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("Reset Zoom", self.reset_zoom)
        menu.addAction("Rotate Right", self.rotate_right)
        menu.addAction("Flip Horizontal", self.flip_horizontal)
        menu.exec_(self.label.mapToGlobal(pos))

    def rotate_right(self):
        self.rotation = (self.rotation + 90) % 360
        self.update_image()

    def flip_horizontal(self):
        self.flipped = not self.flipped
        self.update_image()

    def reset_zoom(self):
        self.zoom = 1.0
        self.update_image()

    def update_image(self):
        transform = QTransform()
        transform.rotate(self.rotation)
        if self.flipped:
            transform.scale(-1, 1)
        transformed_pixmap = self.pixmap.transformed(transform, Qt.SmoothTransformation)
        scaled = transformed_pixmap.scaled(
            transformed_pixmap.size() * self.zoom,
            Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)
        size = scaled.size()
        self.zoom_label.setText(f"{int(self.zoom * 100)}%")
        self.slider.blockSignals(True)
        self.slider.setValue(int(self.zoom * 100))
        self.slider.blockSignals(False)
        self.status_bar.showMessage(f"Image Size: {self.pixmap.width()} x {self.pixmap.height()} | Zoom: {int(self.zoom * 100)}%")


class HyggshiOSCodeMini(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyggshi OS Code Mini")
        self.setWindowIcon(QIcon("icon.png"))  # Ensure you have an icon file named 'icon.png'
        self.resize(1000, 650)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.project_path = "."

        self.plugins = PluginManager()

        self.setup_sidebar()
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.interface_language = self.plugins.get_interface_language()
        self.setup_menu()

        QShortcut(QKeySequence("Ctrl+N"), self, self.new_file)

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

        self.extensions = []
        self.load_extensions()

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
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.project_path))
        self.tree.doubleClicked.connect(self.tree_item_clicked)

        self.dock.setWidget(self.tree)

    def tree_item_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self.add_new_tab(path)

    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction("New File", self.new_file)
        file_menu.addAction("Open File", self.open_file)
        file_menu.addAction("Open Folder", self.open_folder)
        file_menu.addAction("Save File", self.save_file)
        file_menu.addAction("Save File As", self.save_file_as)
        file_menu.addAction("Exit", self.close)

        theme_menu = menubar.addMenu("Theme")
        theme_menu.addAction("Dark Theme", self.apply_dark_theme)
        theme_menu.addAction("Light Theme", self.apply_light_theme)

        lang_menu = menubar.addMenu("Language")

        default_langs = ["Plain Text", "Python", "C++", "JavaScript", "HTML", "Java", "JSON", "Lua", "Markdown"]
        for lang in default_langs:
            act = lang_menu.addAction(lang)
            act.triggered.connect(lambda _, l=lang: self.set_language_for_current_tab(l))

        for lang in self.plugins.get_supported_languages().keys():
            act = lang_menu.addAction(f"[Plugin] {lang}")
            act.triggered.connect(lambda _, l=lang: self.set_language_for_current_tab(l))

        plugin_menu = menubar.addMenu("Plugins")
        plugin_menu.addAction("Reload Plugins", self.reload_plugins)
        plugin_menu.addAction("List Supported Languages", self.show_plugin_languages)

        tool_menu = menubar.addMenu("Tools")
        tool_menu.addAction("Check Syntax", self.check_current_syntax)

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
        else:
            tab.disable_extension(name)

    def new_file(self):
        self.add_new_tab()

    def open_file(self):
        file_types = (
    "Markdown (*.md);;Python (*.py);;C++ (*.cpp *.h);;JavaScript (*.js);;"
    "HTML (*.html *.htm);;Lua (*.lua);;Java (*.java);;JSON (*.json);;"
    "PHP (*.php);;C# (*.cs);;Bash (*.sh);;Text (*.txt);;All Files (*)"
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
        if isinstance(tab, EditorTab) and not tab.save_file():
            tab.save_file_as()

    def save_file_as(self):
        tab = self.current_editor_tab()
        if isinstance(tab, EditorTab):
            tab.save_file_as()

    def add_new_tab(self, path=None):

        image_exts = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp", ".tiff", ".ico", ".avif"]
        txt_exts = [".txt"]

        if path and os.path.splitext(path)[1].lower() in image_exts:
            tab = ImageTab(path, self.statusBar())
            icon_path = "icons/image.png"
            icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        elif path and os.path.splitext(path)[1].lower() in txt_exts:
            tab = EditorTab(path)
            tab.load_file(path)
            icon_path = "icons/text.png"
            icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        else:
            tab = EditorTab(path)
            if path and not tab.load_file(path):
                return
            icon_path = "icons/code.png"
            icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        title = os.path.basename(path) if path else "Untitled"
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
        plugin_langs = self.plugins.get_supported_languages()
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
        plugin_langs = self.plugins.get_supported_languages()
        if lang in plugin_langs:
            tab.editor.setLexer(plugin_langs[lang]["lexer"])
            return

        # Nếu không thì dùng ngôn ngữ mặc định
        tab.set_language(lang)

    def reload_plugins(self):
        self.plugins.load_plugins()
        QMessageBox.information(self, "Plugins", "Plugins đã được tải lại.")

    def show_plugin_languages(self):
        langs = self.plugins.get_supported_languages()
        if not langs:
            QMessageBox.information(self, "Plugins", "Không có plugin nào được nạp.")
        else:
            msg = "\n".join([f"{name} ({info['extension']})" for name, info in langs.items()])
            QMessageBox.information(self, "Plugins đã nạp", msg)

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
        elif ext in [".m", ".mm"]:
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

    def run_current_file(self):
        tab = self.current_editor_tab()
        if not tab or not hasattr(tab, "editor"):
            QMessageBox.warning(self, "Run", "Không có file nào đang mở.")
            return

        ext = os.path.splitext(getattr(tab, "file_path", "") or "")[1].lower()
        code = tab.editor.text()

        if ext == ".py" or not tab.file_path:
            # Nếu là file Python hoặc file chưa lưu, chạy code hiện tại
            try:
                if tab.file_path and ext == ".py":
                    # Nếu đã có file .py, chạy trực tiếp
                    run_path = tab.file_path
                else:
                    # Nếu chưa lưu, ghi ra file tạm
                    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
                        tmp.write(code)
                        run_path = tmp.name
                result = subprocess.run(
                    [sys.executable, run_path],
                    capture_output=True, text=True, timeout=10
                )
                output = result.stdout + ("\n" + result.stderr if result.stderr else "")
                self.output_panel.append_text(f"--- Run {run_path} ---\n{output}")
                self.dock_output.show()
                if not tab.file_path:
                    os.unlink(run_path)  # Xóa file tạm sau khi chạy
            except Exception as e:
                self.output_panel.append_text(f"Lỗi khi chạy file: {e}")
                self.dock_output.show()
        else:
            QMessageBox.information(self, "Run", "Chỉ hỗ trợ chạy file Python trực tiếp.")

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HyggshiOSCodeMini()
    window.show()
    sys.exit(app.exec_())
    # Plugin system: Load plugins from a "plugins" directory at startup

    # Load plugins after main window is created
    # load_plugins(window)