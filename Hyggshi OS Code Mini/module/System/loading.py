from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QLinearGradient, QColor
import os

class LoadingScreen(QDialog):
    def __init__(self, timeout=1999, image_path=None, img_width=80, img_height=80, image_size=(1920, 1080)):
        super().__init__()
        self.image_path = image_path
        self.original_pixmap = None
        self.screen_width, self.screen_height = image_size

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(self.screen_width, self.screen_height)
        # Xóa background trong setStyleSheet để dùng paintEvent vẽ gradient

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if image_path and self.is_valid_image(image_path):
            self.original_pixmap = QPixmap(image_path)
            if not self.original_pixmap.isNull():
                img_label = QLabel()
                img_label.setAlignment(Qt.AlignCenter)
                img_label.setPixmap(self.scale_image(self.original_pixmap, img_width, img_height))
                layout.addWidget(img_label)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.accept)
        self.timer.start(timeout)

    def paintEvent(self, event):
        # Vẽ gradient nền
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#1c60d7"))
        gradient.setColorAt(1, QColor("#26a74b"))
        painter.fillRect(self.rect(), gradient)
        super().paintEvent(event)

    def is_valid_image(self, image_path):
        """Check if the image path exists and is a valid image file."""
        if not os.path.exists(image_path):
            return False

        valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.ico']
        return any(image_path.lower().endswith(ext) for ext in valid_extensions)

    def get_screen_size(self):
        """Get the current screen/window dimensions of the loading screen."""
        return self.screen_width, self.screen_height

    def get_original_image_size(self):
        """Get the original dimensions of the loaded image."""
        if self.original_pixmap and not self.original_pixmap.isNull():
            return self.original_pixmap.width(), self.original_pixmap.height()
        return None, None

    def get_image_file_size(self):
        """Get the file size of the image in bytes."""
        if self.image_path and os.path.exists(self.image_path):
            return os.path.getsize(self.image_path)
        return None

    def get_image_file_size_formatted(self):
        """Get the file size of the image in a human-readable format."""
        size_bytes = self.get_image_file_size()
        if size_bytes is None:
            return "Unknown"

        # Convert bytes to human readable format
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def get_image_info(self):
        """Get comprehensive information about the loaded image."""
        if not self.original_pixmap or self.original_pixmap.isNull():
            return None

        width, height = self.get_original_image_size()
        file_size = self.get_image_file_size_formatted()

        return {
            'path': self.image_path,
            'width': width,
            'height': height,
            'dimensions': f"{width}x{height}",
            'file_size': file_size,
            'aspect_ratio': round(width / height, 2) if height != 0 else None,
            'total_pixels': width * height if width and height else None,
            'screen_size': f"{self.screen_width}x{self.screen_height}"
        }

    def scale_image(self, pixmap, width, height):
        """Scale image to specified dimensions while maintaining aspect ratio."""
        return pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def scale_image_to_fit(self, pixmap, max_width, max_height):
        """Scale image to fit within specified dimensions."""
        return pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def scale_image_exact(self, pixmap, width, height):
        """Scale image to exact dimensions (may distort aspect ratio)."""
        return pixmap.scaled(width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    def resize_image_display(self, new_width, new_height):
        """Resize the displayed image to new dimensions."""
        if self.original_pixmap and not self.original_pixmap.isNull():
            # Find the image label and update it
            for child in self.findChildren(QLabel):
                if child.pixmap() and not child.pixmap().isNull():
                    child.setPixmap(self.scale_image(self.original_pixmap, new_width, new_height))
                    break

    def print_image_info(self):
        """Print detailed image information to console."""
        info = self.get_image_info()
        if info:
            print("=" * 40)
            print("IMAGE INFORMATION")
            print("=" * 40)
            print(f"Path: {info['path']}")
            print(f"Dimensions: {info['dimensions']}")
            print(f"File Size: {info['file_size']}")
            print(f"Aspect Ratio: {info['aspect_ratio']}")
            print(f"Total Pixels: {info['total_pixels']:,}")
            print(f"Screen Size: {info['screen_size']}")
            print("=" * 40)
        else:
            print("No image loaded or image is invalid.")

def show_loading_then_main(main_window_class, image_path=None, img_width=80, img_height=80, image_size=(1920, 1080), print_info=False):
    """
    Show loading screen then main window.

    Args:
        main_window_class: The main window class to show after loading
        image_path: Path to the image file
        img_width: Display width of the image
        img_height: Display height of the image
        image_size: Tuple of (width, height) for the loading screen size
        print_info: Whether to print image information to console
    """
    import sys
    app = QApplication.instance() or QApplication(sys.argv)

    loading = LoadingScreen(image_path=image_path, img_width=img_width, img_height=img_height, image_size=image_size)

    # Print image info if requested
    if print_info:
        loading.print_image_info()

    loading.exec_()

    window = main_window_class()
    window.show()

    sys.exit(app.exec_())

# Example usage:
if __name__ == "__main__":
    from PyQt5.QtWidgets import QMainWindow, QLabel

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Main Application")
            self.setGeometry(100, 100, 800, 600)

            central_widget = QLabel("Main Application Window")
            central_widget.setAlignment(Qt.AlignCenter)
            self.setCentralWidget(central_widget)

    try:
        show_loading_then_main(
            MainWindow,
            image_path="Resources/Image.png", 
            img_width=1090, 
            img_height=615,
            image_size=(1090, 615),
            print_info=True
        )
    except Exception as e:
        import traceback
        print("LỖI khi khởi tạo cửa sổ:", e)
        traceback.print_exc()