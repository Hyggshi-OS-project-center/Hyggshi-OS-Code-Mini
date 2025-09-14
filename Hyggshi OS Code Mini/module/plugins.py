import os
import configparser
from PyQt5.Qsci import *

class PluginManager:
    def __init__(self, plugin_dir="plugins"):
        self.plugin_dir = plugin_dir
        self.languages = {}  # name -> {ext, lexer}
        self.interface_language = "English"
        self.load_plugins()

    def load_plugins(self):
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)

        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".hsi"):
                self.load_hsi_file(os.path.join(self.plugin_dir, filename))

    def load_hsi_file(self, path):
        config = configparser.ConfigParser()
        config.read(path)

        # Load programming language
        if "language" in config:
            name = config["language"].get("name")
            ext = config["language"].get("extension")
            lexer_name = config["language"].get("lexer")

            lexer = self.get_lexer_from_string(lexer_name)
            if name and ext and lexer:
                self.languages[name] = {
                    "extension": ext,
                    "lexer": lexer
                }

    def get_lexer_from_string(self, name):
        lexer_map = {
            "QsciLexerPython": QsciLexerPython,
            "QsciLexerCPP": QsciLexerCPP,
            "QsciLexerJavaScript": QsciLexerJavaScript,
            "QsciLexerHTML": QsciLexerHTML,
            "QsciLexerJava": QsciLexerJava,
            "QsciLexerJSON": QsciLexerJSON,
            "QsciLexerLua": QsciLexerLua,
            "QsciLexerPHP": QsciLexerPHP  # pyright: ignore[reportUndefinedVariable]
        }
        cls = lexer_map.get(name, None)
        return cls() if cls else None

    def get_interface_language(self):
        return self.interface_language

    def get_supported_languages(self):
        return self.languages
