# UI_UX_Enhanced.py - Giao diện VS Code nâng cấp dễ nhìn hơn
# Enhanced VS Code-like interface with better readability

from PyQt5.QtWidgets import QApplication, QStyleFactory, QTextEdit, QPlainTextEdit
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QColor, QPalette, QFont, QFontDatabase, QTextCharFormat, QPainter
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

# ENHANCED FONT CONFIGURATION - Cải thiện để dễ đọc hơn
ENHANCED_FONT_CONFIG = {
    # Font families với độ ưu tiên cao về khả năng đọc
    'primary_fonts': [
        'JetBrains Mono',     # Font tốt nhất cho code
        'Fira Code',          # Font với ligatures
        'Source Code Pro',    # Adobe's monospace
        'Cascadia Code',      # Microsoft's new font
        'SF Mono',            # macOS
        'Consolas',           # Windows default
        'Monaco',             # macOS backup
        'Ubuntu Mono',        # Linux
        'DejaVu Sans Mono',   # Linux backup
        'Courier New',        # Universal fallback
        'monospace'           # System fallback
    ],
    
    # Font sizes được tối ưu cho việc đọc
    'editor_size': 16,        # Tăng từ 14 lên 16 để dễ đọc hơn
    'ui_size': 10,           # Tăng từ 9 lên 10
    'line_height': 1.7,      # Tăng line height để dễ đọc
    'letter_spacing': 0.3,   # Thêm letter spacing
    
    # Font weights
    'normal_weight': QFont.Normal,
    'medium_weight': QFont.Medium,
    'bold_weight': QFont.Bold,
    
    # Font rendering hints
    'antialiasing': True,
    'subpixel_antialiasing': True,
    'hinting': True,
}

# COLOR THEMES - Nhiều theme cho người dùng lựa chọn
COLOR_THEMES = {
    'dark_blue': {
        'name': 'Dark Blue (Easy on Eyes)',
        'main_bg': '#0d1421',          # Nền chính xanh đậm
        'secondary_bg': '#1a2332',     # Nền phụ
        'accent_bg': '#2d4263',        # Màu nhấn
        'text_primary': '#e8f4f8',     # Text chính - màu sáng dễ đọc
        'text_secondary': '#a8c8d8',   # Text phụ
        'highlight': '#4a9eff',        # Màu highlight xanh sáng
        'success': '#2dd4bf',          # Màu thành công
        'warning': '#f59e0b',          # Màu cảnh báo
        'error': '#ef4444',            # Màu lỗi
    },
    'warm_dark': {
        'name': 'Warm Dark (Comfortable)',
        'main_bg': '#1a1625',          # Nền tím đậm ấm
        'secondary_bg': '#2a2139',     
        'accent_bg': '#3d344a',        
        'text_primary': '#f0e6ff',     # Text sáng với tông tím nhẹ
        'text_secondary': '#c4b5d9',   
        'highlight': '#8b5cf6',        # Tím sáng
        'success': '#10b981',          
        'warning': '#f59e0b',          
        'error': '#f87171',            
    },
    'forest_dark': {
        'name': 'Forest Dark (Natural)',
        'main_bg': '#0f1b0f',          # Xanh lá đậm
        'secondary_bg': '#1a2e1a',     
        'accent_bg': '#2d4a2d',        
        'text_primary': '#e8f5e8',     # Text với tông xanh nhẹ
        'text_secondary': '#b8d4b8',   
        'highlight': '#22c55e',        # Xanh lá sáng
        'success': '#16a34a',          
        'warning': '#eab308',          
        'error': '#dc2626',            
    }
}

def get_best_programming_font():
    """
    Tìm font tốt nhất cho lập trình với độ ưu tiên về khả năng đọc.
    """
    font_db = QFontDatabase()
    available_fonts = font_db.families()
    
    # Kiểm tra từng font theo thứ tự ưu tiên
    for font_name in ENHANCED_FONT_CONFIG['primary_fonts']:
        if font_name in available_fonts:
            print(f"✓ Sử dụng font: {font_name}")
            return font_name
    
    # Tìm font monospace bất kỳ
    for font_name in available_fonts:
        if font_db.isFixedPitch(font_db.font(font_name, "", 12)):
            print(f"✓ Sử dụng font fallback: {font_name}")
            return font_name
    
    print("⚠ Sử dụng font mặc định: Courier New")
    return 'Courier New'

