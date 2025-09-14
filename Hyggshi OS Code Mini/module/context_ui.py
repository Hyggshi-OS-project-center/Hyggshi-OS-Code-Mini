import os
import shutil
import subprocess
from PyQt5.QtWidgets import QMenu, QMessageBox, QApplication, QAction, QInputDialog, QDockWidget
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices, QKeySequence

# Try to import ChatAIWidget to interact with AI panel
try:
    from module.ChatAI import ChatAIWidget
except Exception:
    try:
        from ChatAI import ChatAIWidget
    except Exception:
        ChatAIWidget = None


def create_tree_context_menu(main_window, path):
    """Return a QMenu for the file/folder at `path` inside the Explorer.

    main_window is expected to implement the usual helpers used across the app
    (add_new_tab, open_folder, project_path, model, tree, output_panel).
    """
    menu = QMenu()
    # File-specific actions
    if path and os.path.exists(path):
        # New File / New Folder (relative to selected folder)
        parent_dir = os.path.dirname(path) if os.path.isfile(path) else path
        act_new_file = QAction("New File...", menu)
        act_new_file.triggered.connect(lambda: _create_new_file_dialog(main_window, parent_dir))
        menu.addAction(act_new_file)

        act_new_folder = QAction("New Folder...", menu)
        act_new_folder.triggered.connect(lambda: _create_new_folder_dialog(main_window, parent_dir))
        menu.addAction(act_new_folder)

        # Reveal / Open
        act_reveal = QAction("Reveal in File Explorer", menu)
        act_reveal.setShortcut(QKeySequence("Shift+Alt+R"))
        def reveal():
            try:
                if os.name == 'nt':
                    os.startfile(parent_dir)
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(parent_dir))
            except Exception:
                pass
        act_reveal.triggered.connect(reveal)
        menu.addAction(act_reveal)

        act_terminal = QAction("Open in Integrated Terminal", menu)
        act_terminal.triggered.connect(lambda: _open_in_terminal(main_window, parent_dir))
        menu.addAction(act_terminal)

        menu.addSeparator()

        # Chat/extension actions (placeholders)
        menu.addAction("Add Directory to AI Chat", lambda: QMessageBox.information(main_window, "Info", "Not implemented"))
        menu.addAction("Add Directory to New AI Chat", lambda: QMessageBox.information(main_window, "Info", "Not implemented"))

        menu.addSeparator()

        # Find in folder
        act_find = QAction("Find in Folder...", menu)
        act_find.setShortcut(QKeySequence("Shift+Alt+F"))
        act_find.triggered.connect(lambda: _find_in_folder(main_window, parent_dir))
        menu.addAction(act_find)

        menu.addSeparator()

        # Cut/Copy/Paste
        # File cut/copy/paste using internal clipboard
        act_cut = QAction("Cut", menu)
        act_cut.setShortcut(QKeySequence("Ctrl+X"))
        act_cut.triggered.connect(lambda p=path, mw=main_window: _file_clipboard_set(p, True, mw))
        menu.addAction(act_cut)

        act_copy = QAction("Copy", menu)
        act_copy.setShortcut(QKeySequence("Ctrl+C"))
        act_copy.triggered.connect(lambda p=path, mw=main_window: _file_clipboard_set(p, False, mw))
        menu.addAction(act_copy)

        act_paste = QAction("Paste", menu)
        act_paste.setShortcut(QKeySequence("Ctrl+V"))
        # Enable paste if clipboard has file and target is a folder (or parent dir)
        can_paste = False
        if _file_clipboard is not None:
            if os.path.isdir(parent_dir):
                can_paste = True
        act_paste.setEnabled(can_paste)
        act_paste.triggered.connect(lambda target=parent_dir, mw=main_window: _file_clipboard_paste(target, mw))
        menu.addAction(act_paste)

        menu.addSeparator()

        # Copy path / relative path
        act_copy_path = QAction("Copy Path", menu)
        act_copy_path.setShortcut(QKeySequence("Shift+Alt+C"))
        act_copy_path.triggered.connect(lambda: QApplication.clipboard().setText(path))
        menu.addAction(act_copy_path)

        act_copy_rel = QAction("Copy Relative Path", menu)
        act_copy_rel.setShortcut(QKeySequence("Ctrl+M, Ctrl+Shift+C"))
        def copy_rel():
            root = getattr(main_window, 'project_path', None)
            try:
                if root:
                    rel = os.path.relpath(path, root)
                else:
                    rel = path
                QApplication.clipboard().setText(rel)
            except Exception:
                QApplication.clipboard().setText(path)
        act_copy_rel.triggered.connect(copy_rel)
        menu.addAction(act_copy_rel)

        menu.addSeparator()

        # Run/Debug tests (placeholders)
        menu.addAction("Run Tests", lambda: QMessageBox.information(main_window, "Tests", "Run tests not implemented"))
        menu.addAction("Debug Tests", lambda: QMessageBox.information(main_window, "Tests", "Debug tests not implemented"))
        menu.addAction("Run Tests with Coverage", lambda: QMessageBox.information(main_window, "Tests", "Coverage not implemented"))

        menu.addSeparator()

        # Rename / Delete
        act_rename = QAction("Rename...", menu)
        act_rename.setShortcut(QKeySequence("F2"))
        act_rename.triggered.connect(lambda: _rename_item(main_window, path))
        menu.addAction(act_rename)

        act_delete = QAction("Delete", menu)
        act_delete.setShortcut(QKeySequence("Delete"))
        act_delete.triggered.connect(lambda: _delete_item(main_window, path))
        menu.addAction(act_delete)
    else:
        # Empty-space actions
        menu.addAction("New File", lambda: _create_new_file_dialog(main_window, getattr(main_window, 'project_path', '.')))
        menu.addAction("New Folder", lambda: _create_new_folder_dialog(main_window, getattr(main_window, 'project_path', '.')))
        menu.addAction("Reveal in File Explorer", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(getattr(main_window, 'project_path', '.'))))
    return menu
    return menu


