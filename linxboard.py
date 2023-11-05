import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gst, GdkPixbuf, Gdk
import threading

class LinxboardApp:
    def __init__(self):
        # Initialize Gtk and create the main window
        Gtk.init()
        self.window = Gtk.Window()
        self.window.set_title("Linxboard")
        self.window.connect("destroy", Gtk.main_quit)

        # Create a box to hold the buttons
        box = Gtk.Box(spacing=6)
        self.window.add(box)

        # Create a dictionary to hold the sound files and their names
        sounds = {
            "Cats": "cats.mp3",
            "Dogs": "dogs.mp3",
            "Birds": "birds.mp3",
        }

        # Create a button for each sound
        buttons = {}
        for name, file in sounds.items():
            # Create a button box to hold the sound button and remove button
            button_box = Gtk.ButtonBox(layout=Gtk.ButtonBoxStyle.SPREAD)
            box.pack_start(button_box, True, True, 0)

            # Create a sound button
            button = Gtk.Button(label=name)
            button_box.add(button)

            # Create a remove button
            remove_button = Gtk.Button(label="X")
            button_box.add(remove_button)

            # Connect the remove button to the remove_button function
            remove_button.connect("clicked", self.remove_button)
            buttons[name] = button

        # Create a volume control
        volume_control = Gtk.VolumeButton()
        volume_control.set_value(1.0)
        box.pack_start(volume_control, True, True, 0)

        # Create a color picker button
        color_button = Gtk.ColorButton()
        color_button.set_title("Pick a color")
        box.pack_start(color_button, True, True, 0)

        # Create a visualizer button
        visualizer_button = Gtk.ToggleButton(label="Visualizer")
        box.pack_start(visualizer_button, True, True, 0)

        # Create a combo box to select the audio device
        device_combo = Gtk.ComboBoxText()
        device_combo.set_title("Select an audio device")
        box.pack_start(device_combo, True, True, 0)

        # Add the names of the available audio devices to the combo box
        device_names = ["autoaudiosink", "alsasink"]
        for name in device_names:
            device_combo.append_text(name)

        # Select the first device in the list as the default
        device_combo.set_active(0)

        # Create a pipeline to play the sound files
        pipeline = Gst.Pipeline.new("audio-player")

        # Create a GStreamer uridecodebin element
        decodebin = Gst.ElementFactory.make("uridecodebin", "decodebin")
        pipeline.add(decodebin)

        # Define a function to set the audio device
        def set_device(combo):
            # Get the name of the selected device
            device_name = combo.get_active_text()

            # Create a GStreamer audio sink element
            device = Gst.ElementFactory.make(device_name, "device")

            # Set the audio sink for the decodebin
            decodebin.set_property("audio-sink", device)

        # Connect the combo box to the set_device function
        device_combo.connect("changed", set_device)

        # Define a function to play a sound file
        def play_sound(file):
            decodebin.set_property("uri", file)
            pipeline.set_state(Gst.State.PLAYING)

        # Define a function to stop playing a sound
        def stop_sound():
            pipeline.set_state(Gst.State.NULL)