def create_enhanced_font(size=None, weight='normal', italic=False):
    """
    Tạo font object với cấu hình nâng cao cho khả năng đọc tốt nhất.
    """
    if size is None:
        size = ENHANCED_FONT_CONFIG['editor_size']
    
    font = QFont()
    
    # Đặt font family
    best_font = get_best_programming_font()
    font.setFamily(best_font)
    
    # Cấu hình font
    font.setPointSize(size)
    font.setStyleHint(QFont.Monospace)
    font.setFixedPitch(True)
    
    # Weight mapping
    weight_map = {
        'normal': ENHANCED_FONT_CONFIG['normal_weight'],
        'medium': ENHANCED_FONT_CONFIG['medium_weight'],
        'bold': ENHANCED_FONT_CONFIG['bold_weight']
    }
    font.setWeight(weight_map.get(weight, ENHANCED_FONT_CONFIG['normal_weight']))
    font.setItalic(italic)
    
    # Font rendering quality - Quan trọng cho độ sắc nét
    font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
    font.setHintingPreference(QFont.PreferFullHinting)
    
    # Letter spacing để dễ đọc hơn
    font.setLetterSpacing(QFont.AbsoluteSpacing, ENHANCED_FONT_CONFIG['letter_spacing'])
    
    return font

def get_enhanced_stylesheet(theme='dark_blue'):
    """
    CSS stylesheet nâng cấp với focus vào khả năng đọc và trải nghiệm người dùng.
    """
    colors = COLOR_THEMES.get(theme, COLOR_THEMES['dark_blue'])
    best_font = get_best_programming_font()
    editor_size = ENHANCED_FONT_CONFIG['editor_size']
    ui_size = ENHANCED_FONT_CONFIG['ui_size']
    line_height = ENHANCED_FONT_CONFIG['line_height']

    return f"""
    /* Enhanced VS Code Style - {colors['name']} */
    
    * {{
        font-family: '{best_font}', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    }}

    /* Main Window - Improved contrast */
    QMainWindow {{
        background-color: {colors['main_bg']};
        color: {colors['text_primary']};
        font-size: {ui_size}pt;
        font-weight: normal;
    }}

    /* Menu Bar - Better readability */
    QMenuBar {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {colors['secondary_bg']}, stop:1 {colors['main_bg']});
        color: {colors['text_primary']};
        font-size: {ui_size + 1}pt;
        font-weight: 500;
        border: none;
        padding: 6px;
    }}

    QMenuBar::item {{
        background: transparent;
        padding: 10px 20px;
        border-radius: 8px;
        margin: 2px;
        font-weight: 500;
    }}

    QMenuBar::item:selected {{
        background: {colors['highlight']};
        color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}

    QMenuBar::item:hover {{
        background: {colors['accent_bg']};
        color: {colors['text_primary']};
    }}

    /* Menu Dropdown - Enhanced */
    QMenu {{
        background: {colors['secondary_bg']};
        color: {colors['text_primary']};
        border: 2px solid {colors['accent_bg']};
        font-size: {ui_size}pt;
        border-radius: 12px;
        padding: 8px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }}

    QMenu::item {{
        background: transparent;
        padding: 10px 16px;
        border-radius: 8px;
        margin: 2px 4px;
        font-weight: 500;
    }}

    QMenu::item:selected {{
        background: {colors['highlight']};
        color: white;
    }}

    /* Tab Widget - Modern design */
    QTabWidget::pane {{
        border: 2px solid {colors['accent_bg']};
        border-radius: 0 12px 12px 12px;
        background: {colors['main_bg']};
    }}

    QTabBar::tab {{
        background: {colors['secondary_bg']};
        color: {colors['text_secondary']};
        padding: 12px 24px;
        margin-right: 4px;
        margin-top: 4px;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
        font-size: {ui_size}pt;
        font-weight: 600;
        min-width: 120px;
        border: 2px solid transparent;
    }}

    QTabBar::tab:selected {{
        background: {colors['main_bg']};
        color: {colors['text_primary']};
        border-bottom: 3px solid {colors['highlight']};
        font-weight: 700;
        margin-top: 0px;
    }}

    QTabBar::tab:hover:!selected {{
        background: {colors['accent_bg']};
        color: {colors['text_primary']};
        border: 2px solid {colors['highlight']};
    }}

    /* Tree View - File Explorer Enhanced */
    QTreeView {{
        background: {colors['secondary_bg']};
        color: {colors['text_primary']};
        border: none;
        font-size: {ui_size}pt;
        font-weight: 500;
        selection-background-color: {colors['highlight']};
        selection-color: white;
        outline: none;
        border-radius: 8px;
        padding: 4px;
    }}

    QTreeView::item {{
        padding: 10px 12px;
        border-radius: 6px;
        margin: 1px 2px;
        font-size: {ui_size}pt;
        min-height: 24px;
    }}

    QTreeView::item:selected {{
        background: {colors['highlight']};
        color: white;
        border: 2px solid rgba(255,255,255,0.3);
        font-weight: 600;
    }}

    QTreeView::item:hover:!selected {{
        background: {colors['accent_bg']};
        color: {colors['text_primary']};
        border: 1px solid {colors['highlight']};
    }}

    QTreeView::branch:has-children:!has-siblings:closed,
    QTreeView::branch:closed:has-children:has-siblings {{
        border-image: none;
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTYgNEwxMCA4TDYgMTJWNFoiIGZpbGw9IiM4Yjk2YTUiLz4KPHN2Zz4K);
    }}

    QTreeView::branch:open:has-children:!has-siblings,
    QTreeView::branch:open:has-children:has-siblings {{
        border-image: none;
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkwxMiA2TDggMTBMNCA2WiIgZmlsbD0iIzRhOWVmZiIvPgo8L3N2Zz4K);
    }}

    /* Text Editor - Optimized for reading */
    QTextEdit, QPlainTextEdit {{
        background: {colors['main_bg']};
        color: {colors['text_primary']};
        border: 2px solid {colors['accent_bg']};
        border-radius: 12px;
        font-size: {editor_size}pt;
        font-weight: 400;
        line-height: {int(line_height * 100)}%;
        padding: 16px;
        selection-background-color: {colors['highlight']};
        selection-color: white;
    }}

    QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {colors['highlight']};
        background: {colors['main_bg']};
        box-shadow: 0 0 20px rgba(74, 158, 255, 0.3);
    }}

    /* Buttons - Modern and accessible */
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {colors['highlight']}, stop:1 {colors['accent_bg']});
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 10px;
        font-size: {ui_size}pt;
        font-weight: 600;
        margin: 4px;
    }}

    QPushButton:hover {{
        background: {colors['highlight']};
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }}

    QPushButton:pressed {{
        background: {colors['accent_bg']};
        transform: translateY(0px);
    }}

    QPushButton:disabled {{
        background: {colors['accent_bg']};
        color: {colors['text_secondary']};
    }}

    /* Status Bar - Information display */
    QStatusBar {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {colors['highlight']}, stop:1 {colors['accent_bg']});
        color: white;
        border: none;
        font-size: {ui_size}pt;
        font-weight: 600;
        padding: 8px;
    }}

    /* Scrollbars - Smooth and modern */
    QScrollBar:vertical {{
        background: {colors['secondary_bg']};
        width: 18px;
        border-radius: 9px;
        border: none;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {colors['accent_bg']};
        border-radius: 9px;
        min-height: 30px;
        margin: 3px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {colors['highlight']};
    }}

    QScrollBar::handle:vertical:pressed {{
        background: {colors['text_secondary']};
    }}

    QScrollBar:horizontal {{
        background: {colors['secondary_bg']};
        height: 18px;
        border-radius: 9px;
        border: none;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background: {colors['accent_bg']};
        border-radius: 9px;
        min-width: 30px;
        margin: 3px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {colors['highlight']};
    }}

    QScrollBar::add-line, QScrollBar::sub-line {{
        border: none;
        background: none;
    }}

    /* Input Fields */
    QLineEdit {{
        background: {colors['secondary_bg']};
        color: {colors['text_primary']};
        border: 2px solid {colors['accent_bg']};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: {ui_size}pt;
        font-weight: 500;
    }}

    QLineEdit:focus {{
        border: 2px solid {colors['highlight']};
        background: {colors['main_bg']};
    }}

    /* Tooltips */
    QToolTip {{
        background: {colors['secondary_bg']};
        color: {colors['text_primary']};
        border: 2px solid {colors['highlight']};
        border-radius: 8px;
        padding: 8px;
        font-size: {ui_size}pt;
        font-weight: 500;
    }}
    """

