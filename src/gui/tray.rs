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

    gtk::init().map_err(|e| anyhow::anyhow!("GTK init failed: {}", e))?;

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
    let show_id = show_item.id().clone();
    let stop_id = stop_item.id().clone();
    let quit_id = quit_item.id().clone();

    gtk::glib::timeout_add_local(std::time::Duration::from_millis(100), move || {
        while let Ok(event) = menu_rx.try_recv() {
            if event.id() == &show_id {
                let _ = msg_tx.send(Message::ShowWindow);
            } else if event.id() == &stop_id {
                let _ = msg_tx.send(Message::PanicStop);
            } else if event.id() == &quit_id {
                let _ = msg_tx.send(Message::Quit);
                return gtk::glib::ControlFlow::Break;
            }
        }
        gtk::glib::ControlFlow::Continue
    });

    gtk::main();

    Ok(())
}
