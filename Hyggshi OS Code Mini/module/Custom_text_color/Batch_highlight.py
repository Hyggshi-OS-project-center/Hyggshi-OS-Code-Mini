from PyQt5.Qsci import QsciScintilla
from PyQt5.QtGui import QColor

def apply_batch_highlight(editor: QsciScintilla):
    """
    Highlight Batch: keyword, variable, comment, string, number.
    """
    editor.setLexer(None)
    editor.SendScintilla(editor.SCI_STYLESETFONT, 0, b"Consolas")
    editor.SendScintilla(editor.SCI_STYLESETSIZE, 0, 15)
    editor.SendScintilla(editor.SCI_STYLESETFORE, 0, QColor("#eaeaea"))

    style_map = {
        1: QColor("#569CD6"),   # Keyword
        2: QColor("#CE9178"),   # String
        3: QColor("#519730"),   # Comment
        4: QColor("#B5CEA8"),   # Number
        5: QColor("#D19A66"),   # Variable
        6: QColor("#D4D4D4"),   # Default
    }
    for style, color in style_map.items():
        editor.SendScintilla(editor.SCI_STYLESETFORE, style, color)
        editor.SendScintilla(editor.SCI_STYLESETFONT, style, b"Consolas")
        editor.SendScintilla(editor.SCI_STYLESETSIZE, style, 15)

    batch_keywords = [
        "echo", "set", "if", "else", "goto", "call", "pause", "exit", "rem", "for", "in", "do", "not", "exist", "copy", "move", "del", "type", "cd", "md", "rd", "dir"
    ]

    for i in range(editor.lines()):
        text = editor.text(i)
        start_pos = editor.SendScintilla(editor.SCI_POSITIONFROMLINE, i)
        # Comment
        if text.strip().lower().startswith("rem") or text.strip().startswith("::"):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 3)
        # Variable
        elif "%" in text:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 5)
        # String
        elif '"' in text:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 2)
        # Number
        elif any(char.isdigit() for char in text):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 4)
        # Keyword
        elif any(word in text.lower().split() for word in batch_keywords):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 1)
        # Mặc định
        else:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 0)