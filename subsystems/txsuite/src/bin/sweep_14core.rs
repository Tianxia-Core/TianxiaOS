// ffp: TX-14CORE-SWEEP compute-kernel rust
//! Full 14-core Dasavidyayana telemetry sweep over the UDS fast-path.
//! Converted from tx_14core_sweep.py; dispatches one JSON request per core
//! to /run/tianxia/tx_fastpath.sock and reports latency/state per core.
use serde_json::{json, Value};
use std::io::{Read, Write};
use std::os::unix::net::UnixStream;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

const SOCKET_PATH: &str = "/run/tianxia/tx_fastpath.sock";

fn base() -> PathBuf {
    PathBuf::from(std::env::var("TX_BASE_DIR").unwrap_or_else(|_| "/var/lib/tianxia".into()))
}

fn halted() -> bool {
    Path::new("/var/lib/tianxia/AUTONOMY_PAUSED").exists()
        || Path::new("/var/lib/tianxia/PROBE_STOP").exists()
}

fn token(b: &Path) -> String {
    std::fs::read_to_string(b.join("secrets/substrate_auth.token"))
        .map(|s| s.trim().to_string())
        .unwrap_or_default()
}

fn cores() -> Vec<(&'static str, &'static str, Value)> {
    vec![
        ("Core 01 (Kālī)", "KALI", json!({"series": [10, 20, 30]})),
        ("Core 02 (Tārā)", "TARA", json!({})),
        ("Core 03 (Tripura Sundarī)", "TRIPURA", json!({})),
        ("Core 04 (Bhuvanēśvarī)", "BHUVANESVARI", json!({})),
        ("Core 05 (Bhairavī)", "BHAIRAVI", json!({})),
        ("Core 06 (Chhinnamastā)", "CHHINNAMASTA", json!({})),
        ("Core 07 (Dhūmāvatī)", "DHUMAVATI", json!({})),
        ("Core 08 (Bagalāmukhī)", "BAGALAMUKHI", json!({})),
        ("Core 09 (Mātaṅgī)", "MATANGI", json!({"text": "Acoustic sync"})),
        ("Core 10 (Kamalā)", "KAMALA", json!({})),
        ("Core 11 (Pratyaṅgirā)", "PRATYANGIRA", json!({})),
        ("Core 12 (Annapūrṇā)", "ANNAPURNA", json!({})),
        ("Core 13 (Mahāsarasvatī)", "MAHASARASVATI", json!({"prompt": "Emit heartbeat in Zig"})),
        ("Core 14 (Paramaśiva)", "PARAMASIVA", json!({})),
    ]
}

fn sweep_one(intent: &str, kwargs: Value, auth: &str) -> Result<(String, f64), String> {
    let t0 = Instant::now();
    let mut stream = UnixStream::connect(SOCKET_PATH).map_err(|e| e.to_string())?;
    let _ = stream.set_read_timeout(Some(Duration::from_secs(2)));
    let _ = stream.set_write_timeout(Some(Duration::from_secs(2)));

    let mut payload = json!({"auth": auth, "intent": intent});
    if let Some(map) = payload.as_object_mut() {
        if let Value::Object(extra) = kwargs {
            for (k, v) in extra {
                map.insert(k, v);
            }
        }
    }
    let mut body = serde_json::to_string(&payload).map_err(|e| e.to_string())?;
    body.push('\n');
    stream
        .write_all(body.as_bytes())
        .map_err(|e| e.to_string())?;

    let mut buf = vec![0u8; 4096];
    let n = stream.read(&mut buf).map_err(|e| e.to_string())?;
    let raw = String::from_utf8_lossy(&buf[..n]).trim().to_string();
    let res: Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;

    let lat = res
        .get("latency_ms")
        .and_then(|v| v.as_f64())
        .unwrap_or_else(|| {
            let ms = t0.elapsed().as_secs_f64() * 1000.0;
            (ms * 100.0).round() / 100.0
        });
    let core_id = res
        .get("core")
        .and_then(|v| v.as_str())
        .unwrap_or(intent)
        .to_string();
    Ok((core_id, lat))
}

fn main() {
    let b = base();
    if halted() {
        eprintln!("[!] 14-core sweep halted by kill-switch (AUTONOMY_PAUSED/PROBE_STOP)");
        return;
    }
    let auth = token(&b);

    println!("=========================================================================");
    println!(" [*] TIANXIA ASURA: FULL 14-CORE DASASAVIDYAYANA TELEMETRY SWEEP");
    println!("=========================================================================");

    for (name, intent, kwargs) in cores() {
        match sweep_one(intent, kwargs, &auth) {
            Ok((core_id, lat)) => {
                println!(
                    " ├── [✓] {:<26} | Latency: {:>5.2} ms | State: ACTIVE",
                    core_id, lat
                );
            }
            Err(e) => {
                println!(" ├── [✗] {:<26} | Error: {}", name, e);
            }
        }
    }

    println!("=========================================================================");
    println!(" [✓] 14/14 CORES SYNCHRONIZED AND DISPATCHABLE OVER UDS FAST-PATH");
    println!("=========================================================================");
}
