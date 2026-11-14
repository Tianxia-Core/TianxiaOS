// ffp: TX-MESH-WATCHDOG concurrent-daemon rust
//! WireGuard mesh watchdog with fast recovery. Converted from tx_mesh_watchdog.sh.
use std::path::Path;
use std::process::Command;
use std::thread::sleep;
use std::time::Duration;

const XPS_PUBKEY: &str = "qWQATAhmrWpv9V9UFg2z6GsIirtRCIKH2pAdQOUHhS0=";
const LAT_PUBKEY: &str = "qt+z8Sttp5g1T5uq0Mjl/wuHaXRK8F2lGss2P0+PZWU=";
const XPS_LAN_IP: &str = "mesh-node-b.local";
const XPS_WG_IP: &str = "mesh-core-1.internal";
const LAT_WG_IP: &str = "mesh-core-2.internal";
const PORT: &str = "51820";

fn halted() -> bool {
    Path::new("/var/lib/tianxia/AUTONOMY_PAUSED").exists()
        || Path::new("/var/lib/tianxia/PROBE_STOP").exists()
}

fn run(args: &[&str]) -> String {
    Command::new(args[0])
        .args(&args[1..])
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default()
}

fn now() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0)
}

fn main() {
    println!("[mesh-watchdog] rust watchdog start (kill: AUTONOMY_PAUSED/PROBE_STOP)");
    while !halted() {
        let hs = run(&["wg", "show", "wg0", "latest-handshakes"]);
        let latest: i64 = hs
            .lines()
            .find(|l| l.contains(XPS_PUBKEY))
            .and_then(|l| l.split_whitespace().nth(1))
            .and_then(|v| v.parse().ok())
            .unwrap_or(0);
        let delta = now() - latest;
        let ping_ok = Command::new("ping")
            .args(["-c", "1", "-W", "1", XPS_WG_IP])
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false);
        if delta > 20 || !ping_ok {
            let lan_ok = Command::new("nc")
                .args(["-z", "-w", "1", XPS_LAN_IP, "22"])
                .output()
                .map(|o| o.status.success())
                .unwrap_or(false);
            if lan_ok {
                println!("[mesh-watchdog] recovering: delta={} ping={}", delta, ping_ok);
                let _ = run(&["wg", "set", "wg0", "peer", XPS_PUBKEY, "endpoint",
                              &format!("{}:{}", XPS_LAN_IP, PORT), "allowed-ips",
                              &format!("{}/32", XPS_WG_IP), "persistent-keepalive", "10"]);
                let _ = Command::new("ping").args(["-c", "1", "-W", "1", XPS_WG_IP]).output();
                let remote = format!(
                    "wg set wg0 peer {} endpoint sovereign-mesh.local:{} persistent-keepalive 10; ping -c 1 -W 1 {} || true",
                    LAT_PUBKEY, PORT, LAT_WG_IP
                );
                let _ = Command::new("ssh")
                    .args(["-o", "BatchMode=yes", "-o", "ConnectTimeout=2",
                           "-o", "StrictHostKeyChecking=no", &format!("root@{}", XPS_LAN_IP), &remote])
                    .output();
            }
        }
        sleep(Duration::from_secs(5));
    }
    println!("[mesh-watchdog] halted by kill-switch");
}
