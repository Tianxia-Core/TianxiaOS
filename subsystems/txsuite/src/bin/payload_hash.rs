// ffp: TX-PAYLOAD-HASH compute-kernel rust
//! Keccak-256 of the canonical chain-op payload. Converted from tx_payload_hash.py.
//! Fields: chain|op|sender|recipient|target|amount|fee|nonce|ts(6dp)
use sha3::{Digest, Keccak256};
use std::process::exit;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 10 {
        eprintln!("usage: payload_hash <chain> <op> <sender> <recipient> <target> <amount> <fee> <nonce> <ts>");
        exit(64);
    }
    let ts: f64 = match args[9].parse() {
        Ok(v) => v,
        Err(_) => {
            eprintln!("bad ts: {}", args[9]);
            exit(64);
        }
    };
    let payload = format!(
        "{}|{}|{}|{}|{}|{}|{}|{}|{:.6}",
        args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8], ts
    );
    let mut h = Keccak256::new();
    h.update(payload.as_bytes());
    let out = h.finalize();
    let mut hex = String::with_capacity(64);
    for b in out.iter() {
        hex.push_str(&format!("{:02x}", b));
    }
    println!("{}", hex);
}
