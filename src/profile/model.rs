use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::path::PathBuf;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Modifier {
    Ctrl,
    Alt,
    Shift,
    Super,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct HotkeyBinding {
    pub modifiers: Vec<Modifier>,
    pub key: u16,
}

impl HotkeyBinding {
    pub fn display_name(&self) -> String {
        let mut parts: Vec<&str> = self
            .modifiers
            .iter()
            .map(|m| match m {
                Modifier::Ctrl => "Ctrl",
                Modifier::Alt => "Alt",
                Modifier::Shift => "Shift",
                Modifier::Super => "Super",
            })
            .collect();
        parts.push(key_name(self.key));
        parts.join("+")
    }
}

fn key_name(code: u16) -> &'static str {
    match code {
        1 => "Esc",
        2 => "1",
        3 => "2",
        4 => "3",
        5 => "4",
        6 => "5",
        7 => "6",
        8 => "7",
        9 => "8",
        10 => "9",
        11 => "0",
        16 => "Q",
        17 => "W",
        18 => "E",
        19 => "R",
        20 => "T",
        21 => "Y",
        22 => "U",
        23 => "I",
        24 => "O",
        25 => "P",
        30 => "A",
        31 => "S",
        32 => "D",
        33 => "F",
        34 => "G",
        35 => "H",
        36 => "J",
        37 => "K",
        38 => "L",
        44 => "Z",
        45 => "X",
        46 => "C",
        47 => "V",
        48 => "B",
        49 => "N",
        50 => "M",
        57 => "Space",
        59 => "F1",
        60 => "F2",
        61 => "F3",
        62 => "F4",
        63 => "F5",
        64 => "F6",
        65 => "F7",
        66 => "F8",
        67 => "F9",
        68 => "F10",
        87 => "F11",
        88 => "F12",
        _ => "?",
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Sound {
    pub file: PathBuf,
    #[serde(default)]
    pub hotkey: Option<HotkeyBinding>,
    #[serde(default = "default_volume")]
    pub volume: f32,
    #[serde(default)]
    pub color: Option<String>,
}

fn default_volume() -> f32 {
    1.0
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Tab {
    pub sounds: BTreeMap<String, Sound>,
}

impl Tab {
    pub fn new() -> Self {
        Self {
            sounds: BTreeMap::new(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Profile {
    pub tabs: BTreeMap<String, Tab>,
}

impl Profile {
    pub fn new() -> Self {
        let mut tabs = BTreeMap::new();
        tabs.insert("Main".to_string(), Tab::new());
        Self { tabs }
    }
}

pub type ProfileStore = BTreeMap<String, Profile>;

pub fn default_store() -> ProfileStore {
    let mut store = ProfileStore::new();
    store.insert("Default".to_string(), Profile::new());
    store
}
