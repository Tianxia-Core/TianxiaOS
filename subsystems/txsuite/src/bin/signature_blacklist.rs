// ffp: TX-SIGNATURE-BLACKLIST crypto-signer rust
//! Synthesize signature blacklist + Suricata perimeter rules from trap intel.
//! Converted from tx_signature_blacklist.py.
use rusqlite::Connection;
use serde_json::json;
use std::fs;
use std::path::Path;

const DB_PATH: &str = "/dev/shm/tianxia_telemetry.db";
const OUTPUT_DIR: &str = "/var/lib/tianxia/security";

fn main() {
    let out_dir = Path::new(OUTPUT_DIR);
    let _ = fs::create_dir_all(out_dir);
    let json_out = out_dir.join("signature_blacklist.json");
    let rules_out = out_dir.join("tianxia_perimeter_rules.rules");

    let mut signatures: Vec<serde_json::Value> = vec![];
    let mut rules: Vec<String> = vec![];

    if Path::new(DB_PATH).exists() {
        if let Ok(conn) = Connection::open(DB_PATH) {
            let q = conn.prepare(
                "SELECT payload_sha256, COUNT(*), fingerprint_verdict,
                        AVG(session_duration), GROUP_CONCAT(DISTINCT src_ip),
                        MIN(timestamp), MAX(timestamp), raw_headers
                 FROM study_trap_intel
                 WHERE payload_sha256 != 'empty' AND payload_sha256 IS NOT NULL
                 GROUP BY payload_sha256
                 ORDER BY COUNT(*) DESC",
            );
            if let Ok(mut stmt) = q {
                let rows = stmt.query_map([], |r| {
                    Ok((
                        r.get::<_, String>(0)?,
                        r.get::<_, i64>(1)?,
                        r.get::<_, Option<String>>(2)?,
                        r.get::<_, Option<f64>>(3)?,
                        r.get::<_, Option<String>>(4)?,
                        r.get::<_, Option<f64>>(5)?,
                        r.get::<_, Option<f64>>(6)?,
                        r.get::<_, Option<String>>(7)?,
                    ))
                });
                let mut sid: u32 = 1_000_001;
                if let Ok(rows) = rows {
                    for row in rows.flatten() {
                        let (sha, hits, verdict, avg_held, sources, first_seen, last_seen, sample_raw) = row;
                        let src_list: Vec<String> = sources
                            .as_deref()
                            .map(|s| s.split(',').map(|x| x.to_string()).collect())
                            .unwrap_or_default();
                        let avg = ((avg_held.unwrap_or(0.0)) * 100.0).round() / 100.0;
                        signatures.push(json!({
                            "sha256": sha,
                            "verdict": verdict,
                            "hit_count": hits,
                            "avg_tarpit_hold_sec": avg,
                            "source_ips": src_list,
                            "first_seen_epoch": first_seen,
                            "last_seen_epoch": last_seen,
                            "payload_sample": sample_raw.as_deref().unwrap_or("").chars().take(128).collect::<String>(),
                        }));
                        let clean = sample_raw.unwrap_or_default()
                            .trim()
                            .replace('"', "\\\"")
                            .replace('\n', "\\n");
                        if clean.len() > 8 && !clean.starts_with("b'") {
                            let msg_verdict = verdict.clone().unwrap_or_else(|| "UNKNOWN".into());
                            let sample32: String = clean.chars().take(32).collect();
                            rules.push(format!(
                                "drop tcp any any -> any any (msg:\"TIANXIA_DROP {}\"; content:\"{}\"; sid:{}; rev:1;)",
                                msg_verdict, sample32, sid
                            ));
                            sid += 1;
                        }
                    }
                }
            }
        }
    }

    let now = std::process::Command::new("date")
        .args(["-u", "+%Y-%m-%dT%H:%M:%SZ"])
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default();
    let blacklist = json!({
        "generated_utc": now,
        "total_unique_signatures": signatures.len(),
        "signatures": signatures,
    });
    let _ = fs::write(&json_out, serde_json::to_string_pretty(&blacklist).unwrap_or_default());
    let _ = fs::write(&rules_out, format!("{}\n", rules.join("\n")));
    println!(
        "[\u{2713}] Signature Blacklist synthesized ({} signatures).",
        blacklist["total_unique_signatures"]
    );
}
