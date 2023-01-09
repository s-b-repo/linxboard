#!/bin/bash

# Check if the system is Debian-based or Arch-based
if [[ -f /etc/debian_version ]]; then
    # Install the necessary libraries on Debian-based systems
    sudo apt-get update
    sudo apt-get install libgstreamer1.0-dev libgtk-3-dev
elif [[ -f /etc/arch-release ]]; then
    # Install the necessary libraries on Arch-based systems
    sudo pacman -Syu
    sudo pacman -S gstreamer gtk3
else
    echo "This system is not supported."
    exit 1
fi
