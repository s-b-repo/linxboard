use evdev::Key;

use crate::profile::model::Modifier;

pub fn evdev_key_to_modifier(key: Key) -> Option<Modifier> {
    match key {
        Key::KEY_LEFTCTRL | Key::KEY_RIGHTCTRL => Some(Modifier::Ctrl),
        Key::KEY_LEFTALT | Key::KEY_RIGHTALT => Some(Modifier::Alt),
        Key::KEY_LEFTSHIFT | Key::KEY_RIGHTSHIFT => Some(Modifier::Shift),
        Key::KEY_LEFTMETA | Key::KEY_RIGHTMETA => Some(Modifier::Super),
        _ => None,
    }
}

pub fn evdev_key_to_code(key: Key) -> u16 {
    key.0
}

pub fn key_name_to_evdev(name: &str) -> Option<u16> {
    match name.to_uppercase().as_str() {
        "ESC" | "ESCAPE" => Some(Key::KEY_ESC.0),
        "1" => Some(Key::KEY_1.0),
        "2" => Some(Key::KEY_2.0),
        "3" => Some(Key::KEY_3.0),
        "4" => Some(Key::KEY_4.0),
        "5" => Some(Key::KEY_5.0),
        "6" => Some(Key::KEY_6.0),
        "7" => Some(Key::KEY_7.0),
        "8" => Some(Key::KEY_8.0),
        "9" => Some(Key::KEY_9.0),
        "0" => Some(Key::KEY_0.0),
        "Q" => Some(Key::KEY_Q.0),
        "W" => Some(Key::KEY_W.0),
        "E" => Some(Key::KEY_E.0),
        "R" => Some(Key::KEY_R.0),
        "T" => Some(Key::KEY_T.0),
        "Y" => Some(Key::KEY_Y.0),
        "U" => Some(Key::KEY_U.0),
        "I" => Some(Key::KEY_I.0),
        "O" => Some(Key::KEY_O.0),
        "P" => Some(Key::KEY_P.0),
        "A" => Some(Key::KEY_A.0),
        "S" => Some(Key::KEY_S.0),
        "D" => Some(Key::KEY_D.0),
        "F" => Some(Key::KEY_F.0),
        "G" => Some(Key::KEY_G.0),
        "H" => Some(Key::KEY_H.0),
        "J" => Some(Key::KEY_J.0),
        "K" => Some(Key::KEY_K.0),
        "L" => Some(Key::KEY_L.0),
        "Z" => Some(Key::KEY_Z.0),
        "X" => Some(Key::KEY_X.0),
        "C" => Some(Key::KEY_C.0),
        "V" => Some(Key::KEY_V.0),
        "B" => Some(Key::KEY_B.0),
        "N" => Some(Key::KEY_N.0),
        "M" => Some(Key::KEY_M.0),
        "SPACE" => Some(Key::KEY_SPACE.0),
        "F1" => Some(Key::KEY_F1.0),
        "F2" => Some(Key::KEY_F2.0),
        "F3" => Some(Key::KEY_F3.0),
        "F4" => Some(Key::KEY_F4.0),
        "F5" => Some(Key::KEY_F5.0),
        "F6" => Some(Key::KEY_F6.0),
        "F7" => Some(Key::KEY_F7.0),
        "F8" => Some(Key::KEY_F8.0),
        "F9" => Some(Key::KEY_F9.0),
        "F10" => Some(Key::KEY_F10.0),
        "F11" => Some(Key::KEY_F11.0),
        "F12" => Some(Key::KEY_F12.0),
        _ => None,
    }
}
