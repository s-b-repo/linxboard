use std::path::Path;

pub fn check_input_permissions() -> Result<(), String> {
    let uid = unsafe { libc::getuid() };
    if uid == 0 {
        return Ok(());
    }

    let test_path = Path::new("/dev/input");
    if !test_path.exists() {
        return Err("/dev/input does not exist".to_string());
    }

    let entries =
        std::fs::read_dir(test_path).map_err(|e| format!("Cannot read /dev/input: {}", e))?;

    for entry in entries.flatten() {
        let path = entry.path();
        if path
            .file_name()
            .and_then(|n| n.to_str())
            .map_or(false, |n| n.starts_with("event"))
        {
            if std::fs::File::open(&path).is_ok() {
                return Ok(());
            }
        }
    }

    let username = std::env::var("USER").unwrap_or_else(|_| "user".to_string());
    Err(format!(
        "Cannot access /dev/input devices.\n\
         Add your user to the 'input' group:\n\
         \n\
         sudo usermod -aG input {}\n\
         \n\
         Then log out and back in.",
        username
    ))
}
