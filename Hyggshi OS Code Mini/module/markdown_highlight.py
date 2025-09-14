from PyQt5.Qsci import QsciScintilla
from PyQt5.QtGui import QColor

def apply_markdown_highlight(editor: QsciScintilla):
    """
    Đơn giản hóa highlight Markdown cho QsciScintilla.
    Chỉ tô màu heading, bold, list, code, link, blockquote.
    """
    editor.setLexer(None)
    # Đặt font và màu mặc định
    editor.SendScintilla(editor.SCI_STYLESETFONT, 0, b"Consolas")
    editor.SendScintilla(editor.SCI_STYLESETSIZE, 0, 15)
    editor.SendScintilla(editor.SCI_STYLESETFORE, 0, QColor("#eaeaea"))

    # Định nghĩa màu cho các style
    style_map = {
        1: QColor("#569CD6"),   # Heading
        2: QColor("#D19A66"),   # Bold
        3: QColor("#9CDCFE"),   # List
        4: QColor("#C586C0"),   # Inline code
        5: QColor("#D7BA7D"),   # Link
        6: QColor("#CE9178"),   # Blockquote
    }
    for style, color in style_map.items():
        editor.SendScintilla(editor.SCI_STYLESETFORE, style, color)
        editor.SendScintilla(editor.SCI_STYLESETFONT, style, b"Consolas")
        editor.SendScintilla(editor.SCI_STYLESETSIZE, style, 15)

    # Highlight từng dòng
    for i in range(editor.lines()):
        text = editor.text(i)
        start_pos = editor.SendScintilla(editor.SCI_POSITIONFROMLINE, i)
        # Heading
        if text.strip().startswith("#"):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 1)
        # Bold
        elif "**" in text or "__" in text:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 2)
        # List
        elif text.strip().startswith("- ") or text.strip().startswith("* "):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 3)
        # Inline code
        elif "`" in text:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 4)
        # Link
        elif "](" in text:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 5)
        # Blockquote
        elif text.strip().startswith(">"):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 6)
        # Mặc định
        else:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 0)
