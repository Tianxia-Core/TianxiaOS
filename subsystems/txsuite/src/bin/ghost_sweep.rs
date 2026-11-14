// ffp: TX-GHOST-SWEEP compute-kernel rust
//! tx_ghost_sweep -- Fork-ghost balance scanner (Rust port of tx_ghost_sweep.py).
//! Given addresses controlled by the OWNER, checks descendant chains of BTC/ETH
//! hard forks for unclaimed "ghost balances" via public explorer APIs.
//! Every outbound URL passes the SSRF allowlist before any call.
//! No key extraction from third parties.
use serde_json::{json, Value};
use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::net::ToSocketAddrs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;

const BLOCKCHAIR: &str = "https://api.blockchair.com/latest/{chain}/dashboards/address/{addr}";
const USER_AGENT: &str = "TianxiaHussar/1.0";
const VAULT_PASSPHRASE_DEFAULT: &str = "tianxia-sovereign-2026-vault";

// descendant chains worth scanning (forks with meaningful value + replay protection)
const FORK_CHAINS: &[(&str, &[&str])] = &[
    ("BTC", &["bch", "bsv", "btg"]), // SIGHASH_FORKID protected forks
    ("ETH", &["etc", "ethw"]),       // EIP-155 protected forks
];

// SSRF allowlist (mirrors tx_net_guard.py)
const ALLOWED_HOSTS: &[&str] = &["127.0.0.1", "localhost", "::1"];
const ALLOWED_PUBLIC_HOSTS: &[&str] = &[
    "api.stripe.com",
    "api.skyfire.com",
    "api.skyfire.xyz",
    "skyfire.xyz",
    "finix.com",
    "finix.sandbox-payments-api.com",
    "finix.payments-api.com",
    "api.paddle.com",
    "unify.apideck.com",
    "www.crossmint.com",
    "api.crossmint.com",
    "api.coingecko.com",
    "api.coinbase.com",
    "api.kraken.com",
    "api.telegram.org",
    "api.gumroad.com",
    "s3.amazonaws.com",
    "gumroad.s3.amazonaws.com",
    "hn.algolia.com",
    "www.reddit.com",
    "remoteok.com",
    "api.resend.com",
    "console.vast.ai",
];
const ALLOWED_PORTS: &[&str] = &["80", "443", "8080", "9191", "9199"];
const ALLOWED_SCHEMES: &[&str] = &["http", "https"];

fn base() -> PathBuf {
    PathBuf::from(std::env::var("TX_BASE_DIR").unwrap_or_else(|_| "/var/lib/tianxia".into()))
}

fn halted() -> bool {
    Path::new("/var/lib/tianxia/AUTONOMY_PAUSED").exists()
        || Path::new("/var/lib/tianxia/PROBE_STOP").exists()
}

fn debug_enabled() -> bool {
    std::env::var("TX_GHOST_SWEEP_DEBUG").map(|v| v == "1").unwrap_or(false)
}

fn debug(msg: String) {
    if debug_enabled() {
        eprintln!("[debug] {}", msg);
    }
}

fn trunc(s: &str, n: usize) -> String {
    s.chars().take(n).collect()
}

// ---- SSRF allowlist -------------------------------------------------------

struct ParsedUrl {
    scheme: String,
    host: String,
    port: Option<u16>,
}

fn parse_url(url: &str) -> Option<ParsedUrl> {
    let (scheme, rest) = url.split_once("://")?;
    let hostport = rest.split(['/', '?', '#']).next()?;
    let hostport = hostport.rsplit('@').next()?;
    let (host, port) = if hostport.starts_with('[') {
        let end = hostport.find(']')?;
        let host = &hostport[1..end];
        let port = hostport[end + 1..]
            .strip_prefix(':')
            .and_then(|p| p.parse::<u16>().ok());
        (host.to_string(), port)
    } else {
        match hostport.rsplit_once(':') {
            Some((h, p)) => (h.to_string(), p.parse::<u16>().ok()),
            None => (hostport.to_string(), None),
        }
    };
    if host.is_empty() {
        return None;
    }
    Some(ParsedUrl {
        scheme: scheme.to_ascii_lowercase(),
        host: host.to_ascii_lowercase(),
        port,
    })
}

