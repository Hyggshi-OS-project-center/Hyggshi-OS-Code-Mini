"""
shortcut.py - Global and local shortcut manager for Hyggshi OS Code Mini
"""

from PyQt5.QtWidgets import QShortcut, QWidget
from PyQt5.QtGui import QKeySequence

class ShortcutManager:
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.shortcuts = {}

    def add_shortcut(self, keyseq, callback, name=None):
        """Add a shortcut (e.g. 'Ctrl+S') and connect to callback."""
        shortcut = QShortcut(QKeySequence(keyseq), self.parent)
        shortcut.activated.connect(callback)
        if name:
            self.shortcuts[name] = shortcut
        else:
            self.shortcuts[keyseq] = shortcut

    def remove_shortcut(self, keyseq_or_name):
        """Remove a shortcut by key sequence or name."""
        shortcut = self.shortcuts.pop(keyseq_or_name, None)
        if shortcut:
            shortcut.setEnabled(False)
            del shortcut

    def clear(self):
        """Remove all shortcuts."""
        for sc in self.shortcuts.values():
            sc.setEnabled(False)

def example_usage(parent_widget):
    sm = ShortcutManager(parent_widget)
    sm.add_shortcut("Ctrl+S", parent_widget.save_current_file, name="save_file")