def apply_enhanced_theme(app=None, main_window=None, text_editors=None, theme='dark_blue'):
    """
    Áp dụng theme nâng cấp với focus vào trải nghiệm người dùng.
    
    Args:
        app: QApplication instance
        main_window: Main window widget
        text_editors: List of text editor widgets
        theme: Theme name ('dark_blue', 'warm_dark', 'forest_dark')
    """
    if app is None:
        app = QApplication.instance()
    
    if app is not None:
        # Áp dụng Fusion style để có rendering tốt hơn
        app.setStyle(QStyleFactory.create("Fusion"))
        
        # Cấu hình font toàn cục
        main_font = create_enhanced_font(ENHANCED_FONT_CONFIG['ui_size'])
        app.setFont(main_font)
        
        # Áp dụng stylesheet nâng cấp
        stylesheet = get_enhanced_stylesheet(theme)
        app.setStyleSheet(stylesheet)
        
        # Cấu hình text editors riêng biệt
        if text_editors:
            if isinstance(text_editors, (QTextEdit, QPlainTextEdit)):
                apply_enhanced_editor_font(text_editors)
            elif isinstance(text_editors, list):
                for editor in text_editors:
                    apply_enhanced_editor_font(editor)
        
        # In thông tin cấu hình
        colors = COLOR_THEMES.get(theme, COLOR_THEMES['dark_blue'])
        print(f"✓ Đã áp dụng theme: {colors['name']}")
        print(f"✓ Font được sử dụng: {get_best_programming_font()}")
        print(f"✓ Kích thước UI: {ENHANCED_FONT_CONFIG['ui_size']}pt")
        print(f"✓ Kích thước Editor: {ENHANCED_FONT_CONFIG['editor_size']}pt")
        print(f"✓ Line height: {ENHANCED_FONT_CONFIG['line_height']}")

