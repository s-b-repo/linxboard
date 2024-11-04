#!/bin/bash

# Function to install packages for Debian/Ubuntu
install_debian() {
    echo "Updating package list and installing dependencies for Debian/Ubuntu..."
    sudo apt update
    sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-gst-plugins-base-1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good
}

# Function to install packages for Arch Linux
install_arch() {
    echo "Installing dependencies for Arch Linux..."
    sudo pacman -Syu --noconfirm python-gobject gtk3 gst-plugins-base gst-plugins-good
}

# Function to create a symlink
create_symlink() {
    # Create a directory for local bin if it doesn't exist
    mkdir -p ~/.local/bin
    # Create a symbolic link in ~/.local/bin
    ln -sf "$(pwd)/linxboard.py" ~/.local/bin/linxboard
    echo "Created symlink. You can now run the application with 'linxboard'."
}

# Check the distribution and install accordingly
if [[ -f /etc/debian_version ]]; then
    install_debian
elif [[ -f /etc/arch-release ]]; then
    install_arch
else
    echo "Unsupported distribution. This script supports Debian/Ubuntu and Arch Linux."
    exit 1
fi

# Create symbolic link
create_symlink

# Print completion message
echo "Installation completed. Run the application using the command 'linxboard'."
