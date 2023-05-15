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
    remove_button.connect("clicked", remove_button)
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

# Connect the buttons to the play and stop functions
for name, button in buttons.items():
    button.connect("clicked", play_sound, sounds[name])

# Connect the volume control to the playbin
volume_control.connect("value-changed", lambda w: playbin.set_property("volume", w.get_value()))

# Connect the color picker button to a function to change the background color
    def pick_color(button):
   # Open a color chooser dialog
color_dialog = Gtk.ColorChooserDialog(title="Pick a color", parent=window)
response = color_dialog.run()

if response == Gtk.ResponseType.OK:
    # Get the selected color
    color = color_dialog.get_rgba()

    # Set the background color of the window and buttons
    style_provider = Gtk.CssProvider()
    css = """
        GtkWindow, GtkButton {
            background-color: %s;
        }
    """ % color.to_string()
    style_provider.load_from_data(bytes(css.encode()))
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

color_dialog.destroy()

# Connect the visualizer button to a function to toggle the visualizer
visualizer_active = False
def toggle_visualizer(button):
    global visualizer_active
    visualizer_active = not visualizer_active
    if visualizer_active:
        # Add a visualizer element to the pipeline
        visualizer = Gst.ElementFactory.make("visualization", "visualizer")
        pipeline.add(visualizer)
        decodebin.link(visualizer)
        visualizer.link(device)
    else:
        # Remove the visualizer element from the pipeline
        pipeline.remove(visualizer)
        decodebin.unlink(visualizer)
        visualizer.unlink(device)

visualizer_button.connect("toggled", toggle_visualizer)

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
    button_box = Gtk.ButtonBox(layout=Gtk.ButtonBoxStyle.SPREAD)
    box.pack_start(button_box, True, True, 0)

    # Create a sound button
    button = Gtk.Button(label=name)
    button_box.add(button)

    # Create a remove button
    remove_button = Gtk.Button(label="X")
    button_box.add(remove_button)

    # Connect the remove button to the remove_button function
    remove_button.connect("clicked", remove_button)
    buttons[name] = button

    # Connect the button to the play and stop functions
    button.connect("clicked", play_sound, file)

    # Show the button
    button.show()

# Destroy the dialog
dialog.destroy()

# Define a function to remove a sound button
def remove_button(button):
    # Get the button's parent (the button box)
    button_box = button.get_parent()

    # Get the name of the sound associated with the button
    for name, sound_button in buttons.items():
        if sound_button == button:
            break

    # Remove the sound from the sounds dictionary
    del sounds[name]

    # Remove the button from the button box
    button_box.remove(button)
    button_box.remove(remove_button)

    # Destroy the button box
    button_box.destroy()

# Connect the "Import" button to the import_sound function
import_button.connect("clicked", import_sound)

# Show the window
window.show_all()

# Run the GTK main loop
Gtk.main()