def apply_enhanced_editor_font(text_widget):
    """
    Áp dụng font cải tiến cho text editor với tối ưu hóa khả năng đọc.
    """
    if isinstance(text_widget, (QTextEdit, QPlainTextEdit)):
        editor_font = create_enhanced_font(ENHANCED_FONT_CONFIG['editor_size'])
        text_widget.setFont(editor_font)
        
        # Cấu hình tab width tối ưu
        if hasattr(text_widget, 'setTabStopWidth'):
            text_widget.setTabStopWidth(4 * text_widget.fontMetrics().width(' '))
        elif hasattr(text_widget, 'setTabStopDistance'):
            text_widget.setTabStopDistance(4 * text_widget.fontMetrics().horizontalAdvance(' '))
        
        print(f"✓ Đã áp dụng font editor: {editor_font.family()} - {editor_font.pointSize()}pt")

def create_theme_selector():
    """
    Tạo function để người dùng có thể chọn theme.
    """
    from PyQt5.QtWidgets import QComboBox
    
    theme_selector = QComboBox()
    for theme_key, theme_data in COLOR_THEMES.items():
        theme_selector.addItem(theme_data['name'], theme_key)
    
    return theme_selector

def apply_accessibility_improvements(app=None):
    """
    Áp dụng các cải thiện về accessibility (khả năng tiếp cận).
    """
    if app is None:
        app = QApplication.instance()
    
    if app is not None:
        # Tăng contrast cho người có vấn đề về thị giác
        palette = app.palette()
        palette.setColor(QPalette.Highlight, QColor('#4a9eff'))
        palette.setColor(QPalette.HighlightedText, QColor('#ffffff'))
        app.setPalette(palette)
        
        print("✓ Đã áp dụng cải thiện accessibility")

# Wrapper functions để tương thích với code cũ
def set_dark_theme():
    """Wrapper cho compatibility."""
    print("Enhanced dark theme applied.")

def set_vscode_theme(app=None):
    """Wrapper cho compatibility."""
    apply_enhanced_theme(app, theme='dark_blue')

def apply_vscode_theme(app=None):
    """Wrapper cho compatibility."""
    apply_enhanced_theme(app, theme='dark_blue')

# Test và demo function
def demo_all_themes():
    """
    Demo tất cả các theme có sẵn.
    """
    print("=== Available Enhanced Themes ===")
    for theme_key, theme_data in COLOR_THEMES.items():
        print(f"Theme: {theme_key}")
        print(f"  Name: {theme_data['name']}")
        print(f"  Main BG: {theme_data['main_bg']}")
        print(f"  Text: {theme_data['text_primary']}")
        print(f"  Highlight: {theme_data['highlight']}")
        print()

def test_font_configuration():
    """
    Test và hiển thị thông tin font configuration nâng cấp.
    """
    print("=== Enhanced Font Configuration Test ===")
    print(f"Best programming font: {get_best_programming_font()}")
    
    # Test font creation
    test_font = create_enhanced_font()
    print(f"Created font: {test_font.family()}")
    print(f"Font size: {test_font.pointSize()}pt")
    print(f"Letter spacing: {test_font.letterSpacing()}")
    print(f"Fixed pitch: {test_font.fixedPitch()}")
    print(f"Font weight: {test_font.weight()}")
    
    # Available fonts
    font_db = QFontDatabase()
    available_fonts = font_db.families()
    
    print("\n=== Available Programming Fonts ===")
    for font in ENHANCED_FONT_CONFIG['primary_fonts']:
        status = "✓ Available" if font in available_fonts else "✗ Not found"
        print(f"{font}: {status}")
    
    # Demo themes
    demo_all_themes()

if __name__ == "__main__":
    # Test khi chạy file này trực tiếp
    import sys
    app = QApplication(sys.argv)
    test_font_configuration()
    apply_enhanced_theme(app, theme='dark_blue')
    apply_accessibility_improvements(app)