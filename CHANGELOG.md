# Changelog

All notable changes to **TianxiaOS** are documented in this file following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [8.7.0] - 2026-11-13 — *Sovereign Founder Canon & Universal 7-Format Release Edition*

### Added
- **Universal 7-Format Multi-OS Cryptographically Signed Packages & Evergreen Sentinel**:
  - Built, verified, and Ed25519-signed (`.sig` + `SHA256SUMS.sig` + CycloneDX 1.5 `SBOM.cdx.json`) native packages across **`.deb`** (`amd64`, `arm64`), **`.rpm`** (`x86_64`, `aarch64`), **Zero-FUSE `.AppImage`** (`x86_64`, `aarch64`), **Declarative Nix Flake (`flake.nix` + `flake.lock`)**, **`.tar.gz` tarballs**, **Windows PE32+ `.exe`**, and **Android RSA-4096 v2+v3 `.apk` + native ARM64 CLI**.
  - Published public release mirror [`Tianxia-Core/tianxiaos-releases`](https://github.com/Tianxia-Core/tianxiaos-releases) and upgraded `nimbus2` (`v2.5.0`), `007-scanner` (`v2.1.0`), `secrets-vault` (`v2.1.0`), and `tianxia-mobile` (`v2.1.0`).
  - Deployed `tx_package_builder.py` and 6-hour systemd **Package Evergreen Sentinel** (`tx_release_package_sentinel.py` / `tx-release-package-sentinel.timer`).
- **Build Law `v5.0-SOVEREIGN-FOUNDER-CANON` (`33` Clauses, `7/7` Mirrors Sealed)**:
  - Codified the 7-stage Closed-Loop Sovereign Engineering Lifecycle, Universal 7-Format Packaging Mandate, Hussar 7 Winged Sentinel Legions, Cross-DB Relational Fabric, 3-Node X Distribution Law (`@coltakrasax`, `@rasaxmachina`, `@tianxiaos`), and Institutional Due-Diligence Readiness.
- **Hussar 7 Winged Sentinel Legions & 28-DB Relational Fabric (`tx_hussar_legions.py`, `tx_db_nexus.py`)**:
  - Activated all 7 continuous patrol legions (Security, Synergy, Synchronicity, Harmony, Evergreening, `ENHAN³`, DB Nexus) under cgroup v2 containment.
  - Interconnected `1,023` FFPs (`ffp_registry.sqlite3`), `119` ICPs (`icp_profiles.sqlite3`), `12` niches / `41` RGUs / `42` markets (`niche_intelligence.sqlite3`), and `28` hub WAL SQLite databases via `graph.sqlite3` (`1,409` vertices, `3,390` FK-verified edges).
- **Estonian Startup Committee Dossiers (`/dossier/*`), Brand-Kit Pitch Deck & 3-Node X Social Engine**:
  - Generated 12-slide 16:9 Obsidian Brand-Kit Pitch Deck PDF, clean EUR Cap Table (`.csv`, `.xlsx`, `.pdf`), 2:30 Founder Video Script (`v6`), 3 statutory Committee Verification PDFs, and `tx_social_herald.py x-hub`.

### Security & UI Fixes
- **Security Sweep Remediation (`tx_security_sweep.py`)**: Tightened `/var/lib/tianxia/secrets` permissions (`0700`/`0600`), eliminated Forgejo placeholder key in `nixos/modules/forgejo.nix`, and added Unicode Tag block smuggling (`U+E0000..U+E007F`) & bidi isolate arrest to `tx_manas.py`.
- **`/estonia` Subdomain Navigation Pill & 25-Language Parity**: Unified `subdomain_estonia.html` onto `<nav class="tx-home-nav">` with smooth scroll/pointer wake + idle auto-hide (`capture: true`), and removed legacy 7-language fallback clobbering across `/estonia`, `/pay`, and `/shop`.

## [8.6.0] - 2026-11-12 — *Crownforge Global-42 Sovereign Edition*

### Added
- **Multi-Platform Self-Contained Signed Executables**:
  - Native Rust + Zig/C self-contained executables for **Linux (`x86_64` & `aarch64`)**, **Windows (`x86_64 .exe`)**, and **Android (Signed `.apk` + `aarch64` binary)** with Ed25519 signatures (`.sig`), `SHA256SUMS`, and CycloneDX 1.5 `SBOM.cdx.json`.
- **100% Full-Copy Localization Across 42 Global Markets & 25 Languages**:
  - Added full market, regulatory, 29-currency single-currency pricing, RTL (`ar`, `ur`), and 100% DOM copy translation across Hong Kong, Canada, Vietnam, South Korea, Nigeria, Kenya, Brazil, Mexico, Chile, Argentina, Colombia, India, Pakistan, Poland, Finland, Lithuania, Bulgaria, Belgium, The Netherlands, Turkey, Australia, New Zealand, Italy, Spain, Cyprus, Greece, Malta, South Africa, UAE, Saudi Arabia, Estonia, Germany, France, UK, US, Switzerland, Sweden, Norway, Singapore, and Japan.
  - Compositional localization reuse engine (`tx_i18n_engine.py` + `/i18n/<lang>.json` + live `MutationObserver`).
- **Optimal GUI & 9-App Interactive TUI Suite on `latitude-tianxia`**:
  - Deployed native GTK4/Libadwaita desktop GUI apps (`tx-control-center-gui`, `tx-vault-gui`, `tx-topology-gui`, `tx-cockpit-gui`), unified 9-tab Rust interactive TUI (`tianxia tui`), and `.desktop` application entries for Hyprland/`wofi`/Waybar.
- **Interactive Live Workbenches Across All 28 Subdomains**:
  - Upgraded static portals with live MCP/OpenAPI explorers, 8-domain security scanner, Secret Shield scrubber, TetraLedger Merkle verifier, ETAMANGA RPC inspector, Scour signal terminal, and DSS-14.2 14-lens code verifier.
- **Enterprise Governance & Daśavidyāyāna NL Build Law (`v4.4`)**:
  - Integrated `DASAVIDYAYANA_NL.md`, `SECURITY.md`, `CONTRIBUTING.md`, `GOVERNANCE.md`, `CODE_OF_CONDUCT.md`, `CITATION.cff`, `CODEOWNERS`, Dependabot, and automated multi-OS release workflows.

### Fixed
- Resolved NixOS snapshot `chr(36)` syntax regression in `tianxia-2048-lifecycle.nix` and Rosenpass `wg0` guard in `tx-rosenpass-apply.sh` (`0` failed systemd units across `latitude-tianxia` and `tianxia-relay`).
- Fixed loopback `CF-Connecting-IP` rate-limit bucketing and added strict `Content-Security-Policy` headers across edge relays.
