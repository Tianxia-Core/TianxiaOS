// ffp: TX-HW-PROBE concurrent-daemon rust
//! Hardware probe (rtlsdr/Dahua/Jabra). Converted from tx_hw_probe.sh.
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::process::Command;

fn base() -> PathBuf {
    PathBuf::from(std::env::var("TX_BASE_DIR").unwrap_or_else(|_| "/var/lib/tianxia".into()))
}

fn which(cmd: &str) -> Option<PathBuf> {
    let path = std::env::var("PATH").unwrap_or_default();
    for dir in path.split(':') {
        let p = PathBuf::from(dir).join(cmd);
        if p.is_file() {
            return Some(p);
        }
    }
    None
}

fn run_head(args: &[&str], n: usize) -> String {
    if args.is_empty() {
        return String::new();
    }
    Command::new(args[0])
        .args(&args[1..])
        .output()
        .map(|o| {
            String::from_utf8_lossy(&o.stdout)
                .lines()
                .take(n)
                .collect::<Vec<_>>()
                .join("\n")
        })
        .unwrap_or_default()
}

fn main() {
    let b = base();
    let log_dir = b.join("logs");
    let _ = fs::create_dir_all(&log_dir);
    let log_path = log_dir.join("hw_probe.log");
    let mut lf = OpenOptions::new().create(true).append(true).open(&log_path).ok();
    let iso = run_head(&["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], 1);

    let mut out = String::new();
    out.push_str(&format!("[VERITAS] HW probe @ {}\n", iso));
    for cmd in ["rtl_433", "rtl_test", "ffmpeg", "arecord"] {
        if which(cmd).is_some() {
            out.push_str(&format!("[OK] {} found\n", cmd));
        } else {
            out.push_str(&format!("[IREB] {} missing — nix-shell -p rtl_433 ffmpeg alsa-utils\n", cmd));
        }
    }
    let rtl = run_head(&["timeout", "2", "rtl_test"], 5);
    if rtl.is_empty() {
        out.push_str("[IREB] rtlsdr not plugged or no antenna — use wsprd + direct sampling\n");
    } else {
        out.push_str(&format!("{}\n", rtl));
    }
    out.push_str("[PROBE] Dahua: onvif://mesh-node-a.local:80 (check via nmap)\n");
    let nmap = run_head(&["nmap", "-p", "80,554", "mesh-node-a.local"], 10);
    if nmap.is_empty() {
        out.push_str("[IREB] Dahua not on LAN\n");
    } else {
        out.push_str(&format!("{}\n", nmap));
    }
    let pactl = run_head(&["pactl", "list", "sinks"], 10);
    if pactl.is_empty() {
        out.push_str("[IREB] Jabra via pulseaudio not found\n");
    }
    out.push_str("[OK] HW probe complete\n");
    print!("{}", out);
    if let Some(f) = lf.as_mut() {
        let _ = f.write_all(out.as_bytes());
    }
}
