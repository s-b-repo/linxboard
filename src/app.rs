use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use crossbeam_channel::{Receiver as CrossbeamReceiver, Sender as CrossbeamSender};
use iced::widget::{column, container};
use iced::{Element, Length, Subscription, Task};
use rand::seq::SliceRandom;
use tokio::sync::mpsc;

use crate::audio::AudioCommand;
use crate::config::AppSettings;
use crate::gui::dialogs::DialogState;
use crate::gui::{controls, dialogs, tab_panel, toolbar};
use crate::hotkeys::HotkeyEvent;
use crate::profile::model::HotkeyBinding;
use crate::profile::ProfileManager;

#[derive(Debug, Clone)]
pub enum Message {
    ProfileSelected(String),
    ProfileCreateDialog,
    ProfileDeleteCurrent,
    ProfileImportDialog,
    ProfileExportDialog,

    TabSelected(usize),
    TabCreateDialog,
    TabDeleteCurrent,

    SoundPlay(PathBuf),
    SoundStop(PathBuf),
    SoundPlayRandom,
    SoundAddDialog,
    SoundRemove {
        tab: String,
        name: String,
    },
    SoundRenameDialog {
        tab: String,
        name: String,
    },
    SoundSetHotkeyDialog {
        tab: String,
        name: String,
    },
    SoundToggleFavorite {
        tab: String,
        name: String,
    },
    SoundSettingsDialog {
        tab: String,
        name: String,
    },
    SoundSetTrim {
        tab: String,
        name: String,
        start_ms: u64,
        end_ms: Option<u64>,
    },
    SoundSetPlayMode {
        tab: String,
        name: String,
        mode: crate::profile::model::PlayMode,
    },
    SoundSetVolume {
        tab: String,
        name: String,
        volume: f32,
    },

    VolumeChanged(f32),
    LoopToggled(bool),
    PanicStop,

    HotkeyPressed(HotkeyBinding),
    HotkeyReleased(HotkeyBinding),

    TrollModeToggled(bool),
    TrollTick,

    SearchChanged(String),

    DialogInput(String),
    DialogConfirm,
    DialogCancel,

    FileSelected(Option<PathBuf>),
    ExportPathSelected(Option<PathBuf>),

    ShowWindow,
    Quit,
}

pub struct LinxboardApp {
    profile_manager: ProfileManager,
    settings: AppSettings,
    audio_tx: CrossbeamSender<AudioCommand>,
    hotkey_rx: Arc<Mutex<Option<mpsc::UnboundedReceiver<HotkeyEvent>>>>,
    tray_rx: Arc<Mutex<CrossbeamReceiver<Message>>>,

    current_tab_index: usize,
    search_query: String,
    volume: f32,
    loop_enabled: bool,
    troll_mode: bool,
    dialog: Option<DialogState>,
    pending_file_action: FileAction,
    hotkey_capture_target: Option<(String, String)>,
}

#[derive(Debug, Clone, Default)]
enum FileAction {
    #[default]
    None,
    AddSound,
    ImportProfile,
}

impl LinxboardApp {
    pub fn new(
        audio_tx: CrossbeamSender<AudioCommand>,
        hotkey_rx: mpsc::UnboundedReceiver<HotkeyEvent>,
        tray_rx: CrossbeamReceiver<Message>,
    ) -> (Self, Task<Message>) {
        let settings = AppSettings::load();
        let mut profile_manager = ProfileManager::new();

        if let Err(e) = profile_manager.load() {
            log::warn!("Failed to load profiles: {}", e);
            if let Some(migrated) = crate::profile::migration::try_migrate_legacy() {
                log::info!("Migrated {} profiles from Python version", migrated.len());
                profile_manager.profiles = migrated;
                let _ = profile_manager.save();
            }
        }

        if !settings.last_profile.is_empty() {
            profile_manager.select_profile(&settings.last_profile);
        }

        let volume = settings.volume;
        let _ = audio_tx.send(AudioCommand::SetMasterVolume(volume));

        let app = Self {
            profile_manager,
            settings,
            audio_tx,
            hotkey_rx: Arc::new(Mutex::new(Some(hotkey_rx))),
            tray_rx: Arc::new(Mutex::new(tray_rx)),
            current_tab_index: 0,
            search_query: String::new(),
            volume,
            loop_enabled: false,
            troll_mode: false,
            dialog: None,
            pending_file_action: FileAction::None,
            hotkey_capture_target: None,
        };

        (app, Task::none())
    }

    pub fn title(&self) -> String {
        format!("Linxboard - {}", self.profile_manager.current_profile)
    }

