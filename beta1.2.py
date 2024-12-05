import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,
    QGridLayout, QFileDialog, QMessageBox, QLineEdit, QLabel, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
import pygame

# Initialize pygame mixer
pygame.mixer.init()

class SoundBoard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux SoundBoard")
        self.setGeometry(200, 200, 600, 400)

        self.sounds = {}  # Store sound name and file path
        self.profile_path = "soundboard_profiles.json"
        self.load_profiles()

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        
        self.layout = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.layout.addLayout(self.grid_layout)
        
        self.add_controls()
        self.main_widget.setLayout(self.layout)

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

        control_layout.addWidget(self.add_button)
        control_layout.addWidget(self.save_button)
        control_layout.addWidget(self.load_button)
        control_layout.addWidget(self.clear_button)

        self.layout.addLayout(control_layout)

    def add_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Sound File", "", "Audio Files (*.wav *.mp3)")
        if file_path:
            sound_name, ok = QLineEdit.getText(self, "Sound Name", "Enter a name for the sound:")
            if ok and sound_name:
                self.sounds[sound_name] = file_path
                self.add_sound_button(sound_name)

    def add_sound_button(self, sound_name):
        row, col = divmod(len(self.grid_layout.children()), 3)
        button = QPushButton(sound_name)
        button.clicked.connect(lambda: self.play_sound(sound_name))
        self.grid_layout.addWidget(button, row, col)

    def play_sound(self, sound_name):
        file_path = self.sounds.get(sound_name)
        if file_path:
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not play sound: {e}")

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
                for sound_name in self.sounds:
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
                for sound_name in self.sounds:
                    self.add_sound_button(sound_name)
                QMessageBox.information(self, "Success", "Profile loaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not load profile: {e}")

    def clear_sounds(self):
        self.sounds.clear()
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    soundboard = SoundBoard()
    soundboard.show()
    sys.exit(app.exec_())