def create_editor_context_menu(editor, main_window=None):
    """Return a QMenu for a code editor widget.

    editor is expected to have cut/copy/paste methods.
    main_window is optional and only used for dialogs/actions needing parent.
    """
    menu = QMenu()

    def act_or_placeholder(name, shortcut, func_name=None, callback=None, tip=None):
        act = QAction(name, menu)
        if shortcut:
            try:
                act.setShortcut(QKeySequence(shortcut))
            except Exception:
                pass
        def run():
            if callback:
                return callback()
            # try main_window helper
            if main_window and func_name and hasattr(main_window, func_name):
                try:
                    getattr(main_window, func_name)(editor)
                    return
                except Exception:
                    pass
            # try editor helper
            if func_name and hasattr(editor, func_name):
                try:
                    getattr(editor, func_name)()
                    return
                except Exception:
                    pass
            QMessageBox.information(main_window or editor, name, tip or f"{name} not implemented")
        act.triggered.connect(run)
        return act

    # Navigation
    menu.addAction(act_or_placeholder("Go to Definition", "F12", callback=lambda: _go_to_definition(editor, main_window), tip='Go to definition'))
    menu.addAction(act_or_placeholder("Go to References", "Shift+F12", callback=lambda: _go_to_references(editor, main_window), tip='Go to references'))
    # Add symbol actions: insert selected text from editor into AI chat
    def _action_add_current():
        _add_symbol_to_current_chat(editor, main_window)

    def _action_add_new():
        _add_symbol_to_new_chat(editor, main_window)

    menu.addAction("Add Symbol to Current Chat", _action_add_current)
    menu.addAction("Add Symbol to New Chat", _action_add_new)

    # Peek submenu
    peek_menu = QMenu("Peek", menu)
    peek_menu.addAction(act_or_placeholder("Peek Definition", None, func_name='peek_definition', tip='Peek not implemented'))
    peek_menu.addAction(act_or_placeholder("Peek References", None, func_name='peek_references', tip='Peek not implemented'))
    menu.addMenu(peek_menu)

    menu.addSeparator()

    menu.addAction(act_or_placeholder("Find All References", "Shift+Alt+F12", callback=lambda: _find_all_references(editor, main_window), tip='Find all references'))
    menu.addSeparator()

    menu.addAction(act_or_placeholder("Rename Symbol", "F2", callback=lambda: _rename_symbol(editor, main_window), tip='Rename symbol in file'))
    menu.addAction(act_or_placeholder("Change All Occurrences", "Ctrl+F2", callback=lambda: _change_all_occurrences(editor, main_window), tip='Replace occurrences in file'))
    menu.addAction(act_or_placeholder("Refactor...", "Ctrl+Shift+R", callback=lambda: QMessageBox.information(main_window or editor, "Refactor", "Refactor not implemented"), tip='Refactor'))
    menu.addAction(act_or_placeholder("Source Action...", None, callback=lambda: QMessageBox.information(main_window or editor, "Source Action", "Source action not implemented"), tip='Source Action'))

    menu.addSeparator()

    # Clipboard
    try:
        act_cut = QAction("Cut", menu)
        act_cut.setShortcut(QKeySequence("Ctrl+X"))
        act_cut.triggered.connect(lambda: editor.cut())
        menu.addAction(act_cut)
        act_copy = QAction("Copy", menu)
        act_copy.setShortcut(QKeySequence("Ctrl+C"))
        act_copy.triggered.connect(lambda: editor.copy())
        menu.addAction(act_copy)
        act_paste = QAction("Paste", menu)
        act_paste.setShortcut(QKeySequence("Ctrl+V"))
        act_paste.triggered.connect(lambda: editor.paste())
        menu.addAction(act_paste)
    except Exception:
        pass

    menu.addSeparator()

    # Command palette
    menu.addAction(act_or_placeholder("Command Palette...", "Ctrl+Shift+P", callback=lambda: _open_command_palette(main_window), tip='Open command palette'))

    return menu


