// ffp: TX-STATE-SENTINEL compute-kernel rust
//! Vector state-lock integrity sentinel. Converted from tx_state_sentinel.py.
//! Reads transcripts.db read-only, hashes (count:max_id:size), writes the
//! state lock JSON, prints the Bāgalamukhī lock line.
use rusqlite::{Connection, OpenFlags};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

fn base() -> PathBuf {
    PathBuf::from(std::env::var("TX_BASE_DIR").unwrap_or_else(|_| "/var/lib/tianxia".into()))
}

fn compute_integrity(db: &PathBuf) -> (String, i64) {
    if !db.exists() {
        return ("NO_DB_INITIALIZED".into(), 0);
    }
    let conn = match Connection::open_with_flags(db, OpenFlags::SQLITE_OPEN_READ_ONLY) {
        Ok(c) => c,
        Err(e) => return (format!("ERR:{}", e), 0),
    };
    let row: Result<(i64, Option<i64>), _> = conn.query_row(
        "SELECT count(*), max(id) FROM transcript_embeddings;",
        [],
        |r| Ok((r.get(0)?, r.get(1)?)),
    );
    let (count, max_id) = match row {
        Ok(v) => v,
        Err(e) => return (format!("ERR:{}", e), 0),
    };
    let db_size = fs::metadata(db).map(|m| m.len()).unwrap_or(0);
    let sig = format!("{}:{}:{}", count, max_id.unwrap_or(0), db_size);
    let mut h = Sha256::new();
    h.update(sig.as_bytes());
    let digest = h.finalize();
    let hex = digest.iter().map(|b| format!("{:02x}", b)).collect::<String>();
    (hex, count)
}

fn main() {
    let base = base();
    let db = base.join("db").join("transcripts.db");
    let state_file = base.join("db").join(".vector_state.lock");
    let (hash, total) = compute_integrity(&db);
    let locked_at = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0);
    let state = serde_json::json!({
        "verified_hash": hash,
        "total_chunks": total,
        "locked_at": locked_at,
        "status": "STATE_LOCKED"
    });
    if let Some(parent) = state_file.parent() {
        let _ = fs::create_dir_all(parent);
    }
    if let Err(e) = fs::write(&state_file, serde_json::to_string_pretty(&state).unwrap_or_default()) {
        eprintln!("state write failed: {}", e);
    }
    let short: String = hash.chars().take(16).collect();
    println!(
        " [\u{2713}] Bagal\u{0101}mukh\u{012b} Vector State-Lock: {} chunks (Hash: {}...)",
        total, short
    );
}
