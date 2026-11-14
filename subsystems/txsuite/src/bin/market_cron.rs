// ffp: TX-MARKET-CRON concurrent-daemon rust
//! Market refresh cron pass: refresh + cross-venue + arb-once. Converted from tx_market_cron.sh.
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::process::Command;

fn base() -> PathBuf {
    PathBuf::from(std::env::var("TX_BASE_DIR").unwrap_or_else(|_| "/var/lib/tianxia".into()))
}

fn stage(b: &PathBuf, name: &str, cmd: &[&str], envs: &[(&str, &str)]) -> bool {
    println!("[{}] {}", name, chronoish());
    let mut c = Command::new(cmd[0]);
    c.args(&cmd[1..]);
    for (k, v) in envs {
        c.env(k, v);
    }
    let out = c.output();
    let log = b.join("logs").join("market_feed.log");
    if let Some(f) = OpenOptions::new().create(true).append(true).open(&log).ok() {
        let mut f = f;
        if let Ok(o) = &out {
            let _ = f.write_all(&o.stdout);
            let _ = f.write_all(&o.stderr);
        }
    }
    out.map(|o| o.status.success()).unwrap_or(false)
}

fn chronoish() -> String {
    Command::new("date")
        .arg("-Is")
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default()
}

fn main() {
    let b = base();
    let _ = fs::create_dir_all(b.join("logs"));
    let feed = b.join("bin").join("tx_market_feed_rs");
    let feed_cmd = if feed.exists() {
        feed.to_string_lossy().to_string()
    } else {
        b.join("bin").join("tx_market_feed.py").to_string_lossy().to_string()
    };
    let feed_runner = if feed_cmd.ends_with(".py") { "python3" } else { &feed_cmd };
    let feed_arg = if feed_cmd.ends_with(".py") { feed_cmd.as_str() } else { "" };

    let mut c1: Vec<&str> = if feed_arg.is_empty() { vec![feed_runner, "refresh"] } else { vec![feed_runner, feed_arg, "refresh"] };
    stage(&b, "refresh", &c1, &[]);
    c1 = if feed_arg.is_empty() { vec![feed_runner, "spread", "--lookback", "600"] } else { vec![feed_runner, feed_arg, "spread", "--lookback", "600"] };
    stage(&b, "cross-venue (top 5)", &c1, &[]);
    let arb = b.join("bin").join("tx_arb_worker.py").to_string_lossy().to_string();
    stage(&b, "arb-once (min 5bps)", &["python3", &arb, "once"], &[("TX_ARB_MIN_BPS", "5")]);
}
