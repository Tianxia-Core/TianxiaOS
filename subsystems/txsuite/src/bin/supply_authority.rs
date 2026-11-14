// ffp: TX-SUPPLY-AUTHORITY concurrent-daemon rust
//! Tianxia Supply Authority — single-pass system audit. Converted from tx_supply_authority.py.
//! Modes: snapshot | summary | manifest | feed
use rusqlite::Connection;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::process::{exit, Command};
use std::time::{SystemTime, UNIX_EPOCH};

fn base() -> PathBuf {
    PathBuf::from(std::env::var("TX_BASE_DIR").unwrap_or_else(|_| "/var/lib/tianxia".into()))
}

fn safe_run(args: &[&str]) -> String {
    if args.is_empty() {
        return String::new();
    }
    Command::new(args[0])
        .args(&args[1..])
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default()
}

fn file_sha256(p: &Path) -> Option<String> {
    let data = fs::read(p).ok()?;
    let mut h = Sha256::new();
    h.update(&data);
    Some(h.finalize().iter().map(|b| format!("{:02x}", b)).collect())
}

fn py_bool(s: &str) -> &'static str {
    if s.is_empty() {
        "False"
    } else {
        "True"
    }
}

fn probe_bridge(b: &Path) -> Value {
    let bin = b.join("bin").join("tx_gui_bridge.py");
    let log = b.join("logs").join("gui_bridge.log");
    let audit = b.join("logs").join("bridge_audit.jsonl");
    let audit_size = fs::metadata(&audit).map(|m| m.len()).unwrap_or(0);
    let audit_lines = fs::read_to_string(&audit)
        .map(|t| t.lines().count() as u64)
        .unwrap_or(0);
    json!({
        "binary": bin.to_string_lossy(),
        "binary_sha256": file_sha256(&bin),
        "log_exists": log.exists(),
        "audit_exists": audit.exists(),
        "audit_size_bytes": audit_size,
        "audit_lines": audit_lines,
    })
}

fn probe_gui(b: &Path) -> Value {
    let p = b.join("ui").join("index.html");
    json!({
        "path": p.to_string_lossy(),
        "exists": p.exists(),
        "sha256": file_sha256(&p),
        "size_bytes": fs::metadata(&p).map(|m| m.len()).unwrap_or(0),
    })
}

fn probe_manifest(b: &Path) -> Value {
    let p = b.join("manifests").join("substrate_prompt_matrix.json");
    if !p.exists() {
        return json!({"exists": false});
    }
    match fs::read_to_string(&p).ok().and_then(|t| serde_json::from_str::<Value>(&t).ok()) {
        Some(d) => {
            let inner = d.get("substrate_prompt_matrix").unwrap_or(&d);
            let keys: Vec<String> = inner
                .as_object()
                .map(|m| m.keys().cloned().collect())
                .unwrap_or_default();
            json!({"exists": true, "path": p.to_string_lossy(), "keys": keys})
        }
        None => json!({"exists": true, "error": "parse error"}),
    }
}

fn probe_secrets(b: &Path) -> Value {
    let sec = b.join("secrets");
    let mut files = vec![];
    if let Ok(rd) = fs::read_dir(&sec) {
        for e in rd.flatten() {
            if let Ok(meta) = e.metadata() {
                files.push(json!({
                    "name": e.file_name().to_string_lossy(),
                    "size": meta.len(),
                    "mode_oct": format!("0o{:o}", meta.permissions().mode() & 0o777),
                }));
            }
        }
    }
    json!({"dir": sec.to_string_lossy(), "exists": sec.exists(), "files": files})
}

fn probe_substrate_uds() -> Value {
    let sock = "/run/tianxia/tx_fastpath.sock";
    json!({"path": sock, "exists": Path::new(sock).exists()})
}

fn probe_nats() -> Value {
    json!({
        "binary": safe_run(&["command", "-v", "nats-server"]),
        "running": safe_run(&["pgrep", "-af", "nats-server"]),
        "nix_pnat": safe_run(&["command", "-v", "pnats-server"]),
    })
}

fn probe_wg() -> Value {
    json!({
        "binary": safe_run(&["command", "-v", "wg"]),
        "interface": safe_run(&["wg", "show", "2>/dev/null", "|", "head", "-2"]),
        "peers": safe_run(&["wg", "show", "wg0", "peers", "2>/dev/null", "|", "wc", "-l"]),
    })
}

