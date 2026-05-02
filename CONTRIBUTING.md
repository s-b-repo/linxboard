# Contributing to Linxboard

## Development Setup

1. Install Rust via [rustup](https://rustup.rs/)
2. Install system dependencies (see README.md)
3. Clone and build:

```bash
git clone https://github.com/s-b-repo/linxboard.git
cd linxboard
cargo build
```

## Running in Development

```bash
RUST_LOG=debug cargo run
```

## Project Structure

```
src/
├── main.rs          # Entry point, thread spawning
├── app.rs           # iced Application, Message enum, update/view
├── audio/
│   ├── engine.rs    # Audio channel pool, playback, caching
│   └── mod.rs
├── hotkeys/
│   ├── listener.rs  # evdev global hotkey capture
│   ├── keycodes.rs  # Key name ↔ evdev code mapping
│   ├── permissions.rs # Input group check
│   └── mod.rs
├── gui/
│   ├── toolbar.rs   # Profile picker, search, buttons
│   ├── tab_panel.rs # Tab sidebar + sound grid
│   ├── controls.rs  # Volume, loop, random, panic
│   ├── dialogs.rs   # Modal dialogs
│   ├── style.rs     # Theme and colors
│   ├── tray.rs      # System tray
│   └── mod.rs
├── profile/
│   ├── model.rs     # Data structures
│   ├── manager.rs   # CRUD operations
│   ├── migration.rs # Python format import
│   └── mod.rs
└── config/
    ├── paths.rs     # XDG path helpers
    ├── settings.rs  # App settings persistence
    └── mod.rs
```

## Code Style

- Run `cargo clippy` before submitting
- Run `cargo fmt` for formatting
- No unsafe code unless absolutely necessary
- Prefer owned types over references in GUI code (iced lifetime ergonomics)

## Testing

```bash
cargo test
```

For testing audio playback, place a test MP3 in `tests/fixtures/` and run:

```bash
cargo test -- --ignored
```

## Pull Requests

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes
4. Run `cargo clippy && cargo test && cargo fmt --check`
5. Push and open a PR

## Areas for Contribution

- Virtual microphone output (PipeWire integration)
- Drag-and-drop file support
- Theming (dark/light/custom)
- Flatpak/AppImage packaging
- Sound waveform visualization
- MIDI controller support
