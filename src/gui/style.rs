use iced::color;
use iced::widget::button;
use iced::Theme;

pub const BUTTON_WIDTH: f32 = 180.0;
pub const BUTTON_HEIGHT: f32 = 64.0;
pub const SPACING: f32 = 8.0;

pub fn sound_button_style(color: Option<&str>) -> button::Style {
    let bg = match color {
        Some("red") => color!(0xe74c3c),
        Some("green") => color!(0x2ecc71),
        Some("blue") => color!(0x3498db),
        Some("purple") => color!(0x9b59b6),
        Some("orange") => color!(0xe67e22),
        Some("yellow") => color!(0xf39c12),
        Some("pink") => color!(0xe91e63),
        Some("teal") => color!(0x1abc9c),
        _ => color!(0x34495e),
    };

    button::Style {
        background: Some(iced::Background::Color(bg)),
        text_color: color!(0xffffff),
        border: iced::Border {
            radius: 6.0.into(),
            ..Default::default()
        },
        ..Default::default()
    }
}

pub fn panic_button_style(_theme: &Theme, _status: button::Status) -> button::Style {
    button::Style {
        background: Some(iced::Background::Color(color!(0xc0392b))),
        text_color: color!(0xffffff),
        border: iced::Border {
            radius: 4.0.into(),
            ..Default::default()
        },
        ..Default::default()
    }
}

pub fn troll_button_style(active: bool) -> impl Fn(&Theme, button::Status) -> button::Style {
    move |_theme: &Theme, _status: button::Status| {
        let bg = if active {
            color!(0x8e44ad)
        } else {
            color!(0x2c3e50)
        };
        button::Style {
            background: Some(iced::Background::Color(bg)),
            text_color: color!(0xffffff),
            border: iced::Border {
                radius: 4.0.into(),
                ..Default::default()
            },
            ..Default::default()
        }
    }
}
