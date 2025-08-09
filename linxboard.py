#!/usr/bin/env python3
import os, sys, json, random
from pathlib import Path
os.environ.setdefault("SDL_AUDIODRIVER", "pulseaudio")  # PipeWire uses pulse shim

import pygame
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QLineEdit, QSlider, QLabel, QGridLayout, QMessageBox, QFileDialog,
    QTabWidget, QDialog, QCheckBox, QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QTimer, QSize, QStandardPaths
from PySide6.QtGui import QAction, QIcon, QShortcut, QKeySequence

APP_NAME = "Ultimate Soundboard 9000"
AUDIO_EXTS = (".wav", ".mp3", ".ogg", ".flac")

# ---------- audio ----------
class SoundPlayer:
    def __init__(self):
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.init()
            pygame.mixer.set_num_channels(32)
        except Exception as e:
            raise SystemExit(f"Audio init failed: {e}")
        self.cache: dict[str, pygame.mixer.Sound] = {}

    def load(self, path: str) -> pygame.mixer.Sound:
        p = str(Path(path))
        if p not in self.cache:
            self.cache[p] = pygame.mixer.Sound(p)
        return self.cache[p]

    def play(self, path: str, volume: float, loop: bool):
        snd = self.load(path)
        snd.set_volume(max(0.0, min(1.0, volume)))
        loops = -1 if loop else 0
        snd.play(loops=loops)

    def stop_all(self):
        pygame.mixer.stop()

    def set_master_volume(self, v: float):
        for i in range(pygame.mixer.get_num_channels()):
            ch = pygame.mixer.Channel(i)
            ch.set_volume(v)