    pub fn update(&mut self, message: Message) -> Task<Message> {
        match message {
            Message::ProfileSelected(name) => {
                self.profile_manager.select_profile(&name);
                self.current_tab_index = 0;
                self.settings.last_profile = name;
                let _ = self.settings.save();
            }
            Message::ProfileCreateDialog => {
                self.dialog = Some(DialogState::CreateProfile {
                    name: String::new(),
                });
            }
            Message::ProfileDeleteCurrent => {
                let name = self.profile_manager.current_profile.clone();
                self.profile_manager.delete_profile(&name);
                self.current_tab_index = 0;
                let _ = self.profile_manager.save();
            }
            Message::ProfileImportDialog => {
                self.pending_file_action = FileAction::ImportProfile;
                return Task::perform(pick_file(), Message::FileSelected);
            }
            Message::ProfileExportDialog => {
                return Task::perform(save_file(), Message::ExportPathSelected);
            }
            Message::TabSelected(i) => {
                self.current_tab_index = i;
            }
            Message::TabCreateDialog => {
                self.dialog = Some(DialogState::CreateTab {
                    name: String::new(),
                });
            }
            Message::TabDeleteCurrent => {
                let tab_name = self.current_tab_name();
                self.profile_manager.delete_tab(&tab_name);
                self.current_tab_index = 0;
                let _ = self.profile_manager.save();
            }
            Message::SoundPlay(ref path) => {
                self.increment_play_count(path);
                let sound_info = self.find_sound_info(path);
                let (start_ms, end_ms) = sound_info
                    .map(|s| (s.start_ms, s.end_ms))
                    .unwrap_or((0, None));
                let _ = self.audio_tx.send(AudioCommand::Play {
                    path: path.clone(),
                    volume: self.volume,
                    looping: self.loop_enabled,
                    start_ms,
                    end_ms,
                });
            }
            Message::SoundStop(path) => {
                let _ = self.audio_tx.send(AudioCommand::StopSound { path });
            }
            Message::SoundPlayRandom => {
                if let Some(path) = self.random_sound_path() {
                    let _ = self.audio_tx.send(AudioCommand::Play {
                        path,
                        volume: self.volume,
                        looping: false,
                        start_ms: 0,
                        end_ms: None,
                    });
                }
            }
            Message::SoundAddDialog => {
                self.pending_file_action = FileAction::AddSound;
                return Task::perform(pick_file(), Message::FileSelected);
            }
            Message::SoundRemove { tab, name } => {
                self.profile_manager.remove_sound(&tab, &name);
                let _ = self.profile_manager.save();
            }
            Message::SoundRenameDialog { tab, name } => {
                self.dialog = Some(DialogState::RenameSound {
                    tab,
                    old_name: name.clone(),
                    new_name: name,
                });
            }
            Message::SoundSetHotkeyDialog { tab, name } => {
                self.hotkey_capture_target = Some((tab, name));
                self.dialog = Some(DialogState::CaptureHotkey);
            }
            Message::SoundToggleFavorite { tab, name } => {
                self.profile_manager.toggle_favorite(&tab, &name);
                let _ = self.profile_manager.save();
            }
            Message::SoundSettingsDialog { tab, name } => {
                let sound_info = {
                    let profile = self.profile_manager.current();
                    profile
                        .tabs
                        .get(&tab)
                        .and_then(|t| t.sounds.get(&name))
                        .cloned()
                };
                if let Some(sound) = sound_info {
                    self.dialog = Some(DialogState::SoundSettings {
                        tab,
                        name,
                        volume: sound.volume,
                        start_ms: sound.start_ms,
                        end_ms: sound.end_ms,
                        push_to_play: sound.play_mode
                            == crate::profile::model::PlayMode::PushToPlay,
                    });
                }
            }
            Message::SoundSetTrim {
                tab,
                name,
                start_ms,
                end_ms,
            } => {
                self.profile_manager.set_trim(&tab, &name, start_ms, end_ms);
                let _ = self.profile_manager.save();
            }
            Message::SoundSetPlayMode { tab, name, mode } => {
                self.profile_manager.set_play_mode(&tab, &name, mode);
                let _ = self.profile_manager.save();
            }
            Message::SoundSetVolume { tab, name, volume } => {
                self.profile_manager.set_sound_volume(&tab, &name, volume);
                let _ = self.profile_manager.save();
            }
            Message::VolumeChanged(v) => {
                self.volume = v;
                let _ = self.audio_tx.send(AudioCommand::SetMasterVolume(v));
                self.settings.volume = v;
            }
            Message::LoopToggled(enabled) => {
                self.loop_enabled = enabled;
            }
            Message::PanicStop => {
                let _ = self.audio_tx.send(AudioCommand::StopAll);
            }
            Message::HotkeyPressed(binding) => {
                if let Some((tab, name)) = self.hotkey_capture_target.take() {
                    self.profile_manager.set_hotkey(&tab, &name, Some(binding));
                    let _ = self.profile_manager.save();
                    self.dialog = None;
                } else if let Some(sound) = self.find_sound_for_hotkey_full(&binding) {
                    self.increment_play_count(&sound.file);
                    let _ = self.audio_tx.send(AudioCommand::Play {
                        path: sound.file,
                        volume: self.volume * sound.volume,
                        looping: self.loop_enabled,
                        start_ms: sound.start_ms,
                        end_ms: sound.end_ms,
                    });
                }
            }
            Message::HotkeyReleased(binding) => {
                if let Some(sound) = self.find_sound_for_hotkey_full(&binding) {
                    if sound.play_mode == crate::profile::model::PlayMode::PushToPlay {
                        let _ = self
                            .audio_tx
                            .send(AudioCommand::StopSound { path: sound.file });
                    }
                }
            }
            Message::TrollModeToggled(enabled) => {
                self.troll_mode = enabled;
            }
            Message::TrollTick => {
                if self.troll_mode {
                    if let Some(path) = self.random_sound_path() {
                        let _ = self.audio_tx.send(AudioCommand::Play {
                            path,
                            volume: self.volume,
                            looping: false,
                            start_ms: 0,
                            end_ms: None,
                        });
                    }
                }
            }
            Message::SearchChanged(query) => {
                self.search_query = query;
            }
            Message::DialogInput(input) => match &mut self.dialog {
                Some(DialogState::CreateProfile { name }) => *name = input,
                Some(DialogState::CreateTab { name }) => *name = input,
                Some(DialogState::RenameSound { new_name, .. }) => *new_name = input,
                _ => {}
            },
            Message::DialogConfirm => {
                if let Some(dialog) = self.dialog.take() {
                    match dialog {
                        DialogState::CreateProfile { name } => {
                            if !name.is_empty() {
                                self.profile_manager.create_profile(&name);
                                self.profile_manager.select_profile(&name);
                                self.current_tab_index = 0;
                                let _ = self.profile_manager.save();
                            }
                        }
                        DialogState::CreateTab { name } => {
                            if !name.is_empty() {
                                self.profile_manager.create_tab(&name);
                                let _ = self.profile_manager.save();
                            }
                        }
                        DialogState::RenameSound {
                            tab,
                            old_name,
                            new_name,
                        } => {
                            if !new_name.is_empty() {
                                self.profile_manager
                                    .rename_sound(&tab, &old_name, &new_name);
                                let _ = self.profile_manager.save();
                            }
                        }
                        DialogState::CaptureHotkey => {
                            self.hotkey_capture_target = None;
                        }
                        DialogState::SoundSettings { .. } => {}
                    }
                }
            }
            Message::DialogCancel => {
                self.dialog = None;
                self.hotkey_capture_target = None;
            }
            Message::FileSelected(path) => {
                if let Some(path) = path {
                    match &self.pending_file_action {
                        FileAction::AddSound => {
                            let name = path
                                .file_stem()
                                .and_then(|s| s.to_str())
                                .unwrap_or("Sound")
                                .to_string();
                            let tab_name = self.current_tab_name();
                            let sound = crate::profile::model::Sound {
                                file: path,
                                hotkey: None,
                                volume: 1.0,
                                color: None,
                                start_ms: 0,
                                end_ms: None,
                                play_mode: crate::profile::model::PlayMode::Toggle,
                                favorite: false,
                                play_count: 0,
                            };
                            self.profile_manager.add_sound(&tab_name, &name, sound);
                            let _ = self.profile_manager.save();
                        }
                        FileAction::ImportProfile => {
                            if let Err(e) = self.profile_manager.import_profile(&path) {
                                log::error!("Import failed: {}", e);
                            } else {
                                let _ = self.profile_manager.save();
                            }
                        }
                        FileAction::None => {}
                    }
                }
                self.pending_file_action = FileAction::None;
            }
            Message::ExportPathSelected(path) => {
                if let Some(path) = path {
                    let name = self.profile_manager.current_profile.clone();
                    if let Err(e) = self.profile_manager.export_profile(&name, &path) {
                        log::error!("Export failed: {}", e);
                    }
                }
            }
            Message::ShowWindow => {}
            Message::Quit => {
                let _ = self.settings.save();
                std::process::exit(0);
            }
        }
        Task::none()
    }

