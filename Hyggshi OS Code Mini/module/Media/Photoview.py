"""
Photoview.py - Simple image/photo viewer widget with proper zoom functionality
"""

import os
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, 
                            QHBoxLayout, QSizePolicy, QSlider, QScrollArea)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class PhotoView(QWidget):
    def __init__(self, path=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Photo Viewer")
        self.image_path = path

        # Create scroll area for proper zooming
        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(self.scroll_area.palette().Dark)
        self.scroll_area.setStyleSheet("background: #23272e; border: 1px solid #444;")
        
        self.image_label = QLabel("No image loaded")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setStyleSheet("background: #23272e; color: #fff;")
        self.image_label.setScaledContents(False)

        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(False)  # Important for proper zooming

        self.open_btn = QPushButton("Open Image")
        self.open_btn.clicked.connect(self.open_image)

        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn = QPushButton("Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.reset_btn = QPushButton("Fit to Window")
        self.reset_btn.clicked.connect(self.fit_to_window)
        self.actual_size_btn = QPushButton("100%")
        self.actual_size_btn.clicked.connect(self.actual_size)

        # Modern zoom slider
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10)  # 10% zoom (0.1x)
        self.zoom_slider.setMaximum(500)  # 500% zoom (5x)
        self.zoom_slider.setValue(100)  # 100% zoom (1x)
        self.zoom_slider.setFixedHeight(30)
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
        
        # Modern slider styling
        slider_style = """
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: #444;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #4a90e2;
                border: 2px solid #ffffff;
                width: 18px;
                height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #5ba0f2;
                border: 2px solid #ffffff;
            }
            QSlider::handle:horizontal:pressed {
                background: #3a80d2;
            }
            QSlider::sub-page:horizontal {
                background: #4a90e2;
                border-radius: 2px;
            }
            QSlider::add-page:horizontal {
                background: #444;
                border-radius: 2px;
            }
        """
        self.zoom_slider.setStyleSheet(slider_style)

        # Style the buttons
        button_style = """
            QPushButton {
                background: #404040;
                border: 1px solid #555;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #505050;
                border: 1px solid #666;
            }
            QPushButton:pressed {
                background: #303030;
            }
        """
        
        self.zoom_out_btn.setStyleSheet(button_style + "QPushButton { font-size: 18px; padding: 6px 12px; }")
        self.zoom_in_btn.setStyleSheet(button_style + "QPushButton { font-size: 18px; padding: 6px 12px; }")
        self.zoom_out_btn.setText("−")  # Unicode minus
        self.zoom_in_btn.setText("+")   # Plus sign
        
        self.open_btn.setStyleSheet(button_style)
        self.reset_btn.setStyleSheet(button_style)
        self.actual_size_btn.setStyleSheet(button_style)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.open_btn)
        btn_layout.addStretch()  # Push zoom controls to center-right
        btn_layout.addWidget(self.zoom_out_btn)
        btn_layout.addWidget(self.zoom_slider, 2)  # Give slider more space
        btn_layout.addWidget(self.zoom_in_btn)
        btn_layout.addWidget(self.actual_size_btn)
        btn_layout.addWidget(self.reset_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.scroll_area)
        layout.addLayout(btn_layout)

        self._zoom_factor = 1.0
        self._original_pixmap = None
        self._updating_slider = False  # Flag to prevent slider update loops
        
        if path:
            self.load_image(path)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Image", 
            "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.svg *.tiff *.ico *.avif);;All Files (*)"
        )
        if path:
            self.load_image(path)

    def load_image(self, path):
        if not os.path.exists(path):
            self.image_label.setText("File not found.")
            self._original_pixmap = None
            return
            
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.image_label.setText("Cannot load image.")
            self._original_pixmap = None
            return
            
        self.image_path = path
        self._original_pixmap = pixmap
        
        # Fit to window initially
        self.fit_to_window()
        self.setWindowTitle(f"Photo Viewer - {os.path.basename(path)}")

    def scale_image(self, factor):
        """Scale the image by the given factor"""
        if self._original_pixmap is None:
            return
            
        self._zoom_factor *= factor
        
        # Limit zoom range
        self._zoom_factor = max(0.1, min(5.0, self._zoom_factor))
        
        # Scale the pixmap
        scaled_pixmap = self._original_pixmap.scaled(
            self._zoom_factor * self._original_pixmap.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())
        
        # Update slider to match current zoom
        self.update_zoom_slider()

    def zoom_in(self):
        """Zoom in by 25%"""
        if self._original_pixmap is not None:
            self.scale_image(1.25)

    def zoom_out(self):
        """Zoom out by 25%"""
        if self._original_pixmap is not None:
            self.scale_image(0.8)

    def fit_to_window(self):
        """Fit the image to the current window size"""
        if self._original_pixmap is None:
            return
            
        # Get available space in scroll area
        available_size = self.scroll_area.viewport().size()
        
        # Calculate zoom factor to fit image in available space
        zoom_w = available_size.width() / self._original_pixmap.width()
        zoom_h = available_size.height() / self._original_pixmap.height()
        
        # Use the smaller zoom factor to ensure image fits completely
        self._zoom_factor = min(zoom_w, zoom_h)
        
        # Ensure we don't zoom beyond reasonable limits
        self._zoom_factor = max(0.1, min(5.0, self._zoom_factor))
        
        # Apply the zoom
        scaled_pixmap = self._original_pixmap.scaled(
            self._zoom_factor * self._original_pixmap.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())
        
        # Update slider
        self.update_zoom_slider()

    def actual_size(self):
        """Show image at 100% (actual) size"""
        if self._original_pixmap is not None:
            self._zoom_factor = 1.0
            self.image_label.setPixmap(self._original_pixmap)
            self.image_label.resize(self._original_pixmap.size())
            self.update_zoom_slider()

    def on_zoom_slider_changed(self, value):
        """Handle zoom slider changes"""
        if self._updating_slider or self._original_pixmap is None:
            return
            
        # Convert slider value (10-500) to zoom factor (0.1-5.0)
        target_zoom = value / 100.0
        
        # Calculate the scaling factor needed to reach target zoom
        if self._zoom_factor > 0:
            scale_factor = target_zoom / self._zoom_factor
            self._zoom_factor = target_zoom
        else:
            self._zoom_factor = target_zoom
            scale_factor = 1.0
        
        # Apply the zoom
        scaled_pixmap = self._original_pixmap.scaled(
            self._zoom_factor * self._original_pixmap.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())

    def update_zoom_slider(self):
        """Update slider position to match current zoom level"""
        if self._updating_slider:
            return
            
        self._updating_slider = True
        slider_value = int(self._zoom_factor * 100)
        slider_value = max(10, min(500, slider_value))  # Clamp to slider range
        self.zoom_slider.setValue(slider_value)
        # Thêm label hiển thị phần trăm zoom nếu chưa có
        if not hasattr(self, "zoom_label"):
            from PyQt5.QtWidgets import QLabel
            self.zoom_label = QLabel(f"{slider_value}%")
            self.zoom_label.setStyleSheet("color: #fff; font-weight: bold; padding-left: 8px;")
            # Thêm vào layout nút nếu chưa có
            self.layout().itemAt(1).addWidget(self.zoom_label)
        else:
            self.zoom_label.setText(f"{slider_value}%")
        self._updating_slider = False

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Note: We don't auto-fit on resize to preserve user's zoom level



if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    viewer = PhotoView()
    viewer.resize(800, 600)
    viewer.show()
    sys.exit(app.exec_())