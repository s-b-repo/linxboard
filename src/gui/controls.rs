use iced::widget::{button, checkbox, row, slider, text};
use iced::Element;

use crate::app::Message;
use crate::gui::style;

pub fn view<'a>(volume: f32, loop_enabled: bool) -> Element<'a, Message> {
    let vol_label = text(format!("Vol: {}%", (volume * 100.0) as u32)).size(14);
    let vol_slider = slider(0.0..=1.0, volume, Message::VolumeChanged).width(200);

    let loop_check = checkbox("Loop", loop_enabled).on_toggle(Message::LoopToggled);

    let random_btn = button(text("Random")).on_press(Message::SoundPlayRandom);

    let panic_btn = button(text("STOP ALL"))
        .on_press(Message::PanicStop)
        .style(style::panic_button_style);

    row![
        vol_label,
        vol_slider,
        loop_check,
        iced::widget::horizontal_space(),
        random_btn,
        panic_btn,
    ]
    .spacing(12)
    .padding(8)
    .into()
}
