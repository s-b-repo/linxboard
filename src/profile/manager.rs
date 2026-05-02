use std::path::Path;

use anyhow::Context;

use super::model::*;
use crate::config;

pub struct ProfileManager {
    pub profiles: ProfileStore,
    pub current_profile: String,
}

impl ProfileManager {
    pub fn new() -> Self {
        Self {
            profiles: default_store(),
            current_profile: "Default".to_string(),
        }
    }

    pub fn load(&mut self) -> anyhow::Result<()> {
        let path = config::profiles_path();
        if path.exists() {
            let data = std::fs::read_to_string(&path).context("Failed to read profiles.json")?;
            self.profiles = serde_json::from_str(&data).context("Failed to parse profiles.json")?;
        }

        if self.profiles.is_empty() {
            self.profiles = default_store();
        }

        if !self.profiles.contains_key(&self.current_profile) {
            self.current_profile = self
                .profiles
                .keys()
                .next()
                .cloned()
                .unwrap_or_else(|| "Default".to_string());
        }

        Ok(())
    }

    pub fn save(&self) -> anyhow::Result<()> {
        let dir = config::config_dir();
        std::fs::create_dir_all(&dir)?;
        let path = config::profiles_path();
        std::fs::write(&path, serde_json::to_string_pretty(&self.profiles)?)?;
        Ok(())
    }

    pub fn current(&self) -> &Profile {
        self.profiles
            .get(&self.current_profile)
            .expect("current profile must exist")
    }

    pub fn current_mut(&mut self) -> &mut Profile {
        self.profiles
            .get_mut(&self.current_profile)
            .expect("current profile must exist")
    }

    pub fn profile_names(&self) -> Vec<String> {
        self.profiles.keys().cloned().collect()
    }

    pub fn create_profile(&mut self, name: &str) {
        if !self.profiles.contains_key(name) {
            self.profiles.insert(name.to_string(), Profile::new());
        }
    }

    pub fn delete_profile(&mut self, name: &str) {
        if name == "Default" {
            return;
        }
        self.profiles.remove(name);
        if self.current_profile == name {
            self.current_profile = self
                .profiles
                .keys()
                .next()
                .cloned()
                .unwrap_or_else(|| "Default".to_string());
        }
    }

    pub fn select_profile(&mut self, name: &str) {
        if self.profiles.contains_key(name) {
            self.current_profile = name.to_string();
        }
    }

    pub fn create_tab(&mut self, tab_name: &str) {
        let profile = self.current_mut();
        if !profile.tabs.contains_key(tab_name) {
            profile.tabs.insert(tab_name.to_string(), Tab::new());
        }
    }

    pub fn delete_tab(&mut self, tab_name: &str) {
        if tab_name == "Main" {
            return;
        }
        self.current_mut().tabs.remove(tab_name);
    }

    pub fn add_sound(&mut self, tab: &str, name: &str, sound: Sound) {
        let profile = self.current_mut();
        if let Some(tab) = profile.tabs.get_mut(tab) {
            tab.sounds.insert(name.to_string(), sound);
        }
    }

    pub fn remove_sound(&mut self, tab: &str, name: &str) {
        let profile = self.current_mut();
        if let Some(tab) = profile.tabs.get_mut(tab) {
            tab.sounds.remove(name);
        }
    }

    pub fn rename_sound(&mut self, tab: &str, old_name: &str, new_name: &str) {
        let profile = self.current_mut();
        if let Some(tab) = profile.tabs.get_mut(tab) {
            if let Some(sound) = tab.sounds.remove(old_name) {
                tab.sounds.insert(new_name.to_string(), sound);
            }
        }
    }

    pub fn set_hotkey(&mut self, tab: &str, name: &str, hotkey: Option<HotkeyBinding>) {
        let profile = self.current_mut();
        if let Some(tab) = profile.tabs.get_mut(tab) {
            if let Some(sound) = tab.sounds.get_mut(name) {
                sound.hotkey = hotkey;
            }
        }
    }

    pub fn export_profile(&self, name: &str, path: &Path) -> anyhow::Result<()> {
        if let Some(profile) = self.profiles.get(name) {
            let mut export = ProfileStore::new();
            export.insert(name.to_string(), profile.clone());
            std::fs::write(path, serde_json::to_string_pretty(&export)?)?;
        }
        Ok(())
    }

    pub fn import_profile(&mut self, path: &Path) -> anyhow::Result<()> {
        let data = std::fs::read_to_string(path)?;
        let imported: ProfileStore = serde_json::from_str(&data)?;
        for (name, profile) in imported {
            self.profiles.insert(name, profile);
        }
        Ok(())
    }

    pub fn toggle_favorite(&mut self, tab: &str, name: &str) {
        let profile = self.current_mut();
        if let Some(tab) = profile.tabs.get_mut(tab) {
            if let Some(sound) = tab.sounds.get_mut(name) {
                sound.favorite = !sound.favorite;
            }
        }
    }

    pub fn set_trim(&mut self, tab: &str, name: &str, start_ms: u64, end_ms: Option<u64>) {
        let profile = self.current_mut();
        if let Some(tab) = profile.tabs.get_mut(tab) {
            if let Some(sound) = tab.sounds.get_mut(name) {
                sound.start_ms = start_ms;
                sound.end_ms = end_ms;
            }
        }
    }

    pub fn set_play_mode(&mut self, tab: &str, name: &str, mode: PlayMode) {
        let profile = self.current_mut();
        if let Some(tab) = profile.tabs.get_mut(tab) {
            if let Some(sound) = tab.sounds.get_mut(name) {
                sound.play_mode = mode;
            }
        }
    }

    pub fn set_sound_volume(&mut self, tab: &str, name: &str, volume: f32) {
        let profile = self.current_mut();
        if let Some(tab) = profile.tabs.get_mut(tab) {
            if let Some(sound) = tab.sounds.get_mut(name) {
                sound.volume = volume;
            }
        }
    }

    pub fn all_hotkey_bindings(&self) -> Vec<(HotkeyBinding, std::path::PathBuf)> {
        let mut bindings = Vec::new();
        for profile in self.profiles.values() {
            for tab in profile.tabs.values() {
                for sound in tab.sounds.values() {
                    if let Some(ref hotkey) = sound.hotkey {
                        bindings.push((hotkey.clone(), sound.file.clone()));
                    }
                }
            }
        }
        bindings
    }
}
