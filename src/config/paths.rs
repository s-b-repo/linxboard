use std::path::PathBuf;

pub fn config_dir() -> PathBuf {
    dirs::config_dir()
        .unwrap_or_else(|| {
            PathBuf::from(std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string()))
                .join(".config")
        })
        .join("linxboard")
}

pub fn profiles_path() -> PathBuf {
    config_dir().join("profiles.json")
}

pub fn settings_path() -> PathBuf {
    config_dir().join("settings.json")
}

pub fn legacy_config_dir() -> PathBuf {
    dirs::config_dir()
        .unwrap_or_else(|| {
            PathBuf::from(std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string()))
                .join(".config")
        })
        .join("soundboard9000")
}
