// ffp: TX-AUXILIARY-DAEMONS concurrent-daemon rust
//! Tianxia Auxiliary Neural Substrate telemetry HTTP daemon.
//! Converted from tx_auxiliary_daemons.py. Adds kill-switch support.
use serde_json::json;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::thread;
use std::time::Duration;

const DEFAULT_PORT: u16 = 9192;
const MAX_REQUEST: usize = 65536;

fn base_dir() -> PathBuf {
    PathBuf::from(
        std::env::var("TX_BASE_DIR")
            .ok()
            .filter(|v| !v.is_empty())
            .unwrap_or_else(|| "/var/lib/tianxia".into()),
    )
}

fn halted(base: &Path) -> bool {
    base.join("AUTONOMY_PAUSED").exists()
        || base.join("PROBE_STOP").exists()
        || Path::new("/var/lib/tianxia/AUTONOMY_PAUSED").exists()
        || Path::new("/var/lib/tianxia/PROBE_STOP").exists()
}

fn status_body(base: &Path, port: u16) -> String {
    let models = base.join("models");
    let body = json!({
        "status": "ONLINE",
        "port": port,
        "plane": "Tianxia Auxiliary Neural Substrate",
        "models": {
            "whisper_stt": models.join("whisper-v4-turbo.bin").exists(),
            "timesfm_forecaster": models.join("timesfm-1.0-200m.safetensors").exists(),
            "kokoro_tts": models.join("kokoro-82m.onnx").exists(),
            "voices_tensor": models.join("voices.bin").exists()
        }
    });
    serde_json::to_string_pretty(&body).unwrap_or_else(|_| "{}".into())
}

fn respond(stream: &mut TcpStream, code: u16, reason: &str, body: &str) {
    let resp = format!(
        "HTTP/1.1 {} {}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
        code,
        reason,
        body.len(),
        body
    );
    let _ = stream.write_all(resp.as_bytes());
    let _ = stream.flush();
}

fn handle(mut stream: TcpStream, base: PathBuf, port: u16) {
    let _ = stream.set_read_timeout(Some(Duration::from_secs(5)));
    let _ = stream.set_write_timeout(Some(Duration::from_secs(5)));
    let mut buf: Vec<u8> = Vec::with_capacity(1024);
    let mut tmp = [0u8; 2048];
    loop {
        if buf.len() >= MAX_REQUEST {
            break;
        }
        match stream.read(&mut tmp) {
            Ok(0) => break,
            Ok(n) => {
                buf.extend_from_slice(&tmp[..n]);
                if buf.windows(4).any(|w| w == b"\r\n\r\n") {
                    break;
                }
            }
            Err(_) => break,
        }
    }
    let head = String::from_utf8_lossy(&buf).into_owned();
    let method = head
        .split("\r\n")
        .next()
        .and_then(|l| l.split_whitespace().next())
        .unwrap_or("")
        .to_string();
    match method.as_str() {
        "GET" => {
            let body = status_body(&base, port);
            respond(&mut stream, 200, "OK", &body);
        }
        "POST" => {
            let body = json!({"result": "ACK", "status": "PROCESSED"}).to_string();
            respond(&mut stream, 200, "OK", &body);
        }
        _ => respond(&mut stream, 501, "Not Implemented", "{}"),
    }
}

fn main() {
    let base = base_dir();
    let port = match std::env::args().nth(1) {
        Some(a) => match a.parse::<u16>() {
            Ok(p) if p > 0 => p,
            _ => {
                eprintln!("[tx_auxiliary_daemons] invalid port: {}", a);
                std::process::exit(1);
            }
        },
        None => DEFAULT_PORT,
    };
    let listener = match TcpListener::bind(("0.0.0.0", port)) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("[tx_auxiliary_daemons] bind 0.0.0.0:{} failed: {}", port, e);
            std::process::exit(1);
        }
    };
    let _ = listener.set_nonblocking(true);
    println!(
        "[tx_auxiliary_daemons] Tianxia Auxiliary Neural Substrate listening on 0.0.0.0:{} (base={})",
        port,
        base.display()
    );
    if halted(&base) {
        println!("[tx_auxiliary_daemons] halted by kill-switch");
        return;
    }
    loop {
        if halted(&base) {
            println!("[tx_auxiliary_daemons] halted by kill-switch");
            break;
        }
        match listener.accept() {
            Ok((stream, _)) => {
                let b = base.clone();
                let _ = thread::Builder::new()
                    .name("tx-aux-http".into())
                    .spawn(move || handle(stream, b, port));
            }
            Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                thread::sleep(Duration::from_millis(250));
            }
            Err(e) => {
                eprintln!("[tx_auxiliary_daemons] accept error: {}", e);
                thread::sleep(Duration::from_millis(500));
            }
        }
    }
}
