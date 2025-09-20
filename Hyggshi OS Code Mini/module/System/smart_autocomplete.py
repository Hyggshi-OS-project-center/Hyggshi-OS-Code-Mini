import ast
import os
import re
import importlib.util
from collections import defaultdict
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor
from PyQt5.Qsci import QsciScintilla
import keyword
import builtins

class CodeAnalyzer(QThread):
    """Background thread để phân tích code và build suggestions"""
    analysis_complete = pyqtSignal(dict)
    
    def __init__(self, code_text, file_path=None):
        super().__init__()
        self.code_text = code_text
        self.file_path = file_path
        
    def run(self):
        """Chạy phân tích code trong background"""
        try:
            analysis = self.analyze_code(self.code_text)
            self.analysis_complete.emit(analysis)
        except Exception as e:
            print(f"Code analysis error: {e}")
            self.analysis_complete.emit({})
    
    def analyze_code(self, code):
        """Phân tích code Python và trích xuất thông tin"""
        result = {
            'variables': set(),
            'functions': set(),
            'classes': set(),
            'imports': set(),
            'methods': defaultdict(set),  # class_name -> set of methods
            'attributes': defaultdict(set),  # object_name -> set of attributes
            'modules': set()
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Variables (assignments)
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            result['variables'].add(target.id)
                        elif isinstance(target, ast.Attribute):
                            if isinstance(target.value, ast.Name):
                                result['attributes'][target.value.id].add(target.attr)
                
                # Function definitions
                elif isinstance(node, ast.FunctionDef):
                    result['functions'].add(node.name)
                    # Analyze parameters
                    for arg in node.args.args:
                        result['variables'].add(arg.arg)
                
                # Class definitions
                elif isinstance(node, ast.ClassDef):
                    result['classes'].add(node.name)
                    # Analyze class methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            result['methods'][node.name].add(item.name)
                
                # Import statements
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.asname or alias.name
                        result['imports'].add(module_name)
                        result['modules'].add(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result['modules'].add(node.module)
                        for alias in node.names:
                            name = alias.asname or alias.name
                            result['imports'].add(name)
                
                # Method/attribute calls
                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        result['attributes'][node.value.id].add(node.attr)
        
        except SyntaxError:
            # If code has syntax errors, analyze line by line
            self.analyze_incomplete_code(code, result)
        
        return result
    
    def analyze_incomplete_code(self, code, result):
        """Phân tích code không hoàn chỉnh (có lỗi syntax)"""
        lines = code.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Simple regex patterns for common constructs
            patterns = [
                (r'def\s+(\w+)', 'functions'),
                (r'class\s+(\w+)', 'classes'),
                (r'(\w+)\s*=', 'variables'),
                (r'import\s+(\w+)', 'imports'),
                (r'from\s+(\w+)\s+import', 'modules'),
            ]
            
            for pattern, category in patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    result[category].add(match)

class LibraryInspector:
    """Kiểm tra và lấy thông tin từ các thư viện Python"""
    
    @staticmethod
    def get_module_attributes(module_name):
        """Lấy attributes và methods từ module"""
        try:
            if module_name in ['os', 'sys', 'json', 'datetime', 'random', 'math', 're']:
                # Safe modules to import
                module = importlib.import_module(module_name)
                return [attr for attr in dir(module) if not attr.startswith('_')]
            else:
                # For unknown modules, return common patterns
                return LibraryInspector.get_common_patterns(module_name)
        except:
            return []
    
    @staticmethod
    def get_common_patterns(module_name):
        """Trả về patterns thông dụng cho các library"""
        patterns = {
            'numpy': ['array', 'zeros', 'ones', 'arange', 'linspace', 'shape', 'dtype', 'ndim', 'size', 'reshape', 'transpose', 'dot', 'sum', 'mean', 'std', 'min', 'max'],
            'pandas': ['DataFrame', 'Series', 'read_csv', 'read_excel', 'head', 'tail', 'info', 'describe', 'shape', 'columns', 'index', 'loc', 'iloc', 'drop', 'fillna', 'groupby'],
            'matplotlib': ['pyplot', 'plot', 'show', 'figure', 'subplot', 'xlabel', 'ylabel', 'title', 'legend', 'grid', 'savefig'],
            'requests': ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'Session', 'Response'],
            'flask': ['Flask', 'render_template', 'request', 'redirect', 'url_for', 'session', 'flash', 'jsonify'],
            'PyQt5': ['QApplication', 'QMainWindow', 'QWidget', 'QVBoxLayout', 'QHBoxLayout', 'QPushButton', 'QLabel', 'QLineEdit'],
        }
        
        # Fuzzy matching
        for key, values in patterns.items():
            if key.lower() in module_name.lower():
                return values
        
        return []

class SmartAutoComplete:
    """Autocomplete thông minh với khả năng mở rộng"""
    
    def __init__(self, editor):
        self.editor = editor
        self.suggestions_list = QListWidget(editor.parent())
        self.suggestions_list.setWindowFlags(Qt.ToolTip)
        self.suggestions_list.hide()
        
        # Core suggestions
        self.base_suggestions = self.build_base_suggestions()
        
        # Dynamic suggestions from code analysis
        self.dynamic_suggestions = {}
        self.context_suggestions = {}
        
        # Analysis state
        self.analyzer = None
        self.analysis_timer = QTimer()
        self.analysis_timer.setSingleShot(True)
        self.analysis_timer.timeout.connect(self.start_code_analysis)
        
        # UI state
        self.active = False
        self.current_word = ""
        self.show_timer = QTimer()
        self.show_timer.setSingleShot(True)
        self.show_timer.timeout.connect(self.show_suggestions)
        
        # Setup events
        self.setup_events()
    
    def build_base_suggestions(self):
        """Xây dựng gợi ý cơ bản (không đổi)"""
        suggestions = set()
        
        # Python keywords
        suggestions.update(keyword.kwlist)
        
        # Built-in functions
        suggestions.update([name for name in dir(builtins) if not name.startswith('_')])
        
        # Common patterns
        common = [
            # String methods
            'capitalize', 'center', 'count', 'endswith', 'find', 'format', 'index', 'join',
            'lower', 'lstrip', 'replace', 'rstrip', 'split', 'startswith', 'strip', 'upper',
            
            # List methods
            'append', 'clear', 'copy', 'count', 'extend', 'index', 'insert', 'pop', 'remove', 'reverse', 'sort',
            
            # Dict methods
            'get', 'items', 'keys', 'pop', 'popitem', 'setdefault', 'update', 'values',
            
            # File methods
            'read', 'write', 'close', 'readline', 'readlines', 'writelines', 'seek', 'tell',
            
            # Exception handling
            'Exception', 'ValueError', 'TypeError', 'IndexError', 'KeyError', 'AttributeError',
        ]
        
        suggestions.update(common)
        return suggestions
    
    def setup_events(self):
        """Thiết lập events"""
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.cursorPositionChanged.connect(self.on_cursor_changed)
        self.editor.keyPressEvent = self.wrap_key_press_event(self.editor.keyPressEvent)
        
        self.suggestions_list.itemClicked.connect(self.insert_suggestion)
        self.suggestions_list.itemActivated.connect(self.insert_suggestion)
    
    def wrap_key_press_event(self, original_key_press):
        """Wrapper cho key press events"""
        def new_key_press_event(event):
            key = event.key()
            
            if self.active:
                if key == Qt.Key_Escape:
                    self.hide_suggestions()
                    return
                elif key == Qt.Key_Tab or key == Qt.Key_Return:
                    self.accept_current_suggestion()
                    return
                elif key == Qt.Key_Up:
                    self.move_selection(-1)
                    return
                elif key == Qt.Key_Down:
                    self.move_selection(1)
                    return
            
            # Process original key event
            original_key_press(event)
            
            # Trigger analysis và suggestions
            if key not in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right, Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt]:
                self.analysis_timer.start(500)  # Analyze sau 500ms
                self.show_timer.start(100)      # Show suggestions sau 100ms
        
        return new_key_press_event
    
    def on_text_changed(self):
        """Text changed handler"""
        if not self.active:
            self.show_timer.start(200)
    
    def on_cursor_changed(self, line, index):
        """Cursor position changed handler"""
        current = self.get_current_word()
        if self.active and (not current or current != self.current_word):
            self.hide_suggestions()
    
    def start_code_analysis(self):
        """Bắt đầu phân tích code trong background"""
        if self.analyzer and self.analyzer.isRunning():
            return
        
        code = self.editor.text()
        file_path = getattr(self.editor.parent(), 'file_path', None) if hasattr(self.editor, 'parent') else None
        
        self.analyzer = CodeAnalyzer(code, file_path)
        self.analyzer.analysis_complete.connect(self.on_analysis_complete)
        self.analyzer.start()
    
    def on_analysis_complete(self, analysis):
        """Xử lý kết quả phân tích code"""
        self.dynamic_suggestions = analysis
        self.build_context_suggestions()
    
    def build_context_suggestions(self):
        """Xây dựng gợi ý dựa trên context"""
        self.context_suggestions = {}
        
        # Lấy context hiện tại (dòng đang gõ)
        try:
            line, index = self.editor.getCursorPosition()
            current_line = self.editor.text(line)
            
            # Phân tích context
            if '.' in current_line:
                # Object method suggestions
                obj_part = current_line[:index].split('.')[-2].strip()
                self.context_suggestions['object_methods'] = self.get_object_methods(obj_part)
            
            if current_line.strip().startswith('import ') or ' import ' in current_line:
                # Import suggestions
                self.context_suggestions['modules'] = self.get_import_suggestions()
            
            if '(' in current_line and ')' not in current_line[current_line.rfind('('):]:
                # Function parameter suggestions
                func_name = self.extract_function_name(current_line, index)
                self.context_suggestions['parameters'] = self.get_parameter_suggestions(func_name)
                
        except Exception as e:
            print(f"Context analysis error: {e}")
    
    def get_object_methods(self, obj_name):
        """Lấy methods cho object"""
        suggestions = []
        
        # From dynamic analysis
        if obj_name in self.dynamic_suggestions.get('attributes', {}):
            suggestions.extend(list(self.dynamic_suggestions['attributes'][obj_name]))
        
        # From module inspection
        if obj_name in self.dynamic_suggestions.get('imports', set()):
            suggestions.extend(LibraryInspector.get_module_attributes(obj_name))
        
        # Type-based suggestions
        type_suggestions = {
            'str': ['capitalize', 'center', 'count', 'endswith', 'find', 'format', 'join', 'lower', 'replace', 'split', 'strip', 'upper'],
            'list': ['append', 'clear', 'copy', 'count', 'extend', 'index', 'insert', 'pop', 'remove', 'reverse', 'sort'],
            'dict': ['get', 'items', 'keys', 'pop', 'popitem', 'setdefault', 'update', 'values'],
            'file': ['read', 'write', 'close', 'readline', 'readlines', 'seek', 'tell'],
        }
        
        # Guess type from variable name patterns
        for type_name, methods in type_suggestions.items():
            if type_name in obj_name.lower() or self.guess_type(obj_name) == type_name:
                suggestions.extend(methods)
        
        return list(set(suggestions))
    
    def guess_type(self, var_name):
        """Đoán type của variable từ tên"""
        patterns = {
            'str': ['text', 'string', 'name', 'title', 'content', 'message'],
            'list': ['items', 'array', 'elements', 'list', 'data'],
            'dict': ['config', 'settings', 'mapping', 'dict', 'params'],
            'file': ['file', 'handle', 'stream'],
        }
        
        var_lower = var_name.lower()
        for type_name, keywords in patterns.items():
            if any(keyword in var_lower for keyword in keywords):
                return type_name
        
        return None
    
    def get_import_suggestions(self):
        """Lấy gợi ý cho import statements"""
        return [
            'os', 'sys', 'json', 'datetime', 'random', 'math', 're', 'collections',
            'itertools', 'functools', 'pathlib', 'threading', 'multiprocessing',
            'numpy', 'pandas', 'matplotlib', 'seaborn', 'sklearn', 'requests',
            'flask', 'django', 'PyQt5', 'tkinter', 'sqlite3', 'urllib', 'pickle'
        ]
    
    def extract_function_name(self, line, cursor_pos):
        """Trích xuất tên function từ dòng hiện tại"""
        try:
            # Tìm dấu ( gần nhất trước cursor
            paren_pos = line.rfind('(', 0, cursor_pos)
            if paren_pos == -1:
                return None
            
            # Tìm tên function trước dấu (
            func_part = line[:paren_pos].strip()
            func_name = re.search(r'(\w+)$', func_part)
            
            return func_name.group(1) if func_name else None
        except:
            return None
    
    def get_parameter_suggestions(self, func_name):
        """Lấy gợi ý parameters cho function"""
        if not func_name:
            return []
        
        # Common function signatures
        signatures = {
            'print': ['sep=', 'end=', 'file=', 'flush='],
            'open': ['mode=', 'encoding=', 'buffering=', 'newline='],
            'range': ['start', 'stop', 'step'],
            'enumerate': ['start='],
            'zip': ['*iterables'],
            'sorted': ['key=', 'reverse='],
            'max': ['key=', 'default='],
            'min': ['key=', 'default='],
        }
        
        return signatures.get(func_name, [])
    
    def get_current_word(self):
        """Lấy từ hiện tại"""
        try:
            line, index = self.editor.getCursorPosition()
            text = self.editor.text(line)
            
            start = index
            while start > 0 and (text[start-1].isalnum() or text[start-1] in '._'):
                start -= 1
            
            return text[start:index]
        except:
            return ""
    
    def get_all_suggestions(self, word):
        """Lấy tất cả gợi ý cho từ hiện tại"""
        if len(word) < 1:
            return []
        
        word_lower = word.lower()
        all_suggestions = set()
        
        # Base suggestions
        all_suggestions.update([s for s in self.base_suggestions if s.lower().startswith(word_lower)])
        
        # Dynamic suggestions từ code analysis
        if self.dynamic_suggestions:
            for category in ['variables', 'functions', 'classes', 'imports']:
                if category in self.dynamic_suggestions:
                    all_suggestions.update([s for s in self.dynamic_suggestions[category] if s.lower().startswith(word_lower)])
        
        # Context-aware suggestions
        for context_type, suggestions in self.context_suggestions.items():
            all_suggestions.update([s for s in suggestions if s.lower().startswith(word_lower)])
        
        # Sort by relevance (length first, then alphabetically)
        return sorted(list(all_suggestions), key=lambda x: (len(x), x.lower()))[:15]
    
    def show_suggestions(self):
        """Hiển thị danh sách gợi ý"""
        current_word = self.get_current_word()
        
        if len(current_word) < 1:
            self.hide_suggestions()
            return
        
        matches = self.get_all_suggestions(current_word)
        
        if not matches:
            self.hide_suggestions()
            return
        
        # Update suggestions list
        self.suggestions_list.clear()
        for suggestion in matches:
            item = QListWidgetItem(suggestion)
            self.suggestions_list.addItem(item)
        
        # Position và hiển thị
        try:
            line, index = self.editor.getCursorPosition()
            x = self.editor.SendScintilla(self.editor.SCI_POINTXFROMPOSITION, 0, 
                                        self.editor.SendScintilla(self.editor.SCI_GETCURRENTPOS))
            y = self.editor.SendScintilla(self.editor.SCI_POINTYFROMPOSITION, 0, 
                                        self.editor.SendScintilla(self.editor.SCI_GETCURRENTPOS))
            
            global_pos = self.editor.mapToGlobal(self.editor.pos())
            self.suggestions_list.move(global_pos.x() + x, global_pos.y() + y + 20)
            self.suggestions_list.resize(250, min(len(matches) * 22 + 10, 200))
            self.suggestions_list.show()
            
            if self.suggestions_list.count() > 0:
                self.suggestions_list.setCurrentRow(0)
            
            self.active = True
            self.current_word = current_word
            
        except Exception as e:
            print(f"Error showing suggestions: {e}")
    
    def hide_suggestions(self):
        """Ẩn danh sách gợi ý"""
        if self.active:
            self.suggestions_list.hide()
            self.active = False
            self.current_word = ""
    
    def move_selection(self, direction):
        """Di chuyển selection trong danh sách"""
        current_row = self.suggestions_list.currentRow()
        new_row = current_row + direction
        
        if 0 <= new_row < self.suggestions_list.count():
            self.suggestions_list.setCurrentRow(new_row)
    
    def accept_current_suggestion(self):
        """Chấp nhận gợi ý hiện tại"""
        current_item = self.suggestions_list.currentItem()
        if current_item:
            self.insert_suggestion(current_item)
    
    def insert_suggestion(self, item):
        """Chèn gợi ý vào editor"""
        if not item:
            return
        
        suggestion = item.text()
        current_word = self.get_current_word()
        
        try:
            line, index = self.editor.getCursorPosition()
            start_pos = index - len(current_word)
            self.editor.setSelection(line, start_pos, line, index)
            self.editor.replaceSelectedText(suggestion)
            self.hide_suggestions()
        except Exception as e:
            print(f"Error inserting suggestion: {e}")


# Integration functions
def setup_smart_autocomplete(editor):
    """
    Setup smart autocomplete cho QsciScintilla editor
    
    Usage:
    from smart_autocomplete import setup_smart_autocomplete
    setup_smart_autocomplete(self.editor)
    """
    if isinstance(editor, QsciScintilla):
        autocomplete = SmartAutoComplete(editor)
        editor._smart_autocomplete = autocomplete
        return autocomplete
    else:
        print("Error: Editor must be QsciScintilla instance")
        return None

def get_smart_autocomplete(editor):
    """Lấy smart autocomplete instance"""
    return getattr(editor, '_smart_autocomplete', None)

def refresh_autocomplete_analysis(editor):
    """Force refresh code analysis"""
    autocomplete = get_smart_autocomplete(editor)
    if autocomplete:
        autocomplete.start_code_analysis()