import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gst, Gdk
import threading

# Initialize GStreamer
Gst.init(None)

# Create the GUI
window = Gtk.Window()
window.set_title("Sound Board")

# Create a box to hold the buttons
box = Gtk.Box(spacing=6)
window.add(box)

# Create a dictionary to hold the sound files and their names
sounds = {
    "Cats": "cats.mp3",
    "Dogs": "dogs.mp3",
    "Birds": "birds.mp3",
}

# Create a button for each sound
buttons = {}
for name, file in sounds.items():
    button = Gtk.Button(label=name)
    box.pack_start(button, True, True, 0)
    buttons[name] = button

# Create an "Import" button
import_button = Gtk.Button(label="Import")
box.pack_start(import_button, True, True, 0)

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

# Create a pipeline to play the sound files
pipeline = Gst.Pipeline.new("audio-player")

# Create a GStreamer playbin element
playbin = Gst.ElementFactory.make("playbin", "playbin")
pipeline.add(playbin)

# Set the playbin to loop indefinitely
playbin.set_property("loop", -1)

# Set the playbin to automatically play when buffered
playbin.set_property("auto-start", True)

# Set the playbin to use a software volume control
playbin.set_property("volume", 1.0)

# Set the playbin to use the default audio device
device = Gst.parse_launch("autoaudiosink")
playbin.set_property("audio-sink", device)

# Define a function to play a sound file
def play_sound(file):
    playbin.set_property("uri", "file://" + file)
    pipeline.set_state(Gst.State.PLAYING)

# Define a function to stop playing a sound
def stop_sound():
    pipeline.set_state(Gst.State.NULL)

# Connect the buttons to the play and stop functions
for name, button in buttons.items():
    button.connect("clicked", play_sound, sounds[name])

# Define a function to import a new sound
def import_sound():
    # Open a file chooser dialog to select the sound file
    dialog = Gtk.FileChooserDialog("Import Sound", window,
        Gtk.FileChooserAction.OPEN,
        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
         Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

    # Run the dialog and get the selected file
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        file = dialog.get_filename()

        # Add the sound to the sounds dictionary
        name = file.split("/")[-1]
        sounds[name] = file

        # Create a button for the new sound
        button = Gtk.Button(label=name)
        box.pack_start(button, True, True, 0)
        buttons[name] = button

        # Connect the button to the play and stop functions
        button.connect("clicked", play_sound, file)

        # Show the button
        button.show()

# Connect the volume control to the playbin
volume_control.connect("value-changed", lambda w: playbin.set_property("volume", w.get_value()))

# Define a function to stop playing a sound when a different button is clicked
def stop_current_sound(button):
    for name, b in buttons.items():
        if b != button:
            b.disconnect(b.handler_id)
    stop_sound()
    for name, b in buttons.items():
        b.handler_id = b.connect("clicked", stop_current_sound)

# Connect the buttons to the stop function
for name, button in buttons.items():
    button.handler_id = button.connect("clicked", stop_current_sound)

# Connect the "Import" button to the import function
import_button.connect("clicked", import_sound)

# Connect the color picker button to a function to change the button colors
def on_color_set(button):
    color = button.get_rgba()
    for name, b in buttons.items():
        bg_color = Gdk.RGBA()
        bg_color.parse(color.to_string())
        b.override_background_color(Gtk.StateType.NORMAL, bg_color)
color_button.connect("color-set", on_color_set)

# Connect the visualizer button to a function to toggle the visualizer
visualizer_on = False
def on_visualizer_toggled(button):
    global visualizer_on
    if button.get_active():
        visualizer_on = True
        pipeline.set_state(Gst.State.NULL)
        pipeline.remove(playbin)
        pipeline.add(visual)
        visual.link(sink)
        pipeline.set_state(Gst.State.PLAYING)
    else:
        visualizer_on = False
        pipeline.set_state(Gst.State.NULL)
        pipeline.remove(visual)
        pipeline.add(playbin)
        pipeline.set_state(Gst.State.PLAYING)
visualizer_button.connect("toggled", on_visualizer_toggled)

# Show the window
window.show_all()

# Run the GTK main loop
Gtk.main()
