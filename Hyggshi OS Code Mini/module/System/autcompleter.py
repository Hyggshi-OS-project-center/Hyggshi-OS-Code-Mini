import ast
import os
import re
import json
import sqlite3
import importlib.util
from collections import defaultdict, Counter
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QLabel, QToolTip
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QTextCursor, QIcon, QPixmap, QPainter, QFont
from PyQt5.Qsci import QsciScintilla
import keyword
import builtins

class HistoryManager:
    """Quản lý lịch sử và học từ hành vi người dùng"""
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'autocomplete_history.db')
        self.init_database()
        self.usage_patterns = defaultdict(Counter)
        self.completion_frequency = Counter()
        self.context_patterns = defaultdict(list)
    
    def init_database(self):
        """Khởi tạo database để lưu lịch sử"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT,
                    completion TEXT,
                    context TEXT,
                    frequency INTEGER DEFAULT 1,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT,
                    completion TEXT,
                    usage_count INTEGER DEFAULT 1
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database init error: {e}")
    
    def record_completion(self, word, completion, context=""):
        """Ghi lại completion được sử dụng"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if exists
            cursor.execute(
                "SELECT frequency FROM completions WHERE word=? AND completion=? AND context=?",
                (word, completion, context)
            )
            result = cursor.fetchone()
            
            if result:
                cursor.execute(
                    "UPDATE completions SET frequency = frequency + 1, last_used = CURRENT_TIMESTAMP WHERE word=? AND completion=? AND context=?",
                    (word, completion, context)
                )
            else:
                cursor.execute(
                    "INSERT INTO completions (word, completion, context) VALUES (?, ?, ?)",
                    (word, completion, context)
                )
            
            conn.commit()
            conn.close()
            
            # Update in-memory counters
            self.completion_frequency[completion] += 1
            self.usage_patterns[word][completion] += 1
            
        except Exception as e:
            print(f"Record completion error: {e}")
    
    def get_personalized_suggestions(self, word, context=""):
        """Lấy gợi ý được cá nhân hóa"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT completion, frequency FROM completions WHERE word LIKE ? OR completion LIKE ? ORDER BY frequency DESC LIMIT 10",
                (f"{word}%", f"{word}%")
            )
            
            results = cursor.fetchall()
            conn.close()
            
            return [comp for comp, freq in results]
        except Exception as e:
            print(f"Get personalized suggestions error: {e}")
            return []

class IconProvider:
    """Tạo icons cho các loại suggestions"""
    
    def __init__(self):
        self.icons = {}
        self.create_icons()
    
    def create_icons(self):
        """Tạo icons đơn giản bằng text"""
        icon_configs = {
            'class': ('🏛️', '#4FC1FF'),
            'function': ('⚡', '#DCDCAA'),  
            'method': ('🔧', '#DCDCAA'),
            'variable': ('📦', '#9CDCFE'),
            'module': ('📚', '#CE9178'),
            'keyword': ('🔑', '#C586C0'),
            'builtin': ('⭐', '#4FC1FF'),
            'property': ('🏷️', '#9CDCFE'),
            'snippet': ('📝', '#569CD6'),
            'ai': ('🤖', '#00D4AA')
        }
        
        for icon_type, (symbol, color) in icon_configs.items():
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.transparent)
            
            painter = QPainter(pixmap)
            painter.setFont(QFont("Segoe UI Emoji", 10))
            painter.setPen(Qt.white)
            painter.drawText(0, 0, 16, 16, Qt.AlignCenter, symbol)
            painter.end()
            
            self.icons[icon_type] = QIcon(pixmap)
    
    def get_icon(self, suggestion_type):
        """Lấy icon theo loại"""
        return self.icons.get(suggestion_type, self.icons.get('variable'))

class DocstringProvider:
    """Cung cấp docstring và mô tả cho suggestions"""
    
    def __init__(self):
        self.builtin_docs = self.load_builtin_docs()
        self.custom_docs = {}
    
    def load_builtin_docs(self):
        """Load documentation cho built-in functions"""
        docs = {
            'print': 'print(*values, sep=" ", end="\\n", file=sys.stdout, flush=False)\nPrints values to stdout',
            'len': 'len(obj) -> int\nReturns the length of an object',
            'range': 'range(start, stop, step) -> range\nCreates a range of numbers',
            'open': 'open(file, mode="r", encoding=None) -> file object\nOpens a file',
            'str': 'str(object) -> string\nConverts object to string',
            'int': 'int(x) -> integer\nConverts x to integer',
            'list': 'list(iterable) -> list\nCreates a list from iterable',
            'dict': 'dict(**kwargs) -> dictionary\nCreates a dictionary',
            'set': 'set(iterable) -> set\nCreates a set from iterable',
            'tuple': 'tuple(iterable) -> tuple\nCreates a tuple from iterable',
            
            # String methods
            'split': 'str.split(sep=None, maxsplit=-1) -> list\nSplits string into list',
            'join': 'str.join(iterable) -> string\nJoins strings with separator',
            'replace': 'str.replace(old, new, count=-1) -> string\nReplaces occurrences',
            'strip': 'str.strip(chars=None) -> string\nRemoves whitespace from ends',
            'lower': 'str.lower() -> string\nConverts to lowercase',
            'upper': 'str.upper() -> string\nConverts to uppercase',
            
            # List methods
            'append': 'list.append(item) -> None\nAdds item to end of list',
            'extend': 'list.extend(iterable) -> None\nAdds all items from iterable',
            'insert': 'list.insert(index, item) -> None\nInserts item at index',
            'remove': 'list.remove(value) -> None\nRemoves first occurrence',
            'pop': 'list.pop(index=-1) -> item\nRemoves and returns item',
            'sort': 'list.sort(key=None, reverse=False) -> None\nSorts list in place',
            
            # Dict methods  
            'get': 'dict.get(key, default=None) -> value\nGets value for key',
            'keys': 'dict.keys() -> dict_keys\nReturns all keys',
            'values': 'dict.values() -> dict_values\nReturns all values',
            'items': 'dict.items() -> dict_items\nReturns key-value pairs',
            'update': 'dict.update(other) -> None\nUpdates with another dict',
        }
        return docs
    
    def get_docstring(self, suggestion, suggestion_type):
        """Lấy docstring cho suggestion"""
        if suggestion in self.builtin_docs:
            return self.builtin_docs[suggestion]
        
        if suggestion_type == 'keyword':
            return self.get_keyword_doc(suggestion)
        elif suggestion_type == 'module':
            return f"Module: {suggestion}\nImport this module to use its functions"
        elif suggestion_type == 'class':
            return f"Class: {suggestion}\nA custom class definition"
        elif suggestion_type == 'function':
            return f"Function: {suggestion}\nA custom function definition"
        
        return f"{suggestion_type.title()}: {suggestion}"
    
    def get_keyword_doc(self, keyword):
        """Documentation cho Python keywords"""
        keyword_docs = {
            'def': 'def function_name(parameters):\n    """Define a function"""',
            'class': 'class ClassName:\n    """Define a class"""',
            'if': 'if condition:\n    """Conditional statement"""',
            'elif': 'elif condition:\n    """Additional condition"""',
            'else': 'else:\n    """Default condition"""',
            'for': 'for item in iterable:\n    """Loop over items"""',
            'while': 'while condition:\n    """Loop while condition is true"""',
            'try': 'try:\n    """Exception handling"""',
            'except': 'except ExceptionType:\n    """Handle specific exception"""',
            'finally': 'finally:\n    """Always execute this block"""',
            'with': 'with context_manager:\n    """Context manager"""',
            'import': 'import module_name\n"""Import a module"""',
            'from': 'from module import item\n"""Import specific item"""',
            'return': 'return value\n"""Return value from function"""',
            'yield': 'yield value\n"""Generator function"""',
            'break': 'break\n"""Exit loop"""',
            'continue': 'continue\n"""Skip to next iteration"""',
            'pass': 'pass\n"""Do nothing placeholder"""',
        }
        return keyword_docs.get(keyword, f"Python keyword: {keyword}")

class AISnippetProvider:
    """Cung cấp AI-powered code snippets"""
    
    def __init__(self):
        self.snippets = self.load_smart_snippets()
        
    def load_smart_snippets(self):
        """Load các snippets thông minh"""
        snippets = {
            'for': {
                'basic_loop': 'for ${1:item} in ${2:iterable}:\n    ${3:pass}',
                'enumerate_loop': 'for ${1:index}, ${2:item} in enumerate(${3:iterable}):\n    ${4:pass}',
                'range_loop': 'for ${1:i} in range(${2:10}):\n    ${3:pass}',
                'dict_loop': 'for ${1:key}, ${2:value} in ${3:dictionary}.items():\n    ${4:pass}'
            },
            'if': {
                'basic_if': 'if ${1:condition}:\n    ${2:pass}',
                'if_else': 'if ${1:condition}:\n    ${2:pass}\nelse:\n    ${3:pass}',
                'if_elif': 'if ${1:condition}:\n    ${2:pass}\nelif ${3:condition}:\n    ${4:pass}\nelse:\n    ${5:pass}'
            },
            'def': {
                'basic_function': 'def ${1:function_name}(${2:parameters}):\n    """${3:Description}"""\n    ${4:pass}',
                'return_function': 'def ${1:function_name}(${2:parameters}):\n    """${3:Description}"""\n    return ${4:result}',
                'class_method': 'def ${1:method_name}(self${2:, parameters}):\n    """${3:Description}"""\n    ${4:pass}'
            },
            'class': {
                'basic_class': 'class ${1:ClassName}:\n    """${2:Description}"""\n    \n    def __init__(self${3:, parameters}):\n        ${4:pass}',
                'inherited_class': 'class ${1:ClassName}(${2:BaseClass}):\n    """${3:Description}"""\n    \n    def __init__(self${4:, parameters}):\n        super().__init__(${5:parameters})\n        ${6:pass}'
            },
            'try': {
                'basic_try': 'try:\n    ${1:risky_code}\nexcept ${2:Exception} as ${3:e}:\n    ${4:handle_error}',
                'try_finally': 'try:\n    ${1:risky_code}\nexcept ${2:Exception} as ${3:e}:\n    ${4:handle_error}\nfinally:\n    ${5:cleanup}',
                'try_else': 'try:\n    ${1:risky_code}\nexcept ${2:Exception} as ${3:e}:\n    ${4:handle_error}\nelse:\n    ${5:success_code}'
            },
            'with': {
                'file_with': 'with open(${1:filename}, ${2:"r"}) as ${3:f}:\n    ${4:content = f.read()}',
                'context_manager': 'with ${1:context_manager} as ${2:variable}:\n    ${3:pass}'
            }
        }
        return snippets
    
    def get_snippets_for_keyword(self, keyword, context=""):
        """Lấy snippets cho keyword"""
        if keyword in self.snippets:
            snippets = []
            for name, template in self.snippets[keyword].items():
                snippets.append({
                    'name': name.replace('_', ' ').title(),
                    'template': template,
                    'type': 'snippet'
                })
            return snippets
        return []
    
    def expand_snippet(self, template):
        """Expand snippet template (đơn giản hóa)"""
        # Thay thế ${n:placeholder} bằng placeholder
        expanded = re.sub(r'\$\{\d+:([^}]+)\}', r'\1', template)
        expanded = re.sub(r'\$\{\d+\}', '', expanded)
        return expanded

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
            'variables': {},  # name -> type_info
            'functions': {},  # name -> signature_info
            'classes': {},    # name -> class_info
            'imports': {},    # name -> module_info
            'methods': defaultdict(set),
            'attributes': defaultdict(set),
            'modules': set()
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_type = self.infer_type(node.value)
                            result['variables'][target.id] = {
                                'type': var_type,
                                'line': node.lineno
                            }
                        elif isinstance(target, ast.Attribute):
                            if isinstance(target.value, ast.Name):
                                result['attributes'][target.value.id].add(target.attr)
                
                elif isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    result['functions'][node.name] = {
                        'args': args,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node)
                    }
                    for arg in args:
                        result['variables'][arg] = {'type': 'parameter', 'line': node.lineno}
                
                elif isinstance(node, ast.ClassDef):
                    result['classes'][node.name] = {
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'methods': []
                    }
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            result['methods'][node.name].add(item.name)
                            result['classes'][node.name]['methods'].append(item.name)
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.asname or alias.name
                        result['imports'][module_name] = {
                            'full_name': alias.name,
                            'line': node.lineno
                        }
                        result['modules'].add(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result['modules'].add(node.module)
                        for alias in node.names:
                            name = alias.asname or alias.name
                            result['imports'][name] = {
                                'full_name': f"{node.module}.{alias.name}",
                                'line': node.lineno
                            }
        
        except SyntaxError:
            self.analyze_incomplete_code(code, result)
        
        return result
    
    def infer_type(self, node):
        """Suy luận type của assignment"""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return 'str'
            elif isinstance(node.value, (int, float)):
                return 'number'
            elif isinstance(node.value, bool):
                return 'bool'
        elif isinstance(node, ast.List):
            return 'list'
        elif isinstance(node, ast.Dict):
            return 'dict'
        elif isinstance(node, ast.Set):
            return 'set'
        elif isinstance(node, ast.Tuple):
            return 'tuple'
        elif isinstance(node, ast.Call):
            if hasattr(node.func, 'id'):
                return node.func.id
        return 'unknown'
    
    def analyze_incomplete_code(self, code, result):
        """Phân tích code không hoàn chỉnh"""
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
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
                    if category == 'functions':
                        result[category][match] = {'line': line_num, 'args': []}
                    elif category == 'classes':
                        result[category][match] = {'line': line_num, 'methods': []}
                    elif category == 'variables':
                        result[category][match] = {'type': 'unknown', 'line': line_num}
                    else:
                        result[category][match] = {'line': line_num}

class SmartSuggestionItem(QListWidgetItem):
    """Custom list widget item với icon và tooltip"""
    
    def __init__(self, text, suggestion_type, docstring=None):
        super().__init__(text)
        self.suggestion_type = suggestion_type
        self.docstring = docstring
        
        # Set icon
        icon_provider = IconProvider()
        self.setIcon(icon_provider.get_icon(suggestion_type))
        
        # Set tooltip
        if docstring:
            self.setToolTip(docstring)

class AutoCompleter:
    """Advanced AutoCompleter với AI và learning capabilities"""
    
    def __init__(self, editor, api_words=None):
        self.editor = editor
        self.suggestions_list = QListWidget(editor.parent())
        self.suggestions_list.setWindowFlags(Qt.ToolTip)
        self.suggestions_list.hide()
        
        # Initialize components
        self.history_manager = HistoryManager()
        self.docstring_provider = DocstringProvider()
        self.snippet_provider = AISnippetProvider()
        
        # Core suggestions
        self.base_suggestions = self.build_base_suggestions()
        if api_words:
            self.base_suggestions.update(api_words)
        
        # Dynamic suggestions
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
        """Xây dựng gợi ý cơ bản với categorization"""
        suggestions = {}
        
        # Python keywords
        for kw in keyword.kwlist:
            suggestions[kw] = {'type': 'keyword', 'priority': 1}
        
        # Built-in functions
        for name in dir(builtins):
            if not name.startswith('_'):
                suggestions[name] = {'type': 'builtin', 'priority': 2}
        
        # Common patterns với type info
        common_patterns = {
            # String methods
            'capitalize': {'type': 'method', 'priority': 3},
            'center': {'type': 'method', 'priority': 4},
            'count': {'type': 'method', 'priority': 3},
            'endswith': {'type': 'method', 'priority': 3},
            'find': {'type': 'method', 'priority': 3},
            'format': {'type': 'method', 'priority': 2},
            'join': {'type': 'method', 'priority': 2},
            'lower': {'type': 'method', 'priority': 2},
            'replace': {'type': 'method', 'priority': 2},
            'split': {'type': 'method', 'priority': 1},
            'strip': {'type': 'method', 'priority': 2},
            'upper': {'type': 'method', 'priority': 2},
            
            # List methods
            'append': {'type': 'method', 'priority': 1},
            'extend': {'type': 'method', 'priority': 3},
            'insert': {'type': 'method', 'priority': 3},
            'remove': {'type': 'method', 'priority': 2},
            'pop': {'type': 'method', 'priority': 2},
            'sort': {'type': 'method', 'priority': 3},
            
            # Dict methods
            'get': {'type': 'method', 'priority': 1},
            'keys': {'type': 'method', 'priority': 2},
            'values': {'type': 'method', 'priority': 2},
            'items': {'type': 'method', 'priority': 1},
            'update': {'type': 'method', 'priority': 3},
            
            # Common modules
            'os': {'type': 'module', 'priority': 1},
            'sys': {'type': 'module', 'priority': 2},
            'json': {'type': 'module', 'priority': 2},
            'datetime': {'type': 'module', 'priority': 2},
            'random': {'type': 'module', 'priority': 3},
            'math': {'type': 'module', 'priority': 3},
            're': {'type': 'module', 'priority': 3},
        }
        
        suggestions.update(common_patterns)
        return suggestions
    
    def setup_events(self):
        """Thiết lập events"""
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.cursorPositionChanged.connect(self.on_cursor_changed)
        self.editor.keyPressEvent = self.wrap_key_press_event(self.editor.keyPressEvent)
        
        self.suggestions_list.itemClicked.connect(self.on_suggestion_selected)
        self.suggestions_list.itemActivated.connect(self.on_suggestion_selected)
        self.suggestions_list.itemEntered.connect(self.on_suggestion_hover)
    
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
            
            original_key_press(event)
            
            if key not in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right, 
                          Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt]:
                self.analysis_timer.start(500)
                self.show_timer.start(100)
        
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
    
    def on_suggestion_hover(self, item):
        """Hiển thị tooltip khi hover"""
        if isinstance(item, SmartSuggestionItem) and item.docstring:
            QToolTip.showText(self.suggestions_list.mapToGlobal(QPoint(0, 0)), item.docstring)
    
    def on_suggestion_selected(self, item):
        """Xử lý khi suggestion được chọn"""
        if isinstance(item, SmartSuggestionItem):
            # Record usage for learning
            self.history_manager.record_completion(
                self.current_word, 
                item.text(), 
                self.get_current_context()
            )
        self.insert_suggestion(item)
    
    def start_code_analysis(self):
        """Bắt đầu phân tích code"""
        if self.analyzer and self.analyzer.isRunning():
            return
        
        code = self.editor.text()
        file_path = getattr(self.editor.parent(), 'file_path', None) if hasattr(self.editor, 'parent') else None
        
        self.analyzer = CodeAnalyzer(code, file_path)
        self.analyzer.analysis_complete.connect(self.on_analysis_complete)
        self.analyzer.start()
    
    def on_analysis_complete(self, analysis):
        """Xử lý kết quả phân tích"""
        self.dynamic_suggestions = analysis
        self.build_context_suggestions()
    
    def build_context_suggestions(self):
        """Xây dựng context-aware suggestions"""
        self.context_suggestions = {}
        
        try:
            line, index = self.editor.getCursorPosition()
            current_line = self.editor.text(line)
            
            if '.' in current_line:
                obj_part = current_line[:index].split('.')[-2].strip()
                self.context_suggestions['object_methods'] = self.get_object_methods(obj_part)
            
            if current_line.strip().startswith('import ') or ' import ' in current_line:
                self.context_suggestions['modules'] = self.get_import_suggestions()
            
            if '(' in current_line and ')' not in current_line[current_line.rfind('('):]:
                func_name = self.extract_function_name(current_line, index)
                self.context_suggestions['parameters'] = self.get_parameter_suggestions(func_name)
                
        except Exception as e:
            pass
    
    def get_current_context(self):
        """Lấy context hiện tại để learning"""
        try:
            line, index = self.editor.getCursorPosition()
            current_line = self.editor.text(line).strip()
            return current_line[:50]  # Chỉ lấy 50 ký tự đầu
        except:
            return ""
    
    def get_object_methods(self, obj_name):
        """Lấy methods cho object với type awareness"""
        suggestions = []
        
        # From dynamic analysis
        if obj_name in self.dynamic_suggestions.get('attributes', {}):
            suggestions.extend(list(self.dynamic_suggestions['attributes'][obj_name]))
        
        # Type-based suggestions
        if obj_name in self.dynamic_suggestions.get('variables', {}):
            var_type = self.dynamic_suggestions['variables'][obj_name].get('type', 'unknown')
            if var_type == 'str':
                suggestions.extend(['split', 'join', 'replace', 'strip', 'lower', 'upper'])
            elif var_type == 'list':
                suggestions.extend(['append', 'extend', 'insert', 'remove', 'pop', 'sort'])
            elif var_type == 'dict':
                suggestions.extend(['get', 'keys', 'values', 'items', 'update', 'pop'])
            elif var_type == 'set':
                suggestions.extend(['add', 'remove', 'discard', 'union', 'intersection'])
        
        return list(set(suggestions))
    
    def get_import_suggestions(self):
        """Lấy gợi ý cho import statements"""
        return [
            'os', 'sys', 'json', 'datetime', 'random', 'math', 're', 'collections',
            'itertools', 'functools', 'pathlib', 'threading', 'multiprocessing',
            'numpy', 'pandas', 'matplotlib', 'seaborn', 'sklearn', 'requests',
            'flask', 'django', 'PyQt5', 'tkinter', 'sqlite3', 'urllib', 'pickle',
            'ast', 'importlib', 'subprocess', 'logging', 'argparse', 'configparser'
        ]
    
    def extract_function_name(self, line, cursor_pos):
        """Trích xuất tên function từ context"""
        try:
            paren_pos = line.rfind('(', 0, cursor_pos)
            if paren_pos == -1:
                return None
            
            func_part = line[:paren_pos].strip()
            func_name = re.search(r'(\w+)', func_part)
            
            return func_name.group(1) if func_name else None
        except:
            return None
    
    def get_parameter_suggestions(self, func_name):
        """Lấy gợi ý parameters cho function"""
        if not func_name:
            return []
        
        signatures = {
            'print': ['sep=" "', 'end="\\n"', 'file=sys.stdout', 'flush=False'],
            'open': ['mode="r"', 'encoding="utf-8"', 'buffering=-1', 'newline=None'],
            'range': ['start', 'stop', 'step'],
            'enumerate': ['start=0'],
            'zip': ['*iterables'],
            'sorted': ['key=None', 'reverse=False'],
            'max': ['key=None', 'default=None'],
            'min': ['key=None', 'default=None'],
            'round': ['ndigits=None'],
            'format': ['*args', '**kwargs'],
            'join': ['iterable'],
            'split': ['sep=None', 'maxsplit=-1'],
            'replace': ['old', 'new', 'count=-1'],
        }
        
        return signatures.get(func_name, [])
    
    def get_current_word(self):
        """Lấy từ hiện tại tại cursor"""
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
        """Lấy tất cả suggestions với ranking thông minh"""
        if len(word) < 1:
            return []
        
        word_lower = word.lower()
        suggestions = {}
        
        # Base suggestions với priority
        for suggestion, info in self.base_suggestions.items():
            if suggestion.lower().startswith(word_lower):
                suggestions[suggestion] = {
                    'type': info['type'],
                    'priority': info['priority'],
                    'source': 'base'
                }
        
        # Dynamic suggestions từ code analysis
        if self.dynamic_suggestions:
            for var_name, var_info in self.dynamic_suggestions.get('variables', {}).items():
                if var_name.lower().startswith(word_lower):
                    suggestions[var_name] = {
                        'type': 'variable',
                        'priority': 1,  # High priority cho local variables
                        'source': 'dynamic'
                    }
            
            for func_name, func_info in self.dynamic_suggestions.get('functions', {}).items():
                if func_name.lower().startswith(word_lower):
                    suggestions[func_name] = {
                        'type': 'function',
                        'priority': 1,
                        'source': 'dynamic'
                    }
            
            for class_name, class_info in self.dynamic_suggestions.get('classes', {}).items():
                if class_name.lower().startswith(word_lower):
                    suggestions[class_name] = {
                        'type': 'class',
                        'priority': 1,
                        'source': 'dynamic'
                    }
            
            for import_name in self.dynamic_suggestions.get('imports', {}).keys():
                if import_name.lower().startswith(word_lower):
                    suggestions[import_name] = {
                        'type': 'module',
                        'priority': 2,
                        'source': 'dynamic'
                    }
        
        # Context suggestions
        for context_type, context_suggestions in self.context_suggestions.items():
            for suggestion in context_suggestions:
                if suggestion.lower().startswith(word_lower):
                    suggestions[suggestion] = {
                        'type': 'method',
                        'priority': 1,  # High priority cho context-aware
                        'source': 'context'
                    }
        
        # AI Snippets
        if word in ['for', 'if', 'def', 'class', 'try', 'with']:
            snippets = self.snippet_provider.get_snippets_for_keyword(word)
            for snippet in snippets:
                suggestions[f"{word} {snippet['name']}"] = {
                    'type': 'ai',
                    'priority': 0,  # Highest priority
                    'source': 'ai',
                    'template': snippet['template']
                }
        
        # Personalized suggestions từ history
        personal_suggestions = self.history_manager.get_personalized_suggestions(word)
        for suggestion in personal_suggestions:
            if suggestion in suggestions:
                suggestions[suggestion]['priority'] -= 1  # Boost priority
            else:
                suggestions[suggestion] = {
                    'type': 'variable',
                    'priority': 1,
                    'source': 'personal'
                }
        
        # Sort by priority (lower = higher priority), then alphabetically
        sorted_suggestions = sorted(
            suggestions.items(),
            key=lambda x: (x[1]['priority'], len(x[0]), x[0].lower())
        )
        
        return sorted_suggestions[:15]  # Top 15 suggestions
    
    def show_suggestions(self):
        """Hiển thị suggestions với icons và tooltips"""
        current_word = self.get_current_word()
        
        if len(current_word) < 1:
            self.hide_suggestions()
            return
        
        suggestions = self.get_all_suggestions(current_word)
        
        if not suggestions:
            self.hide_suggestions()
            return
        
        self.suggestions_list.clear()
        
        for suggestion_text, info in suggestions:
            suggestion_type = info['type']
            docstring = self.docstring_provider.get_docstring(suggestion_text, suggestion_type)
            
            item = SmartSuggestionItem(suggestion_text, suggestion_type, docstring)
            
            # Add metadata
            item.suggestion_info = info
            
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
            
            # Dynamic sizing dựa trên số suggestions
            item_height = 22
            max_height = min(len(suggestions) * item_height + 10, 300)
            self.suggestions_list.resize(280, max_height)
            
            # Style cho modern look
            self.suggestions_list.setStyleSheet("""
                QListWidget {
                    background-color: #252526;
                    border: 1px solid #464647;
                    color: #cccccc;
                    selection-background-color: #094771;
                    outline: none;
                    border-radius: 6px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                }
                QListWidget::item {
                    padding: 4px 8px;
                    border-bottom: 1px solid #2d2d30;
                }
                QListWidget::item:hover {
                    background-color: #2a2d2e;
                }
                QListWidget::item:selected {
                    background-color: #094771;
                    color: white;
                }
            """)
            
            self.suggestions_list.show()
            
            if self.suggestions_list.count() > 0:
                self.suggestions_list.setCurrentRow(0)
            
            self.active = True
            self.current_word = current_word
            
        except Exception as e:
            print(f"Error showing suggestions: {e}")
    
    def hide_suggestions(self):
        """Ẩn suggestions"""
        if self.active:
            self.suggestions_list.hide()
            self.active = False
            self.current_word = ""
    
    def move_selection(self, direction):
        """Di chuyển selection trong list"""
        current_row = self.suggestions_list.currentRow()
        new_row = current_row + direction
        
        if 0 <= new_row < self.suggestions_list.count():
            self.suggestions_list.setCurrentRow(new_row)
    
    def accept_current_suggestion(self):
        """Chấp nhận suggestion hiện tại"""
        current_item = self.suggestions_list.currentItem()
        if current_item:
            self.on_suggestion_selected(current_item)
    
    def insert_suggestion(self, item):
        """Chèn suggestion vào editor"""
        if not item:
            return
        
        suggestion = item.text()
        current_word = self.get_current_word()
        
        try:
            line, index = self.editor.getCursorPosition()
            start_pos = index - len(current_word)
            
            # Check nếu là AI snippet
            if hasattr(item, 'suggestion_info') and item.suggestion_info.get('source') == 'ai':
                template = item.suggestion_info.get('template', suggestion)
                expanded = self.snippet_provider.expand_snippet(template)
                
                # Insert snippet với proper indentation
                current_line_text = self.editor.text(line)
                indent = len(current_line_text) - len(current_line_text.lstrip())
                indented_snippet = self.indent_snippet(expanded, indent)
                
                # Replace current word với snippet
                self.editor.setSelection(line, start_pos, line, index)
                self.editor.replaceSelectedText(indented_snippet)
            else:
                # Normal suggestion
                self.editor.setSelection(line, start_pos, line, index)
                self.editor.replaceSelectedText(suggestion)
            
            self.hide_suggestions()
            
        except Exception as e:
            print(f"Error inserting suggestion: {e}")
    
    def indent_snippet(self, snippet, indent_level):
        """Thêm indentation cho snippet"""
        lines = snippet.split('\n')
        indented_lines = []
        
        for i, line in enumerate(lines):
            if i == 0:
                # First line keeps current indentation
                indented_lines.append(line)
            else:
                # Subsequent lines get proper indentation
                if line.strip():  # Only indent non-empty lines
                    indented_lines.append(' ' * indent_level + line)
                else:
                    indented_lines.append('')
        
        return '\n'.join(indented_lines)
    
    def get_learning_stats(self):
        """Lấy thống kê learning để debug/monitor"""
        try:
            conn = sqlite3.connect(self.history_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM completions")
            total_completions = cursor.fetchone()[0]
            
            cursor.execute("SELECT completion, SUM(frequency) as total FROM completions GROUP BY completion ORDER BY total DESC LIMIT 10")
            top_completions = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_completions': total_completions,
                'top_completions': top_completions
            }
        except Exception as e:
            print(f"Learning stats error: {e}")
            return {'total_completions': 0, 'top_completions': []}
    
    def run(self):
        """Compatibility method"""
        pass

# Utility functions for integration
def setup_smart_autocomplete(editor):
    """Setup advanced autocomplete cho editor"""
    if isinstance(editor, QsciScintilla):
        autocomplete = AutoCompleter(editor)
        editor._autocomplete = autocomplete
        return autocomplete
    return None

def refresh_autocomplete_analysis(editor):
    """Force refresh code analysis"""
    if hasattr(editor, '_autocomplete'):
        editor._autocomplete.start_code_analysis()

def get_autocomplete_stats(editor):
    """Lấy learning statistics"""
    if hasattr(editor, '_autocomplete'):
        return editor._autocomplete.get_learning_stats()
    return None

def clear_autocomplete_history(editor):
    """Clear learning history"""
    if hasattr(editor, '_autocomplete'):
        try:
            conn = sqlite3.connect(editor._autocomplete.history_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM completions")
            cursor.execute("DELETE FROM patterns")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Clear history error: {e}")
            return False
    return False