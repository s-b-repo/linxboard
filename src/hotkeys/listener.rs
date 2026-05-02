use std::collections::HashSet;
use std::path::PathBuf;

use evdev::{Device, InputEventKind, Key};
use tokio::sync::mpsc;

use super::keycodes::{evdev_key_to_code, evdev_key_to_modifier};
use crate::profile::model::{HotkeyBinding, Modifier};

#[derive(Debug, Clone)]
pub enum HotkeyEvent {
    Pressed(HotkeyBinding),
    Released(HotkeyBinding),
}

pub struct HotkeyListener;

impl HotkeyListener {
    pub fn spawn(event_tx: mpsc::UnboundedSender<HotkeyEvent>) -> tokio::task::JoinHandle<()> {
        tokio::spawn(async move {
            if let Err(e) = Self::run(event_tx).await {
                log::error!("Hotkey listener error: {}", e);
            }
        })
    }

    async fn run(event_tx: mpsc::UnboundedSender<HotkeyEvent>) -> anyhow::Result<()> {
        let keyboards = find_keyboard_devices();
        if keyboards.is_empty() {
            anyhow::bail!("No keyboard devices found");
        }

        for kb_path in keyboards {
            let tx = event_tx.clone();
            tokio::spawn(async move {
                if let Err(e) = listen_device(kb_path.clone(), tx).await {
                    log::warn!("Device {:?} listener stopped: {}", kb_path, e);
                }
            });
        }

        std::future::pending::<()>().await;
        Ok(())
    }
}

fn find_keyboard_devices() -> Vec<PathBuf> {
    let mut keyboards = Vec::new();
    let Ok(entries) = std::fs::read_dir("/dev/input") else {
        return keyboards;
    };

    for entry in entries.flatten() {
        let path = entry.path();
        let name = path.file_name().and_then(|n| n.to_str()).unwrap_or("");
        if !name.starts_with("event") {
            continue;
        }

        if let Ok(device) = Device::open(&path) {
            if let Some(keys) = device.supported_keys() {
                if keys.contains(Key::KEY_A)
                    && keys.contains(Key::KEY_Z)
                    && keys.contains(Key::KEY_SPACE)
                {
                    keyboards.push(path);
                }
            }
        }
    }

    keyboards
}

async fn listen_device(
    path: PathBuf,
    tx: mpsc::UnboundedSender<HotkeyEvent>,
) -> anyhow::Result<()> {
    let device = Device::open(&path)?;
    let mut stream = device.into_event_stream()?;
    let mut active_mods: HashSet<Modifier> = HashSet::new();

    loop {
        let event = stream.next_event().await?;
        if let InputEventKind::Key(key) = event.kind() {
            let value = event.value();

            if let Some(modifier) = evdev_key_to_modifier(key) {
                match value {
                    1 => {
                        active_mods.insert(modifier);
                    }
                    0 => {
                        active_mods.remove(&modifier);
                    }
                    _ => {}
                }
            } else {
                let binding = HotkeyBinding {
                    modifiers: {
                        let mut mods: Vec<Modifier> = active_mods.iter().copied().collect();
                        mods.sort_by_key(|m| match m {
                            Modifier::Ctrl => 0,
                            Modifier::Alt => 1,
                            Modifier::Shift => 2,
                            Modifier::Super => 3,
                        });
                        mods
                    },
                    key: evdev_key_to_code(key),
                };

                match value {
                    1 => {
                        let _ = tx.send(HotkeyEvent::Pressed(binding));
                    }
                    0 => {
                        let _ = tx.send(HotkeyEvent::Released(binding));
                    }
                    _ => {}
                }
            }
        }
    }
}
