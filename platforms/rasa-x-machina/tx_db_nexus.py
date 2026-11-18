#!/usr/bin/env python3
# ffp: FFP-DB-NEXUS data-science python
"""
tx_db_nexus.py — Cross-Database Maintenance & Relational Interconnectivity Engine.

Mahavidya Domains:
  - 09-Matangi (Polyglot FFP AST/Header Discovery & Language Fitness Telemetry)
  - 13-Mahasarasvati (Pure Knowledge, Cross-DB Relational Graph & Provenance Audit)
  - 14-Paramasiva (Unified Sovereign Substrate State & WAL Health Enforcement)

Constructs, populates, maintains, and interconnects the TianxiaOS Relational Fabric:
  1. ffp_registry.sqlite3      — ffp_units + ffp_language_stats across tianxia/ & TianxiaOS/
  2. icp_profiles.sqlite3      — icp_segments (7 Primary Buyer Archetypes + 111 Enterprise ICPs + Collector)
  3. niche_intelligence.sqlite3 — niches, rgu_matrix (41 RGUs), market_locales (42 markets / 25 langs / 29 currencies), evergreen_signals
  4. graph.sqlite3             — db_catalog (25+ SQLite DBs), nexus_nodes, nexus_edges with FOREIGN KEYS ON
                                 linking FFP <-> RGU(41) <-> SKU(22) <-> Subdomain(28) <-> ICP(119) <->
                                 Niche(12) <-> Market(42)/Language(25)/Currency(29) <-> GitHub Repo(35) <-> Mesh Node(5)
  5. Universal Health Pass     — PRAGMA journal_mode=WAL, synchronous=NORMAL, foreign_keys=ON,
                                 integrity_check, optimize across all discovered SQLite DBs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import socket
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

THIS_DIR = Path(__file__).resolve().parent
REPO_DIR = THIS_DIR.parent
WORKSPACE_DIR = REPO_DIR.parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

LOG = logging.getLogger("tx_db_nexus")
if not LOG.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )

REVISION = "TX-DB-NEXUS-1.0.0"

FFP_HEADER_RE = re.compile(
    r"^(?:#|//|/\*+|<!--|--|;)\s*ffp:\s*([A-Za-z0-9_.:-]+)\s+([A-Za-z0-9_/-]+)\s+([A-Za-z0-9_+#-]+)",
    re.IGNORECASE,
)

# Canonical 35 GitHub Repositories in Tianxia-Core (verified via GitHub API)
TIANXIA_CORE_REPOS: List[Tuple[str, str, str, str, str]] = [
    ("TianxiaOS", "PRIVATE", "Nix/Rust/C", "RGU-sovereign-substrate", "latitude-tianxia"),
    (".github", "PUBLIC", "Markdown", "RGU-operators-manual", "tianxia-relay"),
    ("tianxia-mobile", "PRIVATE", "Kotlin/Rust", "RGU-fortress-early-access", "pixel8pro"),
    ("secrets-vault", "PRIVATE", "Rust/Python", "RGU-fortress-early-access", "latitude-tianxia"),
    ("007-scanner", "PRIVATE", "Rust/Python", "RGU-aegis-smb", "latitude-tianxia"),
    ("nimbus2", "PRIVATE", "TypeScript/Python", "RGU-rgu-portfolio-service", "tianxia-relay"),
    ("fortress-core", "PRIVATE", "Rust/eBPF", "RGU-fortress-early-access", "latitude-tianxia"),
    ("ego-hardware-interfaces", "PRIVATE", "C/Zig", "RGU-rtl-sdr-appliance", "latitude-tianxia"),
    ("autarchi-sdr-toolkit", "PRIVATE", "Rust/C", "RGU-rtl-sdr-appliance", "latitude-tianxia"),
    ("precognitive-churn-arrestor", "PRIVATE", "Python/Julia", "RGU-forecast-api", "latitude-tianxia"),
    ("phoenix-oracle-crm", "PRIVATE", "TypeScript/Python", "RGU-iso-merchant-agentic", "latitude-tianxia"),
    ("calypso-barter-exchange", "PRIVATE", "Rust/TypeScript", "RGU-token-marketplace", "tianxia-relay"),
    ("jivascriptocle-whitepaper", "PRIVATE", "LaTeX/Nix", "RGU-kai3-codex", "tianxia-relay"),
    ("framura-sdk-portal", "PRIVATE", "TypeScript/Rust", "RGU-tools-marketplace", "tianxia-relay"),
    ("jetlag-arbitrage-engine", "PRIVATE", "Rust/Julia", "RGU-cross-venue-arb", "latitude-tianxia"),
    ("horizon-weave-artefacts", "PRIVATE", "Nix/Bash", "RGU-asura-matrix", "latitude-tianxia"),
    ("kamadhenu-legal-engine", "PRIVATE", "OCaml/Python", "RGU-underwriting-pack", "latitude-tianxia"),
    ("honeytoken-feed-api", "PRIVATE", "Rust/Go", "RGU-honeytoken-api", "tianxia-relay"),
    ("moat-watch-metrics", "PRIVATE", "Go/Python", "RGU-substrate-research-feed", "latitude-tianxia"),
    ("karma-gov-portal", "PRIVATE", "TypeScript/OCaml", "RGU-sovereign-substrate", "tianxia-relay"),
    ("legion-orchestrator-matrix", "PRIVATE", "Rust/Python", "RGU-vrtti-sprint", "latitude-tianxia"),
    ("genesis-malware-lab", "PRIVATE", "C/Rust", "RGU-aegis-smb", "latitude-tianxia"),
    ("kamadhenu-product-forge", "PRIVATE", "Python/TypeScript", "RGU-blueprint-onepager", "latitude-tianxia"),
    ("karma-development-tui", "PRIVATE", "Rust", "RGU-tools-marketplace", "pixel8pro"),
    ("aether-sovereign-suite", "PRIVATE", "Rust/Nix", "RGU-sovereign-substrate", "latitude-tianxia"),
    ("cardinalis-fintech-core", "PRIVATE", "Rust/Go", "RGU-iso-merchant-agentic", "latitude-tianxia"),
    ("crescendo-wealth-matrix", "PRIVATE", "Julia/Python", "RGU-yield-as-service", "latitude-tianxia"),
    ("fiscus-treasury-nexus", "PRIVATE", "Rust/Solidity", "RGU-stablecoin-basis", "latitude-tianxia"),
    ("pep-governor", "PRIVATE", "OCaml/Rust", "RGU-substrate-api", "latitude-tianxia"),
    ("ananta-smriti-engine", "PRIVATE", "Rust/Python", "RGU-substrate-research-feed", "latitude-tianxia"),
    ("aegis9-hyper-visor", "PRIVATE", "Rust/C", "RGU-aegis-smb", "latitude-tianxia"),
    ("phoenix-core-crypto", "PRIVATE", "Rust/Zig", "RGU-ghost-recovery", "latitude-tianxia"),
    ("phantom-mesh-fabric", "PRIVATE", "Go/Rust", "RGU-fortress-early-access", "tianxia-relay"),
    ("global-proxy-engine", "PRIVATE", "Go/Python", "RGU-signal-x402-api", "tianxia-relay"),
    ("tianxia-unbound-os", "PRIVATE", "Nix", "RGU-sovereign-substrate", "latitude-tianxia"),
]

# Canonical 5 Mesh Nodes
MESH_NODES: List[Dict[str, Any]] = [
    {
        "node_id": "NODE-latitude-tianxia",
        "hostname": "latitude-tianxia",
        "tailscale_ip": "${TX_HUB_HOST:-127.0.0.1}",
        "lan_ip": "<TX_LAN_IPV4>",
        "role": "sovereign_hub_nixos",
        "os": "NixOS 25.11",
        "expected_online": True,
    },
    {
        "node_id": "NODE-tianxia-relay",
        "hostname": "tianxia-relay",
        "tailscale_ip": "10.0.99.254",
        "public_ip": "<TX_RELAY_IPV4>",
        "role": "european_pq_edge_relay",
        "os": "Ubuntu 24.04 LTS (Caddy + Rosenpass + WireGuard)",
        "expected_online": True,
    },
    {
        "node_id": "NODE-pixel8pro",
        "hostname": "pixel8pro",
        "tailscale_ip": "127.0.0.1",
        "role": "mobile_command_termux",
        "os": "Android 16 / Termux",
        "expected_online": True,
    },
    {
        "node_id": "NODE-poco-x5-pro-5g",
        "hostname": "poco-x5-pro-5g",
        "tailscale_ip": "127.0.0.1",
        "role": "mobile_mesh_sentinel",
        "os": "Android / Tailscale Mesh",
        "expected_online": True,
    },
    {
        "node_id": "NODE-xps13-tianxia",
        "hostname": "xps13-tianxia",
        "tailscale_ip": "127.0.0.1",
        "role": "deferred_cold_standby_laptop",
        "os": "Linux Standby Node (Deferred / Exponential Backoff)",
        "expected_online": False,
    },
]

# 7 Primary Buyer Archetypes (explicitly mandated)
PRIMARY_BUYER_ARCHETYPES: List[Dict[str, Any]] = [
    {
        "icp_id": "ICP-ARCH-01",
        "tier_group": "ARCHETYPE_7",
        "rge_division": "RGE-SOVEREIGN",
        "name": "Seed-Series B AI CTOs",
        "demographic_target": "Technical co-founders and Seed–Series B AI CTOs migrating off fragile cloud LLM wrappers to deterministic sovereign inference.",
        "pain_points": "Runaway GPU/API burn, prompt-injection liability, vendor lock-in, non-reproducible agent deployments.",
        "primary_language_resonance": "Rust / Nix / Mojo",
        "vertical_domain_path": "ai.infrastructure.sovereign_cto",
        "productized_module": "SUB-SOV",
        "skus": ["SKU-TX-01", "SKU-TX-05", "SKU-TX-08", "SKU-TX-20", "SKU-TX-21"],
        "subdomains": ["rasaxmachina.com", "substrate.rasaxmachina.com", "vrtti.rasaxmachina.com", "cockpit.rasaxmachina.com"],
        "jurisdictions": ["US", "EE", "GB", "DE", "SG", "CA", "FR", "SE", "CH", "AU"],
    },
    {
        "icp_id": "ICP-ARCH-02",
        "tier_group": "ARCHETYPE_7",
        "rge_division": "RGE-SOVEREIGN",
        "name": "FinOps/Platform Leads",
        "demographic_target": "Cloud FinOps directors, SRE leads, and platform engineering heads enforcing MIF+40/+50 infrastructure cost compression.",
        "pain_points": "Cloud egress rent-seeking, idle token quota waste, unmonitored Kubernetes spend, lack of 4-way ledger reconciliation.",
        "primary_language_resonance": "Go / Rust / Nix",
        "vertical_domain_path": "enterprise.finops.platform_engineering",
        "productized_module": "FOR-FIN",
        "skus": ["SKU-TX-07", "SKU-TX-10", "SKU-TX-11", "SKU-TX-15", "SKU-TX-20"],
        "subdomains": ["cockpit.rasaxmachina.com", "tokens.rasaxmachina.com", "tools.rasaxmachina.com", "ledger.rasaxmachina.com"],
        "jurisdictions": ["US", "DE", "GB", "NL", "EE", "SE", "NO", "CH", "SG", "JP"],
    },
    {
        "icp_id": "ICP-ARCH-03",
        "tier_group": "ARCHETYPE_7",
        "rge_division": "RGE-SENTINEL",
        "name": "CISOs/Red-Teamers",
        "demographic_target": "Enterprise CISOs, SecOps architects, and offensive security red-team leads requiring non-bypassable eBPF/virtwl containment.",
        "pain_points": "Supply-chain RCEs, credential exfiltration, zero-day C2 lateral movement, LLM jailbreaks and tag-smuggling attacks.",
        "primary_language_resonance": "Rust / OCaml / eBPF-C",
        "vertical_domain_path": "cybersecurity.defense.ciso_redteam",
        "productized_module": "AEG-SEC",
        "skus": ["SKU-TX-05", "SKU-TX-16", "SKU-TX-18", "SKU-TX-20", "SKU-TX-21"],
        "subdomains": ["fortress.rasaxmachina.com", "radar.rasaxmachina.com", "vault.rasaxmachina.com", "aegis.rasaxmachina.com"],
        "jurisdictions": ["EE", "US", "GB", "DE", "CH", "FI", "FR", "SG", "IL", "JP"],
    },
    {
        "icp_id": "ICP-ARCH-04",
        "tier_group": "ARCHETYPE_7",
        "rge_division": "RGE-SENTINEL",
        "name": "Sovereign/NATO Defence Integrators",
        "demographic_target": "Baltic/EU/NATO dual-use defence primes, air-gapped enclave integrators, and RF/SDR situational awareness operators.",
        "pain_points": "Foreign cloud jurisdiction exposure, post-quantum key compromise, air-gap update verification, tactical edge telemetry latency.",
        "primary_language_resonance": "Rust / Nix / C",
        "vertical_domain_path": "defense.sovereign.nato_integrators",
        "productized_module": "AEG-DEF",
        "skus": ["SKU-TX-07", "SKU-TX-18", "SKU-TX-20", "SKU-TX-21"],
        "subdomains": ["estonia.rasaxmachina.com", "fortress.rasaxmachina.com", "sdr.rasaxmachina.com", "vault.rasaxmachina.com"],
        "jurisdictions": ["EE", "FI", "SE", "NO", "PL", "LT", "LV", "DE", "GB", "US"],
    },
    {
        "icp_id": "ICP-ARCH-05",
        "tier_group": "ARCHETYPE_7",
        "rge_division": "RGE-CHAPEL",
        "name": "Cross-Border High-Volume Merchants",
        "demographic_target": "Cross-border e-commerce operators, digital goods platforms, and high-volume merchants mitigating false INR disputes and underwriting friction.",
        "pain_points": "Payment processor freezes, false Item-Not-Received chargebacks, opaque multi-carrier TTH delays, multi-currency FX leakage.",
        "primary_language_resonance": "TypeScript / Go / Rust",
        "vertical_domain_path": "commerce.cross_border.high_volume_merchants",
        "productized_module": "MUR-MER",
        "skus": ["SKU-TX-14", "SKU-TX-15", "SKU-TX-17", "SKU-TX-19", "SKU-TX-20"],
        "subdomains": ["tracer.rasaxmachina.com", "pay.rasaxmachina.com", "merchant.rasaxmachina.com", "names.rasaxmachina.com"],
        "jurisdictions": ["EE", "GB", "US", "SG", "HK", "AE", "DE", "NL", "BR", "MX"],
    },
    {
        "icp_id": "ICP-ARCH-06",
        "tier_group": "ARCHETYPE_7",
        "rge_division": "RGE-ALPHA",
        "name": "Quantitative/DeFi Treasuries",
        "demographic_target": "Algorithmic trading desks, crypto family offices, and autonomous DeFi treasuries seeking hash-logged basis, funding-rate, and yield signals.",
        "pain_points": "Unverified backtest curve-fitting, execution slippage, smart-contract pool rug risk, dormant fork/UTXO asset leakage.",
        "primary_language_resonance": "Rust / Julia / Solidity",
        "vertical_domain_path": "quant.defi.autonomous_treasuries",
        "productized_module": "ALP-TRS",
        "skus": ["SKU-TX-04", "SKU-TX-06", "SKU-TX-09", "SKU-TX-12", "SKU-TX-13", "SKU-TX-16"],
        "subdomains": ["alpha.rasaxmachina.com", "yield.rasaxmachina.com", "forecast.rasaxmachina.com", "ledger.rasaxmachina.com", "x402.rasaxmachina.com"],
        "jurisdictions": ["CH", "SG", "HK", "AE", "US", "GB", "EE", "JP", "KR", "KY"],
    },
    {
        "icp_id": "ICP-ARCH-07",
        "tier_group": "ARCHETYPE_7",
        "rge_division": "RGE-SOVEREIGN",
        "name": "Institutional Startup/Gov Evaluators",
        "demographic_target": "Startup Estonia / Dealum committee evaluators, sovereign innovation agencies, venture diligence partners, and regulatory auditors.",
        "pain_points": "Vaporware claims without live telemetry, GDPR/AI Act non-compliance, opaque corporate governance, lack of cryptographic audit trails.",
        "primary_language_resonance": "Rust / TypeScript / Nix",
        "vertical_domain_path": "institutional.governance.startup_evaluators",
        "productized_module": "VER-GOV",
        "skus": ["SKU-TX-01", "SKU-TX-07", "SKU-TX-15", "SKU-TX-20", "SKU-TX-21"],
        "subdomains": ["estonia.rasaxmachina.com", "rasaxmachina.com", "collins.rasaxmachina.com", "ledger.rasaxmachina.com"],
        "jurisdictions": ["EE", "EU", "DE", "FR", "FI", "SE", "NL", "GB", "SG", "CH"],
    },
]

# 6 Named Core Registry ICPs + ICP-COLLECTOR + 5 Portfolio Personas (= 12 named personas; 6+5+100 = 111 Enterprise Registry)
NAMED_ENTERPRISE_ICPS: List[Dict[str, Any]] = [
    {
        "icp_id": "ICP-SOVEREIGN-OP",
        "tier_group": "NAMED_CORE_6",
        "rge_division": "RGE-SOVEREIGN",
        "name": "Sovereign Infrastructure Operator",
        "demographic_target": "Self-hosted NixOS/Linux systems architects running zero-cloud sovereign compute clusters.",
        "pain_points": "Hyperscaler lock-in, telemetry snooping, brittle imperative server configs.",
        "primary_language_resonance": "Nix / Rust / C",
        "vertical_domain_path": "sovereign.substrate.operators",
        "productized_module": "SUB-CORE",
        "skus": ["SKU-TX-01", "SKU-TX-07", "SKU-TX-08", "SKU-TX-11", "SKU-TX-18", "SKU-TX-21"],
        "subdomains": ["substrate.rasaxmachina.com", "fortress.rasaxmachina.com", "cockpit.rasaxmachina.com"],
        "jurisdictions": ["EE", "DE", "CH", "SE", "NO", "FI", "US", "CA"],
    },
    {
        "icp_id": "ICP-TRADER",
        "tier_group": "NAMED_CORE_6",
        "rge_division": "RGE-ALPHA",
        "name": "Systematic Quantitative & Arb Trader",
        "demographic_target": " systematic spot/perps arbitrageurs and predictive signal consumers.",
        "pain_points": "Signal latency, unverified PnL claims, funding-rate regime shifts.",
        "primary_language_resonance": "Rust / Julia / Mojo",
        "vertical_domain_path": "quant.trading.arbitrage",
        "productized_module": "ALP-ARB",
        "skus": ["SKU-TX-04", "SKU-TX-09", "SKU-TX-12", "SKU-TX-13", "SKU-TX-16"],
        "subdomains": ["alpha.rasaxmachina.com", "yield.rasaxmachina.com", "forecast.rasaxmachina.com", "x402.rasaxmachina.com"],
        "jurisdictions": ["SG", "CH", "US", "GB", "HK", "JP", "KR", "AE"],
    },
    {
        "icp_id": "ICP-MERCHANT",
        "tier_group": "NAMED_CORE_6",
        "rge_division": "RGE-CHAPEL",
        "name": "High-Risk & Cross-Border Digital Merchant",
        "demographic_target": "Global merchants needing multi-rail checkout, underwriting dossiers, and Murua TTH dispute defense.",
        "pain_points": "MID termination, chargeback ratios >1%, delayed cross-border fulfilment visibility.",
        "primary_language_resonance": "TypeScript / Go / Python",
        "vertical_domain_path": "fintech.merchant.acquiring",
        "productized_module": "AUR-PAY",
        "skus": ["SKU-TX-14", "SKU-TX-15", "SKU-TX-17"],
        "subdomains": ["tracer.rasaxmachina.com", "merchant.rasaxmachina.com", "pay.rasaxmachina.com"],
        "jurisdictions": ["EE", "GB", "US", "SG", "AE", "NL", "CY", "MT"],
    },
    {
        "icp_id": "ICP-DEFENDER",
        "tier_group": "NAMED_CORE_6",
        "rge_division": "RGE-SENTINEL",
        "name": "Active Cyber-Defense & SecOps Engineer",
        "demographic_target": "Blue-team defenders deploying honeytokens, CISA KEV threat radar, and Aethervault secret isolation.",
        "pain_points": "Alert fatigue, lateral movement post-compromise, exposed service credentials.",
        "primary_language_resonance": "Rust / eBPF-C / OCaml",
        "vertical_domain_path": "cybersecurity.sentinel.secops",
        "productized_module": "AEG-9",
        "skus": ["SKU-TX-18", "SKU-TX-20", "SKU-TX-21"],
        "subdomains": ["radar.rasaxmachina.com", "fortress.rasaxmachina.com", "vault.rasaxmachina.com", "aegis.rasaxmachina.com"],
        "jurisdictions": ["EE", "US", "GB", "DE", "FR", "CH", "SE", "FI"],
    },
    {
        "icp_id": "ICP-BUILDER",
        "tier_group": "NAMED_CORE_6",
        "rge_division": "RGE-CHAPEL",
        "name": "Polyglot Systems & Agentic Builder",
        "demographic_target": "Principal engineers, indie founders, and agent builders shipping high-margin autonomous software.",
        "pain_points": "Framework bloat, slow MVP-to-revenue cycles, ATS resume/contract positioning bottlenecks.",
        "primary_language_resonance": "Rust / TypeScript / Python",
        "vertical_domain_path": "engineering.builders.polyglot",
        "productized_module": "CHP-BLD",
        "skus": ["SKU-TX-01", "SKU-TX-02", "SKU-TX-03", "SKU-TX-05", "SKU-TX-06", "SKU-TX-11", "SKU-TX-20"],
        "subdomains": ["shop.rasaxmachina.com", "tools.rasaxmachina.com", "jobs.rasaxmachina.com", "vrtti.rasaxmachina.com"],
        "jurisdictions": ["US", "EE", "GB", "DE", "IN", "CA", "AU", "BR", "PL", "NG"],
    },
    {
        "icp_id": "ICP-INSTITUTION",
        "tier_group": "NAMED_CORE_6",
        "rge_division": "RGE-SENTINEL",
        "name": "Regulated Enterprise & Institutional Partner",
        "demographic_target": "Regulated financial, healthcare, and public-sector institutions requiring GDPR++ & DORA/NIS2 auditability.",
        "pain_points": "Compliance audit failures, opaque AI decisioning, third-party SaaS data residency violations.",
        "primary_language_resonance": "OCaml / Rust / Nix",
        "vertical_domain_path": "institutional.enterprise.regulated",
        "productized_module": "VER-INS",
        "skus": ["SKU-TX-15", "SKU-TX-17", "SKU-TX-18", "SKU-TX-20", "SKU-TX-21"],
        "subdomains": ["rasaxmachina.com", "estonia.rasaxmachina.com", "collins.rasaxmachina.com", "ledger.rasaxmachina.com"],
        "jurisdictions": ["EE", "DE", "FR", "CH", "GB", "US", "SG", "JP", "SE", "NO"],
    },
    {
        "icp_id": "ICP-FOUNDER",
        "tier_group": "PERSONA_5",
        "rge_division": "RGE-CHAPEL",
        "name": "Bootstrapped & Seed Technical Founder",
        "demographic_target": "Founders building capital-efficient autonomous revenue engines with 100% reinvestment discipline.",
        "pain_points": "Burn-rate exhaustion before PMF, scattered productization, weak pricing psychology.",
        "primary_language_resonance": "TypeScript / Rust / Python",
        "vertical_domain_path": "venture.founders.bootstrapped",
        "productized_module": "MIP-FND",
        "skus": ["SKU-TX-01", "SKU-TX-03", "SKU-TX-06", "SKU-TX-08", "SKU-TX-20"],
        "subdomains": ["rasaxmachina.com", "shop.rasaxmachina.com", "vrtti.rasaxmachina.com"],
        "jurisdictions": ["US", "EE", "GB", "SG", "DE", "CA", "AU", "IN"],
    },
    {
        "icp_id": "ICP-DEVELOPER",
        "tier_group": "PERSONA_5",
        "rge_division": "RGE-SOVEREIGN",
        "name": "Systems & Polyglot Protocol Developer",
        "demographic_target": "Low-level systems programmers adopting SLECO-SO++, KAI³ patterns, and x402 programmatic APIs.",
        "pain_points": "Dependency hell, fragile bash/container pipelines, unverified runtime boundaries.",
        "primary_language_resonance": "Rust / Zig / Nix",
        "vertical_domain_path": "engineering.developers.systems",
        "productized_module": "KAI-DEV",
        "skus": ["SKU-TX-04", "SKU-TX-05", "SKU-TX-07", "SKU-TX-11"],
        "subdomains": ["tools.rasaxmachina.com", "substrate.rasaxmachina.com", "x402.rasaxmachina.com"],
        "jurisdictions": ["US", "DE", "EE", "PL", "GB", "FR", "NL", "JP", "CA", "BR"],
    },
    {
        "icp_id": "ICP-OPERATIONS",
        "tier_group": "PERSONA_5",
        "rge_division": "RGE-SOVEREIGN",
        "name": "Autonomous Ops & Reliability Lead",
        "demographic_target": "DevOps, SecOps, and logistics operations leads running 24/7 unattended service fleets.",
        "pain_points": "Zombie daemons, silent cron failures, multi-node drift, incident MTTR.",
        "primary_language_resonance": "Go / Rust / Nix",
        "vertical_domain_path": "operations.sre.autonomous",
        "productized_module": "PAR-OPS",
        "skus": ["SKU-TX-07", "SKU-TX-08", "SKU-TX-14", "SKU-TX-15"],
        "subdomains": ["cockpit.rasaxmachina.com", "tracer.rasaxmachina.com", "status.rasaxmachina.com"],
        "jurisdictions": ["DE", "US", "GB", "EE", "NL", "SE", "SG", "AU"],
    },
    {
        "icp_id": "ICP-ENTERPRISE",
        "tier_group": "PERSONA_5",
        "rge_division": "RGE-SENTINEL",
        "name": "Enterprise Architecture & Procurement Buyer",
        "demographic_target": "VP Engineering and Enterprise Architecture committees commissioning turnkey sprints and sovereign audits.",
        "pain_points": "Multi-month consultancy bloat, lack of bounded SLA deliverables, security review bottlenecks.",
        "primary_language_resonance": "Rust / OCaml / TypeScript",
        "vertical_domain_path": "enterprise.procurement.turnkey",
        "productized_module": "VRT-ENT",
        "skus": ["SKU-TX-18", "SKU-TX-20", "SKU-TX-21"],
        "subdomains": ["collins.rasaxmachina.com", "vrtti.rasaxmachina.com", "fortress.rasaxmachina.com"],
        "jurisdictions": ["US", "DE", "GB", "CH", "FR", "EE", "SG", "AE", "SA", "JP"],
    },
    {
        "icp_id": "ICP-ANALYST",
        "tier_group": "PERSONA_5",
        "rge_division": "RGE-ALPHA",
        "name": "Quantitative & Threat Intelligence Analyst",
        "demographic_target": "Research analysts synthesizing arXiv, CISA KEV, DeFiLlama, and TimesFM time-series feeds.",
        "pain_points": "Fragmented OSINT feeds, noisy signal-to-action pipelines, lack of provenance hashing.",
        "primary_language_resonance": "Julia / Python / Rust",
        "vertical_domain_path": "intelligence.research.quant_osint",
        "productized_module": "int-ANA",
        "skus": ["SKU-TX-06", "SKU-TX-09", "SKU-TX-13"],
        "subdomains": ["radar.rasaxmachina.com", "alpha.rasaxmachina.com", "forecast.rasaxmachina.com"],
        "jurisdictions": ["US", "GB", "CH", "SG", "EE", "DE", "HK", "JP"],
    },
    {
        "icp_id": "ICP-COLLECTOR",
        "tier_group": "NAMED_EXTENDED",
        "rge_division": "RGE-CHAPEL",
        "name": "Digital Namespace & Scarce Handle Collector",
        "demographic_target": "Telegram Fragment handle investors, Web3 namespace syndicates, and OTC digital asset buyers.",
        "pain_points": "Counterparty escrow risk, centivector valuation opacity, sniping latency on unlocked handles.",
        "primary_language_resonance": "TypeScript / Rust / Solidity",
        "vertical_domain_path": "digital_assets.namespace.nomenagora",
        "productized_module": "NOM-OTC",
        "skus": ["SKU-TX-16", "SKU-TX-19"],
        "subdomains": ["names.rasaxmachina.com", "shop.rasaxmachina.com"],
        "jurisdictions": ["AE", "SG", "HK", "CH", "EE", "GB", "US", "KR"],
    },
]

# 12 Strategic Niches linking RGUs, Mechanism Classes (SR-004), and Subdomains
STRATEGIC_NICHES: List[Dict[str, Any]] = [
    {
        "niche_id": "NICHE-SOVEREIGN-SUBSTRATE",
        "name": "Sovereign NixOS & MicroVM Compute Substrate",
        "rge_division": "RGE-SOVEREIGN",
        "mechanism_class": "attestation",
        "avg_margin_pct": 94.0,
        "subdomains": ["rasaxmachina.com", "substrate.rasaxmachina.com", "cockpit.rasaxmachina.com", "estonia.rasaxmachina.com"],
        "summary": "Hermetic NixOS, Firecracker CoW microVMs, and zero-cloud MIF+50 operator infrastructure.",
    },
    {
        "niche_id": "NICHE-CYBER-FORTRESS",
        "name": "Zero-Trust eBPF Cyber-Defense & Secret Isolation",
        "rge_division": "RGE-SENTINEL",
        "mechanism_class": "attestation",
        "avg_margin_pct": 96.0,
        "subdomains": ["fortress.rasaxmachina.com", "radar.rasaxmachina.com", "vault.rasaxmachina.com", "aegis.rasaxmachina.com"],
        "summary": "Faery Fortress hardening, CISA KEV threat radar, honeytokens, and Aethervault secret custody.",
    },
    {
        "niche_id": "NICHE-QUANT-ARBITRAGE",
        "name": "Cross-Venue & Funding-Rate Quantitative Arbitrage",
        "rge_division": "RGE-ALPHA",
        "mechanism_class": "arbitrage",
        "avg_margin_pct": 92.5,
        "subdomains": ["alpha.rasaxmachina.com", "ledger.rasaxmachina.com"],
        "summary": "Hash-logged perps funding-rate, cross-venue spread, and triangular basis signal engines.",
    },
    {
        "niche_id": "NICHE-AUTOTREASURY-YIELD",
        "name": "DeFi Stablecoin Yield & Dormant UTXO Recovery",
        "rge_division": "RGE-ALPHA",
        "mechanism_class": "keeper",
        "avg_margin_pct": 91.0,
        "subdomains": ["yield.rasaxmachina.com", "ledger.rasaxmachina.com", "pay.rasaxmachina.com"],
        "summary": "TVL-gated stablecoin yield sleeves, EFEMERA receipts, and non-custodial fork-ghost recovery.",
    },
    {
        "niche_id": "NICHE-TIMESFM-INFERENCE",
        "name": "Sovereign Time-Series Forecasting & x402 Signal APIs",
        "rge_division": "RGE-ALPHA",
        "mechanism_class": "inference",
        "avg_margin_pct": 95.0,
        "subdomains": ["forecast.rasaxmachina.com", "x402.rasaxmachina.com", "api.rasaxmachina.com"],
        "summary": "Local TimesFM forecasting and HTTP 402 machine-to-machine micropayment inference endpoints.",
    },
    {
        "niche_id": "NICHE-MURUA-LOGISTICS",
        "name": "Cross-Border Bayesian Consignment Telemetry & Merchant Risk",
        "rge_division": "RGE-CHAPEL",
        "mechanism_class": "signal",
        "avg_margin_pct": 89.5,
        "subdomains": ["tracer.rasaxmachina.com", "merchant.rasaxmachina.com", "pay.rasaxmachina.com"],
        "summary": "Murua TTH carrier matrix, false INR chargeback defense, and merchant underwriting dossiers.",
    },
    {
        "niche_id": "NICHE-VRTTI-EXECUTIVE",
        "name": "Bounded Principal Systems Architecture Sprints (VRTTI)",
        "rge_division": "RGE-CHAPEL",
        "mechanism_class": "attestation",
        "avg_margin_pct": 88.0,
        "subdomains": ["vrtti.rasaxmachina.com", "collins.rasaxmachina.com", "jobs.rasaxmachina.com"],
        "summary": "72-hour to 5-day high-velocity architecture sprints, AST teardowns, and fractional principal retainers.",
    },
    {
        "niche_id": "NICHE-NOMENAGORA-NAMESPACE",
        "name": "Scarce Digital Namespace Valuation & OTC Escrow",
        "rge_division": "RGE-CHAPEL",
        "mechanism_class": "arbitrage",
        "avg_margin_pct": 93.0,
        "subdomains": ["names.rasaxmachina.com", "shop.rasaxmachina.com"],
        "summary": "Centivector 100-point lexical scoring, Fragment handle auctions, and TON ad-split syndication.",
    },
    {
        "niche_id": "NICHE-POLYGLOT-CODICES",
        "name": "Zero-Marginal-Cost Technical Codices & Operator Blueprints",
        "rge_division": "RGE-CHAPEL",
        "mechanism_class": "memory",
        "avg_margin_pct": 98.5,
        "subdomains": ["shop.rasaxmachina.com", "tools.rasaxmachina.com"],
        "summary": "KAI³ 117-pattern codex, Operator's Manual, 5K Blueprint, and polyglot CLI binary packs.",
    },
    {
        "niche_id": "NICHE-COMPUTE-TOKEN-EXCHANGE",
        "name": "Idle Compute & Quota Routing Marketplace",
        "rge_division": "RGE-SOVEREIGN",
        "mechanism_class": "keeper",
        "avg_margin_pct": 87.0,
        "subdomains": ["tokens.rasaxmachina.com", "relay.rasaxmachina.com"],
        "summary": "MIF compute-slot arbitrage and rights-cleared unused LLM quota routing.",
    },
    {
        "niche_id": "NICHE-RF-SDR-EDGE",
        "name": "Autonomous RF Spectrum & RTL-SDR Edge Appliances",
        "rge_division": "RGE-SENTINEL",
        "mechanism_class": "signal",
        "avg_margin_pct": 84.0,
        "subdomains": ["sdr.rasaxmachina.com", "radar.rasaxmachina.com"],
        "summary": "Turnkey RTL-SDR spectrum capture, ADS-B/AIS decoding, and local edge anomaly alerting.",
    },
    {
        "niche_id": "NICHE-VERITAS-MEMORY",
        "name": "Merkle Audit Ledgers & Institutional Knowledge Feeds",
        "rge_division": "RGE-SENTINEL",
        "mechanism_class": "memory",
        "avg_margin_pct": 96.5,
        "subdomains": ["ledger.rasaxmachina.com", "research.rasaxmachina.com", "docs.rasaxmachina.com"],
        "summary": "TetraLedger 4-way cryptographic reconciliation and institutional research provenance streams.",
    },
]

# Canonical SKU -> RGU & Subdomain Mapping (all 21 SKUs + SKU-TX-10B)
CANONICAL_SKUS: List[Dict[str, Any]] = [
    {"sku_id": "SKU-TX-01", "plan_id": "blueprint_5k", "name": "5K Sovereign Infrastructure Blueprint One-Pager", "eur": 9, "usd": 10, "rgu_id": "RGU-blueprint-onepager", "subdomain": "shop.rasaxmachina.com"},
    {"sku_id": "SKU-TX-02", "plan_id": "jobmatch_pwa", "name": "JobMatch PWA — ATS Role Alignment Pass", "eur": 9, "usd": 10, "rgu_id": "RGU-jobmatch-pwa", "subdomain": "jobs.rasaxmachina.com"},
    {"sku_id": "SKU-TX-03", "plan_id": "telegram_vip", "name": "Tianxia Daily Signal Broadcast Channel", "eur": 9, "usd": 10, "rgu_id": "RGU-paid-telegram", "subdomain": "alpha.rasaxmachina.com"},
    {"sku_id": "SKU-TX-04", "plan_id": "substrate_api", "name": "Substrate Intent API & x402 Credit Pack", "eur": 9, "usd": 10, "rgu_id": "RGU-substrate-api", "subdomain": "x402.rasaxmachina.com"},
    {"sku_id": "SKU-TX-05", "plan_id": "kai3_codex", "name": "KAI³ Architecture Codex — 117 Systems Patterns", "eur": 19, "usd": 21, "rgu_id": "RGU-kai3-codex", "subdomain": "shop.rasaxmachina.com"},
    {"sku_id": "SKU-TX-06", "plan_id": "asura_matrix", "name": "Quantitative Game-Theory & Capital Strategy Matrix", "eur": 19, "usd": 21, "rgu_id": "RGU-asura-matrix", "subdomain": "shop.rasaxmachina.com"},
    {"sku_id": "SKU-TX-07", "plan_id": "operators_manual", "name": "TianxiaOS Operator's Manual (180-Page PDF)", "eur": 29, "usd": 32, "rgu_id": "RGU-operators-manual", "subdomain": "substrate.rasaxmachina.com"},
    {"sku_id": "SKU-TX-08", "plan_id": "cockpit_pro", "name": "TianxiaOS Sovereign Cockpit Pro", "eur": 29, "usd": 32, "rgu_id": "RGU-rgu-portfolio-service", "subdomain": "cockpit.rasaxmachina.com"},
    {"sku_id": "SKU-TX-09", "plan_id": "alpha_pro", "name": "Cross-Venue Quantitative Signal Feed", "eur": 29, "usd": 32, "rgu_id": "RGU-arb-alpha-feed", "subdomain": "alpha.rasaxmachina.com"},
    {"sku_id": "SKU-TX-10", "plan_id": "token_market", "name": "Compute & API Quota Routing Exchange", "eur": 29, "usd": 32, "rgu_id": "RGU-token-marketplace", "subdomain": "tokens.rasaxmachina.com"},
    {"sku_id": "SKU-TX-10B", "plan_id": "substrate_sponsor", "name": "Sovereign Open-Source Substrate Patronage", "eur": 10, "usd": 11, "rgu_id": "RGU-substrate-sponsorship", "subdomain": "substrate.rasaxmachina.com"},
    {"sku_id": "SKU-TX-11", "plan_id": "tools_pack", "name": "Tianxia Polyglot CLI & Systems Toolkit (42 Binaries)", "eur": 49, "usd": 54, "rgu_id": "RGU-tools-marketplace", "subdomain": "tools.rasaxmachina.com"},
    {"sku_id": "SKU-TX-12", "plan_id": "hussar_arb", "name": "Multi-Venue Basis & Funding-Rate Analytics Suite", "eur": 49, "usd": 54, "rgu_id": "RGU-funding-rate-arb", "subdomain": "alpha.rasaxmachina.com"},
    {"sku_id": "SKU-TX-13", "plan_id": "timesfm_api", "name": "TimesFM Time-Series Forecasting API", "eur": 49, "usd": 54, "rgu_id": "RGU-forecast-api", "subdomain": "forecast.rasaxmachina.com"},
    {"sku_id": "SKU-TX-14", "plan_id": "murua_pro", "name": "Murua Logistics & Fulfilment SLA Tracer Pro", "eur": 79, "usd": 86, "rgu_id": "RGU-iso-merchant-agentic", "subdomain": "tracer.rasaxmachina.com"},
    {"sku_id": "SKU-TX-15", "plan_id": "tetraledger_team", "name": "TetraLedger 4-Way Reconciliation & Treasury Suite", "eur": 149, "usd": 162, "rgu_id": "RGU-rgu-portfolio-service", "subdomain": "ledger.rasaxmachina.com"},
    {"sku_id": "SKU-TX-16", "plan_id": "ghost_recovery", "name": "Deterministic Multi-Chain UTXO & Dormant Asset Audit", "eur": 149, "usd": 162, "rgu_id": "RGU-ghost-recovery", "subdomain": "yield.rasaxmachina.com"},
    {"sku_id": "SKU-TX-17", "plan_id": "underwriting_pack", "name": "Merchant Risk & Compliance Underwriting Dossier", "eur": 199, "usd": 216, "rgu_id": "RGU-underwriting-pack", "subdomain": "merchant.rasaxmachina.com"},
    {"sku_id": "SKU-TX-18", "plan_id": "fortress_node", "name": "Faery Fortress Zero-Trust Node License", "eur": 249, "usd": 270, "rgu_id": "RGU-fortress-early-access", "subdomain": "fortress.rasaxmachina.com"},
    {"sku_id": "SKU-TX-19", "plan_id": "nomenagora_otc", "name": "NomenAgora Digital Handle & Namespace Escrow", "eur": 450, "usd": 500, "rgu_id": "RGU-nomenagora-sniper-otc", "subdomain": "names.rasaxmachina.com"},
    {"sku_id": "SKU-TX-20", "plan_id": "vrtti_sprint", "name": "VRTTI 72-Hour Bounded Systems Architecture Sprint", "eur": 2250, "usd": 2500, "rgu_id": "RGU-vrtti-sprint", "subdomain": "vrtti.rasaxmachina.com"},
    {"sku_id": "SKU-TX-21", "plan_id": "vrtti_10k", "name": "Turnkey Sovereign Cluster & MicroVM Appliance Deployment", "eur": 9300, "usd": 10000, "rgu_id": "RGU-sovereign-substrate", "subdomain": "collins.rasaxmachina.com"},
]


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def is_hub_host() -> bool:
    h = socket.gethostname().lower()
    return "latitude" in h or (Path("/var/lib/tianxia/db").is_dir() and Path("/etc/NIXOS").exists())


def resolve_db_dir(explicit_dir: Optional[str] = None) -> Path:
    if explicit_dir:
        p = Path(explicit_dir)
    elif is_hub_host():
        p = Path("/var/lib/tianxia/db")
    else:
        p = REPO_DIR / "db"
    p.mkdir(parents=True, exist_ok=True)
    return p


def atomic_write_json(dest: Path, payload: Dict[str, Any], mode: int = 0o644) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=f".{dest.name}.", suffix=".tmp", dir=str(dest.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(raw)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp_name, mode)
        os.replace(tmp_name, str(dest))
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass


def connect_wal(db_path: Path, foreign_keys: bool = True) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=15.0)
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute(f"PRAGMA foreign_keys = {'ON' if foreign_keys else 'OFF'};")
    return conn


def infer_mahavidya_domain(ffp_id: str, ffp_class: str, file_path: str) -> str:
    low = f"{ffp_id} {ffp_class} {file_path}".lower()
    if any(k in low for k in ("nix", "declarative", "flake", "systemd")):
        return "14-Paramasiva"
    if any(k in low for k in ("ledger", "nexus", "graph", "registry", "audit", "veritas", "scour", "telemetry", "metrics")):
        return "13-Mahasarasvati"
    if any(k in low for k in ("power", "battery", "mobile", "sustenance", "queue")):
        return "12-Annapurna"
    if any(k in low for k in ("manas", "breaker", "arrest", "thermal", "watchdog", "hussar")):
        return "11-Pratyangira"
    if any(k in low for k in ("vm", "microvm", "firecracker", "cow", "provision", "rgu", "opportunity", "stripe", "x402", "billing")):
        return "10-Kamala"
    if any(k in low for k in ("ast", "macro", "nim", "parser", "i18n", "polyglot", "lang")):
        return "09-Matangi"
    if any(k in low for k in ("ebpf", "bpf", "virtwl", "acl", "proxy", "firewall", "net_guard", "gate")):
        return "08-Bagalamukhi"
    if any(k in low for k in ("secret", "vault", "quarantine", "crypto", "shield", "gdpr", "ghost")):
        return "07-Dhumavati"
    if any(k in low for k in ("shm", "ring", "wire-codec", "mmap", "broker", "uds")):
        return "06-Chhinnamasta"
    if any(k in low for k in ("security", "sweep", "cgroup", "seccomp", "sandbox", "aegis", "fortress")):
        return "05-Bhairavi"
    if any(k in low for k in ("vnc", "display", "seat", "topology", "subdomain")):
        return "04-Bhuvanesvari"
    if any(k in low for k in ("ui", "hud", "frontend", "cockpit", "css", "gtk", "wayland")):
        return "03-Tripura-Sundari"
    if any(k in low for k in ("mesh", "tailscale", "wireguard", "rosenpass", "relay", "transit")):
        return "02-Tara"
    if any(k in low for k in ("vacuum", "gc", "reap", "cleanup", "evict", "ephemeral")):
        return "01-Kali"
    class_defaults = {
        "concurrent-daemon": "06-Chhinnamasta",
        "wire-codec": "06-Chhinnamasta",
        "edge-agent": "09-Matangi",
        "capability-proxy": "08-Bagalamukhi",
        "state-machine": "08-Bagalamukhi",
        "compute-kernel": "10-Kamala",
        "kernel-interceptor": "08-Bagalamukhi",
        "declarative": "14-Paramasiva",
        "frontend": "03-Tripura-Sundari",
        "cockpit-pwa": "03-Tripura-Sundari",
        "crypto-signer": "07-Dhumavati",
        "ml-inference": "11-Pratyangira",
        "data-science": "13-Mahasarasvati",
        "content-pipeline": "09-Matangi",
        "contract": "10-Kamala",
        "io-edge": "02-Tara",
        "glue": "14-Paramasiva",
    }
    return class_defaults.get(ffp_class.lower(), "13-Mahasarasvati")


def infer_rgu_for_ffp(ffp_id: str, file_path: str, explicit_map: Dict[str, str]) -> str:
    if ffp_id in explicit_map:
        return explicit_map[ffp_id]
    low = f"{ffp_id} {file_path}".lower()
    keyword_to_rgu = [
        ("nomenagora", "RGU-nomenagora-sniper-otc"),
        ("murua", "RGU-iso-merchant-agentic"),
        ("tracer", "RGU-iso-merchant-agentic"),
        ("vrtti", "RGU-vrtti-sprint"),
        ("jobmatch", "RGU-jobmatch-pwa"),
        ("ghost", "RGU-ghost-recovery"),
        ("timesfm", "RGU-forecast-api"),
        ("forecast", "RGU-forecast-api"),
        ("x402", "RGU-signal-x402-api"),
        ("arb", "RGU-arb-alpha-feed"),
        ("funding", "RGU-funding-rate-arb"),
        ("yield", "RGU-yield-as-service"),
        ("tetraledger", "RGU-rgu-portfolio-service"),
        ("cockpit", "RGU-rgu-portfolio-service"),
        ("security", "RGU-fortress-early-access"),
        ("secret", "RGU-fortress-early-access"),
        ("aegis", "RGU-aegis-smb"),
        ("honeytoken", "RGU-honeytoken-api"),
        ("sdr", "RGU-rtl-sdr-appliance"),
        ("token", "RGU-token-marketplace"),
        ("telegram", "RGU-paid-telegram"),
        ("manual", "RGU-operators-manual"),
        ("kai3", "RGU-kai3-codex"),
        ("asura", "RGU-asura-matrix"),
        ("underwriting", "RGU-underwriting-pack"),
        ("scour", "RGU-substrate-research-feed"),
        ("opportunity", "RGU-rgu-portfolio-service"),
        ("nexus", "RGU-substrate-research-feed"),
        ("hussar", "RGU-fortress-early-access"),
        ("manas", "RGU-aegis-smb"),
        ("nixos", "RGU-sovereign-substrate"),
        ("tianxiaos", "RGU-sovereign-substrate"),
    ]
    for kw, rgu in keyword_to_rgu:
        if kw in low:
            return rgu
    return "RGU-sovereign-substrate"


def resonance_tier_for_lang(lang: str) -> str:
    l = lang.lower()
    tiers = {
        "rust": "SR-001 Tier-1 Infrastructure, Crypto & Security Buyers",
        "typescript": "SR-001 Tier-1 Operator Cockpits, Merchant Consoles & PWAs",
        "javascript": "SR-001 Tier-2 Browser/Edge Client Runtime",
        "nix": "SR-001 Tier-1 Reproducible Sovereign Infrastructure",
        "c": "SR-001 Tier-1 SIMD Compute Kernels & eBPF Interceptors",
        "go": "SR-001 Tier-1 Concurrent Network Relays & Proxies",
        "zig": "SR-001 Tier-1 Minimal Wire Codecs & Edge Binaries",
        "nim": "SR-001 Tier-1 Compile-Time AST & Macro Edge Agents",
        "ocaml": "SR-001 Tier-1 Formal Capability Firewalls & State Machines",
        "julia": "SR-001 Tier-1 Quantitative & Statistical Analytics",
        "mojo": "SR-001 Tier-1 High-Velocity ML Inference Kernels",
        "solidity": "SR-001 Tier-1 On-Chain Settlement & Vault Contracts",
        "python": "SR-001 Research, Data-Science & Offline Glue Bridges",
        "bash": "SR-001 SLECO-SO++ Orchestration & Content Pipelines",
    }
    return tiers.get(l, "SR-001 Polyglot Specialized Surface")


def load_explicit_ffp_to_rgu_map() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for candidate in (
        REPO_DIR / "docs" / "faery_fortress" / "registry.json",
        Path("/var/lib/tianxia/docs/faery_fortress/registry.json"),
    ):
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8", errors="ignore"))
                for rgu in data.get("rgus", []):
                    rid = rgu.get("id")
                    if not rid:
                        continue
                    for fid in rgu.get("ffps", []):
                        mapping[str(fid)] = str(rid)
                break
            except Exception:
                continue
    return mapping


def build_ffp_registry(db_dir: Path) -> Dict[str, Any]:
    db_path = db_dir / "ffp_registry.sqlite3"
    explicit_rgu_map = load_explicit_ffp_to_rgu_map()
    scan_roots: List[Path] = []
    for root in (REPO_DIR, WORKSPACE_DIR / "TianxiaOS", Path("/var/lib/tianxia")):
        if root.is_dir() and all(root.resolve() != r.resolve() for r in scan_roots):
            scan_roots.append(root)

    skip_dirs = {
        ".git", "node_modules", "__pycache__", ".venv", "venv", "target", "dist", "build",
        "backups", "sarva_samhita_vault", "persistence", "logs", "state", "db", "registries",
    }
    scan_exts = {
        ".py", ".rs", ".c", ".h", ".go", ".zig", ".nim", ".ml", ".mli", ".fs", ".jl",
        ".mojo", ".nix", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".sh", ".sol", ".html", ".css", ".sql",
    }

    now = utc_now()
    discovered: Dict[str, Tuple[str, str, str, str, str, str, int, str]] = {}

    # Preserve existing non-local peer entries (e.g., TianxiaOS entries synced onto hub) if path not locally present
    if db_path.is_file() and db_path.stat().st_size > 0:
        try:
            old_conn = sqlite3.connect(str(db_path), timeout=5.0)
            for row in old_conn.execute(
                "SELECT ffp_id, ffp_class, language, file_path, mahavidya_domain, rgu_id, sha256, line_count, verified_at FROM ffp_units"
            ):
                if not Path(row[3]).exists():
                    discovered[row[0]] = (row[1], row[2], row[3], row[4], row[5], row[6], int(row[7]), row[8])
            old_conn.close()
        except Exception:
            pass

    seen_realpaths: Set[str] = set()
    for root in scan_roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".tmp")]
            for fname in filenames:
                fp = Path(dirpath) / fname
                if fp.suffix.lower() not in scan_exts:
                    continue
                try:
                    rp = str(fp.resolve())
                    if rp in seen_realpaths:
                        continue
                    st = fp.stat()
                    if st.st_size == 0 or st.st_size > 2_500_000:
                        continue
                    raw_bytes = fp.read_bytes()
                except OSError:
                    continue
                seen_realpaths.add(rp)
                head_lines = raw_bytes[:2048].decode("utf-8", errors="ignore").splitlines()[:15]
                matched = None
                for hl in head_lines:
                    m = FFP_HEADER_RE.match(hl.strip())
                    if m:
                        matched = (m.group(1).strip(), m.group(2).strip().lower(), m.group(3).strip().lower())
                        break
                if not matched:
                    continue
                ffp_id, ffp_class, lang = matched
                sha256_hex = hashlib.sha256(raw_bytes).hexdigest()
                line_count = raw_bytes.count(b"\n") + (1 if raw_bytes and not raw_bytes.endswith(b"\n") else 0)
                try:
                    rel_display = str(fp.relative_to(WORKSPACE_DIR))
                except ValueError:
                    rel_display = str(fp)
                domain = infer_mahavidya_domain(ffp_id, ffp_class, rel_display)
                rgu_id = infer_rgu_for_ffp(ffp_id, rel_display, explicit_rgu_map)

                unique_id = ffp_id
                if unique_id in discovered and discovered[unique_id][2] != rel_display:
                    stem_tag = re.sub(r"[^A-Za-z0-9]+", "-", fp.stem).strip("-").upper()
                    unique_id = f"{ffp_id}::{stem_tag}"
                    idx = 2
                    while unique_id in discovered and discovered[unique_id][2] != rel_display:
                        unique_id = f"{ffp_id}::{stem_tag}-{idx}"
                        idx += 1

                discovered[unique_id] = (
                    ffp_class,
                    lang,
                    rel_display,
                    domain,
                    rgu_id,
                    sha256_hex,
                    line_count,
                    now,
                )

    conn = connect_wal(db_path, foreign_keys=True)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ffp_units (
                ffp_id TEXT PRIMARY KEY,
                ffp_class TEXT NOT NULL,
                language TEXT NOT NULL,
                file_path TEXT NOT NULL,
                mahavidya_domain TEXT NOT NULL,
                rgu_id TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                line_count INTEGER NOT NULL,
                verified_at TEXT NOT NULL
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ffp_units_rgu ON ffp_units(rgu_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ffp_units_lang ON ffp_units(language);")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ffp_language_stats (
                language TEXT PRIMARY KEY,
                unit_count INTEGER NOT NULL,
                total_lines INTEGER NOT NULL,
                primary_ffp_classes TEXT NOT NULL,
                market_resonance_tier TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute("DELETE FROM ffp_units;")
        conn.executemany(
            """
            INSERT INTO ffp_units (
                ffp_id, ffp_class, language, file_path, mahavidya_domain, rgu_id, sha256, line_count, verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            [(fid, *vals) for fid, vals in sorted(discovered.items())],
        )

        lang_agg: Dict[str, Dict[str, Any]] = {}
        for _, (fcls, lang, _, _, _, _, lcnt, _) in discovered.items():
            entry = lang_agg.setdefault(lang, {"count": 0, "lines": 0, "classes": set()})
            entry["count"] += 1
            entry["lines"] += lcnt
            entry["classes"].add(fcls)

        conn.execute("DELETE FROM ffp_language_stats;")
        conn.executemany(
            """
            INSERT INTO ffp_language_stats (
                language, unit_count, total_lines, primary_ffp_classes, market_resonance_tier, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            [
                (
                    lg,
                    st["count"],
                    st["lines"],
                    ",".join(sorted(st["classes"])),
                    resonance_tier_for_lang(lg),
                    now,
                )
                for lg, st in sorted(lang_agg.items(), key=lambda kv: (-kv[1]["count"], kv[0]))
            ],
        )
    conn.close()
    return {
        "db_path": str(db_path),
        "ffp_units_count": len(discovered),
        "languages_count": len(lang_agg),
    }


def _map_vertical_to_rge_and_resonance(vertical: str, module: str) -> Tuple[str, str, List[str], List[str], List[str]]:
    v = f"{vertical} {module}".lower()
    if any(k in v for k in ("fintech.payments", "merchant", "retail", "commerce", "logistics", "marketing", "legal", "media", "education")):
        return (
            "RGE-CHAPEL",
            "TypeScript / Go / Rust",
            ["SKU-TX-01", "SKU-TX-14", "SKU-TX-17", "SKU-TX-20"],
            ["tracer.rasaxmachina.com", "merchant.rasaxmachina.com", "pay.rasaxmachina.com", "vrtti.rasaxmachina.com"],
            ["EE", "GB", "US", "DE", "SG", "AE", "NL", "FR"],
        )
    if any(k in v for k in ("quant", "trading", "treasury", "crypto", "defi", "wealth", "insurance", "arbitrage")):
        return (
            "RGE-ALPHA",
            "Rust / Julia / Solidity",
            ["SKU-TX-06", "SKU-TX-09", "SKU-TX-12", "SKU-TX-13", "SKU-TX-16"],
            ["alpha.rasaxmachina.com", "yield.rasaxmachina.com", "forecast.rasaxmachina.com", "ledger.rasaxmachina.com"],
            ["CH", "SG", "US", "GB", "HK", "AE", "EE", "JP"],
        )
    if any(k in v for k in ("security", "compliance", "healthcare", "defense", "aerospace", "audit", "forensic", "aeg")):
        return (
            "RGE-SENTINEL",
            "Rust / OCaml / eBPF-C",
            ["SKU-TX-15", "SKU-TX-17", "SKU-TX-18", "SKU-TX-21"],
            ["fortress.rasaxmachina.com", "radar.rasaxmachina.com", "vault.rasaxmachina.com", "estonia.rasaxmachina.com"],
            ["EE", "DE", "CH", "US", "GB", "FI", "SE", "NO"],
        )
    return (
        "RGE-SOVEREIGN",
        "Rust / Nix / Go",
        ["SKU-TX-05", "SKU-TX-07", "SKU-TX-08", "SKU-TX-11", "SKU-TX-20"],
        ["substrate.rasaxmachina.com", "cockpit.rasaxmachina.com", "tools.rasaxmachina.com", "rasaxmachina.com"],
        ["EE", "DE", "US", "GB", "SE", "CH", "SG", "CA"],
    )


def parse_100_enterprise_icps() -> List[Dict[str, Any]]:
    candidates = (
        REPO_DIR / "docs" / "faery_fortress" / "registry_views" / "registry_icp.md",
        Path("/var/lib/tianxia/docs/faery_fortress/registry_views/registry_icp.md"),
    )
    parsed: List[Dict[str, Any]] = []
    for path in candidates:
        if not path.is_file():
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        blocks = re.split(r"^##\s+", raw, flags=re.MULTILINE)
        for blk in blocks[1:]:
            lines = [ln.strip() for ln in blk.splitlines() if ln.strip()]
            if not lines:
                continue
            head = lines[0]
            m = re.match(r"(ICP-\d{3})\s*(?:—|-)\s*(?:ICP-\d{3}\s*(?:—|-)\s*)?(.+)$", head)
            if not m:
                continue
            icp_id = m.group(1).strip()
            title = m.group(2).strip().rstrip(".")
            fields: Dict[str, str] = {}
            for ln in lines[1:]:
                if ln.startswith("- ") and ":" in ln:
                    k, v = ln[2:].split(":", 1)
                    fields[k.strip()] = v.strip()
            target = fields.get("enterprise_demographic_target", title)
            pains = fields.get("operational_pain_points", "Legacy operational friction and compliance overhead.")
            mod = fields.get("productized_module", "SUB-MOD")
            vpath = fields.get("vertical_domain_path", "enterprise.sovereign.general")
            rge, resonance, skus, subs, juris = _map_vertical_to_rge_and_resonance(vpath, mod)
            parsed.append(
                {
                    "icp_id": icp_id,
                    "tier_group": "ENTERPRISE_100",
                    "rge_division": rge,
                    "name": f"{icp_id}: {title}",
                    "demographic_target": target,
                    "pain_points": pains,
                    "primary_language_resonance": resonance,
                    "vertical_domain_path": vpath,
                    "productized_module": mod,
                    "skus": skus,
                    "subdomains": subs,
                    "jurisdictions": juris,
                }
            )
        if parsed:
            break

    # Deterministic fallback if run on an isolated host without registry_icp.md
    if len(parsed) < 100:
        existing_ids = {p["icp_id"] for p in parsed}
        divisions = ["RGE-SOVEREIGN", "RGE-SENTINEL", "RGE-CHAPEL", "RGE-ALPHA"]
        for i in range(1, 101):
            cid = f"ICP-{i:03d}"
            if cid in existing_ids:
                continue
            rge = divisions[(i - 1) % 4]
            _, resonance, skus, subs, juris = _map_vertical_to_rge_and_resonance(rge.lower(), f"MOD-{i:03d}")
            parsed.append(
                {
                    "icp_id": cid,
                    "tier_group": "ENTERPRISE_100",
                    "rge_division": rge,
                    "name": f"{cid}: Sovereign Enterprise Vertical #{i:03d}",
                    "demographic_target": f"Institutional {rge} vertical segment #{i:03d}",
                    "pain_points": "Infrastructure drift, audit opacity, high marginal SaaS spend.",
                    "primary_language_resonance": resonance,
                    "vertical_domain_path": f"enterprise.{rge.lower().replace('-', '_')}.v{i:03d}",
                    "productized_module": f"TX-MOD-{i:03d}",
                    "skus": skus,
                    "subdomains": subs,
                    "jurisdictions": juris,
                }
            )
    return sorted(parsed, key=lambda x: x["icp_id"])


def build_icp_profiles(db_dir: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    db_path = db_dir / "icp_profiles.sqlite3"
    now = utc_now()

    enterprise_100 = parse_100_enterprise_icps()
    all_icps: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for item in PRIMARY_BUYER_ARCHETYPES + NAMED_ENTERPRISE_ICPS + enterprise_100:
        if item["icp_id"] in seen:
            continue
        seen.add(item["icp_id"])
        all_icps.append(item)

    conn = connect_wal(db_path, foreign_keys=True)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS icp_segments (
                icp_id TEXT PRIMARY KEY,
                tier_group TEXT NOT NULL,
                rge_division TEXT NOT NULL,
                name TEXT NOT NULL,
                demographic_target TEXT NOT NULL,
                pain_points TEXT NOT NULL,
                primary_language_resonance TEXT NOT NULL,
                vertical_domain_path TEXT NOT NULL,
                productized_module TEXT NOT NULL,
                mapped_skus_json TEXT NOT NULL,
                mapped_subdomains_json TEXT NOT NULL,
                target_jurisdictions_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_icp_rge ON icp_segments(rge_division);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_icp_tier ON icp_segments(tier_group);")
        conn.execute("DELETE FROM icp_segments;")
        conn.executemany(
            """
            INSERT INTO icp_segments (
                icp_id, tier_group, rge_division, name, demographic_target, pain_points,
                primary_language_resonance, vertical_domain_path, productized_module,
                mapped_skus_json, mapped_subdomains_json, target_jurisdictions_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            [
                (
                    it["icp_id"],
                    it["tier_group"],
                    it["rge_division"],
                    it["name"],
                    it["demographic_target"],
                    it["pain_points"],
                    it["primary_language_resonance"],
                    it["vertical_domain_path"],
                    it["productized_module"],
                    json.dumps(it["skus"]),
                    json.dumps(it["subdomains"]),
                    json.dumps(it["jurisdictions"]),
                    now,
                )
                for it in all_icps
            ],
        )
    conn.close()
    return (
        {
            "db_path": str(db_path),
            "icp_segments_total": len(all_icps),
            "primary_archetypes_count": len(PRIMARY_BUYER_ARCHETYPES),
            "enterprise_registry_count": len(all_icps) - len(PRIMARY_BUYER_ARCHETYPES),
        },
        all_icps,
    )


def _classify_rgu_niche_and_mechanism(rgu_id: str, rgo: str) -> Tuple[str, str, float]:
    low = f"{rgu_id} {rgo}".lower()
    if "nomenagora" in low:
        return "NICHE-NOMENAGORA-NAMESPACE", "arbitrage", 93.0
    if "vrtti" in low:
        return "NICHE-VRTTI-EXECUTIVE", "attestation", 88.0
    if any(k in low for k in ("arb", "funding", "cross-venue", "triad", "basis")):
        return "NICHE-QUANT-ARBITRAGE", "arbitrage", 92.5
    if any(k in low for k in ("yield", "ghost", "efemera", "mip-mining")):
        return "NICHE-AUTOTREASURY-YIELD", "keeper", 91.0
    if any(k in low for k in ("forecast", "timesfm", "x402", "intent", "api")):
        return "NICHE-TIMESFM-INFERENCE", "inference", 95.0
    if any(k in low for k in ("merchant", "underwriting", "iso", "murua")):
        return "NICHE-MURUA-LOGISTICS", "signal", 89.5
    if any(k in low for k in ("sdr", "spectrum")):
        return "NICHE-RF-SDR-EDGE", "signal", 84.0
    if any(k in low for k in ("aegis", "fortress", "honeytoken", "bounty", "sentinel")):
        return "NICHE-CYBER-FORTRESS", "attestation", 96.0
    if any(k in low for k in ("token", "vast", "compute")):
        return "NICHE-COMPUTE-TOKEN-EXCHANGE", "keeper", 87.0
    if any(k in low for k in ("manual", "blueprint", "kai3", "asura", "lead-magnet", "digest", "telegram", "jobmatch", "tools")):
        return "NICHE-POLYGLOT-CODICES", "memory", 98.0
    if any(k in low for k in ("research", "portfolio", "ledger")):
        return "NICHE-VERITAS-MEMORY", "memory", 96.5
    return "NICHE-SOVEREIGN-SUBSTRATE", "attestation", 94.0


def load_41_rgus() -> List[Dict[str, Any]]:
    matrix_data: Dict[str, Any] = {}
    for p in (
        REPO_DIR / "docs" / "ndimmorwyn" / "RGU_OPPORTUNITY_MATRIX.json",
        Path("/var/lib/tianxia/docs/ndimmorwyn/RGU_OPPORTUNITY_MATRIX.json"),
    ):
        if p.is_file():
            try:
                matrix_data = json.loads(p.read_text(encoding="utf-8")).get("rgu_matrix", {})
                if matrix_data:
                    break
            except Exception:
                pass

    reg_status: Dict[str, str] = {}
    for p in (
        REPO_DIR / "docs" / "faery_fortress" / "registry.json",
        Path("/var/lib/tianxia/docs/faery_fortress/registry.json"),
    ):
        if p.is_file():
            try:
                for r in json.loads(p.read_text(encoding="utf-8", errors="ignore")).get("rgus", []):
                    if r.get("id"):
                        reg_status[str(r["id"])] = str(r.get("status", "ACTIVE"))
                break
            except Exception:
                pass

    if not matrix_data:
        try:
            import tx_opportunities_miner as miner
            for rid, meta in miner.CANONICAL_RGUS.items():
                matrix_data[rid] = dict(meta)
        except Exception:
            pass

    rows: List[Dict[str, Any]] = []
    for rid, meta in sorted(matrix_data.items()):
        rgo = str(meta.get("rgo", "RGO-SOVEREIGN-OP"))
        niche_id, mech_cls, margin_pct = _classify_rgu_niche_and_mechanism(rid, rgo)
        sub = str(meta.get("subdomain", "rasaxmachina.com"))
        if not sub.endswith("rasaxmachina.com"):
            sub = "shop.rasaxmachina.com"
        rows.append(
            {
                "rgu_id": rid,
                "name": str(meta.get("name", rid)),
                "rgo_id": rgo,
                "niche_id": niche_id,
                "icp_id": str(meta.get("icp", "ICP-SOVEREIGN-OP")),
                "subdomain": sub,
                "price_usd": float(meta.get("price_usd", 29)),
                "sfi_score": float(meta.get("peak_self_funding_index", 85.0)),
                "gross_margin_pct": margin_pct,
                "mip_level": int(meta.get("mip_level", 2)),
                "mif_tier": str(meta.get("mif_tier", "MIF+40")),
                "mechanism_class": mech_cls,
                "projected_monthly_usd": float(meta.get("projected_monthly_cashflow_usd", 500.0)),
                "status": reg_status.get(rid, "ACTIVE"),
            }
        )
    return rows


def load_i18n_catalog() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    for p in (
        REPO_DIR / "ui" / "i18n" / "index.json",
        Path("/var/lib/tianxia/ui/i18n/index.json"),
    ):
        if p.is_file():
            data = json.loads(p.read_text(encoding="utf-8"))
            return data.get("markets", {}), data.get("languages", {}), data.get("currencies", {})
    return {}, {}, {}


def load_subdomains_catalog() -> Dict[str, Dict[str, Any]]:
    for p in (
        REPO_DIR / "config" / "subdomains.json",
        Path("/var/lib/tianxia/config/subdomains.json"),
    ):
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8")).get("subdomains", {})
    return {}


def build_niche_intelligence(db_dir: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    db_path = db_dir / "niche_intelligence.sqlite3"
    now = utc_now()
    rgus = load_41_rgus()
    markets, languages, currencies = load_i18n_catalog()

    # Compute per-niche RGU counts & peak SFI
    niche_counts: Dict[str, int] = {}
    niche_peak_sfi: Dict[str, float] = {}
    for r in rgus:
        nid = r["niche_id"]
        niche_counts[nid] = niche_counts.get(nid, 0) + 1
        niche_peak_sfi[nid] = max(niche_peak_sfi.get(nid, 0.0), r["sfi_score"])

    # Harvest evergreen signals from MERGED_SIGNALS.jsonl + CAREER_OPPORTUNITIES.json
    signals: List[Tuple[str, str, str, str, float, str, str, str]] = []
    seen_sig: Set[str] = set()

    for sig_file in (
        REPO_DIR / "docs" / "ndimmorwyn" / "MERGED_SIGNALS.jsonl",
        Path("/var/lib/tianxia/docs/ndimmorwyn/MERGED_SIGNALS.jsonl"),
    ):
        if sig_file.is_file():
            for raw_ln in sig_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                s = raw_ln.strip()
                if not s:
                    continue
                try:
                    rec = json.loads(s)
                except json.JSONDecodeError:
                    continue
                title = str(rec.get("title") or "").strip()
                url = str(rec.get("url") or "").strip()
                chan = str(rec.get("source") or "scour").strip()
                if not title:
                    continue
                sig_id = "SIG-" + hashlib.sha256(f"{chan}|{title}|{url}".encode("utf-8")).hexdigest()[:16]
                if sig_id in seen_sig:
                    continue
                seen_sig.add(sig_id)
                mapped_rgu = infer_rgu_for_ffp(chan, f"{title} {rec.get('text', '')}", {})
                niche_id, _, _ = _classify_rgu_niche_and_mechanism(mapped_rgu, "")
                metrics = rec.get("metrics") or {}
                sfi = float(rec.get("score") or metrics.get("apy") or (90.0 if chan in ("threat", "defillama", "arxiv") else 78.5))
                sfi = min(99.5, max(50.0, round(sfi, 2)))
                signals.append((sig_id, chan, title[:280], url[:500], sfi, mapped_rgu, niche_id, now))
                if len(signals) >= 600:
                    break
            if signals:
                break

    for vac_file in (
        REPO_DIR / "docs" / "ndimmorwyn" / "CAREER_OPPORTUNITIES.json",
        Path("/var/lib/tianxia/docs/ndimmorwyn/CAREER_OPPORTUNITIES.json"),
    ):
        if vac_file.is_file():
            try:
                vacs = json.loads(vac_file.read_text(encoding="utf-8"))
                for v in vacs[:200]:
                    sid = str(v.get("req_id") or "")
                    title = str(v.get("target_title") or "").strip()
                    url = str(v.get("url") or "").strip()
                    if not sid or not title or sid in seen_sig:
                        continue
                    seen_sig.add(sid)
                    rgu_id = str(v.get("canonical_rgu") or "RGU-vrtti-contract")
                    niche_id, _, _ = _classify_rgu_niche_and_mechanism(rgu_id, "RGO-VRTTI")
                    signals.append((sid, f"vacancy:{v.get('source', 'b2b')}", title[:280], url[:500], 94.5, rgu_id, niche_id, now))
                break
            except Exception:
                pass

    conn = connect_wal(db_path, foreign_keys=True)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS niches (
                niche_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                rge_division TEXT NOT NULL,
                mechanism_class TEXT NOT NULL,
                target_rgu_count INTEGER NOT NULL,
                peak_sfi REAL NOT NULL,
                avg_margin_pct REAL NOT NULL,
                primary_subdomains_json TEXT NOT NULL,
                summary TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rgu_matrix (
                rgu_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                rgo_id TEXT NOT NULL,
                niche_id TEXT NOT NULL REFERENCES niches(niche_id),
                icp_id TEXT NOT NULL,
                subdomain TEXT NOT NULL,
                price_usd REAL NOT NULL,
                sfi_score REAL NOT NULL,
                gross_margin_pct REAL NOT NULL,
                mip_level INTEGER NOT NULL,
                mif_tier TEXT NOT NULL,
                mechanism_class TEXT NOT NULL,
                projected_monthly_usd REAL NOT NULL,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_locales (
                market_code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                native_name TEXT NOT NULL,
                flag TEXT NOT NULL,
                currency_code TEXT NOT NULL,
                default_lang TEXT NOT NULL,
                languages_json TEXT NOT NULL,
                direction TEXT NOT NULL,
                regulatory_regime TEXT NOT NULL,
                payment_rails TEXT NOT NULL,
                edge_routing TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS supported_languages (
                lang_code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                native_name TEXT NOT NULL,
                direction TEXT NOT NULL,
                markets_json TEXT NOT NULL,
                pack_url TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS supported_currencies (
                currency_code TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                decimals INTEGER NOT NULL,
                zero_decimal INTEGER NOT NULL,
                rate_from_eur REAL NOT NULL,
                rate_from_usd REAL NOT NULL,
                countries_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evergreen_signals (
                signal_id TEXT PRIMARY KEY,
                channel TEXT NOT NULL,
                title TEXT NOT NULL,
                source_url TEXT NOT NULL,
                sfi_score REAL NOT NULL,
                mapped_rgu_id TEXT NOT NULL,
                niche_id TEXT NOT NULL,
                ingested_at TEXT NOT NULL
            );
            """
        )

        conn.execute("DELETE FROM rgu_matrix;")
        conn.execute("DELETE FROM niches;")
        conn.executemany(
            """
            INSERT INTO niches (
                niche_id, name, rge_division, mechanism_class, target_rgu_count,
                peak_sfi, avg_margin_pct, primary_subdomains_json, summary, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            [
                (
                    n["niche_id"],
                    n["name"],
                    n["rge_division"],
                    n["mechanism_class"],
                    niche_counts.get(n["niche_id"], 1),
                    niche_peak_sfi.get(n["niche_id"], 90.0),
                    n["avg_margin_pct"],
                    json.dumps(n["subdomains"]),
                    n["summary"],
                    now,
                )
                for n in STRATEGIC_NICHES
            ],
        )

        conn.executemany(
            """
            INSERT INTO rgu_matrix (
                rgu_id, name, rgo_id, niche_id, icp_id, subdomain, price_usd, sfi_score,
                gross_margin_pct, mip_level, mif_tier, mechanism_class, projected_monthly_usd, status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            [
                (
                    r["rgu_id"], r["name"], r["rgo_id"], r["niche_id"], r["icp_id"], r["subdomain"],
                    r["price_usd"], r["sfi_score"], r["gross_margin_pct"], r["mip_level"], r["mif_tier"],
                    r["mechanism_class"], r["projected_monthly_usd"], r["status"], now,
                )
                for r in rgus
            ],
        )

        conn.execute("DELETE FROM market_locales;")
        conn.executemany(
            """
            INSERT INTO market_locales (
                market_code, name, native_name, flag, currency_code, default_lang,
                languages_json, direction, regulatory_regime, payment_rails, edge_routing, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            [
                (
                    mc,
                    str(mv.get("name", mc)),
                    str(mv.get("native_name", mc)),
                    str(mv.get("flag", "")),
                    str(mv.get("currency", "EUR")),
                    str(mv.get("default_lang", "en")),
                    json.dumps(mv.get("languages", ["en"])),
                    str(mv.get("dir", "ltr")),
                    str(mv.get("regime", "GDPR++ v2030.4")),
                    str(mv.get("rails", "Stripe / Solana Pay / Base L2 / x402")),
                    str(mv.get("edge", "Hetzner EU Rosenpass PQ Relay")),
                    now,
                )
                for mc, mv in sorted(markets.items())
            ],
        )

        conn.execute("DELETE FROM supported_languages;")
        conn.executemany(
            """
            INSERT INTO supported_languages (
                lang_code, name, native_name, direction, markets_json, pack_url, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            [
                (
                    lc,
                    str(lv.get("name", lc)),
                    str(lv.get("native_name", lc)),
                    str(lv.get("dir", "ltr")),
                    json.dumps(lv.get("markets", [])),
                    str(lv.get("pack_url", f"/i18n/{lc}.json")),
                    now,
                )
                for lc, lv in sorted(languages.items())
            ],
        )

        conn.execute("DELETE FROM supported_currencies;")
        conn.executemany(
            """
            INSERT INTO supported_currencies (
                currency_code, symbol, name, decimals, zero_decimal, rate_from_eur, rate_from_usd, countries_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            [
                (
                    cc,
                    str(cv.get("symbol", cc)),
                    str(cv.get("name", cc)),
                    int(cv.get("decimals", 2)),
                    1 if cv.get("zero_decimal") else 0,
                    float(cv.get("rate_from_eur", 1.0)),
                    float(cv.get("rate_from_usd", 1.0)),
                    json.dumps(cv.get("countries", [])),
                    now,
                )
                for cc, cv in sorted(currencies.items())
            ],
        )

        conn.execute("DELETE FROM evergreen_signals;")
        conn.executemany(
            """
            INSERT INTO evergreen_signals (
                signal_id, channel, title, source_url, sfi_score, mapped_rgu_id, niche_id, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            signals,
        )
    conn.close()
    return (
        {
            "db_path": str(db_path),
            "niches_count": len(STRATEGIC_NICHES),
            "rgu_matrix_count": len(rgus),
            "market_locales_count": len(markets),
            "supported_languages_count": len(languages),
            "supported_currencies_count": len(currencies),
            "evergreen_signals_count": len(signals),
        },
        rgus,
        markets,
        languages,
        currencies,
    )


def discover_all_sqlite_dbs(db_dir: Path) -> List[Path]:
    candidates: List[Path] = []
    seen: Set[str] = set()

    search_dirs = [
        db_dir,
        REPO_DIR / "db",
        WORKSPACE_DIR / "db",
        WORKSPACE_DIR / "deliverables" / "d48_simulate_enforcement_trigger_sandbox",
        Path.home() / ".local" / "share" / "tianxia",
        Path("/var/lib/tianxia/db"),
        Path("/var/lib/tianxia/persistence"),
        Path("/var/lib/tianxia/murua/data"),
        Path("/var/lib/tianxia/state"),
        Path("/var/lib/tianxia/deliverables/d48_simulate_enforcement_trigger_sandbox"),
    ]
    for sdir in search_dirs:
        if not sdir.is_dir():
            continue
        for item in sorted(sdir.iterdir()):
            if not item.is_file():
                continue
            if item.suffix.lower() not in (".sqlite3", ".db"):
                continue
            rp = str(item.resolve())
            if rp in seen:
                continue
            # Skip 0-byte uninitialized non-db_dir placeholders; graph.sqlite3 in db_dir is populated by us
            if item.stat().st_size == 0 and item.name != "graph.sqlite3":
                continue
            seen.add(rp)
            candidates.append(item)
    return candidates


def inspect_and_maintain_db(db_path: Path, quick_only: bool = False) -> Dict[str, Any]:
    now = utc_now()
    host_scope = socket.gethostname()
    try:
        byte_size = db_path.stat().st_size
    except OSError as exc:
        return {
            "db_id": f"DB-{db_path.stem}",
            "db_name": db_path.name,
            "db_path": str(db_path),
            "host_scope": host_scope,
            "table_count": 0,
            "total_rows": 0,
            "byte_size": 0,
            "journal_mode": "error",
            "integrity_status": f"stat_error:{exc}",
            "inspected_at": now,
        }

    large_db = byte_size >= 100_000_000  # >=100 MB uses O(1) max(rowid) & quick_check(1) for bounded velocity
    try:
        conn = sqlite3.connect(str(db_path), timeout=15.0)
        conn.execute("PRAGMA busy_timeout = 5000;")
        jmode_row = conn.execute("PRAGMA journal_mode = WAL;").fetchone()
        jmode = str(jmode_row[0]).lower() if jmode_row else "unknown"
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")

        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        total_rows = 0
        for tbl in tables:
            safe_tbl = tbl.replace('"', '""')
            try:
                if large_db:
                    cnt_row = conn.execute(f'SELECT COALESCE(MAX(rowid), 0) FROM "{safe_tbl}"').fetchone()
                else:
                    cnt_row = conn.execute(f'SELECT COUNT(*) FROM "{safe_tbl}"').fetchone()
                total_rows += int(cnt_row[0] or 0) if cnt_row else 0
            except sqlite3.Error:
                # Virtual/FTS shadow tables without rowid
                pass

        if quick_only or large_db:
            chk_row = conn.execute("PRAGMA quick_check(1);").fetchone()
        else:
            chk_row = conn.execute("PRAGMA integrity_check;").fetchone()
            conn.execute("PRAGMA optimize;")
        integrity = str(chk_row[0]) if chk_row else "unknown"
        conn.close()
        byte_size = db_path.stat().st_size
    except Exception as exc:
        return {
            "db_id": f"DB-{db_path.stem}",
            "db_name": db_path.name,
            "db_path": str(db_path),
            "host_scope": host_scope,
            "table_count": 0,
            "total_rows": 0,
            "byte_size": byte_size,
            "journal_mode": "error",
            "integrity_status": f"error:{str(exc)[:120]}",
            "inspected_at": now,
        }

    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", f"{db_path.parent.name}-{db_path.name}").strip("-")
    return {
        "db_id": f"DB-{slug}",
        "db_name": db_path.name,
        "db_path": str(db_path),
        "host_scope": host_scope,
        "table_count": len(tables),
        "total_rows": total_rows,
        "byte_size": byte_size,
        "journal_mode": jmode,
        "integrity_status": integrity,
        "inspected_at": now,
    }


def build_relational_graph(
    db_dir: Path,
    icps: List[Dict[str, Any]],
    rgus: List[Dict[str, Any]],
    markets: Dict[str, Any],
    languages: Dict[str, Any],
    currencies: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    graph_path = db_dir / "graph.sqlite3"
    ffp_db_path = db_dir / "ffp_registry.sqlite3"
    subdomains_map = load_subdomains_catalog()
    now = utc_now()

    nodes: Dict[str, Tuple[str, str, str, str]] = {}
    edges: Dict[str, Tuple[str, str, str, float, str]] = {}

    def add_node(nid: str, ntype: str, label: str, meta: Dict[str, Any]) -> None:
        nodes[nid] = (ntype, label, json.dumps(meta, ensure_ascii=False), now)

    def add_edge(src: str, rel: str, dst: str, weight: float, evidence: str) -> None:
        if src not in nodes or dst not in nodes:
            return
        eid = "EDGE-" + hashlib.sha256(f"{src}|{rel}|{dst}".encode("utf-8")).hexdigest()[:20]
        edges[eid] = (src, rel, dst, weight, evidence)

    # 1. Mesh Nodes (5)
    for mn in MESH_NODES:
        add_node(mn["node_id"], "MESH_NODE", mn["hostname"], mn)

    # 2. Niches (12)
    for n in STRATEGIC_NICHES:
        add_node(n["niche_id"], "NICHE", n["name"], n)

    # 3. Subdomains (28)
    fqdn_to_node: Dict[str, str] = {}
    for key, sdata in sorted(subdomains_map.items()):
        fqdn = str(sdata.get("fqdn", f"{key}.rasaxmachina.com"))
        snid = f"SUB-{fqdn}"
        fqdn_to_node[fqdn] = snid
        add_node(snid, "SUBDOMAIN", fqdn, sdata)
        add_edge(snid, "ROUTED_VIA_EDGE", "NODE-tianxia-relay", 1.0, "config/subdomains.json")
        add_edge(snid, "BACKED_BY_HUB", "NODE-latitude-tianxia", 1.0, "config/subdomains.json")

    # 4. RGUs (41)
    rgu_ids_present: Set[str] = set()
    for r in rgus:
        rid = r["rgu_id"]
        rgu_ids_present.add(rid)
        add_node(rid, "RGU", r["name"], r)
        add_edge(rid, "BELONGS_TO_NICHE", r["niche_id"], round(r["sfi_score"] / 100.0, 3), "RGU_OPPORTUNITY_MATRIX.json")
        sub_node = fqdn_to_node.get(r["subdomain"])
        if sub_node:
            add_edge(rid, "SERVED_ON_SUBDOMAIN", sub_node, 1.0, "RGU_OPPORTUNITY_MATRIX.json")

    # 5. SKUs (22)
    for sku in CANONICAL_SKUS:
        sid = sku["sku_id"]
        add_node(sid, "SKU", f"{sid}: {sku['name']}", sku)
        if sku["rgu_id"] in rgu_ids_present:
            add_edge(sku["rgu_id"], "MONETIZED_AS_SKU", sid, 1.0, "ui/pricing.json")
        sub_node = fqdn_to_node.get(sku["subdomain"])
        if sub_node:
            add_edge(sid, "CHECKOUT_SURFACE", sub_node, 1.0, "ui/pricing.json")

    # 6. Markets (42), Languages (25), Currencies (29)
    for lc, lv in sorted(languages.items()):
        add_node(f"LANG-{lc}", "LANGUAGE", f"{lv.get('name', lc)} ({lc})", lv)

    for cc, cv in sorted(currencies.items()):
        add_node(f"CUR-{cc}", "CURRENCY", f"{cv.get('name', cc)} ({cc})", cv)

    for mc, mv in sorted(markets.items()):
        mnid = f"MKT-{mc}"
        add_node(mnid, "MARKET", f"{mv.get('name', mc)} ({mc})", mv)
        cur_id = f"CUR-{mv.get('currency', 'EUR')}"
        add_edge(mnid, "SETTLES_IN_CURRENCY", cur_id, 1.0, "ui/i18n/index.json")
        for lg in mv.get("languages", []):
            add_edge(mnid, "SPEAKS_LANGUAGE", f"LANG-{lg}", 1.0 if lg == mv.get("default_lang") else 0.7, "ui/i18n/index.json")

    # 7. ICPs (119: 7 Archetypes + 111 Enterprise Registry + Collector)
    for icp in icps:
        iid = icp["icp_id"]
        add_node(iid, "ICP", icp["name"], icp)
        for sku_id in icp.get("skus", []):
            add_edge(iid, "PURCHASES_SKU", sku_id, 1.0, "icp_profiles.sqlite3")
        for fqdn in icp.get("subdomains", []):
            sub_node = fqdn_to_node.get(fqdn)
            if sub_node:
                add_edge(iid, "VISITS_PORTAL", sub_node, 1.0, "icp_profiles.sqlite3")
        for mcode in icp.get("jurisdictions", []):
            add_edge(iid, "OPERATES_IN_MARKET", f"MKT-{mcode}", 1.0, "icp_profiles.sqlite3")

    # Link Subdomains & RGUs declared ICPs
    for key, sdata in subdomains_map.items():
        fqdn = str(sdata.get("fqdn", f"{key}.rasaxmachina.com"))
        snid = fqdn_to_node.get(fqdn)
        if snid:
            for icp_ref in sdata.get("icp", []):
                add_edge(str(icp_ref), "VISITS_PORTAL", snid, 1.0, "config/subdomains.json")
    for r in rgus:
        add_edge(r["icp_id"], "TARGETS_RGU", r["rgu_id"], 1.0, "RGU_OPPORTUNITY_MATRIX.json")

    # 8. GitHub Repos (35)
    for rname, vis, plang, target_rgu, deploy_host in TIANXIA_CORE_REPOS:
        gnid = f"REPO-Tianxia-Core/{rname}"
        add_node(
            gnid,
            "GITHUB_REPO",
            f"Tianxia-Core/{rname}",
            {"visibility": vis, "primary_language": plang, "rgu_id": target_rgu, "deploy_node": deploy_host},
        )
        add_edge(gnid, "POWERS_RGU", target_rgu, 1.0, "github:Tianxia-Core")
        add_edge(gnid, "DEPLOYED_ON_NODE", f"NODE-{deploy_host}", 1.0, "github:Tianxia-Core")

    # 9. FFPs from ffp_registry.sqlite3
    if ffp_db_path.is_file():
        fconn = sqlite3.connect(str(ffp_db_path), timeout=5.0)
        for fid, fcls, lang, fpath, dom, rgu_id in fconn.execute(
            "SELECT ffp_id, ffp_class, language, file_path, mahavidya_domain, rgu_id FROM ffp_units"
        ):
            fnid = f"FFP::{fid}"
            add_node(
                fnid,
                "FFP",
                fid,
                {"ffp_class": fcls, "language": lang, "file_path": fpath, "mahavidya_domain": dom, "rgu_id": rgu_id},
            )
            add_edge(fnid, "IMPLEMENTS_RGU", rgu_id, 1.0, fpath)
        fconn.close()

    # Initialize graph.sqlite3 first so it is included in the universal DB catalog pass!
    conn = connect_wal(graph_path, foreign_keys=True)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS db_catalog (
                db_id TEXT PRIMARY KEY,
                db_name TEXT NOT NULL,
                db_path TEXT NOT NULL,
                host_scope TEXT NOT NULL,
                table_count INTEGER NOT NULL,
                total_rows INTEGER NOT NULL,
                byte_size INTEGER NOT NULL,
                journal_mode TEXT NOT NULL,
                integrity_status TEXT NOT NULL,
                inspected_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nexus_nodes (
                node_id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                label TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nexus_nodes_type ON nexus_nodes(node_type);")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nexus_edges (
                edge_id TEXT PRIMARY KEY,
                src_id TEXT NOT NULL REFERENCES nexus_nodes(node_id) ON DELETE CASCADE,
                rel_type TEXT NOT NULL,
                dst_id TEXT NOT NULL REFERENCES nexus_nodes(node_id) ON DELETE CASCADE,
                weight REAL NOT NULL DEFAULT 1.0,
                evidence_ref TEXT NOT NULL
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nexus_edges_src ON nexus_edges(src_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nexus_edges_dst ON nexus_edges(dst_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nexus_edges_rel ON nexus_edges(rel_type);")
    conn.close()

    # Discover & run Universal WAL + Integrity + Optimize Pass across all DBs
    all_dbs = discover_all_sqlite_dbs(db_dir)
    catalog_entries: List[Dict[str, Any]] = []
    host_node_id = "NODE-latitude-tianxia" if is_hub_host() else "NODE-pixel8pro"
    for dbp in all_dbs:
        info = inspect_and_maintain_db(dbp, quick_only=False)
        catalog_entries.append(info)
        add_node(info["db_id"], "DATABASE", info["db_name"], info)
        add_edge(info["db_id"], "RESIDES_ON_NODE", host_node_id, 1.0, info["db_path"])

    # Commit nodes, edges, and db_catalog atomically with FOREIGN KEYS ON
    conn = connect_wal(graph_path, foreign_keys=True)
    with conn:
        conn.execute("DELETE FROM nexus_edges;")
        conn.execute("DELETE FROM nexus_nodes;")
        conn.executemany(
            "INSERT INTO nexus_nodes (node_id, node_type, label, metadata_json, updated_at) VALUES (?, ?, ?, ?, ?);",
            [(nid, *vals) for nid, vals in sorted(nodes.items())],
        )
        conn.executemany(
            "INSERT INTO nexus_edges (edge_id, src_id, rel_type, dst_id, weight, evidence_ref) VALUES (?, ?, ?, ?, ?, ?);",
            [(eid, *vals) for eid, vals in sorted(edges.items())],
        )
        conn.execute("DELETE FROM db_catalog;")
        conn.executemany(
            """
            INSERT INTO db_catalog (
                db_id, db_name, db_path, host_scope, table_count, total_rows,
                byte_size, journal_mode, integrity_status, inspected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            [
                (
                    c["db_id"], c["db_name"], c["db_path"], c["host_scope"], c["table_count"],
                    c["total_rows"], c["byte_size"], c["journal_mode"], c["integrity_status"], c["inspected_at"],
                )
                for c in catalog_entries
            ],
        )
        fk_violations = conn.execute("PRAGMA foreign_key_check;").fetchall()
    conn.close()

    # Refresh graph.sqlite3's own row/byte stats in db_catalog now that nodes/edges are populated
    graph_info = inspect_and_maintain_db(graph_path, quick_only=False)
    conn = connect_wal(graph_path, foreign_keys=True)
    with conn:
        conn.execute(
            """
            UPDATE db_catalog
               SET table_count = ?, total_rows = ?, byte_size = ?, journal_mode = ?, integrity_status = ?, inspected_at = ?
             WHERE db_path = ?;
            """,
            (
                graph_info["table_count"],
                graph_info["total_rows"],
                graph_info["byte_size"],
                graph_info["journal_mode"],
                graph_info["integrity_status"],
                graph_info["inspected_at"],
                str(graph_path),
            ),
        )
        node_breakdown = dict(conn.execute("SELECT node_type, COUNT(*) FROM nexus_nodes GROUP BY node_type").fetchall())
        edge_breakdown = dict(conn.execute("SELECT rel_type, COUNT(*) FROM nexus_edges GROUP BY rel_type").fetchall())
    conn.close()

    for idx, c in enumerate(catalog_entries):
        if c["db_path"] == str(graph_path):
            catalog_entries[idx] = graph_info

    return (
        {
            "db_path": str(graph_path),
            "db_catalog_count": len(catalog_entries),
            "nexus_nodes_count": len(nodes),
            "nexus_edges_count": len(edges),
            "foreign_key_violations": len(fk_violations),
            "node_type_breakdown": node_breakdown,
            "edge_type_breakdown": edge_breakdown,
        },
        catalog_entries,
    )


def quick_verify(db_dir: Path) -> Dict[str, Any]:
    t0 = time.time()
    required = ("ffp_registry.sqlite3", "icp_profiles.sqlite3", "niche_intelligence.sqlite3", "graph.sqlite3")
    missing = [name for name in required if not (db_dir / name).is_file() or (db_dir / name).stat().st_size == 0]
    if missing:
        return {
            "ok": False,
            "mode": "quick-verify",
            "missing_core_dbs": missing,
            "duration_s": round(time.time() - t0, 3),
        }

    all_dbs = discover_all_sqlite_dbs(db_dir)
    failed_dbs: List[str] = []
    for dbp in all_dbs:
        info = inspect_and_maintain_db(dbp, quick_only=True)
        if info["integrity_status"] != "ok":
            failed_dbs.append(f"{dbp.name}:{info['integrity_status']}")

    counts: Dict[str, int] = {}
    for db_name, query_key, sql in [
        ("ffp_registry.sqlite3", "ffp_units", "SELECT COUNT(*) FROM ffp_units"),
        ("icp_profiles.sqlite3", "icp_segments", "SELECT COUNT(*) FROM icp_segments"),
        ("niche_intelligence.sqlite3", "rgu_matrix", "SELECT COUNT(*) FROM rgu_matrix"),
        ("niche_intelligence.sqlite3", "market_locales", "SELECT COUNT(*) FROM market_locales"),
        ("graph.sqlite3", "db_catalog", "SELECT COUNT(*) FROM db_catalog"),
        ("graph.sqlite3", "nexus_nodes", "SELECT COUNT(*) FROM nexus_nodes"),
        ("graph.sqlite3", "nexus_edges", "SELECT COUNT(*) FROM nexus_edges"),
    ]:
        conn = sqlite3.connect(str(db_dir / db_name), timeout=5.0)
        row = conn.execute(sql).fetchone()
        counts[query_key] = int(row[0] or 0) if row else 0
        conn.close()

    ok = (
        not failed_dbs
        and counts.get("ffp_units", 0) >= 50
        and counts.get("icp_segments", 0) >= 118
        and counts.get("rgu_matrix", 0) >= 41
        and counts.get("market_locales", 0) >= 42
        and counts.get("nexus_nodes", 0) >= 250
        and counts.get("nexus_edges", 0) >= 1000
    )
    return {
        "ok": ok,
        "mode": "quick-verify",
        "timestamp_utc": utc_now(),
        "host": socket.gethostname(),
        "db_dir": str(db_dir),
        "databases_verified": len(all_dbs),
        "failed_databases": failed_dbs,
        "counts": counts,
        "duration_s": round(time.time() - t0, 3),
    }


def full_build(db_dir: Path) -> Dict[str, Any]:
    t0 = time.time()
    ffp_summary = build_ffp_registry(db_dir)
    icp_summary, icps = build_icp_profiles(db_dir)
    niche_summary, rgus, markets, languages, currencies = build_niche_intelligence(db_dir)
    graph_summary, catalog = build_relational_graph(db_dir, icps, rgus, markets, languages, currencies)

    failed = [c["db_path"] for c in catalog if c["integrity_status"] != "ok"]
    non_wal = [c["db_path"] for c in catalog if c["journal_mode"] != "wal"]
    ok = (not failed) and (graph_summary["foreign_key_violations"] == 0)

    report = {
        "schema_version": "1.0.0",
        "revision": REVISION,
        "ffp": "FFP-DB-NEXUS",
        "timestamp_utc": utc_now(),
        "host": socket.gethostname(),
        "ok": ok,
        "duration_s": round(time.time() - t0, 3),
        "db_dir": str(db_dir),
        "databases_maintained_total": len(catalog),
        "integrity_failures": failed,
        "non_wal_databases": non_wal,
        "fabric": {
            "ffp_registry": ffp_summary,
            "icp_profiles": icp_summary,
            "niche_intelligence": niche_summary,
            "graph": graph_summary,
        },
        "catalog": catalog,
    }

    # Write health reports atomically
    if is_hub_host() or Path("/var/lib/tianxia/logs").is_dir():
        atomic_write_json(Path("/var/lib/tianxia/logs/db_nexus_health.json"), report)
    local_arch_health = REPO_DIR / "docs" / "architecture" / "DB_NEXUS_HEALTH.json"
    atomic_write_json(local_arch_health, report)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="TianxiaOS Cross-Database Relational Fabric & WAL Maintenance Engine")
    ap.add_argument("--db-dir", default="", help="Override SQLite directory")
    ap.add_argument("--quick-verify", action="store_true", help="Fast bounded verification for Hussar Legion VII")
    ap.add_argument("--json", action="store_true", help="Print JSON report to stdout")
    args = ap.parse_args()

    db_dir = resolve_db_dir(args.db_dir or None)
    if args.quick_verify:
        res = quick_verify(db_dir)
    else:
        res = full_build(db_dir)

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        LOG.info(
            "tx_db_nexus (%s) ok=%s dbs=%s duration=%ss",
            "quick-verify" if args.quick_verify else "full-build",
            res.get("ok"),
            res.get("databases_verified") or res.get("databases_maintained_total"),
            res.get("duration_s"),
        )
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
