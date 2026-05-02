use iced::widget::{button, column, container, row, scrollable, text};
use iced::{Element, Length};

use crate::app::Message;
use crate::gui::style;
use crate::profile::model::Tab;

pub fn view(
    tabs: &[(String, Tab)],
    current_tab_index: usize,
    search_filter: &str,
    grid_columns: usize,
    current_tab_name: &str,
) -> Element<'static, Message> {
    let tab_buttons: Vec<Element<'static, Message>> = tabs
        .iter()
        .enumerate()
        .map(|(i, (name, _))| {
            let name_owned = name.clone();
            let btn = if i == current_tab_index {
                button(text(name_owned).size(14))
                    .on_press(Message::TabSelected(i))
                    .style(|_theme, _status| iced::widget::button::Style {
                        background: Some(iced::Background::Color(iced::color!(0x3498db))),
                        text_color: iced::color!(0xffffff),
                        border: iced::Border {
                            radius: 4.0.into(),
                            ..Default::default()
                        },
                        ..Default::default()
                    })
            } else {
                button(text(name_owned).size(14)).on_press(Message::TabSelected(i))
            };
            btn.width(Length::Fill).into()
        })
        .collect();

    let add_tab_btn: Element<'static, Message> = button(text("+ Tab"))
        .on_press(Message::TabCreateDialog)
        .width(Length::Fill)
        .into();

    let del_tab_btn: Element<'static, Message> = button(text("- Tab"))
        .on_press(Message::TabDeleteCurrent)
        .width(Length::Fill)
        .into();

    let mut tab_list_items = tab_buttons;
    tab_list_items.push(add_tab_btn);
    tab_list_items.push(del_tab_btn);

    let tab_sidebar = container(scrollable(
        column(tab_list_items).spacing(4).width(Length::Fill),
    ))
    .width(120)
    .height(Length::Fill)
    .padding(4);

    let sound_grid = if let Some((_name, tab)) = tabs.get(current_tab_index) {
        build_sound_grid(tab, search_filter, grid_columns, current_tab_name)
    } else {
        column![text("No tab selected")].into()
    };

    let grid_area = container(scrollable(sound_grid))
        .width(Length::Fill)
        .height(Length::Fill)
        .padding(8);

    row![tab_sidebar, grid_area].spacing(4).into()
}

fn build_sound_grid(
    tab: &Tab,
    search_filter: &str,
    columns: usize,
    tab_name: &str,
) -> Element<'static, Message> {
    let filter_lower = search_filter.to_lowercase();

    let filtered_sounds: Vec<(String, crate::profile::model::Sound)> = tab
        .sounds
        .iter()
        .filter(|(name, _)| search_filter.is_empty() || name.to_lowercase().contains(&filter_lower))
        .map(|(name, sound)| (name.clone(), sound.clone()))
        .collect();

    let mut rows: Vec<Element<'static, Message>> = Vec::new();
    let tab_owned = tab_name.to_string();

    for chunk in filtered_sounds.chunks(columns) {
        let mut row_items: Vec<Element<'static, Message>> = Vec::new();

        for (name, sound) in chunk {
            let hotkey_label = sound
                .hotkey
                .as_ref()
                .map(|h| format!("[{}]", h.display_name()));

            let label = if let Some(ref hk) = hotkey_label {
                format!("{}\n{}", name, hk)
            } else {
                name.to_string()
            };

            let color = sound.color.clone();
            let play_btn = button(text(label).size(12).center())
                .width(style::BUTTON_WIDTH)
                .height(style::BUTTON_HEIGHT)
                .on_press(Message::SoundPlay(sound.file.clone()))
                .style(move |_theme, _status| style::sound_button_style(color.as_deref()));

            let tab_for_del = tab_owned.clone();
            let name_for_del = name.clone();
            let del_btn = button(text("x").size(10))
                .on_press(Message::SoundRemove {
                    tab: tab_for_del,
                    name: name_for_del,
                })
                .style(|_theme, _status| iced::widget::button::Style {
                    background: Some(iced::Background::Color(iced::color!(0xc0392b))),
                    text_color: iced::color!(0xffffff),
                    border: iced::Border {
                        radius: 3.0.into(),
                        ..Default::default()
                    },
                    ..Default::default()
                });

            let tab_for_rename = tab_owned.clone();
            let name_for_rename = name.clone();
            let rename_btn = button(text("R").size(10)).on_press(Message::SoundRenameDialog {
                tab: tab_for_rename,
                name: name_for_rename,
            });

            let tab_for_hk = tab_owned.clone();
            let name_for_hk = name.clone();
            let hotkey_btn = button(text("H").size(10)).on_press(Message::SoundSetHotkeyDialog {
                tab: tab_for_hk,
                name: name_for_hk,
            });

            let tab_for_fav = tab_owned.clone();
            let name_for_fav = name.clone();
            let fav_label = if sound.favorite { "*" } else { "." };
            let fav_btn = button(text(fav_label).size(10)).on_press(Message::SoundToggleFavorite {
                tab: tab_for_fav,
                name: name_for_fav,
            });

            let stop_btn =
                button(text("S").size(10)).on_press(Message::SoundStop(sound.file.clone()));

            let tab_for_settings = tab_owned.clone();
            let name_for_settings = name.clone();
            let settings_btn = button(text("G").size(10)).on_press(Message::SoundSettingsDialog {
                tab: tab_for_settings,
                name: name_for_settings,
            });

            let actions = row![
                fav_btn,
                rename_btn,
                hotkey_btn,
                settings_btn,
                stop_btn,
                del_btn
            ]
            .spacing(2);
            let sound_widget = column![play_btn, actions].spacing(2);
            row_items.push(sound_widget.into());
        }

        rows.push(row(row_items).spacing(style::SPACING).into());
    }

    let add_sound_btn: Element<'static, Message> = button(text("+ Add Sound").size(12))
        .width(style::BUTTON_WIDTH)
        .height(style::BUTTON_HEIGHT)
        .on_press(Message::SoundAddDialog)
        .into();
    rows.push(add_sound_btn);

    column(rows).spacing(style::SPACING).into()
}
