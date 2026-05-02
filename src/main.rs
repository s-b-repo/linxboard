mod app;
mod audio;
mod config;
mod gui;
mod hotkeys;
mod profile;

use iced::Size;
use tokio::sync::mpsc;

use app::LinxboardApp;
use audio::{AudioCommand, AudioEngine};
use hotkeys::HotkeyListener;

fn main() -> anyhow::Result<()> {
    env_logger::init();

    if let Err(msg) = hotkeys::check_input_permissions() {
        eprintln!("WARNING: Global hotkeys may not work.\n{}", msg);
    }

    {
        let mut pm = profile::ProfileManager::new();
        if pm.load().is_ok() {
            let bindings = pm.all_hotkey_bindings();
            if !bindings.is_empty() {
                log::info!("Loaded {} hotkey binding(s)", bindings.len());
            }
        }
    }

    let (audio_tx, audio_rx) = crossbeam_channel::unbounded::<AudioCommand>();
    AudioEngine::spawn(audio_rx);

    let (hotkey_tx, hotkey_rx) = mpsc::unbounded_channel();

    let (tray_tx, tray_rx) = crossbeam_channel::unbounded::<app::Message>();
    gui::tray::spawn_tray(tray_tx);

    std::thread::Builder::new()
        .name("hotkey-runtime".into())
        .spawn(move || {
            let rt = tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()
                .expect("Failed to build tokio runtime");
            rt.block_on(async {
                HotkeyListener::spawn(hotkey_tx);
                std::future::pending::<()>().await;
            });
        })?;

    let settings = config::AppSettings::load();

    iced::application(
        LinxboardApp::title,
        LinxboardApp::update,
        LinxboardApp::view,
    )
    .subscription(LinxboardApp::subscription)
    .window_size(Size::new(
        settings.window_width as f32,
        settings.window_height as f32,
    ))
    .run_with(move || LinxboardApp::new(audio_tx, hotkey_rx, tray_rx))
    .map_err(|e| anyhow::anyhow!("GUI error: {}", e))?;

    Ok(())
}
