import gi
import os
import json
import random
import threading
from gi.repository import Gtk, Gdk, GObject, Gst, GLib

gi.require_version("Gst", "1.0")
Gst.init(None)

class linxSoundboard:
    def __init__(self):
        self.sounds = {}
        self.key_bindings = {}
        self.profiles = {}
        self.current_profile = "Default"
        self.style_provider = Gtk.CssProvider()
        self.init_ui()
        self.load_profiles()
        self.setup_audio_pipeline()
        GObject.timeout_add(1000, self.change_border_color)

    def init_ui(self):
        # Main window
        self.window = Gtk.Window(title="Opera GX Soundboard")
        self.window.set_default_size(800, 600)
        self.window.connect("destroy", self.on_destroy)
        self.apply_css()

        # Main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(self.main_box)

        # Toolbar
        toolbar = Gtk.Box(spacing=10)
        self.main_box.pack_start(toolbar, False, False, 0)

        # Profile management
        self.profile_combo = Gtk.ComboBoxText()
        self.profile_combo.connect("changed", self.on_profile_changed)
        toolbar.pack_start(self.profile_combo, False, False, 0)

        add_profile_button = Gtk.Button(label="➕ Profile")
        add_profile_button.connect("clicked", self.add_profile)
        toolbar.pack_start(add_profile_button, False, False, 0)

        remove_profile_button = Gtk.Button(label="➖ Profile")
        remove_profile_button.connect("clicked", self.remove_profile)
        toolbar.pack_start(remove_profile_button, False, False, 0)

        # Search bar
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search sounds...")
        self.search_entry.connect("search-changed", self.on_search)
        toolbar.pack_end(self.search_entry, False, False, 0)

        # Sound grid
        self.sound_grid = Gtk.FlowBox()
        self.sound_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        self.sound_grid.set_max_children_per_line(5)
        self.sound_grid.set_homogeneous(True)
        self.main_box.pack_start(self.sound_grid, True, True, 0)

        # Volume control
        volume_box = Gtk.Box(spacing=10)
        self.main_box.pack_start(volume_box, False, False, 0)

        volume_label = Gtk.Label(label="Volume:")
        volume_box.pack_start(volume_label, False, False, 0)

        self.volume_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1, 0.1)
        self.volume_scale.set_value(0.5)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        volume_box.pack_start(self.volume_scale, True, True, 0)

        # Status bar
        self.status_bar = Gtk.Statusbar()
        self.main_box.pack_start(self.status_bar, False, False, 0)

        self.window.show_all()

    def apply_css(self):
        css = """
        window {
            background-color: #1e1e2f;
            border: 3px solid #00ff00;
            border-radius: 10px;
        }
        button {
            background-color: #2a2a3f;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 10px;
            font-size: 12px;
        }
        button:hover {
            background-color: #3a3a4f;
            box-shadow: 0 0 10px #00ff00;
        }
        .sound-button {
            background-color: #2a2a3f;
            color: white;
            border-radius: 10px;
            border: 2px solid #00ff00;
            padding: 20px;
            font-size: 14px;
        }
        .sound-button:hover {
            background-color: #3a3a4f;
            box-shadow: 0 0 15px #00ff00;
        }
        """
        self.style_provider.load_from_data(css.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def setup_audio_pipeline(self):
        self.pipeline = Gst.Pipeline.new("audio-pipeline")
        self.decodebin = Gst.ElementFactory.make("uridecodebin", "decodebin")
        self.volume = Gst.ElementFactory.make("volume", "volume")
        self.sink = Gst.ElementFactory.make("autoaudiosink", "audio-output")
        self.pipeline.add(self.decodebin)
        self.pipeline.add(self.volume)
        self.pipeline.add(self.sink)
        self.decodebin.connect("pad-added", self.on_pad_added)
        self.volume.link(self.sink)

    def load_profiles(self):
        try:
            if os.path.exists("profiles.json"):
                with open("profiles.json", "r") as file:
                    self.profiles = json.load(file)
            else:
                self.profiles = {"Default": {}}
        except (json.JSONDecodeError, IOError) as e:
            self.show_message(f"Error loading profiles: {str(e)}")
            self.profiles = {"Default": {}}
        self.load_profile_dropdown()

    def load_profile_dropdown(self):
        self.profile_combo.remove_all()
        for profile in self.profiles.keys():
            self.profile_combo.append_text(profile)
        self.profile_combo.set_active(0)

    def on_profile_changed(self, combo):
        self.current_profile = combo.get_active_text()
        self.load_profile_sounds()

    def load_profile_sounds(self):
        for child in self.sound_grid.get_children():
            self.sound_grid.remove(child)
        for sound_name, sound_data in self.profiles[self.current_profile].items():
            self.add_sound_button(sound_name, sound_data["file"], sound_data["key"])

    def add_sound_button(self, name, file, key):
        button = Gtk.Button(label=f"{name}\n({key})")
        button.get_style_context().add_class("sound-button")
        button.connect("clicked", lambda w: self.play_sound(file))
        self.sound_grid.add(button)
        self.sounds[name] = file
        self.key_bindings[key] = file
        self.window.show_all()

    def play_sound(self, file):
        self.pipeline.set_state(Gst.State.NULL)
        self.decodebin.set_property("uri", Gst.filename_to_uri(file))
        self.pipeline.set_state(Gst.State.PLAYING)
        self.status_bar.push(0, f"Playing: {os.path.basename(file)}")

    def on_volume_changed(self, scale):
        self.volume.set_property("volume", scale.get_value())

    def change_border_color(self):
        colors = ["#FF00FF", "#00FFFF", "#00FF00", "#FF0000", "#FFFF00"]
        new_color = random.choice(colors)
        css = f"""
        window {{
            border: 3px solid {new_color};
        }}
        """
        self.style_provider.load_from_data(css.encode("utf-8"))
        return True

    def on_destroy(self, widget):
        self.pipeline.set_state(Gst.State.NULL)
        Gtk.main_quit()

    def show_message(self, message):
        dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, message)
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    app = linxSoundboard()
    Gtk.main()
