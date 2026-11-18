#!/usr/bin/env python3
# ffp: FFP-COMMITTEE-DOSSIER-GEN content-pipeline python
"""
Generates Brand-Kit & PWA-consistent Obsidian (#080808 / #7c5cff / #00f59b / #22d3ee)
Estonian Startup Committee & Investor Dossiers (v8.7.0 / Build Law v5.0):
  1. Rasa-X-Machina_TianxiaOS_Pitch_Deck_2026.pdf (12-slide 16:9 widescreen PDF)
  2. Rasa-X-Machina_OU_Capitalisation_Table_2026.{csv,xlsx,pdf} (Clean EUR, zero $ / ** bugs)
  3. Rasa-X-Machina_Founder_Video_Script_v6_2026.{md,pdf} (2:30 teleprompter script)
  4. 01_Estonian_Startup_Committee_Statutory_Verification_Brief_179423.pdf
  5. 02_TianxiaOS_Architecture_Security_GDPRpp_and_SBOM_Attestation.pdf
  6. 03_Rasa-X-Machina_OU_Cap_Table_Tallinn_IP_and_TalTech_Hiring_Plan.pdf
  7. DEALUM_179423_ZERO_DATA_LOSS_UPDATE_GUIDE.md
  8. X Brand Assets (SVG + PNG avatars & 1500x500 headers for @rasaxmachina & @tianxiaos)
"""
from __future__ import annotations

import csv
import html
import io
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

WORKSPACE = Path("${TX_WORKSPACE:-/var/lib/tianxia}")
TIANXIA = WORKSPACE / "tianxia"
LOGO_SRC = Path("./downloads/rasa_x_machina_logo.svg")
OUT_DIRS = [
    TIANXIA / "docs" / "estonia_committee_packet",
    TIANXIA / "ui" / "dossier",
    WORKSPACE / "TianxiaOS" / "platforms" / "rasa-x-machina" / "docs" / "estonia_committee_packet",
    WORKSPACE / "TianxiaOS" / "platforms" / "rasa-x-machina" / "ui" / "dossier",
    Path("./downloads/Estonia_Dealum_179423_Submission_Ready"),
]
SLIDES_PNG_OUT = Path("${TX_HOME:-/var/lib/tianxia}/.gemini/antigravity-cli/brain/a83391c9-32d2-43d2-b3b1-7de5fd36e19a/scratch/slides_1080p")
X_ASSETS_DIR = TIANXIA / "docs" / "commercial" / "x_brand_assets"

