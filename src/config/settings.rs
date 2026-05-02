use serde::{Deserialize, Serialize};

use super::paths;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    #[serde(default = "default_width")]
    pub window_width: u32,
    #[serde(default = "default_height")]
    pub window_height: u32,
    #[serde(default = "default_volume")]
    pub volume: f32,
    #[serde(default)]
    pub last_profile: String,
    #[serde(default = "default_columns")]
    pub grid_columns: usize,
    #[serde(default)]
    pub minimize_to_tray: bool,
}

fn default_width() -> u32 {
    1024
}
fn default_height() -> u32 {
    700
}
fn default_volume() -> f32 {
    0.7
}
fn default_columns() -> usize {
    3
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            window_width: default_width(),
            window_height: default_height(),
            volume: default_volume(),
            last_profile: String::new(),
            grid_columns: default_columns(),
            minimize_to_tray: false,
        }
    }
}

impl AppSettings {
    pub fn load() -> Self {
        let path = paths::settings_path();
        std::fs::read_to_string(&path)
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default()
    }

    pub fn save(&self) -> anyhow::Result<()> {
        let dir = paths::config_dir();
        std::fs::create_dir_all(&dir)?;
        let path = paths::settings_path();
        std::fs::write(&path, serde_json::to_string_pretty(self)?)?;
        Ok(())
    }
}
