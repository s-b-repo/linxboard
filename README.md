 linux-soundboard-linxboard







 a arch linux sound baord i made tell me a issue and ill try and fix bit new to coding
 python archboard.py to run 

To make this script work on Debian and Arch, you will need to install the GStreamer and GTK3 development libraries. Here is how you can do this:

Debian:

sudo apt-get update
sudo apt-get install libgstreamer1.0-dev libgtk-3-dev

Arch:

sudo pacman -Syu
sudo pacman -S gstreamer gtk3

Once you have installed the necessary libraries, you should be able to run the script on Debian and Arch.

python3 soundboard.py