LOGO_SVG_FALLBACK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="44" height="44"><rect width="512" height="512" rx="96" fill="#080808"/><polygon points="256,48 432,150 432,362 256,464 80,362 80,150" fill="none" stroke="#22d3ee" stroke-width="14"/><path d="M 256 128 L 368 336 L 144 336 Z" fill="none" stroke="#7c5cff" stroke-width="20"/><circle cx="256" cy="268" r="22" fill="#00f59b"/></svg>"""


def load_logo_inline(size_px: int = 42) -> str:
    if LOGO_SRC.exists():
        raw = LOGO_SRC.read_text(encoding="utf-8", errors="ignore").strip()
        raw = raw.replace('width="100%" height="100%"', f'width="{size_px}" height="{size_px}"')
        return raw
    return LOGO_SVG_FALLBACK


def write_minimal_xlsx(path: Path, sheets: list[tuple[str, list[list[str]]]]) -> None:
    """Writes a valid, dependency-free OpenXML .xlsx workbook with multiple sheets."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + "".join(
                f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                for i in range(1, len(sheets) + 1)
            )
            + "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
            + "".join(
                f'<sheet name="{xml_escape(name[:31])}" sheetId="{i}" r:id="rId{i}"/>'
                for i, (name, _) in enumerate(sheets, 1)
            )
            + "</sheets></workbook>",
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(
                f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
                for i in range(1, len(sheets) + 1)
            )
            + "</Relationships>",
        )
        for idx, (_, rows) in enumerate(sheets, 1):
            row_xml = []
            for r_i, row in enumerate(rows, 1):
                cells = []
                for c_i, val in enumerate(row):
                    col_letter = chr(65 + c_i)
                    cells.append(
                        f'<c r="{col_letter}{r_i}" t="inlineStr"><is><t>{xml_escape(str(val))}</t></is></c>'
                    )
                row_xml.append(f'<row r="{r_i}">{"".join(cells)}</row>')
            zf.writestr(
                f"xl/worksheets/sheet{idx}.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<sheetData>{"".join(row_xml)}</sheetData></worksheet>',
            )
    tmp = path.with_suffix(".xlsx.tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(path)


def build_cap_table_files(stage_dir: Path) -> None:
    headers = [
        "Shareholder Name",
        "Role / Title",
        "Share Class",
        "Number of Shares",
        "Nominal Value per Share (EUR)",
        "Total Nominal Capital (EUR)",
        "Fully Diluted Ownership (%)",
        "Voting Power (%)",
    ]
    incorp_rows = [
        [
            "Collins Eyong Takem-Manga-Bechem",
            "Founder & Principal Systems Architect",
            "Ordinary / Common",
            "2500",
            "€1.00",
            "€2,500.00",
            "100.00%",
            "100.00%",
        ],
        [
            "Unallocated Employee Stock Option Pool (ESOP)",
            "Reserved for Tallinn / TalTech Key Engineering Hires (Post-Incorporation)",
            "Options Pool (Authorized Post-Approval)",
            "0",
            "€0.00",
            "€0.00",
            "0.00%",
            "0.00%",
        ],
        [
            "TOTAL ISSUED & OUTSTANDING (UPON INCORPORATION)",
            "Proposed Estonian Entity: RASA-X-MACHINA OÜ (Äriseadustik § 148)",
            "Ordinary / Common",
            "2500",
            "€1.00",
            "€2,500.00",
            "100.00%",
            "100.00%",
        ],
    ]
    proforma_headers = [
        "Capital Stage / Stakeholder",
        "Instrument / Share Class",
        "Valuation / Cap (EUR)",
        "Investment / Nominal (EUR)",
        "Post-Tranche Ownership (%)",
        "Notes & Governance",
    ]
    proforma_rows = [
        [
            "Stage 0: Incorporation Baseline (Upon Committee Approval)",
            "2,500 Ordinary Shares (€1.00 par)",
            "€2,500.00 Nominal Capital",
            "€2,500.00",
            "Founder 100.0%",
            "Zero prior debt; 100% IP assigned to RASA-X-MACHINA OÜ in Tallinn",
        ],
        [
            "Stage 1: Tallinn ESOP + Tranche 1 Bridge (Dealum #179423)",
            "Convertible Note / SAFE + 10% ESOP",
            "€2,500,000 Pre-Money",
            "€150,000 – €300,000 (+ €170k EIS Grant)",
            "Founder ~81.0% | ESOP 10.0% | Bridge ~9.0%",
            "Funds TalTech/Tartu systems hires, 5 Estonian patent filings & CR14 pilot",
        ],
        [
            "Stage 2: Institutional Deep-Tech Seed Expansion",
            "Preferred Seed / SAFE",
            "€10,000,000 Cap",
            "€1,500,000 – €2,500,000",
            "Founder ~67.5% | ESOP 10.0% | Investors ~22.5%",
            "Scales NATO DIANA / EU enterprise nodes toward >€1.2M ARR",
        ],
    ]

    csv_path = stage_dir / "Rasa-X-Machina_OU_Capitalisation_Table_2026.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(incorp_rows)

    xlsx_path = stage_dir / "Rasa-X-Machina_OU_Capitalisation_Table_2026.xlsx"
    write_minimal_xlsx(
        xlsx_path,
        [
            ("Incorporation Cap Table EUR", [headers] + incorp_rows),
            ("Two-Tranche ProForma EUR", [proforma_headers] + proforma_rows),
        ],
    )


SLIDES_DATA = [
    {
        "tag": "01 // EXECUTIVE SUMMARY · RESTRICTED // TLP:AMBER",
        "title": "Rasa-X-Machina // TianxiaOS (v8.7.0)",
        "lead": "Mathematically sealed operating substrate solving runaway cloud LLM OpEx, container breakout vulnerabilities, and multi-agent routing non-determinism.",
        "kpis": [
            ("70.6%–79.6%", "LLM OpEx Reduction", "Local 7.2–14.0ms System-1 pre-filter (@ €0.039 / $0.042 per 1M ops)"),
            ("0.00% 429", "Zero Burst Drop Rate", "Eliminates 41.93% failure rate across 2,722 audited production events"),
            (">€1,295", "Attacker Scan Cost", "Escalated from €23.55 ($25.46) via Vogel Aeroelastic & AF_XDP <3.8μs defense"),
            ("7 Formats", "Signed Native Releases", ".deb · .rpm · AppImage · Nix Flake · .tar.gz · Windows .exe · Android .apk"),
        ],
        "cols": [
            ("Substrate Stack", ["Declarative NixOS Flakes + seL4 Microkit + LionsOS Protection Domains", "Shell-less Nanos Unikernels executing in ephemeral volatile RAM (tmpfs)", "Build Law v5.0 SHA-256 + BLAKE2b Merkle & HMAC-SHA256 Sealed"]),
            ("Commercial & Global Parity", ["28 Live Interactive Polyglot Web Apps (rasaxmachina.com)", "42 Global Markets · 25 Full-Copy Languages (incl. Eesti & RTL) · 29 Currencies", "21 Live Stripe SKUs + €0.00 Discrepancy Veritas-Rex Merkle Ledger"]),
        ],
    },
    {
        "tag": "02 // STRUCTURAL PROBLEM · WHY LEGACY STACKS BREAK",
        "title": "Legacy Cloud & Container Infrastructure Fails Autonomous Workloads",
        "lead": "As enterprises and defense agencies deploy long-horizon agent swarms (surpassing 2B+ sandboxes globally in 2026), AWS/Docker/Kubernetes fail on three axes:",
        "kpis": [
            ("< 30%", "Gross Margin Compression", "€3.25–€7.40/hr GPU rent + 48GB+ static RAM allocation crushes SaaS unit economics"),
            ("Shared Kernel", "Container Escape Surface", "Docker & Linux microVMs expose ambient authority & static SSO session tokens"),
            ("41.93%", "Burst Upstream Failure", "Validated across 1,722 dispatches: naive retries waste 62.67 min socket time"),
            ("30-Day Lag", "Legacy Privacy Debt", "Manual GDPR deletions leave residual PII inside cold snapshots & backups"),
        ],
        "cols": [
            ("The Competitor Gap (E2B / Docker)", ["E2B ($32.5M raised, 2B+ sandboxes) proved massive market demand for agent computers", "Yet legacy sandboxes run unverified Linux guest kernels with 0% LLM token cost reduction"]),
            ("The Sovereign Imperative", ["EU AI Act, NIS2, DORA & NATO tactical edge mandates require mathematical isolation", "Enterprises need deterministic FinOps + zero-ambient-authority execution in one substrate"]),
        ],
    },
    {
        "tag": "03 // FORMALLY VERIFIED OPERATING SUBSTRATE",
        "title": "Hardware-Enforced seL4 Microkit, LionsOS & Ephemeral Nanos Unikernels",
        "lead": "TianxiaOS replaces mutable Linux containers with capability-gated Protection Domains and compile-time AST verification.",
        "kpis": [
            ("seL4 + LionsOS", "Trusted Computing Base", "90% ARM & x86 formal proof coverage; zero global IP stack in TCB"),
            ("0 Shells", "Nanos Unikernel Runtime", "Workloads run in volatile tmpfs RAM; task exit sanitizes memory instantly"),
            ("14 Domains", "DSS-14.2 Static AST Gate", "Every Function-Feature Pair (FFP) passes compile-time AST & Build Law v5.0 gates"),
            ("VirtWL Proxy", "Capability Firewall", "OCaml/Rust Wayland & socket proxy blocks clipboard snooping & SSRF"),
        ],
        "cols": [
            ("Zero Ambient Authority", ["Compromised external parsers lack cryptographic capability tokens to touch adjacent pages", "Eliminates entire classes of container breakout, privilege escalation & lateral movement"]),
            ("Polyglot FFP-First Discipline", ["1,023 verified Function-Feature Pairs across Rust, C/AVX2, OCaml, Zig, Nim & Nix", "Bounded <=8 FFPs per Revenue Generation Unit (RGU) for zero context drift"]),
        ],
    },
    {
        "tag": "04 // INFERENCE ARCHITECTURE & VERITAS PAGING",
        "title": "Deterministic 4-Tier Inference Waterfall & 500 GB Cognitive Paging",
        "lead": "Intercepts and resolves 95%+ of routine agent operations locally before touching expensive frontier cloud GPUs:",
        "kpis": [
            ("Tier 1 · <14ms", "ENHAN3 System-1 Gate", "C/AVX2 SIMD pre-filter @ €0.039/1M ops in <1 GB RAM"),
            ("Tier 2 · 1.58-bit", "BitNet Ternary + VUDA", "Maps CUDA virtual memory to Vulkan page tables on standard CPUs/iGPUs"),
            ("Tier 3 · 600 tok/s", "Distilled Mamba-2 SLMs", "SemanticZip AST binary packing cuts inter-node context payload by 70%"),
            ("300–500 GB", "Veritas Virtual Paging", "Scales 8–32 GB edge nodes via L1-ZRAM + NVMe holographic weight paging"),
        ],
        "cols": [
            ("Tier 4: Constructal Sine-Meander Cloud Router", ["Only the top <5% apex reasoning tasks route to frontier cloud models", "Bejan Constructal flow physics bends burst traffic smoothly with 0.00% HTTP 429 drops"]),
            ("Corroborated Physics", ["Matches 2026 BitNet b1.58 SIMD benchmarks (6.03x RAM cut -> 806 MB RSS)", "Delivers audited 70.6%–79.6% total AI compute OpEx reduction (€5,824 -> €1,190/mo)"]),
        ],
    },
    {
        "tag": "05 // MATHEMATICAL INVARIANTS & HUSSAR 7 SENTINEL LEGIONS",
        "title": "Biomimetic Flow Physics Patrolled by 7 Autonomous Sentinel Legions",
        "lead": "Replaces brittle heuristic orchestration with mathematical invariants and continuous 7-Legion autonomous self-governance.",
        "kpis": [
            ("137.508°", "Fibonacci Phyllotaxis", "Phase-shifts socket activation across WireGuard mesh; caps thermal ceiling <88°C"),
            ("12% Buffer", "MicroVM Crown Shyness", "Hard spatial free-RAM boundary mathematically prevents Linux OOM-killer collisions"),
            ("7 Legions", "Hussar Agentic Army", "Security · Synergy · Sync · Harmony · Evergreen · ENHAN3 · DB-Nexus (60s patrol)"),
            ("3,390 Edges", "Cross-DB Relational Graph", "28 WAL SQLite DBs unified in graph.sqlite3 (1,409 nodes, 0 FK violations)"),
        ],
        "cols": [
            ("IREB Botanical Abscission Compactor", ["Froude limit-cycle pruning at 85% context utilization cuts long-horizon token drift by 70%", "Prevents zombie processes via SLECO-SO++ bounded loops & exponential peer backoff"]),
            ("Hussar Autonomous Patrol (Live on latitude-tianxia)", ["BHAIRAVI-AEGIS, PARAMASIVA-SYNERGY, BHUVANESVARI-SYNC, TRIPURA-HARMONY", "KALACHAKRA-EVERGREEN, CHHINNAMASTA-ENHAN3 & MAHASARASVATI-NEXUS — 7/7 GREEN"]),
        ],
    },
    {
        "tag": "06 // ESTONIA DEFENCETECH · NATO CCDCOE / DIANA CORRIDOR",
        "title": "Faery Fortress Counter-Swarm Defense & GDPR++ Sovereign Privacy",
        "lead": "Engineered in Tallinn for dual-use cyber resilience and privacy 3–5 years ahead of every global jurisdiction.",
        "kpis": [
            ("11.40 Mpps", "AF_XDP Wire-Speed Cut", "<3.8 μs kernel-bypassed packet arrest neutralizing autonomous offensive swarms"),
            ("< 50 ms", "GDPR++ PQ Cryptoshredding", "XChaCha20-Poly1305 + ML-KEM-1024 per-subject key destruction + Merkle receipt"),
            ("Tri-Modal", "SRM Spatial Attestation", "Acoustic impulse + Lamb-wave dispersion + Titan M2 / TPM 2.0 hardware proximity"),
            ("1,563 KEVs", "Live Threat Sinkhole", "Real-time CISA KEV + Feodo C2 botnet sinkholing + Rosenpass PQ WireGuard"),
        ],
        "cols": [
            ("Faery Fortress Deception Matrix", ["Vogel Aeroelastic surface bending yields synthetic shadow schemas to scanners", "Ephemeral Nanos unikernel honeypots trap RCE attempts inside canary TetraLedger voids"]),
            ("GDPR++ Horizon Standard (v2030.4)", ["Outclasses EU GDPR, Estonian IKS, EU AI Act, Swiss revFADP, CPRA & LGPD by 3–5 years", "Zero third-party cookies, 0ms Sec-GPC enforcement & verifiable Merkle erasure proofs"]),
        ],
    },
    {
        "tag": "07 // MARKET OPPORTUNITY & 42-MARKET GLOBAL INFRASTRUCTURE",
        "title": "Anchored in Europe's Deep-Tech Gravity Center Targeting €445M ($480M) SOM",
        "lead": "Deep tech captured 63% of Estonian VC (€194.7M across 216 firms), backed by Estonia's €100M SmartCap Defence Fund.",
        "kpis": [
            ("€1.2T+ ($1.3T)", "Total Addressable Market", "Global Enterprise AI Infrastructure, FinOps, Cloud Sandboxing & Cyber Defense"),
            ("€132B ($142B)", "Serviceable Market (SAM)", "Autonomous Agent Runtimes, MicroVM Isolation & Sovereign Edge Compute"),
            ("€445M ($480M)", "36-Month EU/NATO SOM", "Mapped across 119 structured ICP segments & 147 B2B enterprise targets"),
            ("42 Markets", "Live Localization Matrix", "25 Full-Copy Languages (incl. Eesti, Arabic/Urdu RTL, CJK) & 29 Single-View Currencies"),
        ],
        "cols": [
            ("111-ICP Enterprise Registry (4 Ecosystems)", ["[RGE-01] RGE-SOVEREIGN: Cloud & platform teams eliminating container/token drift", "[RGE-02] RGE-SENTINEL: IAM, CISO & NATO tactical defense integrators"]),
            ("Automated Opportunity & Signal Mining", ["[RGE-03] RGE-CHAPEL: Formal AST code synthesis & compliance automation", "[RGE-04] RGE-ALPHA: Veritas-Rex 4-way cryptographic clearing & Murua logistics"]),
        ],
    },
    {
        "tag": "08 // BUSINESS MODEL, PRICING & LIVE TRACTION",
        "title": "High-Margin Unit Economics Scaling Non-Dilutive Cashflow into Recurring ARR",
        "lead": "Operates under Ndimmôrwyn's Composition Law (>=1.15x standalone return per RGU) across 21 live Stripe SKUs & 6 payment rails.",
        "kpis": [
            ("92% Margin", "Stream 01: VRTTI Sprints", "48-Hr Diagnostics (€1,000–€1,450) & 2-Wk MicroVM Deployments (€7,500–€12,500)"),
            ("88% Margin", "Stream 02: Node SaaS ARR", "€150–€450 / node / mo + 15% performance share on verified LLM token savings"),
            ("€80k–€250k", "Stream 03: Sovereign B2G", "Annual on-premise Faery Fortress & air-gapped defense deployments"),
            ("€0.00 Drift", "Veritas-Rex TetraLedger", "4-way Merkle reconciliation across Stripe, Gumroad, Solana, Base L2 & SQLite"),
        ],
        "cols": [
            ("20-Company Priority B2B/B2G Pipeline", ["Wave 1 (AI Runtimes): E2B, Dust.tt · Wave 2 (AI Security): Lakera AI", "Wave 3 (Automation) & Wave 4 (Allied Defense): Tallinn's DefSecIntel & EU integrators"]),
            ("Live Production Surfaces Today", ["4/5 Active Mesh Nodes (latitude-tianxia NixOS Hub, Hetzner EU PQ Relay, 2 Mobile Enclaves)", "28 Live Interactive Subdomains + GTK4 Desktop Control Center + 9-Tab Rust TUI"]),
        ],
    },
    {
        "tag": "09 // COMPETITIVE SUPERIORITY & 7-FORMAT NATIVE DISTRIBUTION",
        "title": "Structural Superiority & Zero-Friction Multi-OS Enterprise Delivery",
        "lead": "Outclasses Docker, cloud agent sandboxes, and wrapper frameworks across isolation, FinOps, privacy, and binary packaging.",
        "kpis": [
            (".deb & .rpm", "Enterprise Linux Packages", "Signed amd64/arm64 Debian & x86_64/aarch64 RHEL/Fedora packages"),
            (".AppImage", "Zero-FUSE Portable Linux", "Single-file executable bundle running across any Linux distribution"),
            ("flake.nix", "Declarative NixOS Flake", "One-command reproducible execution: nix run github:Tianxia-Core/tianxiaos-releases"),
            (".exe & .apk", "Windows & Android Enclave", "Zero-dependency Windows PE32+ .exe + RSA-4096 v2/v3 signed Android .apk"),
        ],
        "cols": [
            ("TianxiaOS vs. Standard Stacks", ["seL4 + shell-less Nanos tmpfs unikernels vs. shared monolithic Linux kernel", "70.6%–79.6% LLM OpEx cut & 0.00% 429 drops vs. 0% cost cut & 41.93% retry failures"]),
            ("Cryptographic Supply-Chain Trust", ["Detached OpenSSL Ed25519 signatures (.sig) + SHA256SUMS.sig on every package", "CycloneDX 1.5 SBOM.cdx.json + 6-hour automated Package Evergreen Sentinel"]),
        ],
    },
    {
        "tag": "10 // FRONTLINE-TO-FOUNDER TRAJECTORY & AI-NATIVE VELOCITY",
        "title": "Frontline Failure Forensics → Sovereign Founder × 10x–20x Velocity",
        "lead": "Collins Eyong Takem-Manga-Bechem — Founder & Principal Systems Architect (UK & US Dual Citizen, Residing in Tallinn).",
        "kpis": [
            ("10+ → 3+ Yrs", "Frontline-to-Founder", "10+ yrs FinTech triage & ledger forensics (Blockchain.com, CoinLedger, SQUIRE) → 3+ yrs architecting TianxiaOS"),
            ("4.00 GPA", "Pure Math & CS (SUNY)", "Asynchronous half-time Dual Major B.S. in Pure Mathematics & Computer Science alongside R&D"),
            ("10x–20x", "Self-Hosting Velocity", "1 Principal Architect + KAI³ / Pari / DSS-14.2 AST gates = 15-engineer systems output"),
            ("32 Repos", "Rasa-X-Machina Estate", "Signed 7-format native OS releases, 4/5 active mesh nodes & 7 Hussar Sentinel Legions"),
        ],
        "cols": [
            ("Frontline Failure Forensics Built Into Code", ["Diagnosed 50x volatility spikes, API drops, DeFi tax/ledger drift & Stripe Connect stalls first-hand on the front lines (2010–2024)", "Turned lived speech-block/neurodivergent resilience + frontline failure maps into 0.00% HTTP 429 routing & Veritas-Rex TetraLedger"]),
            ("Tallinn Operational Presence & Ecosystem Anchor", ["Already residing in Tallinn, Estonia operating live European sovereign mesh infrastructure without seed headcount bloat", "Ready to incorporate RASA-X-MACHINA OÜ, domicile 5 core patent families in Estonia & hire from TalTech / Univ. of Tartu upon approval"]),
        ],
    },
    {
        "tag": "11 // 24-MONTH ESTONIAN ROADMAP & TWO-TRANCHE CAPITAL ARCHITECTURE",
        "title": "Disciplined Capital Ladder & Deep Integration with Estonia's Ecosystem",
        "lead": "Synchronizes angel/grant efficiency with institutional scale while anchoring core IP and R&D talent in Tallinn.",
        "kpis": [
            ("€2,500 EUR", "Incorporation Cap Table", "2,500 Ordinary Shares @ €1.00 par (100% Founder, zero debt) upon approval"),
            ("€150k–€300k", "Tranche 1 Estonian Bridge", "Convertible/SAFE @ €2.5M Pre-Money (Dealum #179423) + €170k Tehnopol/EIS Grant"),
            ("€1.5M–€2.5M", "Tranche 2 Seed Expansion", "Institutional Deep-Tech Seed @ €10M Cap -> scales EU/NATO ARR past €1.2M+"),
            ("50% R&D Tax", "TalTech & Tartu Hiring", "Recruiting Rust/seL4 engineers from TalTech & Univ. of Tartu + 10% Tallinn ESOP"),
        ],
        "cols": [
            ("Execution Milestones (Q4 2026 – 2028)", ["Q4 2026: Startup Committee approval -> Incorporate RASA-X-MACHINA OÜ & file 5 core patents", "Q1–Q2 2027: Convert first 5–10 B2B sprint/SaaS clients; Tehnopol Cyber & DeepTech cohort"]),
            ("Estonian National Value Creation", ["Q3 2027–2028: NATO DIANA & Foundation CR14 cyber range validation; >€1.2M ARR", "Advances Startup Estonia's 500 deep-tech firm & 60% registered IP 2030 targets"]),
        ],
    },
    {
        "tag": "12 // STATUTORY COMPLIANCE MATRIX · VÄLISMAALASTE SEADUS § 100¹",
        "title": "Every Estonian Startup Committee Criterion Verified & Live in Production",
        "lead": "Application #179423 is under active Startup Committee consideration. Every claim is verifiable live in 60 seconds:",
        "kpis": [
            ("§ 100¹ (1)", "Scalable Global Tech", "Declarative Nix flakes + 7 native OS package formats + 42-market web app suite [VERIFIED]"),
            ("§ 100¹ (2)", "Repeatable SaaS Model", "21 live Stripe SKUs across 29 currencies + 92%-margin 48h sprints [VERIFIED]"),
            ("§ 100¹ (3)", "Proprietary Deep-Tech IP", "seL4/Nanos substrate, 79.6% OpEx waterfall, Faery Fortress & GDPR++ [VERIFIED]"),
            ("§ 100¹ (4)", "Estonian Ecosystem Value", "Tallinn OÜ IP anchor, TalTech/Tartu R&D hiring & NATO DIANA/CR14 fit [VERIFIED]"),
        ],
        "cols": [
            ("1-Click Live Verification Endpoints", ["Committee Companion: https://rasaxmachina.com/estonia", "Flagship Storefront & Cockpit: https://rasaxmachina.com · https://rasaxmachina.com/cockpit", "Public Signed Releases: https://github.com/Tianxia-Core/tianxiaos-releases"]),
            ("Direct Founder & Social Channels", ["Applicant: Collins Eyong Takem-Manga-Bechem (Shielded Contact Portal: https://rasaxmachina.com/collins · Phone Verified in Dealum #179423)", "Official X Ecosystem: @rasaxmachina · @tianxiaos · @coltakrasax"]),
        ],
    },
]


def render_pitch_deck_html() -> str:
    logo = load_logo_inline(38)
    slides_html = []
    for idx, s in enumerate(SLIDES_DATA, 1):
        kpi_cards = "".join(
            f"""<div class="kpi"><div class="kv">{html.escape(v)}</div><div class="kl">{html.escape(l)}</div><div class="ks">{html.escape(sub)}</div></div>"""
            for v, l, sub in s["kpis"]
        )
        col_cards = "".join(
            f"""<div class="panel"><h3>{html.escape(ct)}</h3><ul>{"".join(f"<li>{html.escape(b)}</li>" for b in bullets)}</ul></div>"""
            for ct, bullets in s["cols"]
        )
        slides_html.append(
            f"""<section class="slide">
  <header class="top">
    <div class="brand">{logo}<div><div class="b1">RASA-X-MACHINA // TIANXIAOS</div><div class="b2">{html.escape(s['tag'])}</div></div></div>
    <div class="pill">DEALUM #179423 · SLIDE {idx:02d} / 12</div>
  </header>
  <h1>{html.escape(s['title'])}</h1>
  <p class="lead">{html.escape(s['lead'])}</p>
  <div class="kpis">{kpi_cards}</div>
  <div class="cols">{col_cards}</div>
  <footer class="foot">
    <span>PROPOSED ENTITY UPON COMMITTEE APPROVAL: RASA-X-MACHINA OÜ (TALLINN)</span>
    <span>BUILD LAW v5.0 SEALED · GDPR++ v2030.4 · rasaxmachina.com/estonia</span>
  </footer>
</section>"""
        )
    return f"""<!doctype html>
<!-- ffp: FFP-PITCH-DECK-MASTER content-pipeline html -->
<html lang="en"><head><meta charset="utf-8"/>
<title>Rasa-X-Machina // TianxiaOS Pitch Deck (v8.7.0)</title>
<style>
  @page {{ size: 1280px 720px; margin: 0; }}
  * {{ box-sizing: border-box; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
  html, body {{ margin: 0; padding: 0; background: #050508; color: #f8fafc; font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; }}
  .slide {{
    width: 1280px; height: 720px; padding: 38px 52px 30px; position: relative; overflow: hidden;
    page-break-after: always; break-after: page; display: flex; flex-direction: column;
    background: radial-gradient(circle at 88% 12%, rgba(124,92,255,0.20), transparent 42%),
                radial-gradient(circle at 12% 88%, rgba(34,211,238,0.13), transparent 40%), #07080e;
    border: 1px solid rgba(124,92,255,0.28);
  }}
  .slide:last-child {{ page-break-after: auto; break-after: auto; }}
  .top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.10); }}
  .brand {{ display: flex; align-items: center; gap: 12px; }}
  .b1 {{ font-weight: 800; font-size: 15px; letter-spacing: 0.08em; color: #ffffff; }}
  .b2 {{ font-family: ui-monospace, monospace; font-size: 11px; color: #22d3ee; letter-spacing: 0.06em; margin-top: 2px; }}
  .pill {{ font-family: ui-monospace, monospace; font-size: 11.5px; font-weight: 700; color: #00f59b; background: rgba(0,245,155,0.10); border: 1px solid rgba(0,245,155,0.38); padding: 6px 14px; border-radius: 999px; }}
  h1 {{ font-size: 33px; line-height: 1.14; margin: 0 0 10px; letter-spacing: -0.02em; color: #ffffff; }}
  .lead {{ font-size: 15.5px; color: #cbd5e1; margin: 0 0 20px; line-height: 1.45; max-width: 1120px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 18px; }}
  .kpi {{ background: rgba(14,16,28,0.92); border: 1px solid rgba(124,92,255,0.36); border-radius: 14px; padding: 15px 16px; }}
  .kv {{ font-family: ui-monospace, monospace; font-size: 25px; font-weight: 800; color: #00f59b; margin-bottom: 4px; }}
  .kl {{ font-size: 12.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #f8fafc; margin-bottom: 5px; }}
  .ks {{ font-size: 12px; color: #94a3b8; line-height: 1.38; }}
  .cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; flex: 1; }}
  .panel {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(34,211,238,0.26); border-radius: 14px; padding: 18px 20px; }}
  .panel h3 {{ margin: 0 0 10px; font-size: 16px; color: #c084fc; letter-spacing: 0.01em; }}
  .panel ul {{ margin: 0; padding-left: 18px; color: #e2e8f0; font-size: 13.8px; line-height: 1.55; }}
  .panel li {{ margin-bottom: 8px; }}
  .foot {{ display: flex; justify-content: space-between; align-items: center; padding-top: 10px; margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); font-family: ui-monospace, monospace; font-size: 11px; color: #94a3b8; }}
</style></head><body>{"".join(slides_html)}</body></html>"""


def render_a4_doc_html(badge: str, title: str, subtitle: str, body_html: str) -> str:
    logo = load_logo_inline(34)
    return f"""<!doctype html>
<!-- ffp: FFP-COMMITTEE-BRIEF content-pipeline html -->
<html lang="en"><head><meta charset="utf-8"/><title>{html.escape(title)}</title>
<style>
  @page {{ size: A4 portrait; margin: 12mm 14mm; }}
  * {{ box-sizing: border-box; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
  html, body {{ margin: 0; padding: 0; background: #07080e; color: #f1f5f9; font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; font-size: 10.2pt; line-height: 1.48; }}
  .hdr {{ display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; margin-bottom: 14px; border-bottom: 1.5px solid rgba(124,92,255,0.45); }}
  .hdr-l {{ display: flex; align-items: center; gap: 10px; }}
  .b-top {{ font-weight: 800; font-size: 11pt; color: #fff; letter-spacing: 0.05em; }}
  .b-sub {{ font-family: ui-monospace, monospace; font-size: 8pt; color: #22d3ee; }}
  .tag {{ font-family: ui-monospace, monospace; font-size: 8pt; font-weight: 700; color: #00f59b; border: 1px solid rgba(0,245,155,0.4); background: rgba(0,245,155,0.1); padding: 4px 10px; border-radius: 999px; }}
  h1 {{ font-size: 16.5pt; color: #fff; margin: 0 0 4px; line-height: 1.2; }}
  .sub {{ color: #cbd5e1; font-size: 9.8pt; margin: 0 0 14px; }}
  h2 {{ font-size: 11.5pt; color: #38bdf8; margin: 14px 0 6px; border-left: 3px solid #7c5cff; padding-left: 8px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0 12px; font-size: 8.8pt; }}
  th, td {{ border: 1px solid rgba(255,255,255,0.14); padding: 6px 8px; text-align: left; vertical-align: top; }}
  th {{ background: rgba(124,92,255,0.22); color: #e9d5ff; font-weight: 700; text-transform: uppercase; font-size: 7.8pt; }}
  td {{ background: rgba(15,18,30,0.85); color: #e2e8f0; }}
  .box {{ background: rgba(16,20,34,0.92); border: 1px solid rgba(34,211,238,0.3); border-radius: 8px; padding: 10px 12px; margin-bottom: 10px; }}
  code {{ font-family: ui-monospace, monospace; font-size: 8.4pt; color: #00f59b; }}
  a {{ color: #38bdf8; text-decoration: none; }}
  .ftr {{ margin-top: 14px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.12); font-family: ui-monospace, monospace; font-size: 7.6pt; color: #94a3b8; display: flex; justify-content: space-between; }}
</style></head><body>
  <div class="hdr">
    <div class="hdr-l">{logo}<div><div class="b-top">RASA-X-MACHINA // TIANXIAOS</div><div class="b-sub">Proposed Estonian Entity upon Committee Approval: RASA-X-MACHINA OÜ (Tallinn)</div></div></div>
    <div class="tag">{html.escape(badge)}</div>
  </div>
  <h1>{html.escape(title)}</h1>
  <p class="sub">{html.escape(subtitle)}</p>
  {body_html}
  <div class="ftr"><span>Applicant: Collins Eyong Takem-Manga-Bechem · Direct Contact: https://rasaxmachina.com/collins</span><span>https://rasaxmachina.com/estonia</span></div>
</body></html>"""


VIDEO_SCRIPT_MD = """# Rasa-X-Machina // TianxiaOS — Founder 4-Beat Committee Pitch Video Script (2026)
**Applicant:** Collins Eyong Takem-Manga-Bechem (Founder & Principal Systems Architect)
**Application:** Estonian Startup Committee — Dealum Application `#179423` (*Välismaalaste seadus* § 100¹)
**Proposed Entity Upon Approval:** `RASA-X-MACHINA OÜ` (Tallinn, Republic of Estonia)
**Recorded Deliverables:**
1. **`Rasa-X-Machina_TianxiaOS_Committee_Pitch_2026.mp4`** — 4-Chapter Studio Cut with Brand-Kit 16:9 Slide & Live Substrate B-Roll Cut-Ins
2. **`Collins_Takem_Personal_Founder_Story_No_Slides_2026.mp4`** — Unscripted Personal Founder Reflection (Zero Slide Cut-Ins)

---

### [BEAT 1 // SELF-ADVOCACY HOOK & FRONTLINE FAILURE FORENSICS]
*(Visual: Founder on camera, split-screen with Slide 01 Executive Summary → Slide 02 Structural Problem)*

"Tere, members of the Startup Committee. I'm Collins Takem, founder of Rasa-X-Machina.

As I speak, you will hear that I have a speech block, along with autism and ADHD. I speak openly about hidden conditions because neurodiverse founders are rarely seen here in Estonia, and rather than reading a rigid script, I'm talking with you directly.

Living with speech blocks and mental noise is the exact reason I built TianxiaOS. While working on the incident front lines at Blockchain.com, SQUIRE, and CoinLedger during heavy market waves, I watched cloud platforms hit their own blocks: rate-limited APIs failed over forty percent of the time, runaway cloud bills eroded margins, and shared Linux containers left the door wide open to security breaches."

---

### [BEAT 2 // THE SOLUTION: WHY WE BUILT A NEW SOVEREIGN SUBSTRATE]
*(Visual: Split-screen & full-slide cut-ins of Slide 03 Formally Verified seL4/Nanos Substrate + Slide 06 Faery Fortress & GDPR++ + `rasaxmachina.com/estonia`)*

"Today, over two billion AI agents run on that same fragile foundation. You cannot run autonomous AI safely on aging operating layers.

Just as Estonian engineers built X-Road under lean resource rigor in the nineties, I built a self-hosting compiler pipeline to engineer TianxiaOS from the ground up. Instead of leaky Docker containers, we lock hardware down at Layer Zero and run workloads inside memory-only unikernels—backed by formally verified seL4 microkernels and instant quantum-safe key erasure. Every agent runs in complete isolation, with zero ambient authority."

---

### [BEAT 3 // THE PRODUCT IN ACTION: INPUT COMPRESSION & 4-TIER WATERFALL]
*(Visual: Slide 10 Frontline-to-Founder & SUNY Pure Math/CS → Slide 04 4-Tier Inference Waterfall → Live Cockpit HUD & Slide 09 7 Signed Native Formats)*

"Drawing on my dual degree in Pure Mathematics and Computer Science from SUNY—which I pursue asynchronously in my spare time—our engine attacks AI compute waste from both ends.

First, our compilers trim input prompts by more than half before inference even begins. Second, our Four-Tier Waterfall handles routine agent tasks locally in under fourteen milliseconds for pennies, while running large models on standard hardware. That cuts cloud compute bills by up to eighty percent and drops rate-limit errors to zero.

Full metrics are in our application pack: our engine is already proven across more than twenty-seven hundred production runs and ships in seven signed native formats today."

---

### [BEAT 4 // MARKET, CYBER DEFENSE CORRIDOR, TALLINN ANCHOR & CLOSE]
*(Visual: Slide 08 €132B SAM, 21 Live SKUs & 20-Company Pipeline → Slide 11 Tallinn OÜ Incorporation & TalTech/Tartu Hiring → Slide 12 § 100¹ Live Verification)*

"We serve a €132 billion market across AI infrastructure and cyber defense, with twenty-one live products already earning. We convert our twenty-company target pipeline—including E2B, Dust, Lakera, and Tallinn's DefSecIntel—through high-margin forty-eight-hour diagnostic sprints into monthly node licenses and sovereign defense contracts.

Having NATO's cyber defense center right here in Tallinn is a core reason I chose Estonia. I am already living here in Tallinn. Upon your approval, I will incorporate **Rasa-X-Machina OÜ**, anchor our core patents in Estonia, hire systems engineers from TalTech and the University of Tartu, and prove that neurodiverse deep-tech founders can build world-leading sovereign infrastructure right here in Eesti.

Aitäh, and thank you for your consideration."
"""


DEALUM_GUIDE_MD = """# Dealum Application `#179423` — Zero-Data-Loss Surgical Update & Submission Guide
**Applicant:** Collins Eyong Takem-Manga-Bechem (`collinstaken525-cloud@users.noreply.github.com`)
**Venture:** Rasa-X-Machina (Proposed Estonian Entity upon Startup Committee Approval: `RASA-X-MACHINA OÜ`)
**Authenticated Browser Rule (Build Law Pillar 4.6):** Open `https://app.dealum.com (Application #179423)` **exclusively in Chrome on this Pixel 8 Pro (`pixel8pro`)** where your authenticated session cookies reside. **Do NOT click "Delete", "Reset", or create a new application** — Dealum auto-saves each step per field!

---

## All Ready-to-Upload Files Staged on Your Phone
Every file below is already saved in `./downloads/Estonia_Dealum_179423_Submission_Ready/` on this Pixel 8 Pro (and mirrored live at `https://rasaxmachina.com/estonia#committee-dossiers`):

1. **`rasa_x_machina_logo.svg`** -> Upload in **Step 1 (Overview) → Company logo**
2. **`Rasa-X-Machina_TianxiaOS_Pitch_Deck_2026.pdf`** (12-slide 16:9 Brand-Kit PDF, updated Frontline-to-Founder Slide 10) -> Upload in **Step 1 / Deck slot**
3. **`Rasa-X-Machina_TianxiaOS_Committee_Pitch_2026.mp4`** (Main 4-Beat Committee Pitch Video WITH Slide & Cockpit Cut-Ins) -> Upload to Unlisted YouTube/Vimeo or Dealum Video Link
4. **`Collins_Takem_Personal_Founder_Story_No_Slides_2026.mp4`** (Personal Founder Story Video — ZERO Slide Cut-Ins) -> Optional secondary founder link in Step 2 / Step 9
5. **`Rasa-X-Machina_OU_Capitalisation_Table_2026.csv`** (and `.xlsx` / `.pdf` — clean `EUR` `€1.00` / `€2,500.00`, zero `$` signs, zero `**` asterisks!) -> Upload in **Step 7 (Finance) → Cap table**
6. **`01_Estonian_Startup_Committee_Statutory_Verification_Brief_179423.pdf`** -> Upload in **Step 9 (Other) → Additional files**
7. **`02_TianxiaOS_Architecture_Security_GDPRpp_and_SBOM_Attestation.pdf`** -> Upload in **Step 9 (Other) → Additional files**
8. **`03_Rasa-X-Machina_OU_Cap_Table_Tallinn_IP_and_TalTech_Hiring_Plan.pdf`** -> Upload in **Step 9 (Other) → Additional files**
9. **`Rasa-X-Machina_Founder_Video_Script_v6_2026.pdf`** -> Transcript & visual reference companion for your recorded 4-beat pitch video

---

## 7 Surgical Zero-Data-Loss Field Fixes (Authentic Frontline-to-Founder Alignment)

1. **Step 1 (Overview) → `Company logo` & `Website`**:
   - Upload `rasa_x_machina_logo.svg` (replaces generic `"R"` avatar).
   - Keep Website `https://rasaxmachina.com` (and mention `https://rasaxmachina.com/estonia` + `https://github.com/Tianxia-Core/tianxiaos-releases` in Step 9).
2. **Step 2 (Team) → `Phone`, `Relevant experience` (442 / 500 chars) & `Other commitments` (194 chars)**:
   - Ensure `Phone` inside the private Dealum form includes the `+372` country code prefix (`+372 [REDACTED — never publish raw phone digits on public web/git; public relay: https://rasaxmachina.com/whatsapp]`).
   - Paste into `Relevant experience` (Authentic Frontline-to-Founder trajectory):
     ```text
     3+ yrs architecting tianxiaOS & self-hosting AI compiler harnesses (KAI³, Pari, RASOOM, DSS-14), preceded by 10+ yrs on the technical support & incident-triage front lines at Blockchain.com, SQUIRE & CoinLedger—diagnosing ledger drift, payment stalls & API failures under 50x volatility spikes. Pursuing an asynchronous half-time Dual Major in Pure Math & CS (SUNY, 4.0 GPA) to ground frontline pragmatism in formal mathematical rigor.
     ```
   - Paste into `Do any key team members have other business or educational commitments that may limit their involvement?`:
     ```text
     No limiting commitments. I pursue an asynchronous, half-time online Dual Major in Pure Math & CS (SUNY, 4.0 GPA) outside work hours, directly feeding tianxiaOS's formal methods and R&D velocity.
     ```
3. **Step 2 (Team) → `What are the three things you're focusing on as a CEO?` (962 / 1,000 chars)**:
   ```text
   My primary focus as CEO spans commercial pipeline conversion, Estonian deep-tech scaling, and product delivery:

   1. Commercial Pipeline & RGU Conversion: Converting our 20-company B2B/B2G pipeline (e.g., Dust.tt, E2B, Lakera AI, DefSecIntel) into paid 48-hour diagnostic sprints (€1,000–€1,450) and 2-week microVM deployments (€7,500–€12,500), generating ~92% margin cash flow while deploying automated Revenue Generation Units (RGUs).

   2. Estonian Corporate Anchoring, IP & Funding: Incorporating Rasa-X-Machina OÜ in Tallinn upon Committee approval, securing the Startup TRP, and filing 5 provisional patents locally alongside the EIS / Tehnopol €120k–€170k DeepTech grant and NATO DIANA cohort.

   3. Universal Runtime & Packaging Readiness: Scaling our live 4-node TianxiaOS substrate (TOON/TRON compression, 79.6% LLM OpEx cut, GDPR++ <50ms PQ cryptoshredding, signed .deb/.rpm/AppImage/Nix/.exe/.apk releases) for EU AI Act & NIS2 compliance.
   ```
4. **Step 5 (Market) → `Unique value proposition` & `Competitive advantage`**:
   - Highlights `TOON/TRON/TEC` 50%–67% syntactic compression, `seL4` + `Nanos` tmpfs isolation, `RASOOM` zero-copy ring buffers, and **Frontline Failure Forensics** from Blockchain.com, SQUIRE, and CoinLedger.
5. **Step 7 (Finance) → `Pre-money valuation (€)` & `Cap table`**:
   - Enter **`2500000`** (Tranche 1 Bridge) or **`10000000`** (Tier-2 Institutional Pre-Seed Cap) consistent with your chosen tranche in `What pre-money valuation are you expecting in the current funding round? (€)`.
   - Replace the Cap Table attachment with **`Rasa-X-Machina_OU_Capitalisation_Table_2026.csv`** (clean 4-row EUR CSV, not the MHTML snapshot).
6. **Step 8 (Milestones) — Consistent 12-Month Inflection Gates**:
   - Anchors Q4 2026 Tallinn OÜ incorporation + 5 provisional patents -> Q1 2027 10 enterprise design partners -> Q2 2027 TalTech/UT systems engineering hires -> Q3 2027 NATO DIANA & Foundation CR14 validation.
7. **Step 9 (Other) → 5 Patentable Innovations (495 / 500 chars) + Upload the 3 Statutory Brief PDFs & Video Link**:
   - Paste the 5 patentable innovations (`Constructal Sine-Meander Router`, `Veritas & Aeon SLB Paging`, `RASOOM Tala Ring Buffers`, `TOON/TRON/TEC Compilers`, `SRM Tri-Modal Attestation`), upload `01_...pdf`, `02_...pdf`, and `03_...pdf` under **Additional files**, paste your pitch video link, and click **Save** (or **Submit** when ready).
"""


def build_x_svgs() -> list[tuple[Path, Path, int, int]]:
    X_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    av_rxm = X_ASSETS_DIR / "x_avatar_rasaxmachina.svg"
    av_tx = X_ASSETS_DIR / "x_avatar_tianxiaos.svg"
    bn_rxm = X_ASSETS_DIR / "x_banner_rasaxmachina_1500x500.svg"
    bn_tx = X_ASSETS_DIR / "x_banner_tianxiaos_1500x500.svg"

    if LOGO_SRC.exists():
        shutil.copyfile(LOGO_SRC, av_rxm)
    else:
        av_rxm.write_text(LOGO_SVG_FALLBACK, encoding="utf-8")

    av_tx.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <rect width="512" height="512" fill="#06070c"/>
  <circle cx="256" cy="256" r="210" fill="none" stroke="#7c5cff" stroke-width="10" opacity="0.85"/>
  <polygon points="256,68 418,162 418,350 256,444 94,350 94,162" fill="none" stroke="#00f59b" stroke-width="8"/>
  <text x="256" y="278" text-anchor="middle" fill="#ffffff" font-family="monospace" font-weight="900" font-size="116">TX</text>
  <text x="256" y="338" text-anchor="middle" fill="#22d3ee" font-family="monospace" font-weight="700" font-size="30">seL4 · NixOS</text>
</svg>""",
        encoding="utf-8",
    )

    bn_rxm.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 500" width="1500" height="500">
  <defs><linearGradient id="g1" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#06070d"/><stop offset="55%" stop-color="#110d24"/><stop offset="100%" stop-color="#07151f"/></linearGradient></defs>
  <rect width="1500" height="500" fill="url(#g1)"/>
  <text x="110" y="185" fill="#ffffff" font-family="system-ui,sans-serif" font-weight="800" font-size="64" letter-spacing="2">RASA-X-MACHINA</text>
  <text x="110" y="245" fill="#c084fc" font-family="monospace" font-weight="600" font-size="25">Sovereign Autonomous Systems · Cyber-Defense · Cryptographic Reality Ledgers</text>
  <text x="110" y="320" fill="#00f59b" font-family="monospace" font-weight="700" font-size="22">79.6% LLM OpEx Cut  |  0.00% HTTP 429  |  GDPR++ &lt;50ms PQ Shred  |  42 Markets</text>
  <text x="110" y="385" fill="#94a3b8" font-family="monospace" font-size="20">rasaxmachina.com  ·  @tianxiaos  ·  Founded by @coltakrasax  ·  Tallinn, Estonia</text>
</svg>""",
        encoding="utf-8",
    )

    bn_tx.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 500" width="1500" height="500">
  <defs><linearGradient id="g2" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#05060b"/><stop offset="50%" stop-color="#0c1926"/><stop offset="100%" stop-color="#130d29"/></linearGradient></defs>
  <rect width="1500" height="500" fill="url(#g2)"/>
  <text x="110" y="185" fill="#ffffff" font-family="system-ui,sans-serif" font-weight="800" font-size="66" letter-spacing="1">TianxiaOS v8.7.0</text>
  <text x="110" y="245" fill="#22d3ee" font-family="monospace" font-weight="600" font-size="25">seL4 Microkit · LionsOS · Nanos Unikernels · NixOS Flakes · 7 Hussar Legions</text>
  <text x="110" y="320" fill="#00f59b" font-family="monospace" font-weight="700" font-size="22">Signed Native Packages: .deb · .rpm · AppImage · flake.nix · .tar.gz · .exe · .apk</text>
  <text x="110" y="385" fill="#94a3b8" font-family="monospace" font-size="20">github.com/Tianxia-Core/tianxiaos-releases  ·  By @rasaxmachina &amp; @coltakrasax</text>