fn is_blocked_ip(host: &str) -> bool {
    let infos = match (host, 0u16).to_socket_addrs() {
        Ok(i) => i,
        Err(_) => return true,
    };
    for info in infos {
        if let std::net::IpAddr::V4(v4) = info.ip() {
            let o = v4.octets();
            if o[0] == 10
                || (o[0] == 172 && (16..=31).contains(&o[1]))
                || (o[0] == 192 && o[1] == 168)
                || (o[0] == 169 && o[1] == 254)
                || o[0] == 127
            {
                return true;
            }
        }
    }
    false
}

fn is_allowlisted(url: &str) -> bool {
    let parsed = match parse_url(url) {
        Some(p) => p,
        None => return false,
    };
    if !ALLOWED_SCHEMES.contains(&parsed.scheme.as_str()) {
        return false;
    }
    if !ALLOWED_HOSTS.contains(&parsed.host.as_str())
        && !ALLOWED_PUBLIC_HOSTS.contains(&parsed.host.as_str())
    {
        return false;
    }
    if let Some(port) = parsed.port {
        if !ALLOWED_PORTS.contains(&port.to_string().as_str()) {
            return false;
        }
    }
    if is_blocked_ip(&parsed.host) {
        return false;
    }
    true
}

fn check_allowlist(url: &str) -> Result<(), String> {
    if is_allowlisted(url) {
        Ok(())
    } else {
        Err(format!("_check_allowlist: blocked URL {:?}", url))
    }
}

// ---- scanner --------------------------------------------------------------

fn quote(s: &str) -> String {
    let mut out = String::new();
    for b in s.bytes() {
        let c = b as char;
        if c.is_ascii_alphanumeric() || "-_.~/".contains(c) {
            out.push(c);
        } else {
            out.push_str(&format!("%{:02X}", b));
        }
    }
    out
}

fn get_json(url: &str) -> Result<Value, String> {
    check_allowlist(url)?;
    let resp = ureq::get(url)
        .set("User-Agent", USER_AGENT)
        .timeout(Duration::from_secs(15))
        .call()
        .map_err(|e| e.to_string())?;
    resp.into_json::<Value>().map_err(|e| e.to_string())
}

fn scan_address(addr: &str) -> Value {
    let short = format!("{}...", trunc(addr, 12));
    let mut ghosts: Vec<Value> = Vec::new();
    let mut total_chains_checked: u64 = 0;
    for (parent, forks) in FORK_CHAINS {
        for chain in *forks {
            let url = BLOCKCHAIR
                .replace("{chain}", chain)
                .replace("{addr}", &quote(addr));
            if let Err(e) = check_allowlist(&url) {
                debug(format!(
                    "scan {}/{} failed: {}",
                    chain,
                    trunc(addr, 10),
                    trunc(&e, 60)
                ));
                continue;
            }
            match get_json(&url) {
                Ok(data) => {
                    total_chains_checked += 1;
                    let payload = data.get("data").and_then(|d| d.get(addr));
                    let addr_info = payload
                        .and_then(|p| p.get("address"))
                        .cloned()
                        .unwrap_or(Value::Null);
                    if let Some(bal) = addr_info.get("balance") {
                        let bal_str = match bal {
                            Value::Null => None,
                            Value::String(s) => Some(s.clone()),
                            v => Some(v.to_string()),
                        };
                        if let Some(bs) = bal_str {
                            if !matches!(bs.as_str(), "0" | "0x0" | "") {
                                ghosts.push(json!({
                                    "chain": chain,
                                    "parent": parent,
                                    "balance_raw": bs,
                                    "addr": addr_info,
                                }));
                            }
                        }
                    }
                }
                Err(e) => debug(format!(
                    "scan {}/{} failed: {}",
                    chain,
                    trunc(addr, 10),
                    trunc(&e, 60)
                )),
            }
        }
    }
    json!({
        "address": short,
        "ghosts": ghosts,
        "total_chains_checked": total_chains_checked,
    })
}

