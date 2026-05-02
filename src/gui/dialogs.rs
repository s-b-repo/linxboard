use iced::widget::{button, column, container, row, text, text_input};
use iced::{Element, Length};

use crate::app::Message;

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
    };

    container(content)
        .width(Length::Fill)
        .height(Length::Fill)
        .center_x(Length::Fill)
        .center_y(Length::Fill)
        .into()
}
