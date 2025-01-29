import os
import json
import random
import pygame
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLineEdit, QSlider, QLabel, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QColor

class SoundPlayer(QObject):
    sound_stopped = Signal()

    def __init__(self):
        super().__init__()
        pygame.mixer.init()
        self.current_sound = None

    def play(self, file_path, volume):
        if self.current_sound:
            self.current_sound.stop()
        self.current_sound = pygame.mixer.Sound(file_path)
        self.current_sound.set_volume(volume)
        self.current_sound.play()
        self.sound_stopped.emit()

class SoundButton(QPushButton):
    def __init__(self, text, file_path, key_binding, parent=None):
        super().__init__(text, parent)
        self.file_path = file_path
        self.key_binding = key_binding
        self.setMinimumSize(120, 80)
        self.setStyleSheet("""
            SoundButton {
                background-color: #2a2a3f;
                color: white;
                border: 2px solid #00ff00;
                border-radius: 10px;
                font-size: 14px;
                padding: 10px;
            }
            SoundButton:hover {
                background-color: #3a3a4f;
                border: 2px solid #00ff00;
                box-shadow: 0 0 15px #00ff00;
            }
        """)

class Soundboard(QWidget):
    def __init__(self):
        super().__init__()
        self.sound_player = SoundPlayer()
        self.current_profile = "Default"
        self.profiles = {}
        self.active_buttons = []
        self.colors = ["#FF00FF", "#00FFFF", "#00FF00", "#FF0000", "#FFFF00"]
        
        self.init_ui()
        self.load_profiles()
        self.setup_animations()

    def init_ui(self):
        self.setWindowTitle("Opera GX Soundboard")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: white;
            }
            QComboBox, QLineEdit {
                background-color: #2a2a3f;
                border: 1px solid #00ff00;
                border-radius: 5px;
                padding: 5px;
            }
            QSlider::groove:horizontal {
                background: #2a2a3f;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00ff00;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
        """)

        main_layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self.load_profile)
        toolbar.addWidget(self.profile_combo)

        add_profile_btn = QPushButton("➕ Profile")
        add_profile_btn.clicked.connect(self.add_profile)
        toolbar.addWidget(add_profile_btn)

        remove_profile_btn = QPushButton("➖ Profile")
        remove_profile_btn.clicked.connect(self.remove_profile)
        toolbar.addWidget(remove_profile_btn)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search sounds...")
        self.search_bar.textChanged.connect(self.filter_sounds)
        toolbar.addWidget(self.search_bar)

        main_layout.addLayout(toolbar)

        # Sound grid
        self.sound_grid = QGridLayout()
        self.sound_grid.setSpacing(15)
        main_layout.addLayout(self.sound_grid)

        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.update_volume)
        volume_layout.addWidget(self.volume_slider)
        main_layout.addLayout(volume_layout)

        self.setLayout(main_layout)

    def setup_animations(self):
        self.border_color_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_border)
        self.timer.start(1000)

    def animate_border(self):
        self.border_color_index = (self.border_color_index + 1) % len(self.colors)
        self.setStyleSheet(f"""
            QWidget {{
                border: 3px solid {self.colors[self.border_color_index]};
                border-radius: 10px;
            }}
            {self.styleSheet()}
        """)

    def load_profiles(self):
        try:
            if os.path.exists("profiles.json"):
                with open("profiles.json", "r") as f:
                    self.profiles = json.load(f)
            else:
                self.profiles = {"Default": {}}
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load profiles: {str(e)}")
        
        self.profile_combo.clear()
        self.profile_combo.addItems(self.profiles.keys())
        self.load_profile()

    def save_profiles(self):
        try:
            with open("profiles.json", "w") as f:
                json.dump(self.profiles, f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profiles: {str(e)}")

    def load_profile(self):
        self.current_profile = self.profile_combo.currentText()
        self.clear_sound_grid()
        profile_data = self.profiles.get(self.current_profile, {})
        
        row, col = 0, 0
        for name, data in profile_data.items():
            btn = SoundButton(f"{name}\n({data['key']})", data["file"], data["key"])
            btn.clicked.connect(lambda _, p=data["file"]: self.sound_player.play(p, self.volume_slider.value()/100))
            self.sound_grid.addWidget(btn, row, col)
            self.active_buttons.append(btn)
            col = (col + 1) % 4
            if col == 0:
                row += 1

    def clear_sound_grid(self):
        for btn in self.active_buttons:
            btn.deleteLater()
        self.active_buttons.clear()

    def filter_sounds(self):
        search_text = self.search_bar.text().lower()
        for btn in self.active_buttons:
            visible = search_text in btn.text().lower()
            btn.setVisible(visible)

    def update_volume(self, value):
        if self.sound_player.current_sound:
            self.sound_player.current_sound.set_volume(value/100)

    def add_profile(self):
        name, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if ok and name:
            self.profiles[name] = {}
            self.profile_combo.addItem(name)
            self.save_profiles()

    def remove_profile(self):
        current = self.profile_combo.currentText()
        if current == "Default":
            QMessageBox.warning(self, "Warning", "Cannot delete default profile!")
            return
            
        confirm = QMessageBox.question(
            self, "Confirm Delete", f"Delete profile '{current}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            del self.profiles[current]
            self.profile_combo.removeItem(self.profile_combo.currentIndex())
            self.save_profiles()

if __name__ == "__main__":
    app = QApplication([])
    window = Soundboard()
    window.show()
    app.exec()