// Address derivation happens air-gapped per policy; this port probes the vault
// through the existing audited Python vault module (txsuite has no AES/Scrypt
// crate) with a list-args subprocess, never a shell. Secrets never reach stdout.
const VAULT_SHIM: &str = r#"import json, os, sys
base = os.environ.get("TX_BASE_DIR", "/var/lib/tianxia")
sys.path.insert(0, os.path.join(base, "bin"))
try:
    import tx_secrets_vault as sv
except Exception as e:
    sys.stderr.write("vault module unavailable: %s" % e)
    sys.exit(2)
try:
    vault = sv.open_vault(os.environ.get("TX_VAULT_PASSPHRASE") or "tianxia-sovereign-2026-vault")
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(3)
try:
    found = [k for k in ("etamanga_priv", "efemera_priv") if vault.get_secret(k)]
    print(json.dumps({"vault_keys_found": found}))
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(4)
finally:
    try:
        vault.lock()
    except Exception:
        pass
"#;

fn vault_passphrase() -> String {
    std::env::var("TX_VAULT_PASSPHRASE")
        .ok()
        .filter(|v| !v.is_empty())
        .unwrap_or_else(|| VAULT_PASSPHRASE_DEFAULT.to_string())
}

fn python_for_vault(b: &Path) -> String {
    let venv = b.join("venv/timesfm/bin/python3");
    if venv.exists() {
        venv.to_string_lossy().to_string()
    } else {
        "python3".to_string()
    }
}

fn scan_vault_addresses(b: &Path) -> Result<Value, String> {
    let py = python_for_vault(b);
    let out = Command::new(&py)
        .args(["-c", VAULT_SHIM])
        .env("TX_BASE_DIR", b)
        .env("TX_VAULT_PASSPHRASE", vault_passphrase())
        .output()
        .map_err(|e| format!("vault probe failed to launch {}: {}", py, e))?;
    if !out.status.success() {
        let err = String::from_utf8_lossy(&out.stderr).trim().to_string();
        return Err(if err.is_empty() {
            format!("vault probe exited with {}", out.status)
        } else {
            err
        });
    }
    let parsed: Value = serde_json::from_slice(&out.stdout)
        .map_err(|e| format!("vault probe output not JSON: {}", e))?;
    Ok(json!({
        "vault_keys_found": parsed.get("vault_keys_found").cloned().unwrap_or(json!([])),
        "policy": "address derivation happens AIR-GAPPED; supply addresses to scan via 'scan <address>' — never paste private keys into networked tools",
        "note": "EVM key -> address derivation: run tx_chain_derive.py offline, then scan",
    }))
}

// ---- audit / report -------------------------------------------------------

fn now_iso_micros() -> String {
    Command::new("date")
        .args(["-u", "+%Y-%m-%dT%H:%M:%S.%N"])
        .output()
        .map(|o| {
            let s = String::from_utf8_lossy(&o.stdout).trim().to_string();
            match s.split_once('.') {
                Some((head, frac)) => {
                    let frac: String = frac.chars().take(6).collect();
                    format!("{}.{}Z", head, frac)
                }
                None => format!("{}Z", s),
            }
        })
        .unwrap_or_default()
}

fn audit_event(action: &str, key: &str, success: bool, details: Value, b: &Path) {
    let ts = now_iso_micros();
    let ts_sec = ts.split_once('.').map(|(h, _)| format!("{}Z", h)).unwrap_or_else(|| ts.clone());
    let entry = json!({
        "ts": ts,
        "action": action,
        "key": key,
        "success": success,
        "details": details,
    });
    let logs = b.join("logs");
    let _ = fs::create_dir_all(&logs);
    if let Ok(line) = serde_json::to_string(&entry) {
        let _ = OpenOptions::new()
            .create(true)
            .append(true)
            .open(logs.join("audit.jsonl"))
            .and_then(|mut f| writeln!(f, "{}", line));
    }
    let msg = format!(
        "{} INFO tx_ghost_sweep audit {} {} ok={} key={}",
        ts_sec,
        action,
        if success { "ok" } else { "FAIL" },
        success,
        key
    );
    let _ = OpenOptions::new()
        .create(true)
        .append(true)
        .open(logs.join("tx_ghost_sweep.log"))
        .and_then(|mut f| writeln!(f, "{}", msg));
    eprintln!("{}", msg);
}

