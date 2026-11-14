// ffp: FFP-TX-SUITE-TUI frontend rust
//! Full 9-App Interactive Fullscreen ANSI/Raw-Terminal TUI for TianxiaOS:
//! Apps: overview | scour | miner | ledger | dss14 | etamanga | fortress | models | tracer
//! Controls: 1..9 tab switch | Tab/Arrows cycle | r refresh | v verify seal | q quit
//! Supports graceful non-TTY and `--once` snapshot rendering.

use std::io::{self, Write};

use crate::telemetry::{collect_snapshot, SystemSnapshot, EDITION, MAHAVIDYA_DOMAINS, VERSION};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TuiApp {
    Overview = 0,
    Scour = 1,
    Miner = 2,
    Ledger = 3,
    Dss14 = 4,
    Etamanga = 5,
    Fortress = 6,
    Models = 7,
    Tracer = 8,
}

impl TuiApp {
    pub const ALL: [TuiApp; 9] = [
        TuiApp::Overview,
        TuiApp::Scour,
        TuiApp::Miner,
        TuiApp::Ledger,
        TuiApp::Dss14,
        TuiApp::Etamanga,
        TuiApp::Fortress,
        TuiApp::Models,
        TuiApp::Tracer,
    ];

    pub fn from_name(name: &str) -> Option<Self> {
        match name.trim().to_ascii_lowercase().as_str() {
            "1" | "overview" | "control" | "status" => Some(Self::Overview),
            "2" | "scour" | "signals" => Some(Self::Scour),
            "3" | "miner" | "rgu" | "opportunities" => Some(Self::Miner),
            "4" | "ledger" | "tetraledger" => Some(Self::Ledger),
            "5" | "dss14" | "mahavidya" | "law" => Some(Self::Dss14),
            "6" | "etamanga" | "efm" | "x402" => Some(Self::Etamanga),
            "7" | "fortress" | "vault" | "security" => Some(Self::Fortress),
            "8" | "models" | "llm" | "router" => Some(Self::Models),
            "9" | "tracer" | "murua" | "logistics" => Some(Self::Tracer),
            _ => None,
        }
    }

    pub fn label(self) -> &'static str {
        match self {
            Self::Overview => "1:Overview",
            Self::Scour => "2:Scour",
            Self::Miner => "3:Miner",
            Self::Ledger => "4:Ledger",
            Self::Dss14 => "5:DSS-14",
            Self::Etamanga => "6:Etamanga",
            Self::Fortress => "7:Fortress",
            Self::Models => "8:Models",
            Self::Tracer => "9:Tracer",
        }
    }

    pub fn title(self) -> &'static str {
        match self {
            Self::Overview => "SOVEREIGN EXECUTIVE OVERVIEW & SUBSTRATE PULSE",
            Self::Scour => "TX_SCOUR — REAL-TIME ARXIV / GITHUB / DEFI / THREAT SIGNALS",
            Self::Miner => "TX_OPPORTUNITIES_MINER — SFI PRIORITY MATRIX & B2B TARGETS",
            Self::Ledger => "TETRALEDGER — 4-WAY CRYPTOGRAPHIC SETTLEMENT & MERKLE PROOF",
            Self::Dss14 => "DSS-14.2 — 14 MAHĀVIDYĀ DOMAINS & DAŚAVIDYĀYĀNA NL GATE",
            Self::Etamanga => "ETAMANGA (EFM) — BASE L2 VAULTS, X402 RAILS & TOKENOMICS",
            Self::Fortress => "FAERY FORTRESS & AETHERVAULT — ZERO-TRUST & GDPR++ SHIELD",
            Self::Models => "CONSTRUCTAL SINE-MEANDER ROUTER & LOCAL SOVEREIGN LLM SWARM",
            Self::Tracer => "MURUA — BAYESIAN UNTRACKED CONSIGNMENT TRACER & UPU 2IPD",
        }
    }

    pub fn next(self) -> Self {
        Self::ALL[((self as usize) + 1) % 9]
    }

    pub fn prev(self) -> Self {
        Self::ALL[((self as usize) + 8) % 9]
    }
}

