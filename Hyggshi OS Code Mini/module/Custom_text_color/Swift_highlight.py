from PyQt5.Qsci import QsciScintilla
from PyQt5.QtGui import QColor

def apply_swift_highlight(editor: QsciScintilla):
    """
    Highlight Swift: keyword, string, comment, number, type.
    """
    editor.setLexer(None)
    editor.SendScintilla(editor.SCI_STYLESETFONT, 0, b"Consolas")
    editor.SendScintilla(editor.SCI_STYLESETSIZE, 0, 15)
    editor.SendScintilla(editor.SCI_STYLESETFORE, 0, QColor("#eaeaea"))

    style_map = {
        1: QColor("#008CFF"),   # Keyword
        2: QColor("#BD4C20"),   # String
        3: QColor("#6A9955"),   # Comment
        4: QColor("#81F344"),   # Number
        5: QColor("#4EC9B9"),   # Type
        6: QColor("#D4D4D4"),   # Default
    }
    for style, color in style_map.items():
        editor.SendScintilla(editor.SCI_STYLESETFORE, style, color)
        editor.SendScintilla(editor.SCI_STYLESETFONT, style, b"Consolas")
        editor.SendScintilla(editor.SCI_STYLESETSIZE, style, 15)

    swift_keywords = [
        "func", "var", "let", "class", "struct", "enum", "protocol", "extension", "import",
        "return", "if", "else", "for", "while", "do", "switch", "case", "break", "continue",
        "in", "is", "as", "try", "catch", "throw", "self", "super", "guard", "defer", "where"
    ]
    swift_types = [
        "Int", "Double", "Float", "Bool", "String", "Character", "Array", "Dictionary", "Set", "Any", "Optional"
    ]

    for i in range(editor.lines()):
        text = editor.text(i)
        start_pos = editor.SendScintilla(editor.SCI_POSITIONFROMLINE, i)
        # Comment
        if text.strip().startswith("//") or text.strip().startswith("/*"):
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
        elif any(t in text.split() for t in swift_types):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 5)
        # Keyword
        elif any(word in text.split() for word in swift_keywords):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 1)
        # Mặc định
        else:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 0)