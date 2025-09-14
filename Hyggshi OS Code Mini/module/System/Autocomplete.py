"""
Autocomplete.py - Simple code autocompletion for QScintilla editor in Hyggshi OS Code Mini
"""

from PyQt5.Qsci import QsciScintilla, QsciAPIs
from pygments.lexers.python import PythonLexer

class AutocompleteManager:
    def __init__(self, editor: QsciScintilla, api_words=None):
        self.editor = editor
        self.api = QsciAPIs(self.editor.lexer())
        if api_words:
            for word in api_words:
                self.api.add(word)
        self.api.prepare()
        self.setup_editor()
        self.editor.textChanged.connect(self._on_text_changed)

    def setup_editor(self):
        self.editor.setAutoCompletionSource(QsciScintilla.AcsAll)
        self.editor.setAutoCompletionCaseSensitivity(False)
        self.editor.setAutoCompletionThreshold(1)
        self.editor.setAutoCompletionReplaceWord(True)
        self.editor.setAutoCompletionShowSingle(True)

    def update_api_words(self, words):
        self.api.clear()
        for word in words:
            self.api.add(word)
        self.api.prepare()

    def _on_text_changed(self):
        # Hiển thị gợi ý khi gõ ký tự (nếu không phải xóa/backspace)
        if self.editor.hasFocus():
            self.editor.autoCompleteFromAll()

def setup_editor_with_autocomplete(editor: QsciScintilla, keywords=None):
    lexer = PythonLexer()
    editor.setLexer(lexer)
    autocomplete = AutocompleteManager(editor, api_words=keywords)