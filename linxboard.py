import os
import json
import random
import pygame
import webbrowser
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLineEdit, QSlider, QLabel, QGridLayout, QMessageBox,
    QFileDialog, QInputDialog, QMenu, QTabWidget, QDialog, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, QObject, Signal, QSize
from PySide6.QtGui import QColor, QKeySequence, QAction, QIcon

class AdvancedSoundboard(QWidget):
    def __init__(self):
        super().__init__()
        self.sound_player = SoundPlayer()
        self.current_profile = "Default"
        self.profiles = {}
        self.easter_egg_counter = 0
        self.troll_mode_active = False
        self.volume_before_mute = 50
        self.init_ui()
        self.load_profiles()
        self.setup_animations()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle("Ultimate Soundboard 9000")
        self.setMinimumSize(1024, 768)
        self.setWindowIcon(QIcon("icon.png"))
        self.setup_styles()
        
        main_layout = QVBoxLayout()
        
        # Top toolbar
        toolbar = QHBoxLayout()
        self.setup_toolbar(toolbar)
        main_layout.addLayout(toolbar)

        # Category tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        main_layout.addWidget(self.tabs)

        # Control panel
        control_panel = QHBoxLayout()
        self.setup_control_panel(control_panel)
        main_layout.addLayout(control_panel)

        self.setLayout(main_layout)
        self.setup_context_menu()

    def setup_toolbar(self, toolbar):
        # Profile management
        self.profile_combo = QComboBox()
        self.profile_combo.setFixedWidth(150)
        toolbar.addWidget(self.profile_combo)

        add_profile_btn = self.create_toolbar_button("➕", self.add_profile)
        remove_profile_btn = self.create_toolbar_button("➖", self.remove_profile)
        toolbar.addWidget(add_profile_btn)
        toolbar.addWidget(remove_profile_btn)

        # Sound management
        add_sound_btn = self.create_toolbar_button("🎵 Add Sound", self.add_sound_dialog)
        toolbar.addWidget(add_sound_btn)

        # Easter Egg button (hidden)
        self.easter_egg_btn = QPushButton("🐰")
        self.easter_egg_btn.setVisible(False)
        self.easter_egg_btn.clicked.connect(self.activate_easter_egg)
        toolbar.addWidget(self.easter_egg_btn)

        # Troll Mode
        self.troll_mode_btn = QPushButton("😈 Troll Mode")
        self.troll_mode_btn.setCheckable(True)
        self.troll_mode_btn.toggled.connect(self.toggle_troll_mode)
        toolbar.addWidget(self.troll_mode_btn)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search sounds...")
        self.search_bar.textChanged.connect(self.filter_sounds)
        toolbar.addWidget(self.search_bar)

    def setup_control_panel(self, panel):
        # Volume controls
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.update_volume)
        panel.addWidget(QLabel("🔊 Volume:"))
        panel.addWidget(self.volume_slider)

        # Fake volume slider (April Fools)
        self.fake_volume = QSlider(Qt.Horizontal)
        self.fake_volume.setVisible(False)
        panel.addWidget(self.fake_volume)

        # Special effects
        self.loop_checkbox = QCheckBox("🔁 Loop")
        self.random_btn = QPushButton("🎲 Random Sound")
        self.random_btn.clicked.connect(self.play_random_sound)
        panel.addWidget(self.loop_checkbox)
        panel.addWidget(self.random_btn)

    # --------------------------
    # Core Functionality
    # --------------------------
    
    def add_sound_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Sound")
        
        layout = QVBoxLayout()
        name_input = QLineEdit()
        key_input = QLineEdit()
        file_input = QLineEdit()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(lambda: self.select_sound_file(file_input))
        
        layout.addWidget(QLabel("Sound Name:"))
        layout.addWidget(name_input)
        layout.addWidget(QLabel("Hotkey:"))
        layout.addWidget(key_input)
        layout.addWidget(QLabel("Sound File:"))
        layout.addWidget(file_input)
        layout.addWidget(browse_btn)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
        dialog.setLayout(layout)
        
        if dialog.exec():
            self.add_sound(
                name_input.text(),
                file_input.text(),
                key_input.text().upper()
            )

    def add_sound(self, name, path, key):
        # Add to current category
        pass

    # --------------------------
    # Easter Eggs & Troll Features
    # --------------------------
    
    def mousePressEvent(self, event):
        # Hidden area click detector
        if event.pos().x() < 50 and event.pos().y() < 50:
            self.easter_egg_counter += 1
            if self.easter_egg_counter == 5:
                self.easter_egg_btn.setVisible(True)
                QMessageBox.information(self, "Surprise!", "You found the bunny! 🐇")
        super().mousePressEvent(event)

    def activate_easter_egg(self):
        self.play_sound("secret_sound.mp3")
        webbrowser.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def toggle_troll_mode(self, active):
        self.troll_mode_active = active
        if active:
            self.troll_timer = QTimer()
            self.troll_timer.timeout.connect(self.play_troll_sound)
            self.troll_timer.start(random.randint(5000, 15000))
            
            # Switch to fake volume control
            self.volume_slider.setVisible(False)
            self.fake_volume.setVisible(True)
        else:
            self.troll_timer.stop()
            self.volume_slider.setVisible(True)
            self.fake_volume.setVisible(False)

    def play_troll_sound(self):
        if self.profiles[self.current_profile]:
            random_sound = random.choice(list(self.profiles[self.current_profile].values()))
            self.sound_player.play(random_sound["file"], self.volume_slider.value()/100)

    # --------------------------
    # Additional Features
    # --------------------------
    
    def setup_context_menu(self):
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        
        # Add custom actions
        panic_action = QAction("🚨 Panic Button", self)
        panic_action.triggered.connect(self.stop_all_sounds)
        self.addAction(panic_action)
        
        airhorn_action = QAction("📯 Mega Airhorn", self)
        airhorn_action.triggered.connect(lambda: self.play_sound("airhorn.mp3"))
        self.addAction(airhorn_action)

    def stop_all_sounds(self):
        pygame.mixer.stop()
        self.sound_player.current_sound = None

    def play_random_sound(self):
        # Implement random sound selection
        pass

    # --------------------------
    # Settings Management
    # --------------------------
    
    def load_settings(self):
        try:
            with open("settings.json") as f:
                settings = json.load(f)
                self.restoreGeometry(settings["geometry"])
        except:
            pass

    def save_settings(self):
        settings = {
            "geometry": self.saveGeometry(),
            "volume": self.volume_slider.value()
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    board = AdvancedSoundboard()
    board.show()
    app.exec()
