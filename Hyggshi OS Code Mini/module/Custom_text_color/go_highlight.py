from PyQt5.Qsci import QsciScintilla
from PyQt5.QtGui import QColor

def apply_go_highlight(editor: QsciScintilla):
    """
    Highlight Go: keyword, string, comment, number, type.
    """
    editor.setLexer(None)
    editor.SendScintilla(editor.SCI_STYLESETFONT, 0, b"Consolas")
    editor.SendScintilla(editor.SCI_STYLESETSIZE, 0, 15)
    editor.SendScintilla(editor.SCI_STYLESETFORE, 0, QColor("#eaeaea"))

    style_map = {
        1: QColor("#569CD6"),   # Keyword
        2: QColor("#CE9178"),   # String
        3: QColor("#6A9955"),   # Comment
        4: QColor("#B5CEA8"),   # Number
        5: QColor("#4EC9B0"),   # Type
    }
    for style, color in style_map.items():
        editor.SendScintilla(editor.SCI_STYLESETFORE, style, color)
        editor.SendScintilla(editor.SCI_STYLESETFONT, style, b"Consolas")
        editor.SendScintilla(editor.SCI_STYLESETSIZE, style, 15)

    go_keywords = [
        "func", "var", "const", "type", "struct", "interface", "package", "import",
        "return", "if", "else", "for", "range", "switch", "case", "break", "continue",
        "go", "defer", "map", "chan", "select", "default", "fallthrough", "goto"
    ]
    go_types = [
        "int", "int8", "int16", "int32", "int64", "uint", "uint8", "uint16", "uint32", "uint64",
        "float32", "float64", "complex64", "complex128", "byte", "rune", "string", "bool", "error"
    ]

    for i in range(editor.lines()):
        text = editor.text(i)
        start_pos = editor.SendScintilla(editor.SCI_POSITIONFROMLINE, i)
        # Comment
        if text.strip().startswith("//"):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 3)
        # String
        elif '"' in text or "'" in text:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 2)
        # Number
        elif any(char.isdigit() for char in text):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 4)
        # Type
        elif any(t in text.split() for t in go_types):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 5)
        # Keyword
        elif any(word in text.split() for word in go_keywords):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 1)
        # Mặc định
        else:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 0)