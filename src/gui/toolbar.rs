use iced::widget::{button, pick_list, row, text, text_input};
use iced::Element;

use crate::app::Message;

pub fn view<'a>(
    profile_names: &[String],
    current_profile: &str,
    search_query: &'a str,
    troll_mode: bool,
) -> Element<'a, Message> {
    let profile_picker = pick_list(
        profile_names.to_vec(),
        Some(current_profile.to_string()),
        Message::ProfileSelected,
    )
    .width(200);

    let add_profile_btn = button(text("+")).on_press(Message::ProfileCreateDialog);
    let del_profile_btn = button(text("-")).on_press(Message::ProfileDeleteCurrent);
    let import_btn = button(text("Import")).on_press(Message::ProfileImportDialog);
    let export_btn = button(text("Export")).on_press(Message::ProfileExportDialog);

    let troll_label = if troll_mode {
        "Troll: ON"
    } else {
        "Troll: OFF"
    };
    let troll_btn = button(text(troll_label))
        .on_press(Message::TrollModeToggled(!troll_mode))
        .style(super::style::troll_button_style(troll_mode));

    let search = text_input("Search sounds...", search_query)
        .on_input(Message::SearchChanged)
        .width(200);

    row![
        profile_picker,
        add_profile_btn,
        del_profile_btn,
        import_btn,
        export_btn,
        troll_btn,
        iced::widget::horizontal_space(),
        search,
    ]
    .spacing(8)
    .padding(8)
    .into()
}
