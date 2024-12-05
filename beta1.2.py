from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,
    QGridLayout, QFileDialog, QMessageBox, QInputDialog, QLineEdit, QLabel, QHBoxLayout,
    QScrollArea, QSlider
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import pygame
import os
import json

pygame.mixer.init()

class SoundBoard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux SoundBoard")
        self.setGeometry(200, 200, 600, 400)

        self.sounds = {}
        self.profile_path = "soundboard_profiles.json"
        self.load_profiles()

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.scroll_area_widget.setLayout(self.grid_layout)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)

        self.add_controls()
        self.main_widget.setLayout(self.layout)

        # Drag-and-Drop Enablement
        self.setAcceptDrops(True)

    def add_controls(self):
        control_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Sound")
        self.add_button.clicked.connect(self.add_sound)

        self.save_button = QPushButton("Save Profile")
        self.save_button.clicked.connect(self.save_profiles)

        self.load_button = QPushButton("Load Profile")
        self.load_button.clicked.connect(self.load_profile_dialog)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_sounds)

        self.stop_button = QPushButton("Stop Sound")
        self.stop_button.clicked.connect(self.stop_sound)

        self.theme_button = QPushButton("Toggle Theme")
        self.theme_button.clicked.connect(self.toggle_theme)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)

        control_layout.addWidget(self.add_button)
        control_layout.addWidget(self.save_button)
        control_layout.addWidget(self.load_button)
        control_layout.addWidget(self.clear_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(QLabel("Volume"))
        control_layout.addWidget(self.volume_slider)
        control_layout.addWidget(self.theme_button)

        self.layout.addLayout(control_layout)

    def add_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Sound File", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            sound_name, ok = QInputDialog.getText(self, "Sound Name", "Enter a name for the sound:")
            if ok and sound_name:
                self.add_new_sound(sound_name, file_path)

    def add_new_sound(self, sound_name, file_path):
        self.sounds[sound_name] = file_path
        self.add_sound_button(sound_name)

    def add_sound_button(self, sound_name):
        row, col = divmod(self.grid_layout.count(), 3)
        button = QPushButton(sound_name)
        button.clicked.connect(lambda: self.play_sound(sound_name))
        self.grid_layout.addWidget(button, row, col)
        # Assign a keyboard shortcut (e.g., Alt+Number) dynamically
        button.setShortcut(f"Alt+{self.grid_layout.count()}")

    def play_sound(self, sound_name):
        file_path = self.sounds.get(sound_name)
        if file_path:
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not play sound: {e}")

    def stop_sound(self):
        pygame.mixer.music.stop()

    def set_volume(self, value):
        pygame.mixer.music.set_volume(value / 100)

    def save_profiles(self):
        try:
            with open(self.profile_path, "w") as f:
                json.dump(self.sounds, f)
            QMessageBox.information(self, "Success", "Profile saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save profile: {e}")

    def load_profiles(self):
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, "r") as f:
                    self.sounds = json.load(f)
                for sound_name, file_path in self.sounds.items():
                    self.add_sound_button(sound_name)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load profile: {e}")

    def load_profile_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Profile", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r") as f:
                    self.sounds = json.load(f)
                self.clear_sounds()
                for sound_name, file_path in self.sounds.items():
                    self.add_sound_button(sound_name)
                QMessageBox.information(self, "Success", "Profile loaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load profile: {e}")

    def clear_sounds(self):
        self.sounds.clear()
        while self.grid_layout.count():
            widget = self.grid_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def toggle_theme(self):
        current_palette = QApplication.palette()
        new_theme = "dark" if current_palette.color(Qt.Window).value() > 128 else "light"
        if new_theme == "dark":
            QApplication.setStyle("Fusion")
            dark_palette = current_palette
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.Base, QColor(42, 42, 42))
            dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
            QApplication.setPalette(dark_palette)
        else:
            QApplication.setPalette(QApplication.style().standardPalette())

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                sound_name = os.path.basename(file_path)
                self.add_new_sound(sound_name, file_path)


if __name__ == "__main__":
    app = QApplication([])
    soundboard = SoundBoard()
    soundboard.show()
    app.exec_()
