# UI_UX.py - Improved VS Code Font Configuration
# Cải thiện cấu hình font để giống VS Code hơn

from PyQt5.QtWidgets import QApplication, QStyleFactory, QTextEdit, QPlainTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette, QFont, QFontDatabase, QTextCharFormat

# VS Code Font Configuration - Cải thiện
VSCODE_FONT_CONFIG = {
    # Font families theo độ ưu tiên của VS Code
    'primary_fonts': [
        'Consolas',           # Windows default
        'SF Mono',            # macOS
        'Monaco',             # macOS backup
        'Menlo',              # macOS older
        'Ubuntu Mono',        # Linux
        'Liberation Mono',    # Linux
        'DejaVu Sans Mono',   # Linux backup
        'Courier New',        # Universal fallback
        'monospace'           # System fallback
    ],
    
    # Font sizes for different components
    'editor_size': 14,        # Editor main content (tăng từ 9 lên 14)
    'ui_size': 9,            # UI elements
    'line_height': 1.6,      # Line height multiplier
    
    # Font weights
    'normal_weight': QFont.Normal,
    'bold_weight': QFont.Bold,
    
    # Font rendering hints
    'antialiasing': True,
    'subpixel_antialiasing': True,
}

def set_dark_theme():
    """Dummy implementation of set_dark_theme."""
    print("Dark theme applied.")

def get_best_monospace_font():
    """
    Tìm font monospace tốt nhất có sẵn trên hệ thống.
    Theo thứ tự ưu tiên của VS Code.
    """
    font_db = QFontDatabase()
    available_fonts = font_db.families()
    
    # Kiểm tra từng font theo thứ tự ưu tiên
    for font_name in VSCODE_FONT_CONFIG['primary_fonts']:
        if font_name in available_fonts:
            return font_name
    
    # Nếu không tìm thấy, tìm font monospace bất kỳ
    for font_name in available_fonts:
        if font_db.isFixedPitch(font_db.font(font_name, "", 12)):
            return font_name
    
    # Fallback cuối cùng
    return 'Courier New'

def create_vscode_font(size=None, bold=False, italic=False):
    """
    Tạo font object với cấu hình VS Code chuẩn.
    """
    if size is None:
        size = VSCODE_FONT_CONFIG['editor_size']
    
    font = QFont()
    
    # Đặt font family
    best_font = get_best_monospace_font()
    font.setFamily(best_font)
    
    # Cấu hình font
    font.setPointSize(size)
    font.setStyleHint(QFont.Monospace)
    font.setFixedPitch(True)
    
    # Weight và style
    if bold:
        font.setWeight(VSCODE_FONT_CONFIG['bold_weight'])
    else:
        font.setWeight(VSCODE_FONT_CONFIG['normal_weight'])
    
    font.setItalic(italic)
    
    # Font rendering quality
    if VSCODE_FONT_CONFIG['antialiasing']:
        font.setStyleStrategy(QFont.PreferAntialias)
    
    return font

def set_vscode_font_improved(app=None):
    """
    Cải thiện cấu hình font cho toàn bộ ứng dụng.
    """
    if app is None:
        app = QApplication.instance()
    
    if app is not None:
        # Font cho UI elements
        ui_font = create_vscode_font(VSCODE_FONT_CONFIG['ui_size'])
        app.setFont(ui_font)
        
        print(f"✓ Đã áp dụng font: {ui_font.family()}")
        print(f"✓ Kích thước UI: {VSCODE_FONT_CONFIG['ui_size']}pt")
        print(f"✓ Kích thước Editor: {VSCODE_FONT_CONFIG['editor_size']}pt")

def apply_editor_font(text_widget):
    """
    Áp dụng font cụ thể cho text editor (QTextEdit hoặc QPlainTextEdit).
    """
    if isinstance(text_widget, (QTextEdit, QPlainTextEdit)):
        editor_font = create_vscode_font(VSCODE_FONT_CONFIG['editor_size'])
        text_widget.setFont(editor_font)
        
        # Cấu hình line height và spacing
        cursor = text_widget.textCursor()
        block_format = cursor.blockFormat()
        block_format.setLineHeight(
            VSCODE_FONT_CONFIG['line_height'] * 100,  # QTextBlockFormat expects percentage
            block_format.ProportionalHeight
        )
        cursor.setBlockFormat(block_format)
        
        print(f"✓ Đã áp dụng font editor: {editor_font.family()} - {editor_font.pointSize()}pt")