# ---------- ui ----------
class AdvancedSoundboard(QWidget):
    def __init__(self):
        super().__init__()
        self.sound_player = SoundPlayer()
        self.config_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)) / "soundboard9000"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.config_dir / "settings.json"
        self.profiles_path = self.config_dir / "profiles.json"

        self.current_profile = "Default"
        self.profiles: dict[str, dict] = {}   # name -> {"tabs": {tab: {sound_name: {"file":..., "key":...}}}}
        self.buttons: dict[str, dict] = {}    # runtime widgets per tab
        self.shortcuts: list[QShortcut] = []

        self.easter_egg_counter = 0
        self.troll_mode_active = False
        self.troll_timer = None

        self.init_ui()
        self.load_profiles()
        self.populate_ui()
        self.load_settings()

    # ----- layout -----
    def init_ui(self):
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1024, 700)
        try:
            self.setWindowIcon(QIcon.fromTheme("multimedia-audio-player"))
        except Exception:
            pass
        self.setup_styles()

        main = QVBoxLayout(self)

        # toolbar
        tb = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.setFixedWidth(200)
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        tb.addWidget(self.profile_combo)

        tb.addWidget(self._btn("➕ Profile", self.add_profile))
        tb.addWidget(self._btn("➖ Profile", self.remove_profile))
        tb.addWidget(self._btn("🎵 Add Sound", self.add_sound_dialog))
        tb.addWidget(self._btn("📁 Import", self.import_profile))
        tb.addWidget(self._btn("💾 Export", self.export_profile))

        self.troll_mode_btn = QPushButton("😈 Troll Mode")
        self.troll_mode_btn.setCheckable(True)
        self.troll_mode_btn.toggled.connect(self.toggle_troll_mode)
        tb.addWidget(self.troll_mode_btn)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search…")
        self.search_bar.textChanged.connect(self.filter_sounds)
        tb.addWidget(self.search_bar)
        main.addLayout(tb)

        # tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        main.addWidget(self.tabs)

        # controls
        ctl = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.update_volume)
        ctl.addWidget(QLabel("Volume"))
        ctl.addWidget(self.volume_slider)

        self.loop_checkbox = QCheckBox("Loop")
        ctl.addWidget(self.loop_checkbox)

        self.random_btn = QPushButton("Random")
        self.random_btn.clicked.connect(self.play_random_sound)
        ctl.addWidget(self.random_btn)

        stop = QPushButton("Panic Stop")
        stop.clicked.connect(self.stop_all_sounds)
        ctl.addWidget(stop)
        main.addLayout(ctl)

        # context
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        panic_action = QAction("🚨 Panic Stop", self)
        panic_action.triggered.connect(self.stop_all_sounds)
        self.addAction(panic_action)
        airhorn_action = QAction("📯 Airhorn", self)
        airhorn_action.triggered.connect(lambda: self.play_path_dialog())
        self.addAction(airhorn_action)

        # tray
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self.windowIcon(), self)
            menu = QMenu()
            a_show = menu.addAction("Show")
            a_show.triggered.connect(self.showNormal)
            a_stop = menu.addAction("Panic Stop")
            a_stop.triggered.connect(self.stop_all_sounds)
            a_quit = menu.addAction("Quit")
            a_quit.triggered.connect(QApplication.instance().quit)
            self.tray.setContextMenu(menu)
            self.tray.show()

    def setup_styles(self):
        self.setStyleSheet("""
        QWidget { font-size: 14px; }
        QPushButton { padding: 8px 12px; }
        QTabBar::tab { min-width: 140px; padding: 10px; }
        """)

    def _btn(self, text, slot):
        b = QPushButton(text)
        b.clicked.connect(slot)
        return b

    # ----- profiles/tabs -----
    def ensure_default(self):
        if not self.profiles:
            self.profiles = {"Default": {"tabs": {"Main": {}}}}
        if self.current_profile not in self.profiles:
            self.current_profile = "Default"

    def populate_ui(self):
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        for p in sorted(self.profiles.keys()):
            self.profile_combo.addItem(p)
        self.profile_combo.setCurrentText(self.current_profile)
        self.profile_combo.blockSignals(False)
        self.rebuild_tabs()

    def rebuild_tabs(self):
        self.tabs.clear()
        self.buttons.clear()
        prof = self.profiles[self.current_profile]
        for tab_name in prof["tabs"].keys():
            w = QWidget()
            grid = QGridLayout(w)
            grid.setAlignment(Qt.AlignTop)
            self.tabs.addTab(w, tab_name)
            self.buttons[tab_name] = {}
            # add existing sounds
            for name, meta in prof["tabs"][tab_name].items():
                self._add_sound_button(tab_name, name, meta["file"], meta.get("key",""))
        # add + tab button row
        self.tabs.currentChanged.connect(lambda _: None)

    def on_profile_changed(self, name):
        self.current_profile = name
        self.rebuild_tabs()
        self.rebind_shortcuts()

    def add_profile(self):
        name, ok = QFileDialog.getSaveFileName(self, "New Profile Name as file stub", str(self.config_dir / "NewProfile.json"), "Profile (*.json)")
        if not ok or not name:
            return
        base = Path(name).stem
        if base in self.profiles:
            QMessageBox.warning(self, "Exists", "Profile already exists")
            return
        self.profiles[base] = {"tabs": {"Main": {}}}
        self.current_profile = base
        self.save_profiles()
        self.populate_ui()

    def remove_profile(self):
        if self.current_profile == "Default":
            QMessageBox.information(self, "Blocked", "Default cannot be removed")
            return
        del self.profiles[self.current_profile]
        self.current_profile = "Default"
        self.save_profiles()
        self.populate_ui()

    # ----- sounds -----
    def add_sound_dialog(self):
        tab = self.current_tab()
        if not tab:
            return
        file, _ = QFileDialog.getOpenFileName(self, "Select sound", str(Path.home()), "Audio (*.wav *.mp3 *.ogg *.flac)")
        if not file:
            return
        name = Path(file).stem
        key, ok = QInputDialogWithDefault.get_text(self, "Hotkey (optional)", "e.g. Ctrl+1 or F1", "")
        if ok is False:
            return
        self.add_sound(name, file, key)

    def add_sound(self, name: str, path: str, key: str = ""):
        if not path or not Path(path).exists() or Path(path).suffix.lower() not in AUDIO_EXTS:
            QMessageBox.warning(self, "Invalid", "Pick a valid audio file")
            return
        prof = self.profiles[self.current_profile]
        tab = self.current_tab() or "Main"
        prof["tabs"].setdefault(tab, {})
        prof["tabs"][tab][name] = {"file": path, "key": key}
        self._add_sound_button(tab, name, path, key)
        self.save_profiles()
        self.rebind_shortcuts()

    def _add_sound_button(self, tab: str, name: str, path: str, key: str):
        # grid placement
        w: QWidget = self.tabs.widget(self.tab_index_by_name(tab))
        grid: QGridLayout = w.layout()
        btn = QPushButton(name)
        btn.setMinimumSize(QSize(140, 48))
        btn.clicked.connect(lambda: self.play_path(path))
        row = len(self.buttons[tab]) // 3
        col = len(self.buttons[tab]) % 3
        grid.addWidget(btn, row, col)
        self.buttons[tab][name] = {"button": btn, "file": path, "key": key}
        # per-item context menu
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos, b=btn, n=name: self.sound_ctx_menu(b, n, tab))
        # optional shortcut
        if key:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda p=path: self.play_path(p))
            self.shortcuts.append(sc)

    def rebind_shortcuts(self):
        for sc in self.shortcuts:
            sc.setParent(None)
        self.shortcuts.clear()
        prof = self.profiles[self.current_profile]
        for tab, items in prof["tabs"].items():
            for name, meta in items.items():
                k = meta.get("key", "")
                if k:
                    sc = QShortcut(QKeySequence(k), self)
                    sc.activated.connect(lambda p=meta["file"]: self.play_path(p))
                    self.shortcuts.append(sc)

    def sound_ctx_menu(self, btn: QPushButton, name: str, tab: str):
        m = QMenu(self)
        a_play = m.addAction("Play")
        a_key = m.addAction("Set Hotkey")
        a_ren = m.addAction("Rename")
        a_del = m.addAction("Delete")
        act = m.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        if act == a_play:
            self.play_path(self.buttons[tab][name]["file"])
        elif act == a_key:
            key, ok = QInputDialogWithDefault.get_text(self, "Hotkey", "e.g. Ctrl+R", self.buttons[tab][name].get("key",""))
            if ok:
                self.profiles[self.current_profile]["tabs"][tab][name]["key"] = key
                self.save_profiles(); self.rebind_shortcuts()
        elif act == a_ren:
            new, ok = QInputDialogWithDefault.get_text(self, "Rename", "New name", name)
            if ok and new:
                meta = self.profiles[self.current_profile]["tabs"][tab].pop(name)
                self.profiles[self.current_profile]["tabs"][tab][new] = meta
                btn.setText(new)
                self.buttons[tab][new] = self.buttons[tab].pop(name)
                self.save_profiles()
        elif act == a_del:
            del self.profiles[self.current_profile]["tabs"][tab][name]
            self.save_profiles()
            btn.deleteLater()
            del self.buttons[tab][name]

    def current_tab(self) -> str|None:
        idx = self.tabs.currentIndex()
        if idx < 0: return None
        return self.tabs.tabText(idx)

    def tab_index_by_name(self, name: str) -> int:
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == name:
                return i
        return 0

    # ----- actions -----
    def play_path(self, path: str):
        try:
            self.sound_player.play(path, self.volume_slider.value()/100.0, self.loop_checkbox.isChecked())
        except Exception as e:
            QMessageBox.critical(self, "Play error", str(e))

    def play_path_dialog(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select sound", str(Path.home()), "Audio (*.wav *.mp3 *.ogg *.flac)")
        if f:
            self.play_path(f)

    def stop_all_sounds(self):
        self.sound_player.stop_all()

    def play_random_sound(self):
        prof = self.profiles.get(self.current_profile, {})
        tabs = prof.get("tabs", {})
        items = []
        for t in tabs.values():
            for name, meta in t.items():
                items.append(meta["file"])
        if not items:
            return
        self.play_path(random.choice(items))

    def filter_sounds(self, text: str):
        text = text.lower()
        for tab, items in self.buttons.items():
            for name, meta in items.items():
                meta["button"].setVisible(text in name.lower())

    def update_volume(self, v: int):
        self.sound_player.set_master_volume(v/100.0)

    # ----- troll mode -----
    def toggle_troll_mode(self, active: bool):
        if active:
            if self.troll_timer is None:
                self.troll_timer = QTimer(self)
                self.troll_timer.timeout.connect(self._troll_tick)
            self._arm_troll()
        else:
            if self.troll_timer:
                self.troll_timer.stop()

    def _arm_troll(self):
        if not self.troll_timer: return
        self.troll_timer.start(random.randint(5000, 15000))

    def _troll_tick(self):
        self.play_random_sound()
        self._arm_troll()

    # ----- persistence -----
    def load_profiles(self):
        self.ensure_default()
        if self.profiles_path.exists():
            try:
                self.profiles = json.loads(self.profiles_path.read_text())
            except Exception:
                pass
        self.ensure_default()

    def save_profiles(self):
        self.profiles_path.write_text(json.dumps(self.profiles, indent=2))

    def load_settings(self):
        if self.settings_path.exists():
            try:
                s = json.loads(self.settings_path.read_text())
                if "geometry" in s:
                    self.restoreGeometry(bytes.fromhex(s["geometry"]))
                if "volume" in s:
                    self.volume_slider.setValue(int(s["volume"]))
                if "profile" in s and s["profile"] in self.profiles:
                    self.current_profile = s["profile"]
                    self.populate_ui()
            except Exception:
                pass

    def save_settings(self):
        s = {
            "geometry": self.saveGeometry().toHex().data().decode(),
            "volume": self.volume_slider.value(),
            "profile": self.current_profile
        }
        self.settings_path.write_text(json.dumps(s, indent=2))

    def closeEvent(self, e):
        self.save_settings()
        super().closeEvent(e)

    # ----- import/export -----
    def export_profile(self):
        file, _ = QFileDialog.getSaveFileName(self, "Export profile JSON", str(Path.home()/f"{self.current_profile}.json"), "JSON (*.json)")
        if not file: return
        data = {self.current_profile: self.profiles[self.current_profile]}
        Path(file).write_text(json.dumps(data, indent=2))

    def import_profile(self):
        file, _ = QFileDialog.getOpenFileName(self, "Import profile JSON", str(Path.home()), "JSON (*.json)")
        if not file: return
        try:
            data = json.loads(Path(file).read_text())
            # accept root or {name:profile}
            if "tabs" in data:
                name = Path(file).stem
                self.profiles[name] = data
                self.current_profile = name
            else:
                for k, v in data.items():
                    self.profiles[k] = v
                    self.current_profile = k
            self.save_profiles()
            self.populate_ui()
        except Exception as e:
            QMessageBox.critical(self, "Import error", str(e))

    # ----- easter egg (kept minimal) -----
    def mousePressEvent(self, event):
        if event.pos().x() < 50 and event.pos().y() < 50:
            self.easter_egg_counter += 1
            if self.easter_egg_counter == 5:
                QMessageBox.information(self, "Surprise", "Found it")
        super().mousePressEvent(event)

# small helper
class QInputDialogWithDefault:
    @staticmethod
    def get_text(parent, title, label, default=""):
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(parent, title, label, text=default)
        return text, ok

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = AdvancedSoundboard()
    w.show()
    sys.exit(app.exec())
