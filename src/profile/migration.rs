use std::path::PathBuf;

use serde_json::Value;

use super::model::*;
use crate::config;
use crate::hotkeys::keycodes::key_name_to_evdev;

pub fn try_migrate_legacy() -> Option<ProfileStore> {
    let legacy_dir = config::legacy_config_dir();
    let legacy_path = legacy_dir.join("profiles.json");
    if !legacy_path.exists() {
        return None;
    }

    let data = std::fs::read_to_string(&legacy_path).ok()?;
    let json: Value = serde_json::from_str(&data).ok()?;
    migrate_python_profiles(&json).ok()
}

fn migrate_python_profiles(json: &Value) -> anyhow::Result<ProfileStore> {
    let mut store = ProfileStore::new();

    if let Value::Object(profiles) = json {
        for (profile_name, profile_data) in profiles {
            let profile = parse_python_profile(profile_data)?;
            store.insert(profile_name.clone(), profile);
        }
    }

    Ok(store)
}

fn parse_python_profile(data: &Value) -> anyhow::Result<Profile> {
    let mut profile = Profile::new();

    if let Value::Object(obj) = data {
        if let Some(Value::Object(tabs_obj)) = obj.get("tabs") {
            profile.tabs.clear();
            for (tab_name, tab_data) in tabs_obj {
                let tab = parse_python_tab(tab_data);
                profile.tabs.insert(tab_name.clone(), tab);
            }
        } else {
            let tab = parse_python_tab(data);
            profile.tabs.insert("Main".to_string(), tab);
        }
    }

    Ok(profile)
}

fn parse_python_tab(data: &Value) -> Tab {
    let mut tab = Tab::new();

    if let Value::Object(sounds) = data {
        for (sound_name, sound_data) in sounds {
            if sound_name == "tabs" {
                continue;
            }
            if let Some(sound) = parse_python_sound(sound_data) {
                tab.sounds.insert(sound_name.clone(), sound);
            }
        }
    }

    tab
}

fn parse_python_sound(data: &Value) -> Option<Sound> {
    let obj = data.as_object()?;
    let file = obj.get("file")?.as_str()?;

    let hotkey = obj
        .get("key")
        .and_then(|k| k.as_str())
        .and_then(parse_qt_hotkey);

    Some(Sound {
        file: PathBuf::from(file),
        hotkey,
        volume: 1.0,
        color: None,
    })
}

fn parse_qt_hotkey(key_str: &str) -> Option<HotkeyBinding> {
    if key_str.is_empty() {
        return None;
    }

    let parts: Vec<&str> = key_str.split('+').collect();
    let mut modifiers = Vec::new();
    let mut key_part = "";

    for part in &parts {
        match part.to_lowercase().as_str() {
            "ctrl" => modifiers.push(Modifier::Ctrl),
            "alt" => modifiers.push(Modifier::Alt),
            "shift" => modifiers.push(Modifier::Shift),
            "super" | "meta" => modifiers.push(Modifier::Super),
            _ => key_part = part,
        }
    }

    let key = key_name_to_evdev(key_part)?;
    Some(HotkeyBinding { modifiers, key })
}
