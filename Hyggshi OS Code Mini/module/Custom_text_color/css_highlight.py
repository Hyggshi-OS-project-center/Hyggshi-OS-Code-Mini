from PyQt5.Qsci import QsciScintilla
from PyQt5.QtGui import QColor

def apply_css_highlight(editor: QsciScintilla):
    """
    Highlight CSS: selector, property, value, comment.
    """
    editor.setLexer(None)
    editor.SendScintilla(editor.SCI_STYLESETFONT, 0, b"Consolas")
    editor.SendScintilla(editor.SCI_STYLESETSIZE, 0, 15)
    editor.SendScintilla(editor.SCI_STYLESETFORE, 0, QColor("#eaeaea"))

    style_map = {
        1: QColor("#569CD6"),   # Selector
        2: QColor("#D19A66"),   # Property
        3: QColor("#9CDCFE"),   # Value
        4: QColor("#6A9955"),   # Comment
    }
    for style, color in style_map.items():
        editor.SendScintilla(editor.SCI_STYLESETFORE, style, color)
        editor.SendScintilla(editor.SCI_STYLESETFONT, style, b"Consolas")
        editor.SendScintilla(editor.SCI_STYLESETSIZE, style, 15)

    for i in range(editor.lines()):
        text = editor.text(i)
        start_pos = editor.SendScintilla(editor.SCI_POSITIONFROMLINE, i)
        # Comment
        if "/*" in text and "*/" in text:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 4)
        # Selector
        elif "{" in text:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 1)
        # Property + Value
        elif ":" in text and ";" in text:
            prop_end = text.find(":")
            val_end = text.find(";")
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, prop_end, 2)
            editor.SendScintilla(editor.SCI_SETSTYLING, val_end - prop_end, 3)
        # Mặc định
        else:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 0)