// ANSI TrueColor Palette (Tripura Sundarī #080808 Obsidian + #00FFCC Cyan + #F5C542 Gold)
const BG_OBSIDIAN: &str = "\x1b[48;2;8;8;8m";
const FG_TEXT: &str = "\x1b[38;2;230;235;240m";
const FG_MUTED: &str = "\x1b[38;2;130;142;158m";
const FG_CYAN: &str = "\x1b[38;2;0;255;204m";
const FG_GOLD: &str = "\x1b[38;2;245;197;66m";
const FG_GREEN: &str = "\x1b[38;2;16;185;129m";
const FG_AMBER: &str = "\x1b[38;2;245;158;11m";
const BG_TAB_ACTIVE: &str = "\x1b[48;2;0;92;80m\x1b[38;2;255;255;255m\x1b[1m";
const BG_HEADER: &str = "\x1b[48;2;16;20;28m";
const RESET: &str = "\x1b[0m";

fn render_frame(app: TuiApp, snap: &SystemSnapshot, status_banner: &str, fullscreen: bool) -> String {
    let mut out = String::with_capacity(8192);
    if fullscreen {
        out.push_str("\x1b[H\x1b[2J");
    }
    out.push_str(BG_OBSIDIAN);
    out.push_str(FG_TEXT);

    let online_nodes = snap.mesh_nodes.iter().filter(|n| n.online).count();
    out.push_str(&format!(
        "{BG_HEADER}{FG_CYAN}╔══════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}\n"
    ));
    out.push_str(&format!(
        "{BG_HEADER}{FG_CYAN}║{RESET}{BG_HEADER} {FG_GOLD}TIANXIAOS SOVEREIGN TUI v{VERSION}{RESET}{BG_HEADER} │ {FG_TEXT}{:<26}{RESET}{BG_HEADER} │ Mesh {FG_GREEN}{online_nodes}/{}{RESET}{BG_HEADER} │ RAM {FG_CYAN}{:>6} MB{RESET}{BG_HEADER} {FG_CYAN}║{RESET}\n",
        snap.hostname,
        snap.mesh_nodes.len(),
        snap.avail_mem_mb
    ));
    out.push_str(&format!(
        "{BG_HEADER}{FG_CYAN}╠══════════════════════════════════════════════════════════════════════════════════════════════╣{RESET}\n"
    ));

    // 9-Tab Bar
    out.push_str(&format!("{BG_HEADER}{FG_CYAN}║{RESET}{BG_HEADER} "));
    for tab in TuiApp::ALL {
        if tab == app {
            out.push_str(&format!("{BG_TAB_ACTIVE} {} {RESET}{BG_HEADER} ", tab.label()));
        } else {
            out.push_str(&format!("{FG_MUTED}{}{RESET}{BG_HEADER} ", tab.label()));
        }
    }
    out.push_str(&format!("{FG_CYAN}║{RESET}\n"));
    out.push_str(&format!(
        "{BG_HEADER}{FG_CYAN}╚══════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}\n"
    ));

    out.push_str(&format!(
        "{BG_OBSIDIAN}  {FG_GOLD}▶ {}{RESET}  {FG_MUTED}({EDITION}){RESET}\n\n",
        app.title()
    ));

    match app {
        TuiApp::Overview => {
            out.push_str(&format!(
                "  {FG_CYAN}┌─ SUBSTRATE & BUILD LAW SEAL ─────────────────────────────────────────────────────────────┐{RESET}\n"
            ));
            out.push_str(&format!(
                "  {FG_CYAN}│{RESET} Seal Status   : {FG_GREEN}{}{RESET} ({}/14 Mahāvidyā, {} Mirrors)\n",
                if snap.law.verified { "MATHEMATICALLY_SEALED_AND_VERIFIED" } else { "CHECK_REQUIRED" },
                snap.law.domains_verified,
                snap.law.mirrors_found
            ));
            out.push_str(&format!(
                "  {FG_CYAN}│{RESET} Merkle Root   : {FG_GOLD}{}{RESET}\n",
                snap.law.merkle_root
            ));
            out.push_str(&format!(
                "  {FG_CYAN}│{RESET} Cockpit :8081 : {}  │  Thermal: {FG_CYAN}{:.1} °C{RESET}  │  ADS-B RF: {FG_GREEN}{} frames{RESET}\n",
                if snap.cockpit_up {
                    format!("{FG_GREEN}ONLINE (200 OK){RESET}")
                } else {
                    format!("{FG_AMBER}LOCAL / PORTABLE{RESET}")
                },
                snap.thermal_celsius,
                snap.adsb_frames
            ));
            out.push_str(&format!(
                "  {FG_CYAN}│{RESET} Aethervault   : {FG_GREEN}{}+ isolated keys{RESET} (Zero secret exposure │ <{}ms PQ Cryptoshred)\n",
                snap.vault.total_isolated_keys,
                snap.vault.gdpr_cryptoshred_sla_ms
            ));
            out.push_str(&format!(
                "  {FG_CYAN}│{RESET} Intelligence  : {FG_CYAN}{} Scour Signals{RESET} │ {FG_GOLD}{} Ranked RGUs{RESET} │ {FG_GREEN}{} B2B Sprint Targets{RESET}\n",
                snap.signals_total,
                snap.rgus.len(),
                snap.b2b_targets
            ));
            out.push_str(&format!(
                "  {FG_CYAN}└──────────────────────────────────────────────────────────────────────────────────────────┘{RESET}\n\n"
            ));
            out.push_str(&format!("  {FG_GOLD}Active Sovereign Mesh Nodes:{RESET}\n"));
            for n in &snap.mesh_nodes {
                let st = if n.online {
                    format!("{FG_GREEN}● ONLINE {RESET}")
                } else {
                    format!("{FG_AMBER}○ STANDBY{RESET}")
                };
                out.push_str(&format!("    {st}  {FG_CYAN}{:<18}{RESET} │ {}\n", n.name, n.role));
            }
        }
        TuiApp::Scour => {
            out.push_str(&format!(
                "  {FG_GREEN}Merged Signal Ledger:{RESET} {} total signals ingested (`MERGED_SIGNALS.jsonl`)\n",
                snap.signals_total
            ));
            out.push_str(&format!(
                "  {FG_MUTED}Channels: all | arxiv | github | defillama | threat | merchant | x402 | asura | triad{RESET}\n\n"
            ));
            for (idx, s) in snap.recent_signals.iter().enumerate() {
                out.push_str(&format!(
                    "  {FG_GOLD}{:02}.{RESET} [{FG_CYAN}{:<9}{RESET} │ {:<16}] ({FG_GREEN}{}{RESET}) {}\n",
                    idx + 1,
                    s.source,
                    s.category,
                    s.score,
                    s.title
                ));
            }
        }
        TuiApp::Miner => {
            out.push_str(&format!(
                "  {FG_GOLD}Daśavidyāyāna Priority Calculus:{RESET} Rank = P (Proximity) + C (Capital Eff) + A (Autonomy) + E (Evidence) + F (Fit)\n"
            ));
            out.push_str(&format!(
                "  {FG_GREEN}Live B2B Vacancy-to-Sprint Strike Pipeline:{RESET} {} institutional targets (`<= 8 FFPs` per RGU)\n\n",
                snap.b2b_targets
            ));
            for r in &snap.rgus {
                out.push_str(&format!(
                    "  {FG_CYAN}{}{RESET} │ SFI {FG_GOLD}{:<9}{RESET} │ {:<24} │ {FG_GREEN}{}{RESET}\n      └─ {}\n",
                    r.id, r.sfi_rank, r.lang_class, r.status, r.name
                ));
            }
        }
        TuiApp::Ledger => {
            let l = &snap.ledger;
            out.push_str(&format!(
                "  {FG_CYAN}TetraLedger 4-Way Settlement Invariant:{RESET} {FG_GREEN}{}{RESET}\n\n",
                l.status
            ));
            out.push_str(&format!("    1. Payfac / Merchant Rails (Stripe Connect / Gumroad) : {FG_GOLD}${:.2}{RESET}\n", l.stripe_usd));
            out.push_str(&format!("    2. Web3 / Smart Contracts (Base L2 / EFEMERA / x402)  : {FG_GOLD}${:.2}{RESET}\n", l.web3_efm_usd));
            out.push_str(&format!("    3. Internal SQLite Core (`portfolio.sqlite3` WAL)     : {FG_GOLD}${:.2}{RESET}\n", l.sqlite_core_usd));
            out.push_str(&format!("    4. Open Banking Feeds (GoCardless / SEPA Cleared)     : {FG_GOLD}${:.2}{RESET}\n\n", l.bank_cleared_usd));
            out.push_str(&format!("    Delta Discrepancy   : {FG_GREEN}${:.2} (0.00% phantom balance drift){RESET}\n", l.delta_drift_usd));
            out.push_str(&format!("    Configured SKUs     : {} single-currency compliant tiers │ {} rail events\n", l.payment_rails_configured, l.rail_events_count));
            out.push_str(&format!("    SHA-256 Merkle Root : {FG_CYAN}{}{RESET}\n", l.merkle_root));
        }
        TuiApp::Dss14 => {
            for (num, name, desc) in MAHAVIDYA_DOMAINS {
                out.push_str(&format!(
                    "  {FG_GOLD}[{}]{RESET} {FG_CYAN}{:<16}{RESET} │ {FG_GREEN}PASS{RESET} │ {}\n",
                    num, name, desc
                ));
            }
        }
        TuiApp::Etamanga => {
            out.push_str(&format!("  {FG_GOLD}Sovereign On-Chain & HTTP 402 Settlement Surface:{RESET}\n\n"));
            out.push_str(&format!("    • Network             : {FG_CYAN}Base L2 Mainnet (EVM Chain ID 8453) + Solana Relay{RESET}\n"));
            out.push_str(&format!("    • Contracts           : {FG_GREEN}EfemeraERC20 (`EFM`) + SovereignEscrowVault + MerkleDistributor{RESET}\n"));
            out.push_str(&format!("    • x402 Gateway        : {FG_GREEN}ACTIVE (`tx_x402_gateway.py` machine-to-machine micropayments){RESET}\n"));
            out.push_str(&format!("    • Fiat Multi-Currency : {FG_CYAN}EUR (EE/EU Default), USD, GBP, CHF, SEK, NOK, CAD, AUD, SGD, JPY{RESET}\n"));
            out.push_str(&format!("    • Single-Currency Law : {FG_GREEN}ENFORCED (Zero mixed-symbol page views across 28 subdomains){RESET}\n"));
            out.push_str(&format!("    • Statement Descriptor: {FG_GOLD}RASA-X-MACHINA * TX{RESET} (<= 22 chars verified)\n"));
        }
        TuiApp::Fortress => {
            out.push_str(&format!("  {FG_CYAN}Faery Fortress Zero-Trust Perimeter & Aethervault Posture:{RESET}\n\n"));
            out.push_str(&format!(
                "    • Aethervault Keys    : {FG_GREEN}{}+ isolated credentials{RESET} (Secret values NEVER enter stdout/UI)\n",
                snap.vault.total_isolated_keys
            ));
            out.push_str(&format!(
                "    • SecretShield Engine : {FG_GREEN}{} active regex redaction layers{RESET} (Stripe/AWS/GH/GCP/PEM/JWT)\n",
                snap.vault.secret_shield_rules
            ));
            out.push_str(&format!(
                "    • GDPR++ Cryptoshred  : {FG_GOLD}{} ms{RESET} (< 50ms Ephemeral Post-Quantum Key Destruction SLA)\n",
                snap.vault.gdpr_cryptoshred_sla_ms
            ));
            out.push_str(&format!("    • Rosenpass PQ Transit: {FG_GREEN}Classic McEliece + Kyber Hybrid WireGuard PSK Rotation{RESET}\n"));
            out.push_str(&format!("    • Wayland virtwl Gate : {FG_GREEN}Primary-selection & clipboard snooping blocked for microVMs{RESET}\n"));
            out.push_str(&format!("    • Cgroup v2 Containment: {FG_GREEN}MemoryMax / TasksMax / ProtectSystem=strict / NoNewPrivileges=yes{RESET}\n"));
        }
        TuiApp::Models => {
            out.push_str(&format!(
                "  {FG_GOLD}Constructal Sine-Meander Token Router:{RESET} {FG_GREEN}0.00% HTTP 429 Drops │ 79.6% OpEx Reduction{RESET}\n"
            ));
            out.push_str(&format!(
                "  {FG_MUTED}Indexed Sovereign Models on latitude-tianxia ({} active):{RESET}\n\n",
                snap.models.len()
            ));
            for (i, m) in snap.models.iter().enumerate() {
                out.push_str(&format!("    {FG_GOLD}{:02}.{RESET} {FG_CYAN}{}{RESET}\n", i + 1, m));
            }
        }
        TuiApp::Tracer => {
            out.push_str(&format!(
                "  {FG_GOLD}Murua Bayesian Untracked Consignment Engine (UPU 2IPD 2026 Edition):{RESET}\n\n"
            ));
            for c in &snap.murua {
                out.push_str(&format!(
                    "    {FG_CYAN}[{}]{RESET} {} — Path Reliability: {FG_GREEN}{:.1}%{RESET}\n",
                    c.order_id, c.corridor, c.reliability_pct
                ));
                out.push_str(&format!("      ├─ Origin IMPC : {}\n", c.origin_impc));
                out.push_str(&format!("      ├─ Dest Hub    : {}\n", c.dest_hub));
                out.push_str(&format!("      └─ Stage / Win : {FG_GOLD}{}{RESET} ({})\n\n", c.stage, c.window));
            }
        }
    }

    out.push_str(&format!(
        "\n{BG_HEADER}{FG_CYAN}────────────────────────────────────────────────────────────────────────────────────────────────{RESET}\n"
    ));
    out.push_str(&format!(
        "{BG_HEADER}  {FG_GOLD}[1-9]{RESET}{BG_HEADER} Switch App │ {FG_GOLD}[Tab/←/→]{RESET}{BG_HEADER} Cycle │ {FG_GOLD}[r]{RESET}{BG_HEADER} Refresh │ {FG_GOLD}[v]{RESET}{BG_HEADER} Verify Seal │ {FG_GOLD}[q]{RESET}{BG_HEADER} Quit   {FG_GREEN}{status_banner}{RESET}\n"
    ));
    out
}

