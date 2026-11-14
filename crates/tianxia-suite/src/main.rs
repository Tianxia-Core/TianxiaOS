// ffp: FFP-TX-SUITE-DISPATCH concurrent-daemon rust
//! TianxiaOS Sovereign CLI & 9-App TUI Entrypoint.
//! Supports direct subcommands (`tianxia status`, `tianxia tui --app scour`, etc.)
//! AND dedicated TUI symlink dispatch (`tx-scour-tui`, `tx-miner-tui`, `tx-ledger-tui`, etc.).

mod cli;
mod crypto;
mod telemetry;
mod tui;

use tui::TuiApp;

fn print_help() {
    println!("TianxiaOS Sovereign Suite v{} ({})", telemetry::VERSION, telemetry::EDITION);
    println!();
    println!("USAGE:");
    println!("  tianxia <COMMAND> [OPTIONS]");
    println!("  tianxia tui [--app <overview|scour|miner|ledger|dss14|etamanga|fortress|models|tracer>] [--once]");
    println!();
    println!("COMMANDS:");
    println!("  status [--json]            Show full TianxiaOS substrate, mesh, RGU & Build Law status");
    println!("  verify-law [--json]        Compute SHA-256, BLAKE2b, Merkle Root & HMAC Build Law seal");
    println!("  scour [--limit N] [--json] Inspect real-time tx_scour merged intelligence signals");
    println!("  rgu [--json]               Inspect tx_opportunities_miner SFI rankings & B2B pipeline");
    println!("  ledger [--json]            Inspect TetraLedger 4-way cryptographic settlement status");
    println!("  audit <path> [--json]      Audit file/directory for FFP headers, SLECO-SO++ & secrets");
    println!("  vault-status [--json]      Zero-knowledge Aethervault & GDPR++ cryptoshred check");
    println!("  mesh [--json]              Inspect sovereign Tailscale / Rosenpass PQ mesh nodes");
    println!("  tui [--app MODE] [--once]  Launch interactive 9-App Fullscreen ANSI TUI");
    println!("  version [--json]           Print version, target architecture & Build Law edition");
}

fn detect_symlink_tui_app(argv0: &str) -> Option<TuiApp> {
    let bin = argv0.rsplit(['/', '\\']).next().unwrap_or(argv0);
    match bin {
        "tx-scour-tui" => Some(TuiApp::Scour),
        "tx-miner-tui" => Some(TuiApp::Miner),
        "tx-ledger-tui" => Some(TuiApp::Ledger),
        "tx-dss14-tui" => Some(TuiApp::Dss14),
        "tx-etamanga-tui" => Some(TuiApp::Etamanga),
        "tx-fortress-tui" => Some(TuiApp::Fortress),
        "tx-models-tui" => Some(TuiApp::Models),
        "tx-tracer-tui" => Some(TuiApp::Tracer),
        "tx-sovereign-tui" => Some(TuiApp::Overview),
        _ => None,
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let argv0 = args.first().map(String::as_str).unwrap_or("tianxia");
    let as_json = args.iter().any(|a| a == "--json");
    let once = args.iter().any(|a| a == "--once");

    if let Some(default_app) = detect_symlink_tui_app(argv0) {
        if args.iter().any(|a| a == "-h" || a == "--help") {
            print_help();
            std::process::exit(0);
        }
        let mut app = default_app;
        for i in 1..args.len() {
            if args[i] == "--app" && i + 1 < args.len() {
                if let Some(parsed) = TuiApp::from_name(&args[i + 1]) {
                    app = parsed;
                }
            }
        }
        std::process::exit(tui::run_tui(app, once));
    }

    if args.len() < 2 {
        std::process::exit(cli::cmd_status(false));
    }

    let cmd = args[1].as_str();
    let code = match cmd {
        "-h" | "--help" | "help" => {
            print_help();
            0
        }
        "-V" | "--version" | "version" => cli::cmd_version(as_json),
        "status" => cli::cmd_status(as_json),
        "verify-law" | "law" => cli::cmd_verify_law(as_json),
        "scour" => {
            let mut limit = 8usize;
            for i in 2..args.len() {
                if args[i] == "--limit" && i + 1 < args.len() {
                    limit = args[i + 1].parse().unwrap_or(8);
                }
            }
            cli::cmd_scour(limit, as_json)
        }
        "rgu" | "miner" => cli::cmd_rgu(as_json),
        "ledger" | "tetraledger" => cli::cmd_ledger(as_json),
        "vault-status" | "vault" => cli::cmd_vault_status(as_json),
        "mesh" => cli::cmd_mesh(as_json),
        "audit" => {
            let target = args
                .iter()
                .skip(2)
                .find(|a| !a.starts_with('-'))
                .map(String::as_str)
                .unwrap_or(".");
            cli::cmd_audit(target, as_json)
        }
        "tui" => {
            let mut app = TuiApp::Overview;
            for i in 2..args.len() {
                if args[i] == "--app" && i + 1 < args.len() {
                    match TuiApp::from_name(&args[i + 1]) {
                        Some(parsed) => app = parsed,
                        None => {
                            eprintln!("[tianxia tui] Unknown --app mode: {}", args[i + 1]);
                            std::process::exit(2);
                        }
                    }
                } else if let Some(rest) = args[i].strip_prefix("--app=") {
                    if let Some(parsed) = TuiApp::from_name(rest) {
                        app = parsed;
                    }
                }
            }
            tui::run_tui(app, once)
        }
        other => {
            eprintln!("[tianxia] Unknown subcommand: '{other}'. Run `tianxia --help`.");
            2
        }
    };
    std::process::exit(code);
}
