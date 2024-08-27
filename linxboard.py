import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, GObject, Gst

class LinxboardApp:
    def __init__(self):
        # Initialize GTK and GStreamer
        Gtk.init()
        Gst.init(None)

        # Create the main window
        self.window = Gtk.Window(title="Linxboard")
        self.window.connect("destroy", Gtk.main_quit)

        # Create a box to hold the buttons
        box = Gtk.Box(spacing=6)
        self.window.add(box)

        # Create a dictionary to hold the sound files and their names
        self.sounds = {
            "Cats": "cats.mp3",
            "Dogs": "dogs.mp3",
            "Birds": "birds.mp3",
        }

        # Initialize pipeline
        self.pipeline = Gst.Pipeline.new("audio-player")

        # Create GStreamer elements
        self.decodebin = Gst.ElementFactory.make("uridecodebin", "decodebin")
        self.pipeline.add(self.decodebin)
        self.sink = Gst.ElementFactory.make("autoaudiosink", "audio-output")
        self.pipeline.add(self.sink)

        # Link elements
        self.decodebin.connect("pad-added", self.on_pad_added)

        # Create a button for each sound
        for name, file in self.sounds.items():
            button = Gtk.Button(label=name)
            box.pack_start(button, True, True, 0)
            button.connect("clicked", self.play_sound, file)

        # Create a volume control
        volume_control = Gtk.VolumeButton()
        volume_control.set_value(1.0)
        volume_control.connect("value-changed", self.on_volume_changed)
        box.pack_start(volume_control, True, True, 0)

        # Display the window
        self.window.show_all()

    def on_pad_added(self, element, pad):
        sink_pad = self.sink.get_static_pad("sink")
        if not sink_pad.is_linked():
            pad.link(sink_pad)

    def play_sound(self, widget, file):
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

if __name__ == "__main__":
    app = LinxboardApp()
    Gtk.main()