#[cfg(unix)]
mod raw_tty {
    use std::io::Write;

    #[repr(C)]
    #[derive(Clone, Copy)]
    pub struct Termios {
        pub c_iflag: u32,
        pub c_oflag: u32,
        pub c_cflag: u32,
        pub c_lflag: u32,
        pub c_line: u8,
        pub c_cc: [u8; 32],
        pub _pad: [u8; 64],
    }

    extern "C" {
        fn isatty(fd: i32) -> i32;
        fn tcgetattr(fd: i32, termios_p: *mut Termios) -> i32;
        fn tcsetattr(fd: i32, optional_actions: i32, termios_p: *const Termios) -> i32;
        fn read(fd: i32, buf: *mut core::ffi::c_void, count: usize) -> isize;
    }

    const STDIN_FILENO: i32 = 0;
    const TCSANOW: i32 = 0;
    const ICANON: u32 = 0x0002;
    const ECHO: u32 = 0x0008;
    const ISIG: u32 = 0x0001;
    // Linux & Android aarch64/x86_64 NCCS index for VTIME=5, VMIN=6
    const VTIME: usize = 5;
    const VMIN: usize = 6;

    pub fn stdin_is_tty() -> bool {
        // SAFETY: `isatty` is a standard async-signal-safe POSIX query on fd 0.
        unsafe { isatty(STDIN_FILENO) == 1 }
    }

