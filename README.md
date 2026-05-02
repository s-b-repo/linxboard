# Linxboard

A high-performance Linux soundboard written in Rust with true global hotkeys. Works on every Linux distro, on both X11 and Wayland.

![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![Rust](https://img.shields.io/badge/rust-1.70%2B-orange)
![Platform](https://img.shields.io/badge/platform-Linux-green)

## Why Linxboard?

| | Linxboard (Rust) | Traditional Soundboards |
|---|---|---|
| Global hotkeys | Works unfocused (evdev kernel-level) | Only when window focused |
| Wayland support | Native, no XWayland | Usually X11 only |
| Audio latency | ~5.8ms (256-frame buffer) | ~11.6ms+ (512+ frame buffer) |
| Dependencies | Single binary | Python + pip + Qt + SDL + ... |
| Channels | 32 simultaneous | Typically 8-16 |
| Startup time | Instant | 2-5 seconds |

## Features

- **Global hotkeys** via evdev (work even when the window is unfocused, on X11 and Wayland)
- **Low-latency audio** playback (MP3, WAV, OGG, FLAC) with 32 simultaneous channels
- **Profile management** with tabs to organize sounds
- **Per-sound volume** and custom button colors
- **Master volume**, loop mode, random play, panic stop
- **Troll mode** (random sounds play at intervals)
- **System tray** integration
- **Import/export** profiles as JSON
- **Auto-migration** from the Python linxboard version
- **Single binary** — no runtime dependencies beyond system audio libs
- **Drag-and-drop** audio files to add sounds
- **Configurable grid** — 2, 3, 4, or 5 columns

## Installation

### From Source (All Distros)

Requires Rust 1.70+ ([install Rust](https://rustup.rs/)).

```bash
git clone https://github.com/s-b-repo/linxboard.git
cd linxboard
cargo build --release
```

The binary is at `target/release/linxboard`. Copy it anywhere on your `$PATH`:

```bash
sudo cp target/release/linxboard /usr/local/bin/
```

### Build Dependencies

<details>
<summary>Debian / Ubuntu / Kali</summary>

```bash
sudo apt install build-essential pkg-config libasound2-dev libgtk-3-dev libxdo-dev
```
</details>

<details>
<summary>Arch Linux / Manjaro</summary>

```bash
sudo pacman -S base-devel alsa-lib gtk3 xdotool
```
</details>

<details>
<summary>Fedora / RHEL</summary>

```bash
sudo dnf install gcc pkg-config alsa-lib-devel gtk3-devel libxdo-devel
```
</details>

<details>
<summary>openSUSE</summary>

```bash
sudo zypper install gcc pkg-config alsa-devel gtk3-devel libxdo-devel
```
</details>

## Quick Start

```bash
# 1. Build
cargo build --release

# 2. Set up global hotkey permissions (one-time)
sudo usermod -aG input $USER
# Log out and back in after this

# 3. Run
./target/release/linxboard
```

## Usage

### Adding Sounds

Click the **"+ Add Sound"** button or drag-and-drop audio files onto the window. Supported formats: MP3, WAV, OGG, FLAC.

### Hotkeys

1. Right-click a sound button
2. Select "Set Hotkey"
3. Press your desired key combination (e.g., `Ctrl+F1`)
4. The hotkey works globally — even when Linxboard is in the background

### Profiles & Tabs

- **Profiles**: Independent sound collections (e.g., "Gaming", "Streaming", "Meetings")
- **Tabs**: Organize sounds within a profile (e.g., "Effects", "Music", "Alerts")
- Use the toolbar dropdown to switch profiles
- Import/export profiles as JSON for sharing

### Controls

| Control | Action |
|---------|--------|
| Volume slider | Master volume (affects all sounds) |
| Loop checkbox | Newly played sounds loop until stopped |
| Random button | Play a random sound from the current profile |
| STOP ALL | Immediately silence all playing sounds |
| Troll Mode | Automatically play random sounds every 5-15 seconds |

## Global Hotkeys

Linxboard uses Linux's evdev subsystem to capture keyboard input at the kernel level. This means hotkeys work regardless of which window is focused, and they work identically on X11 and Wayland.

### Setup

Your user must be in the `input` group:

```bash
sudo usermod -aG input $USER
```

**Then log out and back in** (or reboot). Verify with:

```bash
groups | grep input
```

### How It Works

```
Keyboard → /dev/input/eventN → evdev → Linxboard hotkey listener
                                              ↓
                                        Audio playback
```

No compositor cooperation or D-Bus portals needed. Works on GNOME, KDE, Sway, i3, Hyprland, and every other environment.

## Configuration

All config is stored in `~/.config/linxboard/`:

```
~/.config/linxboard/
├── profiles.json    # All profiles, tabs, and sound bindings
└── settings.json    # Window size, volume, preferences
```

### Profile Format

```json
{
  "Default": {
    "tabs": {
      "Main": {
        "sounds": {
          "Air Horn": {
            "file": "/home/user/sounds/airhorn.mp3",
            "hotkey": { "modifiers": ["Ctrl"], "key": 59 },
            "volume": 1.0,
            "color": "red"
          }
        }
      }
    }
  }
}
```

### Migration from Python Version

If you previously used the Python linxboard (`~/.config/soundboard9000/`), your profiles are automatically imported on first run. No manual steps needed.

## Architecture

```
┌────────────────────────────────────────────┐
│              GUI Thread (iced)              │
│  Profiles, UI state, message handling      │
└──────────┬─────────────────────┬───────────┘
           │ AudioCommand        │ HotkeyBinding
           ▼                     ▼
  ┌─────────────────┐  ┌─────────────────────┐
  │  Audio Thread    │  │  Hotkey Thread(s)   │
  │  32 rodio Sinks  │  │  evdev listeners    │
  │  file byte cache │  │  per keyboard       │
  └─────────────────┘  └─────────────────────┘
```

- **GUI**: iced (Elm architecture, native Wayland via winit)
- **Audio**: rodio + symphonia (ALSA/PipeWire/PulseAudio backends)
- **Hotkeys**: evdev (kernel-level, X11/Wayland/TTY agnostic)
- **IPC**: crossbeam channels (lock-free, bounded)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

This project is licensed under the GNU General Public License v3.0 — see [LICENSE](LICENSE) for details.