def _create_new_file_dialog(main_window, folder):
    name, ok = QInputDialog.getText(main_window, "New File", "File name:")
    if not ok or not name:
        return
    path = os.path.join(folder, name)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('')
        try:
            main_window.model.setRootPath(getattr(main_window, 'project_path', '.'))
            main_window.tree.setRootIndex(main_window.model.index(getattr(main_window, 'project_path', '.')))
        except Exception:
            pass
    except Exception as e:
        QMessageBox.critical(main_window, "New File", f"Failed to create file: {e}")


def _create_new_folder_dialog(main_window, folder):
    name, ok = QInputDialog.getText(main_window, "New Folder", "Folder name:")
    if not ok or not name:
        return
    path = os.path.join(folder, name)
    try:
        os.makedirs(path, exist_ok=True)
        try:
            main_window.model.setRootPath(getattr(main_window, 'project_path', '.'))
            main_window.tree.setRootIndex(main_window.model.index(getattr(main_window, 'project_path', '.')))
        except Exception:
            pass
    except Exception as e:
        QMessageBox.critical(main_window, "New Folder", f"Failed to create folder: {e}")


def _open_in_terminal(main_window, folder):
    # Try to use existing integrated terminal if app has it, otherwise open system terminal
    try:
        if hasattr(main_window, 'toggle_terminal'):
            main_window.toggle_terminal()
            return
    except Exception:
        pass
    try:
        if os.name == 'nt':
            subprocess.Popen(['cmd', '/K'], cwd=folder)
        else:
            subprocess.Popen(['x-terminal-emulator'], cwd=folder)
    except Exception:
        QMessageBox.information(main_window, 'Terminal', f'Open terminal at: {folder}')


def _find_in_folder(main_window, folder):
    if hasattr(main_window, 'search_dock') and hasattr(main_window, 'search_input'):
        try:
            main_window.search_dock.show()
            main_window.search_input.setText('')
            main_window.search_input.setFocus()
        except Exception:
            QMessageBox.information(main_window, 'Find', f'Open search for: {folder}')
    else:
        QMessageBox.information(main_window, 'Find', f'Find in folder: {folder}')


def _rename_item(main_window, path):
    base = os.path.basename(path)
    new, ok = QInputDialog.getText(main_window, 'Rename', 'New name:', text=base)
    if not ok or not new:
        return
    new_path = os.path.join(os.path.dirname(path), new)
    try:
        os.rename(path, new_path)
        try:
            main_window.model.setRootPath(getattr(main_window, 'project_path', '.'))
            main_window.tree.setRootIndex(main_window.model.index(getattr(main_window, 'project_path', '.')))
        except Exception:
            pass
    except Exception as e:
        QMessageBox.critical(main_window, 'Rename', f'Failed to rename: {e}')


def _delete_item(main_window, path):
    reply = QMessageBox.question(main_window, 'Delete', f'Delete {path}?', QMessageBox.Yes | QMessageBox.No)
    if reply != QMessageBox.Yes:
        return
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        try:
            main_window.model.setRootPath(getattr(main_window, 'project_path', '.'))
            main_window.tree.setRootIndex(main_window.model.index(getattr(main_window, 'project_path', '.')))
        except Exception:
            pass
    except Exception as e:
        QMessageBox.critical(main_window, 'Delete', f'Failed to delete: {e}')


# Simple file clipboard helpers (copy/cut/paste)
_file_clipboard = None
_file_clipboard_cut = False