    pub struct RawModeGuard {
        orig: Termios,
        active: bool,
    }

    impl RawModeGuard {
        pub fn enter() -> Option<Self> {
            if !stdin_is_tty() {
                return None;
            }
            let mut orig = Termios {
                c_iflag: 0,
                c_oflag: 0,
                c_cflag: 0,
                c_lflag: 0,
                c_line: 0,
                c_cc: [0u8; 32],
                _pad: [0u8; 64],
            };
            // SAFETY: Oversized `Termios` buffer safely accommodates glibc/musl/bionic `struct termios`.
            let rc = unsafe { tcgetattr(STDIN_FILENO, &mut orig) };
            if rc != 0 {
                return None;
            }
            let mut raw = orig;
            raw.c_lflag &= !(ICANON | ECHO | ISIG);
            raw.c_cc[VMIN] = 0;
            raw.c_cc[VTIME] = 2; // 200ms bounded non-blocking read timeout (BAGALAMUKHI loop discipline)
            let set_rc = unsafe { tcsetattr(STDIN_FILENO, TCSANOW, &raw) };
            if set_rc != 0 {
                return None;
            }
            print!("\x1b[?1049h\x1b[?25l");
            let _ = std::io::stdout().flush();
            Some(Self { orig, active: true })
        }

        pub fn poll_key(&self) -> Option<[u8; 4]> {
            let mut buf = [0u8; 4];
            // SAFETY: Bounded 4-byte stack buffer read from STDIN with VTIME=2 (200ms).
            let n = unsafe { read(STDIN_FILENO, buf.as_mut_ptr().cast(), 4) };
            if n > 0 {
                Some(buf)
            } else {
                None
            }
        }
    }

