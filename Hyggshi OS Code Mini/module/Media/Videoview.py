"""
Videoview.py - Simple video viewer widget for Hyggshi OS Code Mini
Requires: PyQt5 and opencv-python (cv2)
Fixed window expanding issue
"""

import sys
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton, 
                             QFileDialog, QApplication, QHBoxLayout, QSlider, QSizePolicy)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

try:
    import cv2
except ImportError:
    cv2 = None

class VideoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video Viewer")
        self.video_path = None
        self.cap = None
        self.is_playing = False
        self.total_frames = 0
        self.current_frame = 0
        self.fps = 30
        self.fixed_size = (640, 480)  # Default video display size
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        
        # Video display label with fixed size policy
        self.frame_label = QLabel("No video loaded")
        self.frame_label.setAlignment(Qt.AlignCenter)
        self.frame_label.setMinimumSize(self.fixed_size[0], self.fixed_size[1])
        self.frame_label.setMaximumSize(self.fixed_size[0], self.fixed_size[1])
        self.frame_label.setStyleSheet("border: 1px solid gray;")
        self.frame_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.frame_label.setScaledContents(False)  # Important: don't auto-scale contents
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderMoved.connect(self.seek_video)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        self._seeking = False
        
        # Buttons
        self.open_btn = QPushButton("Open Video")
        self.open_btn.clicked.connect(self.open_video)
        
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_video)
        self.play_btn.setEnabled(False)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_video)
        self.pause_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_video)
        self.stop_btn.setEnabled(False)
        
        # Info labels
        self.info_label = QLabel("")
        self.time_label = QLabel("00:00 / 00:00")
        
        # Layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.open_btn)
        button_layout.addWidget(self.play_btn)
        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.time_label)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.frame_label, 0, Qt.AlignCenter)
        layout.addWidget(self.progress_slider)
        layout.addLayout(button_layout)
        layout.addWidget(self.info_label)
        
        # Set fixed window size to prevent expansion
        self.setFixedSize(680, 600)

    def format_time(self, frame_num):
        """Convert frame number to MM:SS format"""
        if self.fps > 0:
            seconds = frame_num / self.fps
            minutes = int(seconds // 60)
            seconds = int(seconds % 60)
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"

    def open_video(self):
        if cv2 is None:
            self.frame_label.setText("OpenCV (cv2) is not installed.")
            return
            
        # Add more common video formats
        filter_str = (
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v "
            "*.mpg *.mpeg *.3gp *.ogv *.asf *.rm *.rmvb *.vob *.divx);;"
            "All Files (*)"
        )
        path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", filter_str)
        if path:
            self.video_path = path
            if self.cap:
                self.cap.release()
                
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                self.frame_label.setText("Failed to open video file.")
                self.cap = None
                return
            
            # Get video properties
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            if self.fps <= 0:
                self.fps = 30  # Default fps
                
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Update info
            filename = path.split('/')[-1] if '/' in path else path.split('\\')[-1]
            total_time = self.format_time(self.total_frames)
            self.info_label.setText(f"File: {filename} | Resolution: {width}x{height} | "
                                  f"FPS: {self.fps:.1f} | Duration: {total_time}")
            
            # Enable controls
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_slider.setEnabled(True)
            
            # Show first frame
            self.current_frame = 0
            self.show_first_frame()
            self.update_time_display()

    def show_first_frame(self):
        """Show the first frame of the video"""
        if not self.cap:
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = self.cap.read()
        if ret:
            self.display_frame(frame)
        else:
            self.frame_label.setText("Could not read video frame.")

    def show_frame(self):
        """Alias for show_first_frame for compatibility with main app."""
        self.show_first_frame()

    def play_video(self):
        if self.cap and not self.is_playing:
            # Calculate timer interval based on FPS
            interval = int(1000 / self.fps) if self.fps > 0 else 33
            self.timer.start(interval)
            self.is_playing = True
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)

    def pause_video(self):
        if self.is_playing:
            self.timer.stop()
            self.is_playing = False
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)

    def stop_video(self):
        self.timer.stop()
        self.is_playing = False
        self.current_frame = 0
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.show_first_frame()
        
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.progress_slider.setValue(0)
        self.update_time_display()

    def next_frame(self):
        if not self.cap or self._seeking:
            return
            
        ret, frame = self.cap.read()
        if not ret:
            # End of video - loop back to start
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame = 0
            self.timer.stop()
            self.is_playing = False
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            return
        
        self.current_frame += 1
        self.display_frame(frame)
        
        # Update progress slider
        if self.total_frames > 0:
            progress = int((self.current_frame / self.total_frames) * 100)
            self.progress_slider.setValue(progress)
        
        self.update_time_display()

    def display_frame(self, frame):
        """Display frame in the label with proper scaling"""
        if frame is None:
            return
            
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        # Create QImage
        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Convert to pixmap and scale to fit label size while maintaining aspect ratio
        pixmap = QPixmap.fromImage(qimg)
        label_size = self.frame_label.size()
        
        # Scale the pixmap to fit the label size while keeping aspect ratio
        scaled_pixmap = pixmap.scaled(
            label_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        self.frame_label.setPixmap(scaled_pixmap)

    def on_slider_pressed(self):
        """Called when user starts dragging the slider"""
        self._seeking = True
        if self.is_playing:
            self.timer.stop()

    def on_slider_released(self):
        """Called when user releases the slider"""
        self._seeking = False
        if self.is_playing:
            # Calculate timer interval based on FPS
            interval = int(1000 / self.fps) if self.fps > 0 else 33
            self.timer.start(interval)

    def seek_video(self, value):
        """Seek to specific position in video"""
        if not self.cap or self.total_frames == 0:
            return

        target_frame = int((value / 100.0) * self.total_frames)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        self.current_frame = target_frame

        # Đọc đúng frame tại vị trí seek, không đọc thêm frame mới
        ret, frame = self.cap.read()
        if ret:
            self.display_frame(frame)
            # Không tăng self.current_frame ở đây, vì đã set đúng vị trí rồi

        self.update_time_display()

    def update_time_display(self):
        """Update the time display"""
        current_time = self.format_time(self.current_frame)
        total_time = self.format_time(self.total_frames)
        self.time_label.setText(f"{current_time} / {total_time}")

    def closeEvent(self, event):
        self.timer.stop()
        if self.cap:
            self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = VideoView()
    viewer.show()
    sys.exit(app.exec_())