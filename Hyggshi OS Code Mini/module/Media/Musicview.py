"""
Musicview.py - Simple music player widget for Hyggshi OS Code Mini
Requires: PyQt5 and pygame (for audio playback)
Optimized seeking, error handling, time accuracy, and UI state management.
"""

import sys
import os
import time
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QApplication, QSlider, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

class MusicView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Music Player")
        self.music_path = None
        self.music_length = 0
        self._user_seeking = False
        self._seek_target = 0
        self._start_time = 0
        self._pause_time = 0
        self._is_playing = False
        self._is_paused = False

        self.init_ui()

        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except pygame.error as e:
                self.label.setText(f"Failed to init audio: {e}")
                self.open_btn.setEnabled(False)

    def init_ui(self):
        self.label = QLabel("No music loaded" if PYGAME_AVAILABLE else "pygame is not installed")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; padding: 10px;")

        self.open_btn = QPushButton("Open Music")
        self.open_btn.clicked.connect(self.open_music)
        self.open_btn.setEnabled(PYGAME_AVAILABLE)

        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_music)
        self.play_btn.setEnabled(False)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_music)
        self.pause_btn.setEnabled(False)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_music)
        self.stop_btn.setEnabled(False)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setValue(0)
        self.slider.setEnabled(False)
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderMoved.connect(self.on_slider_moved)
        self.slider.sliderReleased.connect(self.on_slider_released)

        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("color: white;")
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setStyleSheet("color: white;")
        time_layout = QHBoxLayout()
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addLayout(btn_layout)
        layout.addWidget(self.slider)
        layout.addLayout(time_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_display)

        self.setStyleSheet("""
            QWidget { background-color: #2b2d31; }
            QLabel { color: white; font-size: 12px; }
            QPushButton { color: #cccccc; background-color: #404249; border: 1px solid #5d5f66; border-radius: 4px; padding: 8px 16px; font-size: 11px; }
            QPushButton:hover { background-color: #4a4d54; }
            QPushButton:pressed { background-color: #36393f; }
            QPushButton:disabled { color: #888; background-color: #36393f; border-color: #444; }
            QSlider { height: 20px; }
            QSlider::groove:horizontal { border: 1px solid #999999; height: 8px; background: #36393f; margin: 2px 0; border-radius: 4px; }
            QSlider::handle:horizontal { background: #5865f2; border: 1px solid #5c5c5c; width: 18px; margin: -2px 0; border-radius: 3px; }
            QSlider::sub-page:horizontal { background: #5865f2; border: 1px solid #999999; height: 8px; border-radius: 4px; }
        """)

    def format_time(self, seconds):
        seconds = max(0, int(seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def open_music(self):
        if not PYGAME_AVAILABLE:
            self.label.setText("pygame is not installed.")
            return

        file_filter = (
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.aac *.m4a *.wma *.opus *.aiff *.alac);;"
            "All Files (*)"
        )
        path, _ = QFileDialog.getOpenFileName(self, "Open Music File", "", file_filter)
        if not path:
            return

        self.stop_music()
        try:
            pygame.mixer.music.load(path)
            self.music_path = path
            self.music_length, bitrate = self.get_music_info()
            filename = os.path.basename(path)
            self.label.setText(f"Loaded: {filename} ({bitrate} kbps)")
            self.total_time_label.setText(self.format_time(self.music_length))
            self.current_time_label.setText("00:00")
            self.slider.setEnabled(self.music_length > 0)
            self.slider.setValue(0)
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self._is_playing = False
            self._is_paused = False
            self._seek_target = 0
        except Exception as e:
            self.label.setText(
                f"Cannot load file: {e}\n"
                "File may be corrupted or unsupported.\n"
                "Try converting with Audacity or an online converter."
            )
            self.reset_controls()

    def reset_controls(self):
        self.music_path = None
        self.music_length = 0
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.slider.setEnabled(False)
        self.slider.setValue(0)
        self.current_time_label.setText("00:00")
        self.total_time_label.setText("00:00")
        self._is_playing = False
        self._is_paused = False
        self._seek_target = 0

    def play_music(self):
        if not (PYGAME_AVAILABLE and self.music_path):
            return
        try:
            if self._is_paused:
                pygame.mixer.music.unpause()
                self._start_time = time.time() - self._pause_time
                self._is_paused = False
            else:
                pygame.mixer.music.load(self.music_path)
                start_pos = self._seek_target if self._seek_target > 0 else 0
                try:
                    pygame.mixer.music.play(start=start_pos)
                    self._start_time = time.time() - start_pos
                except Exception:
                    pygame.mixer.music.play()
                    self._start_time = time.time()
                    self._seek_target = 0
            self._is_playing = True
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.timer.start(100)
        except Exception as e:
            self.label.setText(f"Error playing music: {e}")
            self.reset_controls()

    def pause_music(self):
        if not (PYGAME_AVAILABLE and self._is_playing and not self._is_paused):
            return
        try:
            pygame.mixer.music.pause()
            self._pause_time = time.time() - self._start_time
            self._is_paused = True
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.timer.stop()
        except Exception as e:
            print(f"Error pausing music: {e}")

    def stop_music(self):
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self._is_playing = False
        self._is_paused = False
        self._seek_target = 0
        self.play_btn.setEnabled(bool(self.music_path))
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.slider.setValue(0)
        self.current_time_label.setText("00:00")
        self.timer.stop()

    def on_slider_pressed(self):
        self._user_seeking = True

    def on_slider_moved(self, value):
        if self._user_seeking and self.music_length > 0:
            pos = (value / 1000.0) * self.music_length
            self.current_time_label.setText(self.format_time(pos))

    def on_slider_released(self):
        if not (self._user_seeking and PYGAME_AVAILABLE and self.music_path and self.music_length > 0):
            self._user_seeking = False
            return
        try:
            value = self.slider.value()
            new_pos = (value / 1000.0) * self.music_length
            was_playing = self._is_playing and not self._is_paused
            pygame.mixer.music.stop()
            self._seek_target = new_pos
            if was_playing:
                pygame.mixer.music.load(self.music_path)
                try:
                    pygame.mixer.music.play(start=self._seek_target)
                    self._start_time = time.time() - self._seek_target
                    self._is_playing = True
                    self._is_paused = False
                    self.timer.start(100)
                except Exception:
                    pygame.mixer.music.play()
                    self._start_time = time.time()
                    self._seek_target = 0
                    self.slider.setValue(0)
            else:
                self._is_playing = False
                self._is_paused = False
        except Exception as e:
            print(f"Seek error: {e}")
            self._seek_target = 0
            self.slider.setValue(0)
            self.current_time_label.setText("00:00")
        self._user_seeking = False

    def update_display(self):
        if not (PYGAME_AVAILABLE and self.music_path and self._is_playing and self.music_length > 0):
            return
        if self._user_seeking:
            return
        try:
            if self._is_paused:
                pos = self._pause_time
            else:
                pos = time.time() - self._start_time
            if pos >= self.music_length or not pygame.mixer.music.get_busy():
                self.stop_music()
                return
            pos = max(0, min(pos, self.music_length))
            percent = int((pos / self.music_length) * 1000)
            self.slider.setValue(percent)
            self.current_time_label.setText(self.format_time(pos))
        except Exception as e:
            print(f"Update error: {e}")

    def get_music_info(self):
        default_bitrate = 128
        try:
            import mutagen
            audio = mutagen.File(self.music_path)
            if audio and hasattr(audio, 'info'):
                length = getattr(audio.info, 'length', 0)
                bitrate = getattr(audio.info, 'bitrate', default_bitrate * 1000)
                if isinstance(bitrate, (int, float)) and bitrate > 0:
                    bitrate = int(bitrate / 1000)
                else:
                    bitrate = default_bitrate
                return max(0, length), bitrate
        except ImportError:
            print("mutagen not installed - using file size estimation")
        except Exception as e:
            print(f"Error reading metadata: {e}")
        try:
            file_size = os.path.getsize(self.music_path)
            estimated_length = file_size / (default_bitrate * 1000 / 8)
            return min(max(0, estimated_length), 7200), default_bitrate
        except Exception as e:
            print(f"Error estimating duration: {e}")
            return 0, default_bitrate

    def closeEvent(self, event):
        self.timer.stop()
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except Exception:
                pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = MusicView()
    viewer.resize(500, 400)
    viewer.show()
    sys.exit(app.exec_())