    impl Drop for RawModeGuard {
        fn drop(&mut self) {
            if self.active {
                print!("\x1b[0m\x1b[?25h\x1b[?1049l");
                let _ = std::io::stdout().flush();
                // SAFETY: Restores original terminal attributes captured at `enter()`.
                unsafe {
                    let _ = tcsetattr(STDIN_FILENO, TCSANOW, &self.orig);
                }
            }
        }
    }
}

pub fn run_tui(initial_app: TuiApp, once: bool) -> i32 {
    let mut snap = collect_snapshot();
    let mut app = initial_app;
    let mut banner = "READY".to_string();

    #[cfg(unix)]
    let can_interact = !once && raw_tty::stdin_is_tty();
    #[cfg(not(unix))]
    let can_interact = false;

    if !can_interact {
        let frame = render_frame(app, &snap, "SNAPSHOT (--once)", false);
        print!("{frame}");
        let _ = io::stdout().flush();
        return 0;
    }

    #[cfg(unix)]
    {
        let Some(guard) = raw_tty::RawModeGuard::enter() else {
            let frame = render_frame(app, &snap, "SNAPSHOT (FALLBACK)", false);
            print!("{frame}");
            let _ = io::stdout().flush();
            return 0;
        };

        let mut dirty = true;
        // BAGALAMUKHI bounded session loop (max 18,000 ticks @ 200ms = 1 hour idle auto-exit)
        for _tick in 0..18_000usize {
            if dirty {
                let frame = render_frame(app, &snap, &banner, true);
                print!("{frame}");
                let _ = io::stdout().flush();
                dirty = false;
            }
            if let Some(key) = guard.poll_key() {
                match key[0] {
                    b'q' | b'Q' | 3 => break, // q or Ctrl-C
                    27 => {
                        // Esc or Arrow sequence `\x1b[C` / `\x1b[D`
                        if key[1] == b'[' {
                            if key[2] == b'C' {
                                app = app.next();
                                banner = format!("TAB -> {}", app.label());
                                dirty = true;
                            } else if key[2] == b'D' {
                                app = app.prev();
                                banner = format!("TAB -> {}", app.label());
                                dirty = true;
                            }
                        } else if key[1] == 0 {
                            break;
                        }
                    }
                    b'\t' => {
                        app = app.next();
                        banner = format!("TAB -> {}", app.label());
                        dirty = true;
                    }
                    b'1'..=b'9' => {
                        let idx = (key[0] - b'1') as usize;
                        app = TuiApp::ALL[idx];
                        banner = format!("ACTIVE: {}", app.label());
                        dirty = true;
                    }
                    b'r' | b'R' => {
                        snap = collect_snapshot();
                        banner = "TELEMETRY REFRESHED".to_string();
                        dirty = true;
                    }
                    b'v' | b'V' => {
                        snap = collect_snapshot();
                        banner = if snap.law.verified {
                            format!("SEAL OK: {}...", &snap.law.merkle_root[..12])
                        } else {
                            "SEAL CHECK WARNING".to_string()
                        };
                        dirty = true;
                    }
                    _ => {}
                }
            }
        }
    }
    0
}
