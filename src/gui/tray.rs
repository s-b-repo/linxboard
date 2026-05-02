use crossbeam_channel::Sender;

use crate::app::Message;

pub fn spawn_tray(msg_tx: Sender<Message>) {
    std::thread::Builder::new()
        .name("tray-icon".into())
        .spawn(move || {
            if let Err(e) = run_tray(msg_tx) {
                log::warn!("System tray unavailable: {}", e);
            }
        })
        .ok();
}

fn run_tray(msg_tx: Sender<Message>) -> anyhow::Result<()> {
    use muda::{Menu, MenuEvent, MenuItem};
    use tray_icon::{Icon, TrayIconBuilder};

    let menu = Menu::new();
    let show_item = MenuItem::new("Show", true, None);
    let stop_item = MenuItem::new("Stop All", true, None);
    let quit_item = MenuItem::new("Quit", true, None);

    menu.append(&show_item)?;
    menu.append(&stop_item)?;
    menu.append(&quit_item)?;

    let pixel: [u8; 4] = [0x34, 0x49, 0x5e, 0xff];
    let icon_data: Vec<u8> = pixel.iter().copied().cycle().take(32 * 32 * 4).collect();
    let icon = Icon::from_rgba(icon_data, 32, 32)
        .unwrap_or_else(|_| Icon::from_rgba(vec![0; 4], 1, 1).unwrap());

    let _tray = TrayIconBuilder::new()
        .with_menu(Box::new(menu))
        .with_icon(icon)
        .with_tooltip("Linxboard")
        .build()?;

    let menu_rx = MenuEvent::receiver();
    loop {
        if let Ok(event) = menu_rx.recv() {
            if event.id() == show_item.id() {
                let _ = msg_tx.send(Message::ShowWindow);
            } else if event.id() == stop_item.id() {
                let _ = msg_tx.send(Message::PanicStop);
            } else if event.id() == quit_item.id() {
                let _ = msg_tx.send(Message::Quit);
                break;
            }
        }
    }

    Ok(())
}