def _file_clipboard_set(path, cut=False, main_window=None):
    global _file_clipboard, _file_clipboard_cut
    _file_clipboard = path
    _file_clipboard_cut = bool(cut)
    if main_window:
        try:
            if _file_clipboard_cut:
                main_window.output_panel.append_text(f"[Clipboard] Cut: {_file_clipboard}\n")
            else:
                main_window.output_panel.append_text(f"[Clipboard] Copied: {_file_clipboard}\n")
        except Exception:
            pass


def _file_clipboard_paste(target_folder, main_window=None):
    global _file_clipboard, _file_clipboard_cut
    if not _file_clipboard:
        QMessageBox.information(main_window, 'Paste', 'Clipboard is empty.')
        return
    try:
        basename = os.path.basename(_file_clipboard)
        dest = os.path.join(target_folder, basename)
        if _file_clipboard_cut:
            shutil.move(_file_clipboard, dest)
            _file_clipboard = None
            _file_clipboard_cut = False
        else:
            if os.path.isdir(_file_clipboard):
                shutil.copytree(_file_clipboard, dest)
            else:
                shutil.copy2(_file_clipboard, dest)
        try:
            main_window.output_panel.append_text(f"[Clipboard] Pasted to: {dest}\n")
        except Exception:
            pass
    except Exception as e:
        QMessageBox.critical(main_window, 'Paste', f'Paste failed: {e}')


def _add_symbol_to_current_chat(editor, main_window):
    """Get selection from editor and place it into the existing AI panel input box."""
    try:
        # Try to get selection from QsciScintilla or QTextEdit
        sel = None
        if hasattr(editor, 'selectedText'):
            sel = editor.selectedText()
        elif hasattr(editor, 'textCursor'):
            sel = editor.textCursor().selectedText()
        if not sel:
            QMessageBox.information(main_window, 'Add Symbol', 'No text selected in editor.')
            return

        # Ensure chat panel exists
        if not hasattr(main_window, 'chat_ai_widget') or main_window.chat_ai_widget is None:
            try:
                # toggle creates widget if missing
                if hasattr(main_window, 'toggle_chat_ai_panel'):
                    main_window.toggle_chat_ai_panel()
            except Exception:
                pass

        widget = getattr(main_window, 'chat_ai_widget', None)
        if widget is None and hasattr(main_window, 'chat_ai_dock') and main_window.chat_ai_dock is not None:
            try:
                widget = main_window.chat_ai_dock.widget()
            except Exception:
                widget = None

        if widget and hasattr(widget, 'input_box'):
            widget.input_box.setText(sel)
            widget.input_box.setFocus()
            try:
                widget.update_send_enabled()
            except Exception:
                pass
            # Auto-send after inserting
            try:
                if hasattr(widget, 'on_send'):
                    widget.on_send()
                elif hasattr(widget, 'send_btn') and hasattr(widget.send_btn, 'click'):
                    widget.send_btn.click()
            except Exception:
                pass
            QMessageBox.information(main_window, 'Add Symbol', 'Selected text added to AI input box and sent to AI.')
        else:
            QMessageBox.information(main_window, 'Add Symbol', 'AI panel not available.')
    except Exception as e:
        QMessageBox.critical(main_window, 'Add Symbol', f'Error: {e}')


def _add_symbol_to_new_chat(editor, main_window):
    """Create a new AI panel and put selected text into its input box."""
    try:
        sel = None
        if hasattr(editor, 'selectedText'):
            sel = editor.selectedText()
        elif hasattr(editor, 'textCursor'):
            sel = editor.textCursor().selectedText()
        if not sel:
            QMessageBox.information(main_window, 'Add Symbol', 'No text selected in editor.')
            return

        if ChatAIWidget is None:
            QMessageBox.information(main_window, 'Add Symbol', 'ChatAIWidget not available.')
            return

        dock = QDockWidget('AI Assistant (New)', main_window)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        widget = ChatAIWidget(main_window)
        widget.input_box.setText(sel)
        widget.update_send_enabled()
        dock.setWidget(widget)
        main_window.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.show()
        # Auto-send on new chat
        try:
            if hasattr(widget, 'on_send'):
                widget.on_send()
            elif hasattr(widget, 'send_btn') and hasattr(widget.send_btn, 'click'):
                widget.send_btn.click()
        except Exception:
            pass
    except Exception as e:
        QMessageBox.critical(main_window, 'Add Symbol', f'Error creating new AI panel: {e}')


