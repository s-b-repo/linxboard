
import gi
import os
import json
import random
from gi.repository import Gtk, Gdk, GObject, Gst

gi.require_version("Gst", "1.0")
Gst.init(None)

class LinxboardApp:
    MAX_SOUNDS_PER_PROFILE = 10  # Configurable max number of sounds per profile

    def __init__(self):
        self.sounds = {}
        self.key_bindings = {}
        self.profiles = {}
        self.current_profile = "Default"
        self.init_ui()
        self.load_profiles()
        self.setup_audio_pipeline()
        GObject.timeout_add(1000, self.change_border_color)

    def init_ui(self):
        # Set up the main window
        self.window = Gtk.Window(title="Linxboard")
        self.window.set_default_size(600, 400)
        self.window.connect("destroy", Gtk.main_quit)

        # Enable drag-and-drop for sound files
        self.window.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.window.drag_dest_add_uri_targets()
        self.window.connect("drag-data-received", self.on_drag_data_received)

        # Add CSS for neon border and dynamic background
        self.apply_css()

        # Main layout with toolbar, profile selector, and sound buttons
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window.add(vbox)

        # Toolbar with profile management and settings
        toolbar = Gtk.Box(spacing=6)
        vbox.pack_start(toolbar, False, False, 0)

        # Dropdown for profile selection
        self.profile_combo = Gtk.ComboBoxText()
        self.profile_combo.connect("changed", self.on_profile_changed)
        toolbar.pack_start(self.profile_combo, True, True, 0)
        self.load_profile_dropdown()

        # Buttons for adding/removing sounds and settings
        add_button = Gtk.Button(label="Add Sound")
        add_button.connect("clicked", self.add_sound)
        toolbar.pack_start(add_button, True, True, 0)

        remove_button = Gtk.Button(label="Remove Sound")
        remove_button.connect("clicked", self.remove_sound)
        toolbar.pack_start(remove_button, True, True, 0)

        # Sound button area
        self.sound_box = Gtk.Box(spacing=6)
        vbox.pack_start(self.sound_box, True, True, 0)

        # Volume control
        self.volume_button = Gtk.VolumeButton()
        self.volume_button.connect("value-changed", self.on_volume_changed)
        vbox.pack_start(self.volume_button, False, False, 0)

        # Display the window
        self.window.show_all()

    def apply_css(self):
        # Apply CSS for neon border and customizable background
        style_provider = Gtk.CssProvider()
        css = """
        window {
            background: #222;
            border: 3px solid #00ff00;  /* Initial border color */
            border-radius: 10px;
        }
        button {
            background-color: #444;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 5px;
        }
        button:hover {
            background-color: #555;
            box-shadow: 0 0 10px #00ff00;
        }
        """
        style_provider.load_from_data(css.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def setup_audio_pipeline(self):
        # Setup GStreamer pipeline for playback
        self.pipeline = Gst.Pipeline.new("audio-pipeline")
        self.decodebin = Gst.ElementFactory.make("uridecodebin", "decodebin")
        self.sink = Gst.ElementFactory.make("autoaudiosink", "audio-output")
        self.volume = Gst.ElementFactory.make("volume", "volume")
        self.pipeline.add(self.decodebin)
        self.pipeline.add(self.volume)
        self.pipeline.add(self.sink)
        self.decodebin.connect("pad-added", self.on_pad_added)
        self.volume.link(self.sink)

    def load_profiles(self):
        # Load profiles from a configuration file (JSON)
        try:
            if os.path.exists("profiles.json"):
                with open("profiles.json", "r") as file:
                    self.profiles = json.load(file)
            else:
                self.profiles = {"Default": {}}
            self.load_profile_dropdown()
        except json.JSONDecodeError:
            self.show_message("Error loading profiles.json. Check file format.")

    def load_profile_dropdown(self):
        # Load profiles into the dropdown
        self.profile_combo.remove_all()
        for profile in self.profiles.keys():
            self.profile_combo.append_text(profile)
        self.profile_combo.set_active(0)

    def add_sound(self, widget=None, sound_file=None):
        # Adding sound dialog with file chooser
        if not sound_file:
            dialog = Gtk.FileChooserDialog(
                title="Select Sound File",
                parent=self.window,
                action=Gtk.FileChooserAction.OPEN,
                buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
            )
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                sound_file = dialog.get_filename()
            dialog.destroy()

        if sound_file and os.path.isfile(sound_file):
            name = self.request_input("Enter Sound Name")
            if name and not self.is_sound_duplicate(name):
                key = self.request_key_binding()
                if key and not self.is_key_binding_duplicate(key):
                    if len(self.profiles[self.current_profile]) < self.MAX_SOUNDS_PER_PROFILE:
                        self.profiles[self.current_profile][name] = {"file": sound_file, "key": key}
                        self.add_sound_button(name, sound_file, key)
                        self.save_profiles()
                    else:
                        self.show_message(f"Maximum of {self.MAX_SOUNDS_PER_PROFILE} sounds reached in this profile.")
                else:
                    self.show_message("Key binding already in use.")
            else:
                self.show_message("Sound with this name already exists.")
        elif sound_file:
            self.show_message("Invalid file selected.")

    def add_sound_button(self, name, file, key):
        button = Gtk.Button(label=name)
        button.connect("clicked", lambda w: self.play_sound(file))
        self.sound_box.pack_start(button, True, True, 0)
        self.sounds[name] = file
        self.key_bindings[key] = file
        self.window.show_all()

    def save_profiles(self):
        try:
            with open("profiles.json", "w") as file:
                json.dump(self.profiles, file)
        except IOError:
            self.show_message("Error saving profiles.")

    def play_sound(self, file):
        # Stop pipeline if playing
        self.pipeline.set_state(Gst.State.NULL)
        # Set URI and play
        self.decodebin.set_property("uri", Gst.filename_to_uri(file))
        self.pipeline.set_state(Gst.State.PLAYING)

    def remove_sound(self, widget):
        # Create a dialog to select which sound to remove
        dialog = Gtk.Dialog(title="Remove Sound", parent=self.window)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        combo = Gtk.ComboBoxText()
        for sound_name in self.profiles[self.current_profile].keys():
            combo.append_text(sound_name)
        dialog.get_content_area().pack_start(combo, True, True, 0)
        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            selected_sound = combo.get_active_text()
            if selected_sound:
                del self.profiles[self.current_profile][selected_sound]
                self.sound_box.foreach(lambda w: self.sound_box.remove(w))
                self.load_profile_sounds()
                self.save_profiles()
        dialog.destroy()

    def on_profile_changed(self, combo):
        self.current_profile = combo.get_active_text()
        self.load_profile_sounds()

    def load_profile_sounds(self):
        self.sound_box.foreach(lambda w: self.sound_box.remove(w))
        for sound_name, sound_data in self.profiles[self.current_profile].items():
            self.add_sound_button(sound_name, sound_data["file"], sound_data["key"])

    def on_pad_added(self, element, pad):
        if not self.volume.get_static_pad("src").is_linked():
            pad.link(self.volume.get_static_pad("sink"))

    def request_input(self, message):
        dialog = Gtk.Dialog(title=message, parent=self.window)
        entry = Gtk.Entry()
        dialog.get_content_area().pack_start(entry, True, True, 0)
        dialog.show_all()
        response = dialog.run()
        text = entry.get_text() if response == Gtk.ResponseType.OK else ""
        dialog.destroy()
        return text

    def request_key_binding(self):
        dialog = Gtk.Dialog(title="Press Key for Binding", parent=self.window)
        label = Gtk.Label(label="Press the key combination:")
        dialog.get_content_area().pack_start(label, True, True, 0)
        dialog.show_all()
        key = None

        def on_key_press(widget, event):
            nonlocal key
            key = Gdk.keyval_name(event.keyval)
            dialog.response(Gtk.ResponseType.OK)

        self.window.connect("key-press-event", on_key_press)
        response = dialog.run()
        self.window.disconnect_by_func(on_key_press)
        dialog.destroy()
        return key if response == Gtk.ResponseType.OK else None

    def is_sound_duplicate(self, name):
        return name in self.profiles[self.current_profile]

    def is_key_binding_duplicate(self, key):
        return key in self.key_bindings

    def on_volume_changed(self, widget, value):
        self.volume.set_property("volume", value)

    def show_message(self, message):
        dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, message)
        dialog.run()
        dialog.destroy()

    def change_border_color(self):
        colors = ["#FF00FF", "#00FFFF", "#00FF00", "#FF0000", "#FFFF00"]
        new_color = random.choice(colors)
        css = f"""
        window {{
            border: 3px solid {new_color};
        }}
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        return True

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        uris = data.get_uris()
        for uri in uris:
            path = Gdk.filename_from_uri(uri)[0]
            if path and os.path.isfile(path):
                self.add_sound(sound_file=path)

if __name__ == "__main__":
    app = LinxboardApp()
    Gtk.main()
