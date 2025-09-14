"""
QsciLexer.py - Wrapper for QScintilla lexers for Hyggshi OS Code Mini
"""

from PyQt5.Qsci import QsciLexerPython, QsciLexerCPP, QsciLexerJavaScript, QsciLexerMarkdown, QsciLexerHTML, QsciLexerCSS, QsciLexerBash, QsciLexerJSON, QsciLexerJava, QsciLexerCSharp, QsciLexerRuby, QsciLexerXML, QsciLexerYAML, QsciLexerSQL

LEXER_MAP = {
    "python": QsciLexerPython,
    "cpp": QsciLexerCPP,
    "c++": QsciLexerCPP,
    "js": QsciLexerJavaScript,
    "javascript": QsciLexerJavaScript,
    "md": QsciLexerMarkdown,
    "markdown": QsciLexerMarkdown,
    "html": QsciLexerHTML,
    "css": QsciLexerCSS,
    "bash": QsciLexerBash,
    "sh": QsciLexerBash,
    "json": QsciLexerJSON,
    "java": QsciLexerJava,
    "csharp": QsciLexerCSharp,
    "cs": QsciLexerCSharp,
    "ruby": QsciLexerRuby,
    "xml": QsciLexerXML,
    "yaml": QsciLexerYAML,
    "yml": QsciLexerYAML,
    "sql": QsciLexerSQL,
}

def get_lexer(language: str, parent=None):
    """
    Return a QScintilla lexer instance for the given language string.
    """
    key = language.lower()
    lexer_cls = LEXER_MAP.get(key)
    if lexer_cls:
        return lexer_cls(parent)
    return