fn probe_rgu_portfolio(b: &Path) -> Value {
    let db = b.join("db").join("portfolio.sqlite3");
    let mut out = json!({"db": db.to_string_lossy(), "exists": db.exists()});
    if !db.exists() {
        return out;
    }
    if let Ok(conn) = Connection::open(&db) {
        let one = |sql: &str| -> Option<i64> { conn.query_row(sql, [], |r| r.get(0)).ok() };
        let obj = out.as_object_mut().unwrap();
        obj.insert("templates".into(), json!(one("SELECT COUNT(*) FROM rgu_templates").unwrap_or(0)));
        obj.insert("allocations".into(), json!(one("SELECT COUNT(*) FROM rgu_allocations").unwrap_or(0)));
        obj.insert("open_allocations".into(),
                   json!(one("SELECT COUNT(*) FROM rgu_allocations WHERE status='open'").unwrap_or(0)));
        obj.insert("keys_active".into(),
                   json!(one("SELECT COUNT(*) FROM rgu_keys WHERE status='active'").unwrap_or(0)));
        obj.insert("revenue_events".into(),
                   json!(one("SELECT COUNT(*) FROM rgu_revenue_events").unwrap_or(0)));
        obj.insert("experiments_running".into(),
                   json!(one("SELECT COUNT(*) FROM rgu_experiments WHERE status='running'").unwrap_or(0)));
        let pnl: f64 = conn
            .query_row("SELECT COALESCE(SUM(amount_usd),0) FROM rgu_revenue_events WHERE kind='pnl'", [], |r| r.get(0))
            .unwrap_or(0.0);
        obj.insert("realized_pnl_usd".into(), json!((pnl * 10000.0).round() / 10000.0));
    } else {
        out.as_object_mut().unwrap().insert("error".into(), json!("open failed"));
    }
    out
}

fn probe_billing(b: &Path) -> Value {
    let db = b.join("db").join("billing.sqlite3");
    let mut out = json!({"db": db.to_string_lossy(), "exists": db.exists()});
    if !db.exists() {
        return out;
    }
    if let Ok(conn) = Connection::open(&db) {
        let obj = out.as_object_mut().unwrap();
        obj.insert("rgu_events".into(),
                   json!(conn.query_row("SELECT COUNT(*) FROM rgu_events", [], |r| r.get::<_, i64>(0)).unwrap_or(0)));
        obj.insert("tenants".into(),
                   json!(conn.query_row("SELECT COUNT(DISTINCT tenant) FROM rgu_events", [], |r| r.get::<_, i64>(0)).unwrap_or(0)));
    } else {
        out.as_object_mut().unwrap().insert("error".into(), json!("open failed"));
    }
    out
}

fn probe_mistakes(b: &Path) -> Value {
    let db = b.join("db").join("mistakes.sqlite3");
    if !db.exists() {
        return json!({"exists": false});
    }
    match Connection::open(&db) {
        Ok(conn) => json!({
            "exists": true,
            "total": conn.query_row("SELECT COUNT(*) FROM mistakes", [], |r| r.get::<_, i64>(0)).unwrap_or(0)
        }),
        Err(e) => json!({"exists": true, "error": e.to_string()}),
    }
}

fn probe_routes() -> Value {
    let routes = [
        ("rebuild", "nix", "nixos-rebuild switch"),
        ("clean", "nix", "nix-collect-garbage -d"),
        ("wg", "mesh", "wg show wg0"),
        ("htop", "telemetry", "htop"),
        ("browser", "gui", "chromium"),
        ("terminal", "gui", "foot"),
        ("nats", "nats", "nats stream ls"),
        ("clock", "cmd", "date"),
        ("uptime", "cmd", "uptime"),
    ];
    let arr: Vec<Value> = routes
        .iter()
        .map(|(kw, m, cmd)| json!({"kw": kw, "module": m, "cmd": cmd}))
        .collect();
    json!({"routes": arr})
}

fn snapshot() -> Value {
    let b = base();
    let ts = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs_f64()).unwrap_or(0.0);
    let iso = safe_run(&["date", "+%Y-%m-%dT%H:%M:%S%z"]);
    let uname = safe_run(&["uname", "-srm"]);
    json!({
        "ts": ts,
        "iso": iso,
        "host": {
            "platform": format!("Linux-{}", uname.split_whitespace().nth(2).unwrap_or("unknown")),
            "python": "rust",
            "cwd": b.to_string_lossy(),
        },
        "bridge": probe_bridge(&b),
        "gui": probe_gui(&b),
        "manifest": probe_manifest(&b),
        "secrets": probe_secrets(&b),
        "substrate_uds": probe_substrate_uds(),
        "nats": probe_nats(),
        "wireguard": probe_wg(),
        "rgu_portfolio": probe_rgu_portfolio(&b),
        "billing": probe_billing(&b),
        "mistakes": probe_mistakes(&b),
        "router": probe_routes(),
        "endpoints": {
            "public": ["/api/health", "/api/billing/tiers",
                      "/api/rgu/templates", "/api/rgu/experiments",
                      "/api/ops/snapshot"],
            "authed": ["/api/intent", "/api/task/close",
                      "/api/billing/usage", "/api/rgu/portfolio",
                      "/api/rgu/portfolio/upsert", "/api/rgu/market",
                      "/api/rgu/revenue", "/api/rgu/keys",
                      "/api/rgu/experiment", "/api/rgu/template-add",
                      "/api/commercial/summary",
                      "/stream", "/stream/task/{id}", "/stream/rgu-market"],
        },
    })
}

