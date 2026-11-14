// ffp: TX-SYNC-SIGNATURES crypto-signer rust
//! Compile study-trap intel into signature blacklist + replicate. Converted from tx_sync_signatures.sh.
use rusqlite::Connection;
use serde_json::json;
use std::fs;
use std::process::Command;

const DB_PATH: &str = "/dev/shm/tianxia_telemetry.db";
const JSON_PATH: &str = "/var/lib/tianxia/security/signature_blacklist.json";
const TARGETS: &[(&str, &str, &str)] = &[
    ("xps13", "mesh-node-b.local:22", "/var/lib/tianxia/security/signature_blacklist.json"),
    ("pixel", "mesh-node-c.local:8022", "${TX_HOME:-/var/lib/tianxia}/.tianxia/security/signature_blacklist.json"),
    ("pixel_wg", "mesh-core-3.internal:8022", "${TX_HOME:-/var/lib/tianxia}/.tianxia/security/signature_blacklist.json"),
    ("poco", "mesh-core-4.internal:8022", "${TX_HOME:-/var/lib/tianxia}/.tianxia/security/signature_blacklist.json"),
];

fn main() {
    if !std::path::Path::new(DB_PATH).exists() {
        eprintln!("[sync-signatures] telemetry db absent: {}", DB_PATH);
        std::process::exit(0);
    }
    let conn = match Connection::open(DB_PATH) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("[sync-signatures] db open failed: {}", e);
            std::process::exit(0);
        }
    };
    let mut stmt = match conn.prepare(
        "SELECT payload_sha256, fingerprint_verdict, COUNT(*), AVG(session_duration), GROUP_CONCAT(DISTINCT src_ip), MIN(timestamp), MAX(timestamp), raw_headers
         FROM study_trap_intel WHERE quarantined = 1
         GROUP BY payload_sha256",
    ) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("[sync-signatures] query prep failed: {}", e);
            std::process::exit(0);
        }
    };
    let rows = match stmt.query_map([], |r| {
        Ok(json!({
            "sha256": r.get::<_, String>(0)?,
            "verdict": r.get::<_, Option<String>>(1)?,
            "hit_count": r.get::<_, i64>(2)?,
            "avg_tarpit_hold_sec": ((r.get::<_, Option<f64>>(3)?.unwrap_or(0.0)) * 100.0).round() / 100.0,
            "source_ips": r.get::<_, Option<String>>(4)?,
            "first_seen_epoch": r.get::<_, Option<f64>>(5)?,
            "last_seen_epoch": r.get::<_, Option<f64>>(6)?,
            "payload_sample": r.get::<_, Option<String>>(7)?.unwrap_or_default().chars().take(128).collect::<String>(),
        }))
    }) {
        Ok(r) => r,
        Err(e) => {
            eprintln!("[sync-signatures] query failed: {}", e);
            std::process::exit(0);
        }
    };
    let signatures: Vec<serde_json::Value> = rows.filter_map(|r| r.ok()).collect();
    let now = std::process::Command::new("date")
        .args(["-u", "+%Y-%m-%dT%H:%M:%S+00:00"])
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default();
    let output = json!({
        "generated_utc": now,
        "total_unique_signatures": signatures.len(),
        "signatures": signatures,
    });
    if let Some(parent) = std::path::Path::new(JSON_PATH).parent() {
        let _ = fs::create_dir_all(parent);
    }
    if let Err(e) = fs::write(JSON_PATH, serde_json::to_string_pretty(&output).unwrap_or_default()) {
        eprintln!("[sync-signatures] write failed: {}", e);
        return;
    }
    println!("[sync-signatures] wrote {} signatures -> {}", signatures.len(), JSON_PATH);
    for (node, hostport, remote_file) in TARGETS {
        let mut parts = hostport.split(':');
        let ip = parts.next().unwrap_or("");
        let port = parts.next().unwrap_or("22");
        let ping_ok = Command::new("ping")
            .args(["-c", "1", "-W", "1", ip])
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false);
        if ping_ok {
            let _ = Command::new("rsync")
                .args([
                    "-avz",
                    "-e",
                    &format!("ssh -p {} -i /root/.ssh/id_ed25519 -o ConnectTimeout=3 -o StrictHostKeyChecking=no", port),
                    JSON_PATH,
                    &format!("root@{}:{}", ip, remote_file),
                ])
                .output();
            println!("[sync-signatures] replicated -> {}", node);
        }
    }
}
