import gi
import os
from gi.repository import Gtk, GObject, Gst, Gdk

gi.require_version('Gst', '1.0')

class LinxboardApp:
    def __init__(self):
        # Initialize GTK and GStreamer
        Gtk.init()
        Gst.init(None)

        # Create the main window
        self.window = Gtk.Window(title="Linxboard")
        self.window.connect("destroy", Gtk.main_quit)
        self.window.set_default_size(400, 300)
        self.window.connect("key-press-event", self.on_key_press)

        # Create a box to hold the buttons
        self.box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        self.window.add(self.box)

        # Create a dictionary to hold the sound files, buttons, and key bindings
        self.sounds = {}
        self.buttons = {}
        self.key_bindings = {}

        # Initialize pipeline
        self.pipeline = Gst.Pipeline.new("audio-player")

        # Create GStreamer elements
        self.decodebin = Gst.ElementFactory.make("uridecodebin", "decodebin")
        self.pipeline.add(self.decodebin)
        self.sink = Gst.ElementFactory.make("autoaudiosink", "audio-output")
        self.pipeline.add(self.sink)

        # Link elements
        self.decodebin.connect("pad-added", self.on_pad_added)

        # Add control buttons for adding/removing sounds
        control_box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.HORIZONTAL)
        self.box.pack_start(control_box, False, False, 0)

        add_button = Gtk.Button(label="Add Sound")
        add_button.connect("clicked", self.add_sound)
        control_box.pack_start(add_button, True, True, 0)

        remove_button = Gtk.Button(label="Remove Sound")
        remove_button.connect("clicked", self.remove_sound)
        control_box.pack_start(remove_button, True, True, 0)

        # Create a volume control
        volume_control = Gtk.VolumeButton()
        volume_control.set_value(1.0)
        volume_control.connect("value-changed", self.on_volume_changed)
        self.box.pack_start(volume_control, False, False, 0)

        # Display the window
        self.window.show_all()

    def on_pad_added(self, element, pad):
        sink_pad = self.sink.get_static_pad("sink")
        if not sink_pad.is_linked():
            pad.link(sink_pad)

    def play_sound(self, file):
        # Stop the pipeline if it's playing
        self.pipeline.set_state(Gst.State.NULL)
        
        # Set the URI to the file
        self.decodebin.set_property("uri", Gst.filename_to_uri(file))
        
        # Start playing
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_volume_changed(self, widget, value):
        volume = self.pipeline.get_by_name("volume")
        if volume:
            volume.set_property("volume", value)

    def add_sound(self, widget):
        # Create a file chooser dialog to select the sound file
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

            # Get sound name from the user
            name_dialog = Gtk.Dialog(title="Enter Sound Name", parent=self.window)
            name_dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
            name_entry = Gtk.Entry()
            name_dialog.get_content_area().pack_start(name_entry, True, True, 0)
            name_dialog.show_all()
            response = name_dialog.run()

            if response == Gtk.ResponseType.OK:
                sound_name = name_entry.get_text()
                self.sounds[sound_name] = sound_file

                # Add a new button for the sound
                button = Gtk.Button(label=sound_name)
                button.connect("clicked", lambda w, f=sound_file: self.play_sound(f))
                self.box.pack_start(button, True, True, 0)
                self.buttons[sound_name] = button
                self.window.show_all()
            name_dialog.destroy()

            # Bind the sound to a key combination
            self.bind_key(sound_name)

    def remove_sound(self, widget):
        # Create a dialog to select which sound to remove
        dialog = Gtk.Dialog(title="Remove Sound", parent=self.window)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

        combo = Gtk.ComboBoxText()
        for sound_name in self.sounds.keys():
            combo.append_text(sound_name)
        dialog.get_content_area().pack_start(combo, True, True, 0)
        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            selected_sound = combo.get_active_text()
            if selected_sound:
                # Remove the sound from the dictionary and the button
                self.sounds.pop(selected_sound, None)
                button = self.buttons.pop(selected_sound, None)
                if button:
                    self.box.remove(button)
                self.key_bindings.pop(selected_sound, None)
                self.window.show_all()
        dialog.destroy()

    def bind_key(self, sound_name):
        # Create a dialog to input the key combination
        dialog = Gtk.Dialog(title="Bind Key Combination", parent=self.window)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        label = Gtk.Label(label="Press the key combination:")
        dialog.get_content_area().pack_start(label, True, True, 0)
        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            # Wait for the key press
            event = Gdk.EventKey()
            keyval = event.keyval
            key_name = Gdk.keyval_name(keyval)
            self.key_bindings[key_name] = self.sounds[sound_name]
        dialog.destroy()

    def on_key_press(self, widget, event):
        # Check if the key press matches any bindings
        key_name = Gdk.keyval_name(event.keyval)
        if key_name in self.key_bindings:
            self.play_sound(self.key_bindings[key_name])

if __name__ == "__main__":
    app = LinxboardApp()
    Gtk.main()
