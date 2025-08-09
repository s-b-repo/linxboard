Arch:

sudo pacman -S python python-pip python-pyside6 python-pygame sdl2_mixer pipewire pipewire-pulse

Debian 12/Ubuntu 24.04:

sudo apt update

sudo apt install python3 python3-pip python3-pyside6 python3-pygame libsdl2-mixer-2.0-0 pulseaudio

pip3 install PySide6 --break-system-packages

# If using PipeWire:
sudo apt install pipewire-audio wireplumber

Run:

python3 soundboard.py
