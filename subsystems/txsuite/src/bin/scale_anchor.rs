// ffp: TX-SCALE-ANCHOR wire-codec rust
//! SCALE-codec encoder + Blake2b substrate extrinsic anchor. Converted from tx_scale.py.
//! Payload: Pallet(u8) || Call(u8) || Compact<u32>(block) || AccountId32 || Blake2b256(target)
use blake2::{Blake2b, Digest};
use rusqlite::Connection;
use std::path::PathBuf;
use std::process::exit;
use std::time::{SystemTime, UNIX_EPOCH};

const CHAIN_RPC: &str = "https://rpc-etamanga.rasaxmachina.com";
const PALLET: u8 = 0x42;
const CALL: u8 = 0x01;

fn base() -> PathBuf {
    PathBuf::from(std::env::var("TX_BASE_DIR").unwrap_or_else(|_| "/var/lib/tianxia".into()))
}

fn compact_u32(n: u32) -> Result<Vec<u8>, String> {
    if n < 64 {
        Ok(vec![((n << 2) | 0x00) as u8])
    } else if n < (1 << 14) {
        Ok((((n << 2) | 0x01) as u16).to_le_bytes().to_vec())
    } else if n < (1 << 30) {
        Ok(((n << 2) | 0x02).to_le_bytes().to_vec())
    } else {
        Err("compact u32 overflow".into())
    }
}

fn blake2b_256(data: &[u8]) -> Vec<u8> {
    let mut h = Blake2b::<blake2::digest::consts::U32>::new();
    h.update(data);
    h.finalize().to_vec()
}

fn hex_encode(b: &[u8]) -> String {
    b.iter().map(|x| format!("{:02x}", x)).collect()
}

fn decode_hex(s: &str) -> Option<Vec<u8>> {
    let s = s.trim().trim_start_matches("0x");
    if s.len() % 2 != 0 {
        return None;
    }
    let bytes = s.as_bytes();
    let mut out = Vec::with_capacity(s.len() / 2);
    let mut i = 0;
    while i < bytes.len() {
        let hi = (bytes[i] as char).to_digit(16)?;
        let lo = (bytes[i + 1] as char).to_digit(16)?;
        out.push((hi * 16 + lo) as u8);
        i += 2;
    }
    Some(out)
}

fn encode_payload(block: u32, account: &[u8; 32], target: &[u8]) -> Result<Vec<u8>, String> {
    let mut p = vec![PALLET, CALL];
    p.extend_from_slice(&compact_u32(block)?);
    p.extend_from_slice(account);
    p.extend_from_slice(&blake2b_256(target));
    Ok(p)
}

fn chain_tip() -> Result<u64, String> {
    let body = serde_json::json!({"jsonrpc":"2.0","id":1,"method":"chain_getHeader","params":[]});
    let resp = ureq::post(CHAIN_RPC)
        .timeout(std::time::Duration::from_secs(20))
        .set("Content-Type", "application/json")
        .send_string(&body.to_string())
        .map_err(|e| e.to_string())?;
    let v: serde_json::Value = resp.into_json().map_err(|e| e.to_string())?;
    let number = v["result"]["number"].as_str().ok_or("no header number")?;
    let n = u64::from_str_radix(number.trim_start_matches("0x"), 16).map_err(|e| e.to_string())?;
    Ok(n + 1)
}

fn cmd_anchor(target_hex: &str) -> i32 {
    let target = match decode_hex(target_hex) {
        Some(t) => t,
        None => {
            println!("{}", serde_json::json!({"error": "bad target hex"}));
            return 1;
        }
    };
    let tip = match chain_tip() {
        Ok(t) => t,
        Err(e) => {
            println!("{}", serde_json::json!({"error": e.chars().take(80).collect::<String>()}));
            return 1;
        }
    };
    let acct = [0u8; 32];
    let payload = match encode_payload(tip as u32, &acct, &target) {
        Ok(p) => p,
        Err(e) => {
            println!("{}", serde_json::json!({"error": e}));
            return 1;
        }
    };
    let proof = hex_encode(&blake2b_256(&payload));
    let now = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs_f64()).unwrap_or(0.0);
    let db = base().join("db").join("vacuum.sqlite3");
    if let Ok(conn) = Connection::open(&db) {
        let _ = conn.execute(
            "CREATE TABLE IF NOT EXISTS substrate_anchors
             (ts REAL, block INTEGER, target TEXT, payload TEXT, proof TEXT, mode TEXT)",
            [],
        );
        let _ = conn.execute(
            "INSERT INTO substrate_anchors VALUES (?1,?2,?3,?4,?5,?6)",
            rusqlite::params![now, tip, &target_hex[..target_hex.len().min(66)], hex_encode(&payload), proof, "paper"],
        );
        let _ = conn.execute(
            "INSERT INTO vacuum_runs VALUES (?1,?2,?3,?4,?5)",
            rusqlite::params![now, "scale-anchor", 1, 1, "paper"],
        );
    }
    let payload_hex = hex_encode(&payload);
    let out = serde_json::json!({
        "mode": "paper",
        "block": tip,
        "payload_bytes": payload.len(),
        "payload_hex": format!("{}...", &payload_hex[..payload_hex.len().min(120)]),
        "proof": format!("{}...", &proof[..proof.len().min(32)]),
        "submit": false
    });
    println!("{}", serde_json::to_string_pretty(&out).unwrap_or_default());
    0
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 || args[1] != "anchor" {
        println!("usage: scale_anchor anchor <target_hex> [--submit]");
        exit(1);
    }
    exit(cmd_anchor(&args[2]));
}
