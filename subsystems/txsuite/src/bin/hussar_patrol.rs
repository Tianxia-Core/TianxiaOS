// ffp: TX-HUSSAR-PATROL concurrent-daemon rust
//! Hussar patrol sweep over the Tianxia fastpath Unix socket.
//! Converted from tx_hussar_patrol.py.
use serde_json::{json, Value};
use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::os::unix::net::UnixStream;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Duration, Instant};

const SOCKET_PATH: &str = "/run/tianxia/tx_fastpath.sock";
const CORES: [&str; 14] = [
    "KALI",
    "TARA",
    "TRIPURA",
    "BHUVANESVARI",
    "BHAIRAVI",
    "CHHINNAMASTA",
    "DHUMAVATI",
    "BAGALAMUKHI",
    "MATANGI",
    "KAMALA",
    "PRATYANGIRA",
    "ANNAPURNA",
    "MAHASARASVATI",
    "PARAMASIVA",
];

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

fn now_stamp() -> String {
    Command::new("date")
        .arg("+%Y-%m-%d %H:%M:%S")
        .output()
        .ok()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default()
}

fn read_token(base: &Path) -> String {
    let candidates = [
        base.join("secrets").join("substrate_auth.token"),
        PathBuf::from("/var/lib/tianxia/secrets/substrate_auth.token"),
    ];
    for p in candidates {
        if let Ok(s) = fs::read_to_string(&p) {
            let t = s.trim();
            if !t.is_empty() {
                return t.to_string();
            }
        }
    }
    String::new()
}

fn sweep(token: &str) -> (usize, f64) {
    let t0 = Instant::now();
    let mut active = 0usize;
    let stream = match UnixStream::connect(SOCKET_PATH) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("[tx_hussar_patrol] fastpath unavailable: {}", e);
            return (0, t0.elapsed().as_secs_f64() * 1000.0);
        }
    };
    let _ = stream.set_read_timeout(Some(Duration::from_secs(3)));
    let _ = stream.set_write_timeout(Some(Duration::from_secs(3)));
    let mut reader = match stream.try_clone() {
        Ok(c) => BufReader::new(c),
        Err(e) => {
            eprintln!("[tx_hussar_patrol] socket clone failed: {}", e);
            return (0, t0.elapsed().as_secs_f64() * 1000.0);
        }
    };
    let mut writer = stream;
    for core in CORES {
        let payload = json!({"auth": token, "intent": core}).to_string() + "\n";
        if let Err(e) = writer.write_all(payload.as_bytes()) {
            eprintln!("[tx_hussar_patrol] write error: {}", e);
            break;
        }
        if let Err(e) = writer.flush() {
            eprintln!("[tx_hussar_patrol] flush error: {}", e);
            break;
        }
        let mut line = String::new();
        match reader.read_line(&mut line) {
            Ok(0) => break,
            Ok(_) => {
                if let Ok(v) = serde_json::from_str::<Value>(line.trim()) {
                    if v.get("status").and_then(|s| s.as_str()) == Some("SUCCESS") {
                        active += 1;
                    }
                }
            }
            Err(e) => {
                eprintln!("[tx_hussar_patrol] read error: {}", e);
                break;
            }
        }
    }
    (active, t0.elapsed().as_secs_f64() * 1000.0)
}

fn main() {
    let base = base_dir();
    let _ = fs::create_dir_all(base.join("logs"));
    let _ = fs::create_dir_all("/var/lib/tianxia/logs");
    let token = read_token(&base);
    while !halted(&base) {
        let (active, ms) = sweep(&token);
        println!(
            "[{}] [✓] Hussar Patrol Sweep: {}/14 Cores Active | Latency: {:>5.2} ms",
            now_stamp(),
            active,
            ms
        );
        let _ = std::io::stdout().flush();
        for _ in 0..20 {
            if halted(&base) {
                break;
            }
            std::thread::sleep(Duration::from_millis(500));
        }
    }
    println!("[tx_hussar_patrol] halted by kill-switch");
}