</svg>""",
        encoding="utf-8",
    )
    return [
        (av_rxm, X_ASSETS_DIR / "x_avatar_rasaxmachina_512.png", 512, 512),
        (av_tx, X_ASSETS_DIR / "x_avatar_tianxiaos_512.png", 512, 512),
        (bn_rxm, X_ASSETS_DIR / "x_banner_rasaxmachina_1500x500.png", 1500, 500),
        (bn_tx, X_ASSETS_DIR / "x_banner_tianxiaos_1500x500.png", 1500, 500),
    ]


def main() -> int:
    work_dir = TIANXIA / "docs" / "estonia_committee_packet"
    work_dir.mkdir(parents=True, exist_ok=True)
    html_src_dir = work_dir / "_html_masters"
    html_src_dir.mkdir(parents=True, exist_ok=True)

    if LOGO_SRC.exists():
        shutil.copyfile(LOGO_SRC, work_dir / "rasa_x_machina_logo.svg")

    build_cap_table_files(work_dir)
    (work_dir / "Rasa-X-Machina_Founder_Video_Script_v6_2026.md").write_text(VIDEO_SCRIPT_MD, encoding="utf-8")
    (work_dir / "DEALUM_179423_ZERO_DATA_LOSS_UPDATE_GUIDE.md").write_text(DEALUM_GUIDE_MD, encoding="utf-8")

    # HTML masters for Chromium --print-to-pdf + individual 1920x1080 slide renders for video B-roll
    deck_master = render_pitch_deck_html()
    (html_src_dir / "deck.html").write_text(deck_master, encoding="utf-8")
    slides_1080_dir = html_src_dir / "slides_1080p"
    slides_1080_dir.mkdir(parents=True, exist_ok=True)
    logo_slide = load_logo_inline(38)
    for s_idx, s in enumerate(SLIDES_DATA, 1):
        kpi_cards = "".join(
            f"""<div class="kpi"><div class="kv">{html.escape(v)}</div><div class="kl">{html.escape(l)}</div><div class="ks">{html.escape(sub)}</div></div>"""
            for v, l, sub in s["kpis"]
        )
        col_cards = "".join(
            f"""<div class="panel"><h3>{html.escape(ct)}</h3><ul>{"".join(f"<li>{html.escape(b)}</li>" for b in bullets)}</ul></div>"""
            for ct, bullets in s["cols"]
        )
        single_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; }}
  html {{ zoom: 1.5; overflow: hidden; background: #07080e; }}
  body {{ margin: 0; padding: 0; background: #07080e; color: #f8fafc; font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; overflow: hidden; }}
  .slide {{
    width: 1280px; height: 720px; padding: 38px 52px 30px; position: relative; overflow: hidden;
    display: flex; flex-direction: column;
    background: radial-gradient(circle at 88% 12%, rgba(124,92,255,0.20), transparent 42%),
                radial-gradient(circle at 12% 88%, rgba(34,211,238,0.13), transparent 40%), #07080e;
    border: 1px solid rgba(124,92,255,0.28);
  }}
  .top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.10); }}
  .brand {{ display: flex; align-items: center; gap: 12px; }}
  .b1 {{ font-weight: 800; font-size: 15px; letter-spacing: 0.08em; color: #ffffff; }}
  .b2 {{ font-family: ui-monospace, monospace; font-size: 11px; color: #22d3ee; letter-spacing: 0.06em; margin-top: 2px; }}
  .pill {{ font-family: ui-monospace, monospace; font-size: 11.5px; font-weight: 700; color: #00f59b; background: rgba(0,245,155,0.10); border: 1px solid rgba(0,245,155,0.38); padding: 6px 14px; border-radius: 999px; }}
  h1 {{ font-size: 33px; line-height: 1.14; margin: 0 0 10px; letter-spacing: -0.02em; color: #ffffff; }}
  .lead {{ font-size: 15.5px; color: #cbd5e1; margin: 0 0 20px; line-height: 1.45; max-width: 1120px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 18px; }}
  .kpi {{ background: rgba(14,16,28,0.92); border: 1px solid rgba(124,92,255,0.36); border-radius: 14px; padding: 15px 16px; }}
  .kv {{ font-family: ui-monospace, monospace; font-size: 25px; font-weight: 800; color: #00f59b; margin-bottom: 4px; }}
  .kl {{ font-size: 12.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #f8fafc; margin-bottom: 5px; }}
  .ks {{ font-size: 12px; color: #94a3b8; line-height: 1.38; }}
  .cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; flex: 1; }}
  .panel {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(34,211,238,0.26); border-radius: 14px; padding: 18px 20px; }}
  .panel h3 {{ margin: 0 0 10px; font-size: 16px; color: #c084fc; letter-spacing: 0.01em; }}
  .panel ul {{ margin: 0; padding-left: 18px; color: #e2e8f0; font-size: 13.8px; line-height: 1.55; }}
  .panel li {{ margin-bottom: 8px; }}
  .foot {{ display: flex; justify-content: space-between; align-items: center; padding-top: 10px; margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); font-family: ui-monospace, monospace; font-size: 11px; color: #94a3b8; }}
</style></head><body><section class="slide">
  <header class="top">
    <div class="brand">{logo_slide}<div><div class="b1">RASA-X-MACHINA // TIANXIAOS</div><div class="b2">{html.escape(s['tag'])}</div></div></div>
    <div class="pill">DEALUM #179423 · SLIDE {s_idx:02d} / 12</div>
  </header>
  <h1>{html.escape(s['title'])}</h1>
  <p class="lead">{html.escape(s['lead'])}</p>
  <div class="kpis">{kpi_cards}</div>
  <div class="cols">{col_cards}</div>
  <footer class="foot">
    <span>PROPOSED ENTITY UPON COMMITTEE APPROVAL: RASA-X-MACHINA OÜ (TALLINN)</span>
    <span>BUILD LAW v5.0 SEALED · GDPR++ v2030.4 · rasaxmachina.com/estonia</span>
  </footer>
</section></body></html>"""
        (slides_1080_dir / f"slide_{s_idx:02d}.html").write_text(single_html, encoding="utf-8")

    cap_html = render_a4_doc_html(
        "CLEAN EUR CAP TABLE · ÄRISEADUSTIK § 148",
        "RASA-X-MACHINA OÜ (Proposed) — Capitalisation Table & Two-Tranche Model",
        "Prepared for Estonian Startup Committee Dealum Application #179423. Strict EUR single-currency schedule (zero prior dilutive debt).",
        """
        <h2>1. Incorporation Share Capital Baseline (Upon Startup Committee Approval)</h2>
        <table>
          <tr><th>Shareholder Name</th><th>Role / Title</th><th>Share Class</th><th>Shares</th><th>Par (EUR)</th><th>Nominal Capital</th><th>Ownership</th><th>Voting</th></tr>
          <tr><td><strong>Collins Eyong Takem-Manga-Bechem</strong></td><td>Founder &amp; Principal Systems Architect</td><td>Ordinary / Common</td><td>2,500</td><td>€1.00</td><td>€2,500.00</td><td>100.00%</td><td>100.00%</td></tr>
          <tr><td>Unallocated Tallinn ESOP Pool</td><td>Reserved for Key TalTech / Tartu Hires</td><td>Options Pool (Post-Approval)</td><td>0</td><td>€0.00</td><td>€0.00</td><td>0.00%</td><td>0.00%</td></tr>
          <tr><td><strong>TOTAL ISSUED UPON INCORPORATION</strong></td><td><strong>Proposed RASA-X-MACHINA OÜ (Tallinn)</strong></td><td><strong>Ordinary</strong></td><td><strong>2,500</strong></td><td><strong>€1.00</strong></td><td><strong>€2,500.00</strong></td><td><strong>100.00%</strong></td><td><strong>100.00%</strong></td></tr>
        </table>
        <div class="box"><strong>Statutory Governance Note:</strong> Registering with full <strong>€2,500.00 EUR</strong> nominal share capital under Estonian Commercial Code (<em>Äriseadustik</em> § 148) eliminates the unpaid-capital shareholder liability reserve, establishes immediate institutional bankability, and assigns 100% of proprietary TianxiaOS IP cleanly into the Estonian entity upon approval.</div>
        <h2>2. Disciplined Two-Tranche Capital &amp; ESOP Roadmap (EUR)</h2>
        <table>
          <tr><th>Stage</th><th>Instrument</th><th>Pre-Money / Cap</th><th>Target Capital</th><th>Post-Stage Split</th></tr>
          <tr><td><strong>Stage 0: Incorporation</strong></td><td>Ordinary Shares</td><td>€2,500 Nominal</td><td>€2,500.00</td><td>Founder 100.0%</td></tr>
          <tr><td><strong>Tranche 1: Estonian Bridge (Dealum #179423)</strong></td><td>Convertible Note / SAFE + 10% ESOP</td><td>€2,500,000 Pre-Money</td><td>€150,000 – €300,000 (+ €170k Tehnopol/EIS Non-Dilutive Grant)</td><td>Founder ~81.0% · ESOP 10.0% · Bridge ~9.0%</td></tr>
          <tr><td><strong>Tranche 2: Institutional Seed Expansion</strong></td><td>Preferred / SAFE</td><td>€10,000,000 Cap</td><td>€1,500,000 – €2,500,000</td><td>Founder ~67.5% · ESOP 10.0% · Investors ~22.5%</td></tr>
        </table>
        """,
    )
    (html_src_dir / "cap_table.html").write_text(cap_html, encoding="utf-8")

    brief01_html = render_a4_doc_html(
        "ADDITIONAL FILE 01 · STATUTORY BRIEF",
        "Estonian Aliens Act (VMS § 100¹) — 60-Second Committee Verification Matrix",
        "Prepared for the 7 Voting Organizations of the Estonian Startup Committee evaluating Dealum Application #179423.",
        """
        <div class="box"><strong>Pre-Approval Transparency Statement:</strong> Dealum Application <code>#179423</code> is actively under Startup Committee consideration prior to incorporating <strong>RASA-X-MACHINA OÜ</strong> in Tallinn. Every technical benchmark, 4-node European cluster, signed multi-OS release, and payment rail below is live today and independently verifiable without login walls.</div>
        <h2>1. Statutory Criteria Mapping (Välismaalaste seadus § 100¹)</h2>
        <table>
          <tr><th>Statutory Criterion</th><th>Production Proof Implemented Today</th><th>1-Click Live Verification URL</th></tr>
          <tr><td><strong>1. Technology-Based &amp; Innovative Deep-Tech Moat</strong></td><td>Polyglot seL4/LionsOS/NixOS microVM substrate; 4-Tier Inference Waterfall cutting LLM OpEx by <strong>79.6%</strong>; <strong>0.00% HTTP 429</strong> across 2,722 events; <strong>GDPR++ &lt;50ms</strong> Post-Quantum Cryptoshredding; 7 Hussar Sentinel Legions.</td><td><code>https://rasaxmachina.com/estonia</code><br/><code>https://rasaxmachina.com/api/v1/hussar/status</code></td></tr>
          <tr><td><strong>2. Global Scalability &amp; Zero-Friction Distribution</strong></td><td>28 interactive web apps localized across <strong>42 global markets, 25 full-copy languages (incl. Eesti), and 29 currencies</strong> + <strong>7 signed native OS executable formats</strong> (<code>.deb</code>, <code>.rpm</code>, <code>AppImage</code>, <code>flake.nix</code>, <code>.tar.gz</code>, <code>.exe</code>, <code>.apk</code>).</td><td><code>https://github.com/Tianxia-Core/tianxiaos-releases</code><br/><code>https://rasaxmachina.com/#executables</code></td></tr>
          <tr><td><strong>3. Repeatable High-Margin Business Model</strong></td><td>21 live Stripe SKUs across 6 payment rails: 92%-margin 48h diagnostic sprints (€1k–€1.45k) converting into 88%-margin node SaaS (€150–€450/mo + 15% savings share) &amp; €80k–€250k B2G contracts; €0.00 Merkle discrepancy.</td><td><code>https://pay.rasaxmachina.com/</code><br/><code>https://rasaxmachina.com/api/v1/ledger/verify</code></td></tr>
          <tr><td><strong>4. Direct Contribution to Estonia's Startup Ecosystem</strong></td><td>Founder already residing in Tallinn; anchors 3 deep-tech patent families in Estonia (advancing Startup Estonia's 60% IP target); hires Rust/seL4 engineers from TalTech &amp; Univ. of Tartu; integrates with Tehnopol, CR14 &amp; NATO DIANA.</td><td><code>https://rasaxmachina.com/collins</code><br/><code>https://rasaxmachina.com/vrtti</code></td></tr>
        </table>
        <h2>2. Alignment with All 7 Startup Committee Voting Organizations</h2>
        <table>
          <tr><th>Organization</th><th>Direct Institutional Synergy</th></tr>
          <tr><td><strong>Startup Estonia &amp; Tehnopol</strong></td><td>Advances the 500 Deep-Tech Startup &amp; 60% IP 2030 goals; purpose-built for Tehnopol Cyber Accelerator, €170k DeepTech Network &amp; NATO DIANA Estonian cohort.</td></tr>
          <tr><td><strong>Superangel, EstBAN &amp; SWG</strong></td><td>Disciplined €150k–€300k initial bridge @ €2.5M pre-money on clean 100% founder EUR cap table, backed by immediate 92%-margin B2B diagnostic cashflow.</td></tr>
          <tr><td><strong>Founders Society &amp; Garage48</strong></td><td>Frontline-to-Founder pedigree: 10+ yrs FinTech incident triage &amp; ledger forensics (Blockchain.com, CoinLedger, SQUIRE) → 3+ yrs architecting TianxiaOS (live 4-node OS, GTK4 GUI, 9-tab Rust TUI &amp; 32-repo GitHub estate) solo at 10x–20x velocity.</td></tr>
        </table>
        """,
    )
    (html_src_dir / "brief01.html").write_text(brief01_html, encoding="utf-8")

    brief02_html = render_a4_doc_html(
        "ADDITIONAL FILE 02 · ARCHITECTURE, GDPR++ & SBOM",
        "TianxiaOS Technical Architecture, Security Audit, GDPR++ & Signed SBOM Attestation",
        "Cryptographic verification dossier for technical evaluators, CISOs, and defence reviewers.",
        """
        <h2>1. Polyglot Architecture &amp; Verified Runtime Benchmarks (v8.7.0)</h2>
        <table>
          <tr><th>Subsystem</th><th>Implementation &amp; Language Resonance</th><th>Measured Production Telemetry</th></tr>
          <tr><td><strong>4-Tier Inference Waterfall</strong></td><td>C/AVX2 System-1 pre-filter + BitNet b1.58 ternary CPU + VUDA Vulkan + Constructal Router</td><td><strong>70.6%–79.6% OpEx cut</strong>; 7.2–14.0ms local filter; <strong>0.00% HTTP 429</strong> across 2,722 events</td></tr>
          <tr><td><strong>Faery Fortress &amp; MANAS</strong></td><td>Rust AF_XDP wire arrestor + Vogel Aeroelastic deception + Unicode tag smuggling shield</td><td><strong>11.40 Mpps (&lt;3.8 μs)</strong> wire cut; escalates attacker scan cost €23.55 → <strong>&gt;€1,295</strong></td></tr>
          <tr><td><strong>GDPR++ Horizon Engine</strong></td><td>Per-subject ephemeral <code>XChaCha20-Poly1305 + ML-KEM-1024</code> envelope key destruction</td><td><strong>&lt;50 ms</strong> cryptographic erasure + SHA-256 Merkle receipt (3–5 yrs ahead of EU GDPR/CPRA)</td></tr>
          <tr><td><strong>Hussar 7 Sentinel Legions &amp; DB Nexus</strong></td><td>7 continuous patrol legions + <code>graph.sqlite3</code> relational fabric across 28 WAL SQLite DBs</td><td><strong>7/7 Legions GREEN</strong>; <code>1,023</code> FFPs, <code>1,409</code> nodes, <code>3,390</code> FK-verified edges</td></tr>
        </table>
        <h2>2. Universal 7-Format Multi-OS Executables &amp; Offline Signature Verification</h2>
        <div class="box">
          All release packages are published at <code>https://github.com/Tianxia-Core/tianxiaos-releases/releases/tag/v8.7.0</code> and <code>https://rasaxmachina.com/releases/</code> with CycloneDX 1.5 <code>SBOM.cdx.json</code> and detached OpenSSL Ed25519 signatures:<br/>
          • <strong>Debian / Ubuntu:</strong> <code>tianxiaos_8.7.0_amd64.deb</code>, <code>tianxiaos_8.7.0_arm64.deb</code><br/>
          • <strong>RHEL / Fedora:</strong> <code>tianxiaos-8.7.0-1.x86_64.rpm</code>, <code>tianxiaos-8.7.0-1.aarch64.rpm</code><br/>
          • <strong>Universal Portable Linux:</strong> <code>TianxiaOS-8.7.0-x86_64.AppImage</code>, <code>TianxiaOS-8.7.0-aarch64.AppImage</code>, <code>.tar.gz</code><br/>
          • <strong>Declarative Nix Flake:</strong> <code>nix run github:Tianxia-Core/tianxiaos-releases</code> (<code>flake.nix</code>)<br/>
          • <strong>Windows &amp; Android:</strong> <code>tianxia-v8.7.0-windows-x86_64.exe</code> &amp; RSA-4096 v2/v3 signed <code>TianxiaOS-Sovereign-v8.7.0-android.apk</code><br/>
          • <strong>Verify Offline:</strong> <code>openssl pkeyutl -verify -pubin -inkey RELEASE_SIGNING_KEY.pub.pem -rawin -in SHA256SUMS -sigfile SHA256SUMS.sig</code>
        </div>
        """,
    )
    (html_src_dir / "brief02.html").write_text(brief02_html, encoding="utf-8")

    brief03_html = render_a4_doc_html(
        "ADDITIONAL FILE 03 · TALLINN IP, CAP TABLE & HIRING",
        "RASA-X-MACHINA OÜ (Proposed) — Tallinn IP Assignment, Fiscal & TalTech R&D Plan",
        "Corporate governance, intellectual property anchoring, and Estonian workforce expansion schedule (2026–2028).",
        """
        <h2>1. Clean Estonian Incorporation &amp; Sovereign IP Assignment</h2>
        <div class="box">Upon Startup Committee approval of Dealum Application <code>#179423</code>, founder <strong>Collins Eyong Takem-Manga-Bechem</strong> will immediately incorporate <strong>RASA-X-MACHINA OÜ</strong> in Tallinn with <strong>€2,500.00 EUR</strong> paid-in nominal share capital (2,500 Ordinary Shares @ €1.00 par, 100% founder-owned, zero debt) and execute an irrevocable Assignment of Intellectual Property anchoring TianxiaOS and five provisional patent families in the Republic of Estonia: (1) <em>Constructal Sine-Meander Multi-Model Flow Routing</em>, (2) <em>Veritas &amp; Aeon SLB Weight-Space Paging</em>, (3) <em>RASOOM Tala-Paced seL4 Ring Buffers</em>, (4) <em>TOON/TRON/TEC Syntactic Compression</em>, and (5) <em>SRM Tri-Modal Acoustic-Spatial Hardware Attestation</em>.</div>
        <h2>2. Tallinn Engineering Hiring &amp; Estonian Fiscal Contribution Forecast</h2>
        <table>
          <tr><th>Phase</th><th>Tallinn R&amp;D Headcount &amp; University Collaboration</th><th>Target Revenue &amp; Estonian Tax Impact</th></tr>
          <tr><td><strong>Phase 1 (Q4 2026 – Q1 2027)</strong></td><td>Principal Architect (Tallinn) + 10% ESOP establishment; joint capstone/research outreach with <strong>TalTech</strong> Dept. of Software Science &amp; <strong>Univ. of Tartu</strong> cryptography lab.</td><td>€15k–€25k/mo B2B diagnostic &amp; SaaS run-rate; direct Estonian VAT, social tax &amp; payroll tax contributions.</td></tr>
          <tr><td><strong>Phase 2 (Q2 – Q4 2027)</strong></td><td>Hire <strong>2 full-time Tallinn Systems Engineers</strong> (Rust / seL4 / eBPF) leveraging Estonia's 50% R&amp;D employee income-tax grant &amp; Tehnopol DeepTech cohort.</td><td>€45k–€75k/mo ARR across 25+ enterprise nodes; high-wage Estonian social &amp; income tax generation.</td></tr>
          <tr><td><strong>Phase 3 (2028)</strong></td><td>Expand Tallinn engineering &amp; NATO DIANA / Foundation CR14 cyber-defense delivery team to <strong>6–8 specialists</strong> in Tallinn.</td><td><strong>&gt;€1.2M+ ARR</strong> (75%+ EBITDA margin) high-value software &amp; dual-use cyber export from Estonia.</td></tr>
        </table>
        """,
    )
    (html_src_dir / "brief03.html").write_text(brief03_html, encoding="utf-8")

    video_html = render_a4_doc_html(
        "FOUNDER PITCH VIDEO SCRIPT · 2:30 TIMECODED",
        "Rasa-X-Machina // TianxiaOS — 2:30 Committee Pitch Video Script (v6.0)",
        "Teleprompter-ready narrative (~365 words @ 145 WPM) with live B-roll cues for Dealum Application #179423.",
        "<div class='box' style='white-space:pre-wrap;font-size:9.3pt;line-height:1.52'>"
        + html.escape(VIDEO_SCRIPT_MD)
        + "</div>",
    )
    (html_src_dir / "video_script.html").write_text(video_html, encoding="utf-8")

    x_jobs = build_x_svgs()

    # Render all PDFs & PNGs on latitude-lan via Headless Chromium in a single SSH batch!
    remote_tmp = "/tmp/tx_dossier_render"
    subprocess.run(["ssh", "latitude-lan", f"rm -rf {remote_tmp} && mkdir -p {remote_tmp}/x {remote_tmp}/slides_1080p"], check=True, timeout=20)
    subprocess.run(
        ["scp", "-q", *map(str, html_src_dir.glob("*.html")), f"latitude-lan:{remote_tmp}/"],
        check=True,
        timeout=30,
    )
    subprocess.run(
        ["scp", "-q", *map(str, (html_src_dir / "slides_1080p").glob("*.html")), f"latitude-lan:{remote_tmp}/slides_1080p/"],
        check=True,
        timeout=30,
    )
    subprocess.run(
        ["scp", "-q", *[str(s) for s, _, _, _ in x_jobs], f"latitude-lan:{remote_tmp}/x/"],
        check=True,
        timeout=30,
    )

    remote_script = f"""set +e
CH=/run/current-system/sw/bin/chromium
for pair in \\
  "deck.html:Rasa-X-Machina_TianxiaOS_Pitch_Deck_2026.pdf" \\
  "cap_table.html:Rasa-X-Machina_OU_Capitalisation_Table_2026.pdf" \\
  "video_script.html:Rasa-X-Machina_Founder_Video_Script_v6_2026.pdf" \\
  "brief01.html:01_Estonian_Startup_Committee_Statutory_Verification_Brief_179423.pdf" \\
  "brief02.html:02_TianxiaOS_Architecture_Security_GDPRpp_and_SBOM_Attestation.pdf" \\
  "brief03.html:03_Rasa-X-Machina_OU_Cap_Table_Tallinn_IP_and_TalTech_Hiring_Plan.pdf"; do
  in_f="${{pair%%:*}}"
  out_f="${{pair##*:}}"
  "$CH" --headless --disable-gpu --no-sandbox --disable-extensions --no-pdf-header-footer \\
    --print-to-pdf="{remote_tmp}/$out_f" "file://{remote_tmp}/$in_f" >/dev/null 2>&1
done
for shtml in {remote_tmp}/slides_1080p/slide_*.html; do
  spng="${{shtml%.html}}.png"
  "$CH" --headless --disable-gpu --no-sandbox --disable-extensions --hide-scrollbars --window-size=1920,1080 \\
    --screenshot="$spng" "file://$shtml" >/dev/null 2>&1
done
"$CH" --headless --disable-gpu --no-sandbox --disable-extensions --hide-scrollbars --window-size=1920,1080 \\
  --virtual-time-budget=2500 --screenshot="{remote_tmp}/slides_1080p/live_cockpit_1080p.png" "http://127.0.0.1:8081/cockpit" >/dev/null 2>&1
"$CH" --headless --disable-gpu --no-sandbox --disable-extensions --hide-scrollbars --window-size=1920,1080 \\
  --virtual-time-budget=2500 --screenshot="{remote_tmp}/slides_1080p/live_estonia_1080p.png" "http://127.0.0.1:8081/estonia" >/dev/null 2>&1
"$CH" --headless --disable-gpu --no-sandbox --disable-extensions --window-size=512,512 --screenshot="{remote_tmp}/x/x_avatar_rasaxmachina_512.png" "file://{remote_tmp}/x/x_avatar_rasaxmachina.svg" >/dev/null 2>&1
"$CH" --headless --disable-gpu --no-sandbox --disable-extensions --window-size=512,512 --screenshot="{remote_tmp}/x/x_avatar_tianxiaos_512.png" "file://{remote_tmp}/x/x_avatar_tianxiaos.svg" >/dev/null 2>&1
"$CH" --headless --disable-gpu --no-sandbox --disable-extensions --window-size=1500,500 --screenshot="{remote_tmp}/x/x_banner_rasaxmachina_1500x500.png" "file://{remote_tmp}/x/x_banner_rasaxmachina_1500x500.svg" >/dev/null 2>&1
"$CH" --headless --disable-gpu --no-sandbox --disable-extensions --window-size=1500,500 --screenshot="{remote_tmp}/x/x_banner_tianxiaos_1500x500.png" "file://{remote_tmp}/x/x_banner_tianxiaos_1500x500.svg" >/dev/null 2>&1
ls -la {remote_tmp}/*.pdf {remote_tmp}/slides_1080p/*.png | head -n 30
"""
    res = subprocess.run(["ssh", "latitude-lan", remote_script], capture_output=True, text=True, timeout=150)
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr, file=sys.stderr)

    subprocess.run(["scp", "-q", f"latitude-lan:{remote_tmp}/*.pdf", f"{work_dir}/"], check=True, timeout=45)
    subprocess.run(["scp", "-q", f"latitude-lan:{remote_tmp}/x/*.png", f"{X_ASSETS_DIR}/"], check=True, timeout=30)
    SLIDES_PNG_OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(["scp", "-q", f"latitude-lan:{remote_tmp}/slides_1080p/*.png", f"{SLIDES_PNG_OUT}/"], check=True, timeout=45)

    # Copy all deliverables across all 3 target directories + /sdcard/Download X assets subfolder
    deliverables = [
        "rasa_x_machina_logo.svg",
        "Rasa-X-Machina_TianxiaOS_Pitch_Deck_2026.pdf",
        "Rasa-X-Machina_OU_Capitalisation_Table_2026.csv",
        "Rasa-X-Machina_OU_Capitalisation_Table_2026.xlsx",
        "Rasa-X-Machina_OU_Capitalisation_Table_2026.pdf",
        "Rasa-X-Machina_Founder_Video_Script_v6_2026.md",
        "Rasa-X-Machina_Founder_Video_Script_v6_2026.pdf",
        "01_Estonian_Startup_Committee_Statutory_Verification_Brief_179423.pdf",
        "02_TianxiaOS_Architecture_Security_GDPRpp_and_SBOM_Attestation.pdf",
        "03_Rasa-X-Machina_OU_Cap_Table_Tallinn_IP_and_TalTech_Hiring_Plan.pdf",
        "DEALUM_179423_ZERO_DATA_LOSS_UPDATE_GUIDE.md",
    ]
    for dest_dir in OUT_DIRS[1:]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        is_public_web_dir = (dest_dir.name == "dossier")
        for fname in deliverables:
            if is_public_web_dir and fname.endswith(".md"):
                continue
            src = work_dir / fname
            if src.exists():
                shutil.copyfile(src, dest_dir / fname)

    dl_x = Path("./downloads/Estonia_Dealum_179423_Submission_Ready/X_Social_Brand_Kit")
    dl_x.mkdir(parents=True, exist_ok=True)
    for f in X_ASSETS_DIR.iterdir():
        if f.is_file():
            shutil.copyfile(f, dl_x / f.name)

    print(json.dumps({"ok": True, "generated_files": deliverables}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
