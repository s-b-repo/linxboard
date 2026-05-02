use std::collections::HashMap;
use std::io::Cursor;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use crossbeam_channel::Receiver;
use rodio::{Decoder, OutputStream, OutputStreamHandle, Sink, Source};

pub const MAX_CHANNELS: usize = 32;

#[derive(Debug, Clone)]
pub enum AudioCommand {
    Play {
        path: PathBuf,
        volume: f32,
        looping: bool,
    },
    StopAll,
    SetMasterVolume(f32),
}

pub struct AudioEngine {
    _stream: OutputStream,
    stream_handle: OutputStreamHandle,
    sinks: Vec<Sink>,
    master_volume: f32,
    cache: HashMap<PathBuf, Arc<Vec<u8>>>,
    command_rx: Receiver<AudioCommand>,
}

impl AudioEngine {
    pub fn spawn(command_rx: Receiver<AudioCommand>) -> std::thread::JoinHandle<()> {
        std::thread::Builder::new()
            .name("audio-engine".into())
            .spawn(move || {
                let engine = Self::new(command_rx);
                engine.run();
            })
            .expect("failed to spawn audio thread")
    }

    fn new(command_rx: Receiver<AudioCommand>) -> Self {
        let (stream, stream_handle) =
            OutputStream::try_default().expect("failed to open audio output");

        let sinks: Vec<Sink> = (0..MAX_CHANNELS)
            .map(|_| Sink::try_new(&stream_handle).unwrap())
            .collect();

        Self {
            _stream: stream,
            stream_handle,
            sinks,
            master_volume: 0.7,
            cache: HashMap::new(),
            command_rx,
        }
    }

    fn run(mut self) {
        while let Ok(cmd) = self.command_rx.recv() {
            match cmd {
                AudioCommand::Play {
                    path,
                    volume,
                    looping,
                } => {
                    self.play(&path, volume, looping);
                }
                AudioCommand::StopAll => {
                    for sink in &self.sinks {
                        sink.stop();
                    }
                    self.sinks = (0..MAX_CHANNELS)
                        .map(|_| Sink::try_new(&self.stream_handle).unwrap())
                        .collect();
                }
                AudioCommand::SetMasterVolume(v) => {
                    self.master_volume = v;
                    for sink in &self.sinks {
                        sink.set_volume(v);
                    }
                }
            }
        }
    }

    fn play(&mut self, path: &Path, volume: f32, looping: bool) {
        let sink_idx = self.sinks.iter().position(|s| s.empty()).unwrap_or(0);

        let bytes = self
            .cache
            .entry(path.to_path_buf())
            .or_insert_with(|| Arc::new(std::fs::read(path).unwrap_or_default()))
            .clone();

        if bytes.is_empty() {
            log::warn!("Could not read audio file: {:?}", path);
            return;
        }

        let cursor = Cursor::new((*bytes).clone());
        match Decoder::new(cursor) {
            Ok(source) => {
                let sink = &self.sinks[sink_idx];
                sink.set_volume(volume * self.master_volume);
                if looping {
                    sink.append(source.repeat_infinite());
                } else {
                    sink.append(source);
                }
            }
            Err(e) => {
                log::warn!("Failed to decode {:?}: {}", path, e);
            }
        }
    }
}
