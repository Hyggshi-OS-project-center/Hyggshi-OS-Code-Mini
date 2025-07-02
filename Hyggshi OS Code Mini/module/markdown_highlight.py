
from PyQt5.Qsci import QsciScintilla
from PyQt5.QtGui import QColor

def apply_markdown_highlight(editor: QsciScintilla):
    editor.setLexer(None)
    # Define styles
    editor.SendScintilla(editor.SCI_STYLESETFORE, 1, QColor("#569CD6"))  # Heading
    editor.SendScintilla(editor.SCI_STYLESETFORE, 2, QColor("#D19A66"))  # Bold
    editor.SendScintilla(editor.SCI_STYLESETFORE, 3, QColor("#9CDCFE"))  # List or code
    editor.SendScintilla(editor.SCI_STYLESETFORE, 4, QColor("#C586C0"))  # Inline code
    editor.SendScintilla(editor.SCI_STYLESETFORE, 5, QColor("#FFFFFF"))
    editor.SendScintilla(editor.SCI_STYLESETFORE, 6, QColor("#CE9178"))  # Blockquote
    editor.SendScintilla(editor.SCI_STYLESETFORE, 7, QColor("#608B4E"))
    editor.SendScintilla(editor.SCI_STYLESETFORE, 8, QColor("#D7BA7D"))  # Link
    editor.SendScintilla(editor.SCI_STYLESETFORE, 9, QColor("#4EC9B0"))
    editor.SendScintilla(editor.SCI_STYLESETFORE, 10, QColor("#C586C0"))  # Image
    editor.SendScintilla(editor.SCI_STYLESETFORE, 11, QColor("#000000FF"))  # Horizontal rule
    editor.SendScintilla(editor.SCI_STYLESETFORE, 12, QColor("#9CDCFE"))  # Task list
    editor.SendScintilla(editor.SCI_STYLESETFORE, 13, QColor("#D7BA7D"))  # Strikethrough
    editor.SendScintilla(editor.SCI_STYLESETFORE, 14, QColor("#CE9178"))  # Footnote
    # Cải thiện font và màu mặc định
    font_color = QColor("#FFFFFF")  # Màu sáng hơn (giống GitHub Dark)
    editor.SendScintilla(editor.SCI_STYLESETFORE, 0, font_color)
    editor.SendScintilla(editor.SCI_STYLESETSIZE, 0, 15)  # Tăng kích cỡ chữ
    editor.SendScintilla(editor.SCI_STYLESETFONT, 0, b"Consolas")  # Font dễ đọc

    # Các style phụ nếu cần:
    editor.SendScintilla(editor.SCI_STYLESETSIZE, 1, 13)
    editor.SendScintilla(editor.SCI_STYLESETSIZE, 2, 13)
    editor.SendScintilla(editor.SCI_STYLESETSIZE, 3, 13)


    # Apply styles line by line
    for i in range(editor.lines()):
        text = editor.text(i)
        start_pos = editor.SendScintilla(editor.SCI_POSITIONFROMLINE, i)


        if text.strip().startswith("#"):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 1)
        elif "**" in text:
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 2)
        elif text.strip().startswith("- ") or text.strip().startswith("* "):
            editor.SendScintilla(editor.SCI_STARTSTYLING, start_pos, 31)
            editor.SendScintilla(editor.SCI_SETSTYLING, len(text), 3)