def get_vscode_stylesheet_improved():
    """
    CSS stylesheet cải thiện với font configuration tốt hơn.
    """
    best_font = get_best_monospace_font()
    editor_size = VSCODE_FONT_CONFIG['editor_size']
    ui_size = VSCODE_FONT_CONFIG['ui_size']
    line_height = VSCODE_FONT_CONFIG['line_height']
    
    return f"""
    /* VS Code Style Stylesheet - Improved Font */
    
    /* Global font configuration */
    * {{
        font-family: '{best_font}', 'Consolas', 'SF Mono', 'Monaco', monospace;
    }}
    
    /* Main window */
    QMainWindow {{
        background-color: #1e1e1e;
        color: #cccccc;
        font-family: '{best_font}', 'Consolas', monospace;
        font-size: {ui_size}pt;
    }}
    
    /* Menu bar với font rõ ràng */
    QMenuBar {{
        background-color: #3c3c3c;
        color: #cccccc;
        border: none;
        padding: 2px;
        font-family: '{best_font}', 'Consolas', monospace;
        font-size: {ui_size}pt;
        font-weight: normal;
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: 6px 12px;
        border-radius: 3px;
        font-weight: normal;
    }}
    
    QMenuBar::item:selected {{
        background-color: #2a2d2e;
        color: #ffffff;
    }}
    
    /* Menu dropdown */
    QMenu {{
        background-color: #252526;
        color: #cccccc;
        border: 1px solid #464647;
        padding: 4px;
        font-family: '{best_font}', 'Consolas', monospace;
        font-size: {ui_size}pt;
    }}
    
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 3px;
    }}
    
    QMenu::item:selected {{
        background-color: #264f78;
        color: #ffffff;
    }}
    
    /* Tab widget */
    QTabBar::tab {{
        background-color: #2d2d30;
        color: #969696;
        padding: 8px 16px;
        border: 1px solid #464647;
        border-bottom: none;
        font-family: '{best_font}', 'Consolas', monospace;
        font-size: {ui_size}pt;
        min-width: 80px;
    }}
    
    QTabBar::tab:selected {{
        background-color: #1e1e1e;
        color: #cccccc;
        border-bottom: 2px solid #569cd6;
        font-weight: normal;
    }}
    
    QTabBar::tab:hover {{
        background-color: #2a2d2e;
        color: #cccccc;
    }}
    
    /* Text Editor - VS Code style */
    QTextEdit, QPlainTextEdit {{
        background-color: #1e1e1e;
        color: #cccccc;
        border: none;
        selection-background-color: #264f78;
        selection-color: #ffffff;
        font-family: '{best_font}', 'Consolas', 'SF Mono', 'Monaco', monospace;
        font-size: {editor_size}pt;
        line-height: {line_height};
        padding: 4px;
    }}
    
    /* TreeView - File explorer */
    QTreeView {{
        background-color: #252526;
        color: #cccccc;
        border: none;
        outline: none;
        font-family: '{best_font}', 'Consolas', monospace;
        font-size: {ui_size}pt;
    }}
    
    QTreeView::item {{
        padding: 4px 2px;
        border: none;
        min-height: 20px;
    }}
    
    QTreeView::item:selected {{
        background-color: #264f78;
        color: #ffffff;
    }}
    
    QTreeView::item:hover {{
        background-color: #2a2d2e;
    }}
    
    /* Buttons */
    QPushButton {{
        background-color: #0e639c;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 3px;
        font-family: '{best_font}', 'Consolas', monospace;
        font-size: {ui_size}pt;
        font-weight: normal;
    }}
    
    QPushButton:hover {{
        background-color: #1177bb;
    }}
    
    QPushButton:pressed {{
        background-color: #264f78;
    }}
    
    /* Status bar */
    QStatusBar {{
        background-color: #0e639c;
        color: white;
        border: none;
        font-family: '{best_font}', 'Consolas', monospace;
        font-size: {ui_size}pt;
        padding: 2px;
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        background-color: #1e1e1e;
        width: 14px;
        border: none;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: #424242;
        border-radius: 7px;
        min-height: 20px;
        margin: 0px 2px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: #4f4f4f;
    }}
    
    QScrollBar:horizontal {{
        background-color: #1e1e1e;
        height: 14px;
        border: none;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: #424242;
        border-radius: 7px;
        min-width: 20px;
        margin: 2px 0px;
    }}
    """

def apply_vscode_theme_improved(app=None, main_window=None, text_editors=None):
    """
    Áp dụng theme VS Code cải thiện với font configuration tốt hơn.
    
    Args:
        app: QApplication instance
        main_window: Main window widget
        text_editors: List of text editor widgets
    """
    if app is None:
        app = QApplication.instance()
    
    if app is not None:
        # Áp dụng Fusion style
        app.setStyle(QStyleFactory.create("Fusion"))
        
        # Cấu hình font
        set_vscode_font_improved(app)
        
        # Áp dụng stylesheet
        app.setStyleSheet(get_vscode_stylesheet_improved())
        
        # Cấu hình các text editor riêng biệt
        if text_editors:
            if isinstance(text_editors, (QTextEdit, QPlainTextEdit)):
                apply_editor_font(text_editors)
            elif isinstance(text_editors, list):
                for editor in text_editors:
                    apply_editor_font(editor)
        
        print("✓ Đã áp dụng VS Code theme cải thiện!")
        print(f"✓ Font được sử dụng: {get_best_monospace_font()}")

# Compatibility functions
def set_vscode_theme(app=None):
    """Wrapper cho compatibility với code cũ."""
    apply_vscode_theme_improved(app)

def set_vscode_font(app=None, font_name="Consolas", font_size=14):
    """Wrapper cho compatibility với code cũ."""
    set_vscode_font_improved(app)

def apply_vscode_theme(app=None):
    """Wrapper cho compatibility với code cũ."""
    apply_vscode_theme_improved(app)

# Test function
def test_font_configuration():
    """Test và hiển thị thông tin font configuration."""
    print("=== VS Code Font Configuration Test ===")
    print(f"Best monospace font: {get_best_monospace_font()}")
    
    # Test font creation
    test_font = create_vscode_font()
    print(f"Created font: {test_font.family()}")
    print(f"Font size: {test_font.pointSize()}pt")
    print(f"Fixed pitch: {test_font.fixedPitch()}")
    print(f"Font weight: {test_font.weight()}")
    
    # Available fonts
    font_db = QFontDatabase()
    available_fonts = font_db.families()
    
    print("\n=== Available VS Code Fonts ===")
    for font in VSCODE_FONT_CONFIG['primary_fonts']:
        status = "✓ Available" if font in available_fonts else "✗ Not found"
        print(f"{font}: {status}")

if __name__ == "__main__":
    # Test khi chạy file này trực tiếp
    import sys
    app = QApplication(sys.argv)
    test_font_configuration()
    apply_vscode_theme_improved(app)