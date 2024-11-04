!/bin/bash

# Check if the script is running with root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root"
  exit 1
fi

# Check if the operating system is supported (Arch Linux or Debian)
if [ -f /etc/arch-release ]; then
  # Arch Linux
  pacman -Sy --noconfirm gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly pip
  pip install PyGObject
elif [ -f /etc/debian_version ]; then
  # Debian-based systems (Debian, Ubuntu, etc.)
  apt-get update
  apt install python3-gi gir1.2-gtk-3.0 gir1.2-gst-plugins-base-1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good
  pip install PyGObject
else
  echo "Unsupported operating system"
  exit 1
fi

echo "Requirements installation completed successfully"
