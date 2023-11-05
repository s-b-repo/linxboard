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
  apt-get install -y gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly pip
  pip install PyGObject
else
  echo "Unsupported operating system"
  exit 1
fi

echo "Requirements installation completed successfully"