def _go_to_definition(editor, main_window):
    """Simple go-to-definition: find word under cursor and search in open files or project."""
    try:
        word = None
        if hasattr(editor, 'selectedText'):
            word = editor.selectedText() or None
        if not word and hasattr(editor, 'wordUnderCursor'):
            try:
                word = editor.wordUnderCursor()
            except Exception:
                word = None
        if not word:
            QMessageBox.information(main_window, 'Go to Definition', 'No symbol selected or under cursor.')
            return
        # Naive search: look in currently open tabs for definition (def/class or var)
        mw = main_window
        for i in range(mw.tabs.count()):
            tab = mw.tabs.widget(i)
            if hasattr(tab, 'editor'):
                text = tab.editor.text()
                if f"def {word}" in text or f"class {word}" in text or f"{word} =" in text:
                    mw.tabs.setCurrentIndex(i)
                    QMessageBox.information(main_window, 'Go to Definition', f'Found in {mw.tabs.tabText(i)}')
                    return
        QMessageBox.information(main_window, 'Go to Definition', f'Definition for {word} not found in open tabs.')
    except Exception as e:
        QMessageBox.critical(main_window, 'Go to Definition', f'Error: {e}')


def _go_to_references(editor, main_window):
    try:
        # Reuse simple search for occurrences of selected word
        if hasattr(editor, 'selectedText'):
            word = editor.selectedText()
        else:
            word = None
        if not word:
            QMessageBox.information(main_window, 'Find References', 'No symbol selected.')
            return
        found = []
        mw = main_window
        for i in range(mw.tabs.count()):
            tab = mw.tabs.widget(i)
            if hasattr(tab, 'editor'):
                text = tab.editor.text()
                if word in text:
                    found.append(mw.tabs.tabText(i))
        QMessageBox.information(main_window, 'References', f'Found in: {", ".join(found)}' if found else f'No references found for {word}')
    except Exception as e:
        QMessageBox.critical(main_window, 'Find References', f'Error: {e}')


def _find_all_references(editor, main_window):
    # Alias to _go_to_references
    return _go_to_references(editor, main_window)


def _rename_symbol(editor, main_window):
    try:
        if hasattr(editor, 'selectedText'):
            word = editor.selectedText()
        else:
            word = None
        if not word:
            QMessageBox.information(main_window, 'Rename', 'No symbol selected to rename.')
            return
        new, ok = QInputDialog.getText(main_window, 'Rename Symbol', f'Rename "{word}" to:')
        if not ok or not new:
            return
        # Replace whole-word occurrences in current tab only
        import re
        tab = main_window.tabs.currentWidget()
        if hasattr(tab, 'editor'):
            txt = tab.editor.text()
            pattern = r"\b" + re.escape(word) + r"\b"
            new_txt, count = re.subn(pattern, new, txt)
            tab.editor.setText(new_txt)
            QMessageBox.information(main_window, 'Rename', f'Renamed {count} occurrences in current tab.')
    except Exception as e:
        QMessageBox.critical(main_window, 'Rename', f'Error: {e}')


def _change_all_occurrences(editor, main_window):
    # Simple replace across open tabs
    try:
        if hasattr(editor, 'selectedText'):
            word = editor.selectedText()
        else:
            word = None
        if not word:
            QMessageBox.information(main_window, 'Change All', 'No symbol selected to replace.')
            return
        new, ok = QInputDialog.getText(main_window, 'Change All Occurrences', f'Replace "{word}" with:')
        if not ok:
            return
        mw = main_window
        count = 0
        import re
        pattern = r"\b" + re.escape(word) + r"\b"
        for i in range(mw.tabs.count()):
            tab = mw.tabs.widget(i)
            if hasattr(tab, 'editor'):
                txt = tab.editor.text()
                new_txt, replaced = re.subn(pattern, new, txt)
                if replaced:
                    tab.editor.setText(new_txt)
                    count += 1
        QMessageBox.information(main_window, 'Change All', f'Replaced in {count} tabs.')
    except Exception as e:
        QMessageBox.critical(main_window, 'Change All', f'Error: {e}')


def _open_command_palette(main_window):
    try:
        cmd, ok = QInputDialog.getText(main_window, 'Command Palette', 'Enter command:')
        if not ok or not cmd:
            return
        QMessageBox.information(main_window, 'Command Palette', f'Command entered: {cmd}')
    except Exception as e:
        QMessageBox.critical(main_window, 'Command Palette', f'Error: {e}')


