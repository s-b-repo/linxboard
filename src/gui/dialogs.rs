use iced::widget::{button, column, container, row, slider, text, text_input, toggler};
use iced::{Element, Length};

use crate::app::Message;
use crate::profile::model::PlayMode;

#[derive(Debug, Clone)]
pub enum DialogState {
    CreateProfile {
        name: String,
    },
    CreateTab {
        name: String,
    },
    RenameSound {
        tab: String,
        old_name: String,
        new_name: String,
    },
    CaptureHotkey,
    SoundSettings {
        tab: String,
        name: String,
        volume: f32,
        start_ms: u64,
        end_ms: Option<u64>,
        push_to_play: bool,
    },
}

pub fn view(dialog: &DialogState) -> Element<'static, Message> {
    let content: Element<'static, Message> = match dialog {
        DialogState::CreateProfile { name } => {
            let input = text_input("Profile name...", name)
                .on_input(Message::DialogInput)
                .on_submit(Message::DialogConfirm);
            let ok = button(text("Create")).on_press(Message::DialogConfirm);
            let cancel = button(text("Cancel")).on_press(Message::DialogCancel);

            column![
                text("New Profile").size(18),
                input,
                row![ok, cancel].spacing(8),
            ]
            .spacing(12)
            .padding(20)
            .width(300)
            .into()
        }
        DialogState::CreateTab { name } => {
            let input = text_input("Tab name...", name)
                .on_input(Message::DialogInput)
                .on_submit(Message::DialogConfirm);
            let ok = button(text("Create")).on_press(Message::DialogConfirm);
            let cancel = button(text("Cancel")).on_press(Message::DialogCancel);

            column![text("New Tab").size(18), input, row![ok, cancel].spacing(8),]
                .spacing(12)
                .padding(20)
                .width(300)
                .into()
        }
        DialogState::RenameSound {
            old_name, new_name, ..
        } => {
            let input = text_input(old_name, new_name)
                .on_input(Message::DialogInput)
                .on_submit(Message::DialogConfirm);
            let ok = button(text("Rename")).on_press(Message::DialogConfirm);
            let cancel = button(text("Cancel")).on_press(Message::DialogCancel);

            column![
                text("Rename Sound").size(18),
                input,
                row![ok, cancel].spacing(8),
            ]
            .spacing(12)
            .padding(20)
            .width(300)
            .into()
        }
        DialogState::CaptureHotkey => {
            let cancel = button(text("Cancel")).on_press(Message::DialogCancel);

            column![
                text("Press a key combination...").size(18),
                text("The next key press will be captured as the hotkey.").size(12),
                cancel,
            ]
            .spacing(12)
            .padding(20)
            .width(350)
            .into()
        }
        DialogState::SoundSettings {
            tab,
            name,
            volume,
            start_ms,
            end_ms,
            push_to_play,
        } => {
            let vol_label = text(format!("Volume: {}%", (*volume * 100.0) as u32)).size(14);
            let vol_slider = slider(0.0..=1.0f32, *volume, {
                let tab = tab.clone();
                let name = name.clone();
                move |v| Message::SoundSetVolume {
                    tab: tab.clone(),
                    name: name.clone(),
                    volume: v,
                }
            })
            .width(200);

            let trim_label = text(format!(
                "Trim: {}ms - {}",
                start_ms,
                end_ms.map_or("end".to_string(), |e| format!("{}ms", e))
            ))
            .size(14);

            let trim_start_slider = slider(0.0..=30000.0f32, *start_ms as f32, {
                let tab = tab.clone();
                let name = name.clone();
                let end = *end_ms;
                move |v| Message::SoundSetTrim {
                    tab: tab.clone(),
                    name: name.clone(),
                    start_ms: v as u64,
                    end_ms: end,
                }
            })
            .width(200);

            let trim_end_slider = slider(0.0..=30000.0f32, end_ms.unwrap_or(30000) as f32, {
                let tab = tab.clone();
                let name = name.clone();
                let start = *start_ms;
                move |v| Message::SoundSetTrim {
                    tab: tab.clone(),
                    name: name.clone(),
                    start_ms: start,
                    end_ms: if v as u64 >= 30000 {
                        None
                    } else {
                        Some(v as u64)
                    },
                }
            })
            .width(200);

            let mode_toggle = toggler(*push_to_play)
                .label("Push-to-Play (hold key to play, release to stop)")
                .on_toggle({
                    let tab = tab.clone();
                    let name = name.clone();
                    move |enabled| Message::SoundSetPlayMode {
                        tab: tab.clone(),
                        name: name.clone(),
                        mode: if enabled {
                            PlayMode::PushToPlay
                        } else {
                            PlayMode::Toggle
                        },
                    }
                });

            let done = button(text("Done")).on_press(Message::DialogCancel);

            column![
                text(format!("Settings: {}", name)).size(18),
                vol_label,
                vol_slider,
                trim_label,
                text("Start:").size(12),
                trim_start_slider,
                text("End:").size(12),
                trim_end_slider,
                mode_toggle,
                done,
            ]
            .spacing(8)
            .padding(20)
            .width(400)
            .into()
        }
    };

    container(content)
        .width(Length::Fill)
        .height(Length::Fill)
        .center_x(Length::Fill)
        .center_y(Length::Fill)
        .into()
}
