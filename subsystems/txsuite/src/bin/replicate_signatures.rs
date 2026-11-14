// ffp: TX-REPLICATE-SIGNATURES crypto-signer rust
//! Replicate signature blacklist to mesh nodes. Converted from tx_replicate_signatures.sh.
use std::path::Path;
use std::process::Command;

const TARGETS: &[(&str, &str, &str)] = &[
    ("xps13", "mesh-core-2.internal:22", "/var/lib/tianxia/security"),
    ("pixel8pro", "mesh-core-3.internal:8022", "${TX_HOME:-/var/lib/tianxia}/.tianxia/security"),
    ("poco", "mesh-core-4.internal:8022", "${TX_HOME:-/var/lib/tianxia}/.tianxia/security"),
];

fn main() {
    let src = "/var/lib/tianxia/security/signature_blacklist.json";
    if !Path::new(src).exists() {
        std::process::exit(0);
    }
    for (node, hostport, remote_dir) in TARGETS {
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
                    &format!("--rsync-path=mkdir -p {} && rsync", remote_dir),
                    src,
                    &format!("root@{}:{}/", ip, remote_dir),
                ])
                .output();
            println!("[replicated] {}", node);
        }
    }
    println!("[\u{2713}] Mesh signature replication finished.");
}