    pub fn view(&self) -> Element<'_, Message> {
        if let Some(ref dialog) = self.dialog {
            return dialogs::view(dialog);
        }

        let profile_names = self.profile_manager.profile_names();
        let toolbar_view = toolbar::view(
            &profile_names,
            &self.profile_manager.current_profile,
            &self.search_query,
            self.troll_mode,
        );

        let tabs: Vec<(String, crate::profile::model::Tab)> = self
            .profile_manager
            .current()
            .tabs
            .iter()
            .map(|(k, v)| (k.clone(), v.clone()))
            .collect();

        let current_tab_name = self.current_tab_name();
        let tab_view = tab_panel::view(
            &tabs,
            self.current_tab_index,
            &self.search_query,
            self.settings.grid_columns,
            &current_tab_name,
        );

        let controls_view: Element<'static, Message> =
            controls::view(self.volume, self.loop_enabled);

        let content = column![toolbar_view, tab_view, controls_view]
            .spacing(4)
            .height(Length::Fill);

        container(content)
            .width(Length::Fill)
            .height(Length::Fill)
            .padding(4)
            .into()
    }

    pub fn subscription(&self) -> Subscription<Message> {
        let mut subs = Vec::new();

        if self.troll_mode {
            subs.push(iced::time::every(Duration::from_secs(8)).map(|_| Message::TrollTick));
        }

        let hotkey_rx = self.hotkey_rx.clone();
        subs.push(Subscription::run_with_id(
            "hotkeys",
            futures::stream::unfold(hotkey_rx, |rx| async move {
                let mut receiver = rx.lock().unwrap().take()?;
                let event = receiver.recv().await?;
                *rx.lock().unwrap() = Some(receiver);
                let msg = match event {
                    HotkeyEvent::Pressed(b) => Message::HotkeyPressed(b),
                    HotkeyEvent::Released(b) => Message::HotkeyReleased(b),
                };
                Some((msg, rx))
            }),
        ));

        let tray_rx = self.tray_rx.clone();
        subs.push(Subscription::run_with_id(
            "tray",
            futures::stream::unfold(tray_rx, |rx| async move {
                let msg = {
                    let rx_guard = rx.lock().unwrap();
                    rx_guard.try_recv().ok()
                };
                if let Some(msg) = msg {
                    Some((msg, rx))
                } else {
                    tokio::time::sleep(Duration::from_millis(100)).await;
                    let msg = rx.lock().unwrap().try_recv().ok()?;
                    Some((msg, rx))
                }
            }),
        ));

        Subscription::batch(subs)
    }

    fn find_sound_for_hotkey_full(
        &self,
        binding: &HotkeyBinding,
    ) -> Option<crate::profile::model::Sound> {
        let profile = self.profile_manager.current();
        for tab in profile.tabs.values() {
            for sound in tab.sounds.values() {
                if sound.hotkey.as_ref() == Some(binding) {
                    return Some(sound.clone());
                }
            }
        }
        None
    }

    fn find_sound_info(&self, path: &PathBuf) -> Option<crate::profile::model::Sound> {
        let profile = self.profile_manager.current();
        for tab in profile.tabs.values() {
            for sound in tab.sounds.values() {
                if &sound.file == path {
                    return Some(sound.clone());
                }
            }
        }
        None
    }

    fn increment_play_count(&mut self, path: &PathBuf) {
        let profile = self.profile_manager.current_mut();
        for tab in profile.tabs.values_mut() {
            for sound in tab.sounds.values_mut() {
                if &sound.file == path {
                    sound.play_count += 1;
                    return;
                }
            }
        }
    }

    fn random_sound_path(&self) -> Option<PathBuf> {
        let profile = self.profile_manager.current();
        let all_sounds: Vec<&crate::profile::model::Sound> = profile
            .tabs
            .values()
            .flat_map(|t| t.sounds.values())
            .collect();
        all_sounds
            .choose(&mut rand::thread_rng())
            .map(|s| s.file.clone())
    }

    fn current_tab_name(&self) -> String {
        self.profile_manager
            .current()
            .tabs
            .keys()
            .nth(self.current_tab_index)
            .cloned()
            .unwrap_or_else(|| "Main".to_string())
    }
}

async fn pick_file() -> Option<PathBuf> {
    let handle = rfd::AsyncFileDialog::new()
        .add_filter("Audio", &["mp3", "wav", "ogg", "flac"])
        .add_filter("JSON", &["json"])
        .add_filter("All", &["*"])
        .pick_file()
        .await?;
    Some(handle.path().to_path_buf())
}

async fn save_file() -> Option<PathBuf> {
    let handle = rfd::AsyncFileDialog::new()
        .add_filter("JSON", &["json"])
        .set_file_name("profile.json")
        .save_file()
        .await?;
    Some(handle.path().to_path_buf())
}