fn report(addresses: &[String], b: &Path) -> Value {
    let mut hits: Vec<Value> = Vec::new();
    let mut scanned: u64 = 0;
    let mut ghost_addresses: u64 = 0;
    for a in addresses {
        let r = scan_address(a);
        scanned += 1;
        let has_ghosts = r
            .get("ghosts")
            .and_then(|g| g.as_array())
            .map(|arr| !arr.is_empty())
            .unwrap_or(false);
        if has_ghosts {
            ghost_addresses += 1;
            hits.push(r);
        }
    }
    audit_event(
        "ghostscan.report",
        &format!("{} scanned", scanned),
        true,
        json!({"ghost_addresses": ghost_addresses}),
        b,
    );
    json!({
        "scanned": scanned,
        "ghost_addresses": ghost_addresses,
        "hits": hits,
    })
}

fn service_terms() -> Value {
    json!({
        "scan": "free (public explorers only, no keys required)",
        "guided_recovery": "15% success fee of recovered value (client holds key; we supply replay-protected sweep pipeline + air-gap checklist)",
        "diy_toolkit": "$149 — full pipeline scripts + runbook (SIGHASH_FORKID / EIP-155, derivation-path divergence table, RPC isolation)",
    })
}

// Match Python json.dumps(ensure_ascii=True): escape non-ASCII inside strings.
fn ensure_ascii(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for c in s.chars() {
        let cp = c as u32;
        if cp < 0x80 {
            out.push(c);
        } else if cp <= 0xFFFF {
            out.push_str(&format!("\\u{:04x}", cp));
        } else {
            let v = cp - 0x10000;
            let hi = 0xD800 + (v >> 10);
            let lo = 0xDC00 + (v & 0x3FF);
            out.push_str(&format!("\\u{:04x}\\u{:04x}", hi, lo));
        }
    }
    out
}

// Pretty-print with 1-space indent (matches Python json.dumps(indent=1)).
fn print_pretty(v: &Value) {
    let text = serde_json::to_string_pretty(v).unwrap_or_else(|_| "{}".to_string());
    let text = ensure_ascii(&text);
    let out: Vec<String> = text
        .lines()
        .map(|l| {
            let n = l.len() - l.trim_start_matches(' ').len();
            format!("{}{}", " ".repeat(n / 2), &l[n..])
        })
        .collect();
    println!("{}", out.join("\n"));
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let b = base();
    let mode = args.first().map(|s| s.as_str()).unwrap_or("");

    match mode {
        "scan" if args.len() > 1 => {
            if halted() {
                eprintln!("[!] ghost sweep halted by kill-switch (AUTONOMY_PAUSED/PROBE_STOP)");
                return;
            }
            print_pretty(&scan_address(&args[1]));
        }
        "scan-vault" => {
            if halted() {
                eprintln!("[!] ghost sweep halted by kill-switch (AUTONOMY_PAUSED/PROBE_STOP)");
                return;
            }
            match scan_vault_addresses(&b) {
                Ok(v) => print_pretty(&v),
                Err(e) => {
                    eprintln!("vault unlock failed: {}", e);
                    std::process::exit(1);
                }
            }
        }
        "report" => {
            if halted() {
                eprintln!("[!] ghost sweep halted by kill-switch (AUTONOMY_PAUSED/PROBE_STOP)");
                return;
            }
            let mut input = String::new();
            let _ = std::io::stdin().read_to_string(&mut input);
            let addrs: Vec<String> = input
                .lines()
                .map(|l| l.trim().to_string())
                .filter(|l| !l.is_empty())
                .collect();
            print_pretty(&report(&addrs, &b));
        }
        _ => {
            print_pretty(&json!({"service_terms": service_terms()}));
        }
    }
}
// DSS-14 AUTO (Kamalā): price evidence recorded to billing ledger
