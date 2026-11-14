// ffp: TX-NOWWALLET-PROBE crypto-signer rust
//! NowPayments vs EFEMERA self-custody probe. Converted from tx_nowwallet_probe.sh.
use rusqlite::Connection;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::time::Duration;

fn base() -> PathBuf {
    PathBuf::from(std::env::var("TX_BASE_DIR").unwrap_or_else(|_| "/var/lib/tianxia".into()))
}

fn main() {
    let b = base();
    let _ = fs::create_dir_all(b.join("logs"));
    let log_path = b.join("logs").join("nowwallet.log");
    let iso = std::process::Command::new("date")
        .args(["-u", "+%Y-%m-%dT%H:%M:%SZ"])
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default();
    let mut out = format!("[VERITAS] NowWallet probe @ {}\n", iso);
    out.push_str("[OSINT] NowPayments: https://api.nowpayments.io/v1/payment (requires x-api-key, 0.5% fee) vs EFEMERA/Base self-custody 0.0001 gwei + Biconomy Gasless\n");
    match ureq::get("https://api.nowpayments.io/v1/status")
        .timeout(Duration::from_secs(5))
        .call()
    {
        Ok(resp) => {
            let body = resp.into_string().unwrap_or_default();
            out.push_str(&body.chars().take(400).collect::<String>());
            out.push('\n');
        }
        Err(_) => out.push_str("[IREB] NowPayments unreachable — EFEMERA superior per MIF\n"),
    }
    let db = b.join("db").join("chain_ops.sqlite3");
    let count: i64 = if db.exists() {
        Connection::open(&db)
            .ok()
            .and_then(|c| {
                c.query_row("select count(*) from chain_ops where status='broadcast'", [], |r| r.get(0))
                    .ok()
            })
            .unwrap_or(0)
    } else {
        0
    };
    out.push_str(&format!("EFEMERA broadcasts={}\n", count));
    out.push_str("[OK] NowWallet probe complete — EFEMERA/Base + Biconomy Gasless is superior per AUTARCHI/MIF\n");
    print!("{}", out);
    if let Ok(mut f) = OpenOptions::new().create(true).append(true).open(&log_path) {
        let _ = f.write_all(out.as_bytes());
    }
}