fn py_repr_list(v: &Value) -> String {
    let items: Vec<String> = v
        .as_array()
        .map(|a| a.iter().map(|x| format!("'{}'", x.as_str().unwrap_or(""))).collect())
        .unwrap_or_default();
    format!("[{}]", items.join(", "))
}

fn cmd_summary(s: &Value) {
    println!("== Tianxia Supply Authority @ {} ==", s["iso"].as_str().unwrap_or(""));
    println!("  host:   {} (py {})", s["host"]["platform"].as_str().unwrap_or(""),
             s["host"]["python"].as_str().unwrap_or(""));
    println!("  base:   {}", s["host"]["cwd"].as_str().unwrap_or(""));
    println!("  bridge: log={} audit={} lines",
             if s["bridge"]["log_exists"].as_bool().unwrap_or(false) { "True" } else { "False" },
             s["bridge"]["audit_lines"].as_u64().unwrap_or(0));
    println!("  gui:    {} bytes  sha256={}",
             s["gui"]["size_bytes"].as_u64().unwrap_or(0),
             s["gui"]["sha256"].as_str().unwrap_or("None"));
    let keys = s["manifest"].get("keys").cloned().unwrap_or(json!([]));
    println!("  manifest: {}", py_repr_list(&keys));
    let nfiles = s["secrets"]["files"].as_array().map(|a| a.len()).unwrap_or(0);
    println!("  secrets: {} ({} files)", s["secrets"]["dir"].as_str().unwrap_or(""), nfiles);
    println!("  substrate uds: {{'path': '{}', 'exists': {}}}",
             s["substrate_uds"]["path"].as_str().unwrap_or(""),
             if s["substrate_uds"]["exists"].as_bool().unwrap_or(false) { "True" } else { "False" });
    println!("  nats:  binary={} running={}",
             py_bool(s["nats"]["binary"].as_str().unwrap_or("")),
             py_bool(s["nats"]["running"].as_str().unwrap_or("")));
    println!("  wg:    binary={} peers={}",
             py_bool(s["wireguard"]["binary"].as_str().unwrap_or("")),
             s["wireguard"]["peers"].as_str().unwrap_or(""));
    let r = &s["rgu_portfolio"];
    println!("  rgu:   templates={} open={} revenue={} keys={} pnl=${}",
             r["templates"].as_i64().unwrap_or(0),
             r["open_allocations"].as_i64().unwrap_or(0),
             r["revenue_events"].as_i64().unwrap_or(0),
             r["keys_active"].as_i64().unwrap_or(0),
             r["realized_pnl_usd"].as_f64().unwrap_or(0.0));
    println!("  billing: events={} tenants={}",
             s["billing"]["rgu_events"].as_i64().unwrap_or(0),
             s["billing"]["tenants"].as_i64().unwrap_or(0));
    println!("  mistakes: total={}", s["mistakes"]["total"].as_i64().unwrap_or(0));
    println!("  router: {} keyword routes",
             s["router"]["routes"].as_array().map(|a| a.len()).unwrap_or(0));
}

fn cmd_manifest(s: &Value) {
    let p = base().join("docs").join("MANIFEST.json");
    if let Some(parent) = p.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let _ = fs::write(&p, serde_json::to_string_pretty(s).unwrap_or_default());
    println!("wrote {}", p.to_string_lossy());
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(|s| s.as_str()).unwrap_or("");
    match mode {
        "snapshot" => println!("{}", serde_json::to_string_pretty(&snapshot()).unwrap_or_default()),
        "summary" => cmd_summary(&snapshot()),
        "manifest" => cmd_manifest(&snapshot()),
        "feed" => {
            let s = snapshot();
            cmd_summary(&s);
            println!();
            cmd_manifest(&s);
        }
        other => {
            eprintln!("usage: supply_authority snapshot|summary|manifest|feed (got '{}')", other);
            exit(64);
        }
    }
}
