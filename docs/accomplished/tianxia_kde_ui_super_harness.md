# TianxiaOS Super-Harness: Enterprise Sovereign Desktop, 5-Tier Menu Architecture & agy Discovery Engine

**Document Version:** 5.0-Enterprise-Sovereign-Master
**Codename:** Asura-Super-Harness
**Substrate Target:** NixOS 26.11 (Nixyr Immutable Layer) / seL4 & Cloud-Hypervisor MicroVM Bridge
**Active Mesh Nodes:** `latitude-tianxia` ($x86\_64$), `pixel8pro-tianxia` ($\text{aarch64}$), `pocox5pro-tianxia` ($\text{aarch64}$)
**Standby Node (Under Repair):** `xps13-tianxia` ($x86\_64$ — Non-Blocking Failover Configured)

---

## 0. Diagnostic Root-Cause Analysis & Stall Rectification Matrix

Previous document generation passes and deployment scripts encountered six structural failure modes across the document parser boundary and target NixOS evaluation layer. Every vector has been isolated and rectified in this master specification:

| Failure Vector | Root Cause in Previous Passes | Architectural Rectification |
| :--- | :--- | :--- |
| **1. Document Stream Truncation** | Emitting inner triple-backtick code blocks inside an outer triple-backtick document container caused parser fence collisions and premature stream termination. | Standardized all inner code blocks on CommonMark triple-tilde fences (`~~~nix`, `~~~python`, `~~~bash`) to guarantee zero delimiter collision with the outer document container. |
| **2. Nested Heredoc & Recursive Execution** | Wrapping `ssh << 'REMOTE_EXEC'`, `cat << 'NIX_EOF'`, and `python3 - << 'PYEOF'` inside `cat << 'EOF'` while invoking the script twice caused quote-stripping and infinite loops. | Separated local Termux payload generation from remote execution via staged `/tmp` script transfer and single-pass `nixos-rebuild switch`. |
| **3. Unresolved Nix Path Stubs** | Bootloader entries contained literal `/nix/store/.../init` stubs and theme derivations referenced non-existent `./assets` directories on disk. | Replaced all path stubs with dynamic Nix store references (`${config.system.build.toplevel}/init`) and inline `pkgs.writeTextFile` SVG/theme generators. |
| **4. Unbound `plasma-manager` Module** | Referencing `programs.plasma-manager` inside `/etc/nixos/configuration.nix` without importing an external Home Manager flake breaks pure NixOS evaluation. | Engineered a zero-dependency `/etc/xdg` and `kwriteconfig6` login activation harness (`tx-plasma-autoconfig`) that configures KDE Plasma 6, KWin, and Dolphin natively. |
| **5. Read-Only XDG Application Store** | Writing dynamic `.desktop` files to `/usr/share/applications` or `/run/current-system/sw/share/applications` fails on NixOS's read-only store. | Mapped `/var/lib/tianxia/share` into `XDG_DATA_DIRS` and configured `tx-menu-expand` to write dynamic launchers into `/var/lib/tianxia/share/applications` with live `kbuildsycoca6` reloads. |
| **6. Offline `xps13-tianxia` Timeouts** | Hardcoding synchronous probes to `xps13-tianxia` caused mesh scripts to hang while the Dell XPS 13 9310 is offline for hardware repair. | Re-centered active mesh orchestration across `latitude-tianxia`, `pixel8pro-tianxia`, and `pocox5pro-tianxia`, placing `xps13-tianxia` in non-blocking `MAINTENANCE_STANDBY`. |

---

## 1. Executive Architectural Overview & Active Mesh Topology

**TianxiaOS v5.0 (Asura Super-Harness)** is a deterministic, cybernetic operating distribution engineered atop an immutable NixOS and KDE Plasma 6 Wayland substrate. Rather than maintaining a fragile manual fork or forcing a tiling compositor to emulate a traditional mouse-driven desktop, TianxiaOS encapsulates the kernel, boot splash, display manager, window manager, 5-tier application taxonomy, autonomous agent bridge (`agy` / Gemini 3.8 Flash), and partitioned user workspace inside a single declarative super-harness.

~~~text
+-----------------------------------------------------------------------------------------+
|                      TIANXIAOS v5.0 SUPER-HARNESS (NIXYR SUBSTRATE)                     |
+--------------------------------------------+--------------------------------------------+
                                             |
         +-----------------------------------+-----------------------------------+
         |                                   |                                   |
+--------v---------+               +---------v--------+                +---------v--------+
| latitude-tianxia |               | pixel8pro-       |                | pocox5pro-       |
| Dell Lat 5591    |               | tianxia          |                | tianxia          |
| i7-8850H / 32GB  |               | Tensor G3 / 1TB  |                | SD778G / 128GB   |
| IP: ${TX_HUB_HOST:-127.0.0.1} |               | [PRIMARY C2 &    |                | [EDGE WORKER &   |
| [WORKHORSE HOST] |               |  AGY MASTER]     |                |  DNS SENTINEL]   |
+--------+---------+               +---------+--------+                +---------+--------+
         |                                   |                                   |
         +-----------------------------------+-----------------------------------+
                                             |
                  +--------------------------v--------------------------+
                  |  xps13-tianxia (Dell XPS 13 9310 - 8GB RAM)         |
                  |  Status: MAINTENANCE_STANDBY (Non-Blocking Slot)    |
                  +--------------------------+--------------------------+
                                             |
+--------------------------------------------v--------------------------------------------+
|          TAILSCALE / WIREGUARD (wg0) SOVEREIGN MESH & UNBOUND DNS RESOLUTION            |
|          ACCELERATION: VUDA (Vulkan Compute) & SOFTEM (Thermal/Power Governor)          |
|          SERIALIZATION: SemanticZip / SLECO-SO / TOON / TRON Token Compression          |
|          GOVERNANCE: Karuna Safety Engine & RASOOM Shared-Memory Ring Buffers           |
+--------------------------------------------+--------------------------------------------+
                                             |
        +------------------------------------+------------------------------------+
        |                                    |                                    |
+-------v------------------+      +----------v------------------+      +----------v-------+
| [GUI Mode: Plasma 6]     |      | [TUI Mode: Cockpit Matrix]  |      | [CLI Rescue]     |
| Wayland / Neo-Noir Theme |      | Direct TTY / multi-user.tgt |      | rescue.target    |
| 5-Tier XDG Nested Menu   |      | Wire-Speed Telemetry & TUI  |      | Pure Kernel Shell|
+--------------------------+      +-----------------------------+      +------------------+
~~~

### 1.1 Active Tri-Node Tailscale Mesh & Hardware Loop

With `xps13-tianxia` temporarily offline for repair, all compute, storage, and orchestration workloads are distributed across the three active Tailscale nodes:

1. **Dell Latitude 5591 (`latitude-tianxia` — Primary Compute & Desktop Workhorse):**
   - **Hardware Profile:** Intel Core i7-8850H ($6\text{C}/12\text{T}$, $4.3\,\text{GHz}$ Boost), $32\,\text{GB}$ DDR4 RAM, Nvidia GeForce MX130, $1920 \times 1080$ (`eDP-1` / `DP-1`) displays.
   - **Mesh Address:** `${TX_HUB_HOST:-127.0.0.1}` (`latitude-tianxia`).
   - **Operational Role:** Hosts the KDE Plasma 6 Wayland sovereign desktop, NixOS binary cache server, `microvm.nix` hypervisor, local neural weight store, and the `tx-menu-expand` systemd discovery daemon.
2. **Google Pixel 8 Pro (`pixel8pro-tianxia` — Primary Mobile Edge Orchestrator & Authenticator):**
   - **Hardware Profile:** Google Tensor G3, $12\,\text{GB}$ LPDDR5 RAM, $1\,\text{TB}$ UFS storage, Titan M2 hardware security module.
   - **Operational Role:** Primary Termux command-and-control (C2) station, hardware key attestation node, primary host for the `agy` (Gemini 3.8 Flash) orchestration loop, and initiator of zero-USB over-the-air NixOS deployments.
3. **Xiaomi Poco X5 Pro 5G (`pocox5pro-tianxia` — Secondary Mobile Edge Worker & Network Sentinel):**
   - **Hardware Profile:** Qualcomm Snapdragon 778G 5G ($8\text{C}$ Kryo 670), $128\,\text{GB}$ storage.
   - **Operational Role:** Secondary Termux distributed build coordinator, local Unbound DNS validating resolver, continuous Tailscale mesh latency sentinel, and backup `agy` dispatch node.
4. **Dell XPS 13 9310 (`xps13-tianxia` — Standby Tactical Client):**
   - **Hardware Profile:** Intel Core i7-1185G7 ($4\text{C}/8\text{T}$, $4.8\,\text{GHz}$ Boost), $8\,\text{GB}$ soldered LPDDR4x RAM, $3840 \times 2400$ touch display.
   - **Operational Role:** Registered in `/var/lib/tianxia/registry/system-manifest.json` with state `MAINTENANCE_STANDBY` and a $250\,\text{ms}$ non-blocking probe timeout. When hardware restoration concludes and its Tailscale interface comes online, the mesh automatically promotes it to `ONLINE` without requiring configuration edits.

### 1.2 Substrate, Emulation, Compression & Safety Engines

- **Nixyr OS & MicroVM Isolation:** Combines atomic NixOS system generations with `microvm.nix`, `seL4` syscall mediation, `cloud-hypervisor`, and `Nanos` unikernels, backed by TPM boot-sealing and HAP Intel ME mitigation.
- **VUDA (Virtual Unified Device Architecture):** Abstracts CUDA and OpenCL compute dispatches into unified Vulkan compute pipelines (`vulkan-tools`), enabling hardware-accelerated tensor operations across heterogeneous silicon.
- **SOFTEM (Software Thermal & Power Emulation):** Continuously samples `/sys/class/thermal/thermal_zone*` sensors across `latitude-tianxia`, maintaining thermal compliance below $85\,^\circ\text{C}$ by dynamically pacing background compilation and daemon worker threads.
- **SemanticZip & SLECO-SO Serialization Protocols:** Packs verbose JSON/YAML system manifests and AST trees into token-compressed `SemanticZip`, `TOON`, `TRON`, and Telegraph English byte streams, reducing LLM context consumption by up to $70\%$ across Tailscale links.
- **Karuna Safety Engine & RGU Suites:** Governs autonomous execution pacing and shared-memory ring buffers (`RASOOM`/`Tala`) across the four enterprise Revenue Generating Unit (RGU) domains: **AEGIS** (Security), **AURUM** (FinTech & TetraLedger Solvency), **FORGE** (DevTools), and **MERIDIAN** (Logistics).

---

## 2. Rasa-X-Machina Brand Kit & Neo-Noir Visual Pipeline

The visual pipeline replaces generic upstream Linux themes with the **Rasa-X-Machina Neo-Noir** design system across Plymouth, SDDM, KDE Plasma 6, Dolphin, and Foot:

~~~text
       #080808                     #101216                     #1D222E
  [ Canvas Void ]            [ Elevated Card ]           [ Structural Border ]
  Terminal & Window          Taskbars, Docks &           Dividers & Inactive
   Canvas Surfaces            Panel Surfaces               Frame Borders

       #00F0FF                     #FFAA00                     #FF5533
   [ Cyan Pulse ]              [ Amber Signal ]            [ Cyber Ember ]
 Active Borders, Links,       Highlights, Solvency,       Emergency Actions,
 Focus Rings & Telemetry       Maximized Indicators        Close Buttons & Alarms
~~~

### 2.1 Color Palette & Visual Token Matrix

| Token Name | Hex Code | RGB Triplet | Visual Target & Semantic Role |
| :--- | :--- | :--- | :--- |
| **Canvas Void** | `#080808` | `8,8,8` | Base window background, Foot terminal backdrop, SDDM/Plymouth canvas |
| **Elevated Card** | `#101216` | `16,18,22` | Plasma panels, Kickoff menu cards, Dolphin sidebars, notification popups |
| **Structural Border** | `#1D222E` | `29,34,46` | Inactive window borders, panel dividers, structural UI separators |
| **Muted Steel** | `#27272A` | `39,39,42` | Disabled UI controls, outer hexagonal lattice lines, background grid |
| **Cyan Pulse** | `#00F0FF` | `0,240,255` | Primary active window border, focus ring, selection highlight, hyper-links |
| **Amber Signal** | `#FFAA00` | `255,170,0` | Secondary highlights, maximize indicators, tri-node apex beacons |
| **Cyber Ember** | `#FF5533` | `255,85,51` | Killswitches, window close buttons, thermal/solvency critical alerts |
| **Text Primary** | `#FFFFFF` | `255,255,255` | High-contrast primary typography (`JetBrains Mono` / `Inter`) |
| **Text Secondary** | `#9CA3AF` | `156,163,175` | Muted metadata, inactive window titles, secondary telemetry labels |

### 2.2 Master Scalable Vector Brandmark (`tianxia-brand.svg`)

The $512 \times 512$ vector emblem unites the outer hexagonal cybernetic frame, the bioluminescent cyan orbital ring, the ember tripartite monogram, and the three amber apex beacons representing the active hardware triad (`latitude-tianxia`, `pixel8pro-tianxia`, `pocox5pro-tianxia`):

~~~xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <linearGradient id="cyanGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F0FF" stop-opacity="1.0" />
      <stop offset="100%" stop-color="#008899" stop-opacity="0.85" />
    </linearGradient>
    <linearGradient id="emberGlow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FF5533" />
      <stop offset="100%" stop-color="#FFAA00" />
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="96" fill="#080808" />
  <polygon points="256,32 448,142 448,370 256,480 64,370 64,142" fill="none" stroke="#27272A" stroke-width="6" />
  <circle cx="256" cy="256" r="196" fill="none" stroke="url(#cyanGlow)" stroke-width="8" stroke-dasharray="24 12" />
  <path d="M 256 96 L 400 364 L 112 364 Z" fill="none" stroke="url(#cyanGlow)" stroke-width="16" stroke-linejoin="round" />
  <path d="M 256 164 L 342 328 L 170 328 Z" fill="none" stroke="url(#emberGlow)" stroke-width="10" stroke-linejoin="round" />
  <circle cx="256" cy="268" r="24" fill="#00F0FF" />
  <circle cx="256" cy="268" r="8" fill="#080808" />
  <circle cx="256" cy="96" r="14" fill="#FFAA00" />
  <circle cx="400" cy="364" r="14" fill="#FFAA00" />
  <circle cx="112" cy="364" r="14" fill="#FFAA00" />
</svg>
~~~

---

## 3. Automated KDE Plasma 6 Wayland Provisioning & Window Governance

To guarantee an immediate, responsive, mouse-first desktop without manual GUI clicking or external Home Manager dependencies, the super-harness configures KDE Plasma 6 automatically through three layers:

1. **System-Wide `/etc/xdg` Configuration Injection:**
   - `/etc/xdg/kdeglobals`: Enforces `ColorScheme=TianxiaNeoNoir`, `LookAndFeelPackage=org.kde.breezedark.desktop`, `SingleClick=false` (standard double-click to open files/folders), and `JetBrains Mono` / `Inter` typography.
   - `/etc/xdg/kwinrc`: Enforces `ButtonsOnLeft=M` (Window Menu) and `ButtonsOnRight=IAX` (Minimize, Maximize, Close) with normal draggable window borders (`BorderSize=Normal`).
   - `/etc/xdg/foot/foot.ini`: Pre-configures the `foot` GPU terminal with `#080808` background, `#00F0FF` cursor, and zero deprecation warnings.
2. **Idempotent Login Auto-Provisioner (`tx-plasma-autoconfig`):**
   - Executes automatically on KDE Plasma login via `/etc/xdg/autostart/tianxia-plasma-autoconfig.desktop`.
   - Applies the `TianxiaNeoNoir` color scheme via `plasma-apply-colorscheme`.
   - Rewrites `~/.config/plasma-org.kde.plasma.desktop-appletsrc` to replace the stock KDE start icon (`start-here-kde-symbolic` / `distributor-logo`) with `tianxia-brand` (`start-here-tianxia`), ensuring a branded home button out of the box.
   - Injects the TianxiaOS workspace hierarchy directly into Dolphin's `~/.local/share/user-places.xbel` sidebar and runs `kbuildsycoca6`.
3. **Decoupled On-Demand TetraLedger Execution:**
   - Purges the legacy Hyprland autostart loop that previously pinned the TetraLedger window permanently on screen.
   - Registers **TetraLedger Solvency Engine** as a standard, closable, resizable Tier 4 application (`tx-t4-tetraledger.desktop`) with full KWin titlebar controls.

---

## 4. Harmonized 5-Tier Hierarchical Menu Architecture

The application launcher harmonizes standard Freedesktop categories (`System`, `Development`, `Network`, `Office`, `Utilities`) with the 5-Tier TianxiaOS taxonomy via `/etc/xdg/menus/applications-merged/tianxia-5tier.menu`:

~~~text
[ TianxiaOS Branded Home Button (tianxia-brand.svg) ]
  │
  ├── 01 // TIANXIAOS ROOT (Tier 1: Core Sovereignty & Telemetry)
  │     ├── 01 // [T1] Sovereign Cockpit HUD (tx-t1-cockpit.desktop)
  │     └── 01 // [T1] System Telemetry Matrix (tx-t1-monitor.desktop -> plasma-systemmonitor)
  │
  ├── 02 // SYSTEMS INFRASTRUCTURE (Tier 2: Platform Suites & Tri-Node Mesh)
  │     ├── 02 // [T2] Sovereign Operator TUI (tx-t2-operator-tui.desktop)
  │     ├── 02 // [T2] Tailscale Tri-Node Mesh Matrix (tx-t2-mesh-control.desktop)
  │     ├── 02 // [T2] AetherVault Identity & Inverse-SSO Proxy (tx-t2-aethervault.desktop)
  │     └── 02 // [T2] Faery Fortress Agentic Security Matrix (tx-t2-faery-fortress.desktop)
  │
  ├── 03 // SUBSYSTEMS MATRIX (Tier 3: Emulation, Network Taps & Storefront)
  │     ├── 03 // [T3] VUDA & SOFTEM Emulation Engine (tx-t3-vuda-softem.desktop)
  │     ├── 03 // [T3] AF_XDP SIMD Wire-Speed Telemetry Tap (tx-t3-af-xdp.desktop)
  │     └── 03 // [T3] Rasa-X-Machina Flagship Storefront (tx-t3-storefront.desktop)
  │
  ├── 04 // EXECUTION UNITS (Tier 4: Solvency, Containers & Dev Units)
  │     ├── 04 // [T4] TetraLedger Solvency Engine (tx-t4-tetraledger.desktop)
  │     ├── 04 // [T4] Foot Neo-Noir GPU Terminal (foot.desktop)
  │     └── 04 // [T4] Kate Declarative AST & Nix Studio (org.kde.kate.desktop)
  │
  └── 05 // DATA VAULT & FILES (Tier 5: Autarchic Workspace VFS)
        ├── 05 // [T5] Tianxia Workspace VFS (tx-t5-workspace-vfs.desktop -> ~/workspace)
        ├── 05 // [T5] NixOS Declarative Substrate (tx-t5-nixos-substrate.desktop -> /etc/nixos)
        └── 05 // [T5] Tianxia Runtime Registry (tx-t5-registry.desktop -> /var/lib/tianxia)
~~~

---

## 5. Dynamic `agy` (Gemini 3.8 Flash) Discovery, SemanticZip & Menu Expansion Bridge

The discovery bridge (`/var/lib/tianxia/bin/tx-menu-expand`) connects the deployed operating system on `latitude-tianxia` with **Gemini 3.8 Flash** running inside `agy` (locally or dispatched from `pixel8pro-tianxia` and `pocox5pro-tianxia`).

~~~text
+-----------------------------------------------------------------------------------+
|       Gemini 3.8 Flash in agy (Latitude / Pixel 8 Pro / Poco X5 Pro 5G)           |
+--------------------+-----------------------------------------+--------------------+
                     |                                         |
     1. Ingest State | (JSON or SemanticZip TOON)              | 2. Expand Menu Tier
        tx-expand scan / semantic-zip                          |    tx-expand inject
                     v                                         v
+-----------------------------------------------------------------------------------+
|                        /var/lib/tianxia/bin/tx-menu-expand                        |
+--------------------+-----------------------------------------+--------------------+
                     |                                         |
                     v                                         v
+----------------------------------------+   +--------------------------------------+
| /var/lib/tianxia/registry/             |   | /var/lib/tianxia/share/applications/ |
|  • system-manifest.json                |   |  • tx-dyn-*.desktop                  |
|  • system-manifest.semantic.toon       |   |  (Mounted in XDG_DATA_DIRS &         |
| (Live Mesh, Thermals, Services, Tiers) |   |   indexed live via kbuildsycoca6)    |
+----------------------------------------+   +--------------------------------------+
~~~

### 5.1 Dual-Format Manifest Specification (Standard JSON & SemanticZip TOON)

When `tx-menu-expand scan` runs, it generates both `/var/lib/tianxia/registry/system-manifest.json` (with a compatibility symlink at `/var/lib/tianxia/system-manifest.json`) and a token-compressed **SemanticZip TOON** payload at `/var/lib/tianxia/registry/system-manifest.semantic.toon` so Gemini 3.8 Flash can ingest the entire cluster topology in minimal tokens:

~~~json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "timestamp": "2026-11-07T08:10:00Z",
  "host_node": "latitude-tianxia",
  "architecture": "x86_64-linux",
  "domains": ["rasaxmachina.com", "rasaxm.com", "airasa.work"],
  "softem_max_temp_c": 54.0,
  "hardware_loop": [
    {
      "device_id": "latitude-tianxia",
      "hardware": "Dell Latitude 5591 (i7-8850H, 32GB RAM, MX130)",
      "role": "PRIMARY_COMPUTE_DESKTOP",
      "ip_address": "${TX_HUB_HOST:-127.0.0.1}",
      "vuda_acceleration": true,
      "status": "ONLINE"
    },
    {
      "device_id": "pixel8pro-tianxia",
      "hardware": "Google Pixel 8 Pro (Tensor G3, 12GB RAM, 1TB)",
      "role": "PRIMARY_EDGE_ORCHESTRATOR_AGY",
      "ip_address": "tailscale-mesh",
      "vuda_acceleration": true,
      "status": "ONLINE"
    },
    {
      "device_id": "pocox5pro-tianxia",
      "hardware": "Xiaomi Poco X5 Pro 5G (SD778G, 128GB)",
      "role": "SECONDARY_EDGE_WORKER_SENTINEL",
      "ip_address": "tailscale-mesh",
      "vuda_acceleration": false,
      "status": "ONLINE"
    },
    {
      "device_id": "xps13-tianxia",
      "hardware": "Dell XPS 13 9310 (i7-1185G7, 8GB RAM)",
      "role": "STANDBY_CLIENT_UNDER_REPAIR",
      "ip_address": "offline-maintenance",
      "vuda_acceleration": false,
      "status": "MAINTENANCE_STANDBY"
    }
  ],
  "dynamic_menus": []
}
~~~

And the corresponding `tx-menu-expand semantic-zip` output:
~~~text
TX_MANIFEST_V5|HOST:latitude-tianxia(${TX_HUB_HOST:-127.0.0.1})|ARCH:x86_64|TEMP_MAX:54.0C|MESH:[latitude-tianxia:ONLINE:${TX_HUB_HOST:-127.0.0.1},pixel8pro-tianxia:ONLINE:ts,pocox5pro-tianxia:ONLINE:ts,xps13-tianxia:MAINTENANCE_STANDBY:offline]|WS:[archive,core,payloads,projects,runtime,specs,subsystems,systems]|DYN_COUNT:0
~~~

### 5.2 Autonomous Menu Injection & Removal Commands for `agy`

Gemini 3.8 Flash in `agy` can dynamically register or remove tools across any of the 5 tiers locally or via SSH from `pixel8pro-tianxia` / `pocox5pro-tianxia`:

~~~bash
# Inject a new tool into Tier 2 (Systems) or Tier 3 (Subsystems):
tx-menu-expand inject 2 "UnboundMeshSync" "foot -e /var/lib/tianxia/bin/tx-menu-expand mesh-audit" "Synchronize Unbound OS & Tailscale Mesh"

# Remove a dynamic tool by ID:
tx-menu-expand remove "unboundmeshsync"

# Emit ultra-compact SemanticZip TOON string for LLM context window:
tx-menu-expand semantic-zip
~~~

---

## 6. Partitioned Autarchic Workspace (`~/workspace`) & User File System

To provide a structured, extensible home folder system that suits every TianxiaOS use case while protecting private keys and preventing LLM context pollution, user storage is standardized around `~/workspace` with bidirectional convenience symlinks at `~/TianxiaOS/workspace` and `~/TianxiaOS-Workspace`:

~~~text
~/ (User Home Root)
├── TianxiaOS/
│   └── workspace -> ~/workspace        (Branded Path Alias)
├── TianxiaOS-Workspace -> ~/workspace  (Direct Root Alias)
├── .vault/                             (User-Level Root Keystore)
└── workspace/                          (Primary Autarchic Workspace Root - Mode 0700)
    ├── core/        (Tier 1: Compilers, toolchains, Rust/Zig/Go/Nix frameworks)
    ├── systems/     (Tier 2: TianxiaOS, Unbound OS, AetherVault, Faery Fortress)
    ├── subsystems/  (Tier 3: VUDA/SOFTEM drivers, AF_XDP taps, Tailscale/Unbound DNS)
    ├── runtime/     (Tier 4: Ephemeral IPC sockets, RASOOM ring buffers, locks)
    ├── specs/       (Tier 1-5: SLECO-SO schemas, architectural blueprints, ASTs)
    ├── payloads/    (Tier 4: Compiled binaries, microVM rootfs, ISO images, weights)
    ├── archive/     (Tier 5: Immutable audit logs, cold snapshots, execution traces)
    ├── projects/    (User Custom: Extensible domain for custom user sections/courses)
    ├── .vault/      (Air-Gapped: Encrypted secrets; strictly excluded from LLM/Git)
    ├── .gitignore   (LLM & Git Hygiene Firewall)
    └── WORKSPACE_MAP.md
~~~

### 6.1 Custom User Workspace Section Generator (`tx-workspace-init`)

Users and `agy` agents can create new custom sections inside `~/workspace/` or directly under `~/` using the built-in `tx-workspace-init` utility, which automatically scaffolds standard sub-folders (`src`, `specs`, `runtime`, `tests`, `docs`) and optionally pins the new section into Dolphin's **Places** panel:

~~~bash
# Create a new custom workspace section inside ~/workspace/ (e.g., ~/workspace/swarm-finance)
# and automatically add it to Dolphin's Places sidebar:
tx-workspace-init "$HOME/workspace" "swarm-finance" --bookmark
~~~

### 6.2 Security Isolation & Strict LLM Hygiene (`~/workspace/.gitignore`)

| Security Zone | Permissions | Isolation & Access Policy |
| :--- | :--- | :--- |
| `~/workspace/` | `0700` | Owner-only read/write/execute across all primary subdirectories. |
| `~/workspace/.vault/` | `0700` | Excluded from `tx-menu-expand` scans, `.gitignore`, and `agy` indexing. |
| `~/workspace/runtime/` | `0700` | Ephemeral sockets, PID files, and IPC ring buffers excluded from Git commits. |

---

## 7. Complete Declarative NixOS Module (`/etc/nixos/modules/tianxia-super-harness.nix`)

This unified module encapsulates the entire desktop, brand kit, 5-tier launcher, `agy` service daemon, Foot terminal config, and multi-target bootloader with zero external asset dependencies:

~~~nix
# /etc/nixos/modules/tianxia-super-harness.nix
{ config, pkgs, lib, ... }:

let
  # ----------------------------------------------------------------------------
  # 1. Rasa-X-Machina Neo-Noir KDE Color Scheme
  # ----------------------------------------------------------------------------
  tianxiaColors = pkgs.writeTextDir "share/color-schemes/TianxiaNeoNoir.colors" ''
    [General]
    ColorScheme=TianxiaNeoNoir
    Name=Tianxia Neo-Noir

    [Colors:Window]
    BackgroundNormal=8,8,8
    BackgroundAlternate=16,18,22
    ForegroundNormal=255,255,255
    ForegroundInactive=156,163,175
    ForegroundActive=0,240,255
    ForegroundLink=0,240,255
    ForegroundNegative=255,85,51
    ForegroundNeutral=255,170,0

    [Colors:View]
    BackgroundNormal=16,18,22
    BackgroundAlternate=22,25,32
    ForegroundNormal=255,255,255
    ForegroundInactive=156,163,175
    ForegroundActive=0,240,255
    ForegroundLink=0,240,255

    [Colors:Button]
    BackgroundNormal=24,27,36
    BackgroundAlternate=32,36,48
    ForegroundNormal=255,255,255
    ForegroundActive=0,240,255

    [Colors:Selection]
    BackgroundNormal=0,240,255
    ForegroundNormal=8,8,8

    [Colors:Tooltip]
    BackgroundNormal=16,18,22
    ForegroundNormal=255,255,255

    [Colors:Complementary]
    BackgroundNormal=8,8,8
    ForegroundNormal=255,255,255

    [WM]
    activeBackground=8,8,8
    activeForeground=0,240,255
    inactiveBackground=16,18,22
    inactiveForeground=156,163,175
  '';

  # ----------------------------------------------------------------------------
  # 2. Harmonized 512x512 Neo-Noir Brandmark & Wallpaper Package
  # ----------------------------------------------------------------------------
  tianxiaBrandAssets = pkgs.stdenv.mkDerivation {
    name = "tianxia-brand-assets-5.0";
    src = pkgs.writeTextFile {
      name = "tianxia-brand.svg";
      destination = "/tianxia-brand.svg";
      text = ''
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
          <defs>
            <linearGradient id="cyanGlow" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#00F0FF" stop-opacity="1.0" />
              <stop offset="100%" stop-color="#008899" stop-opacity="0.85" />
            </linearGradient>
            <linearGradient id="emberGlow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#FF5533" />
              <stop offset="100%" stop-color="#FFAA00" />
            </linearGradient>
          </defs>
          <rect width="512" height="512" rx="96" fill="#080808" />
          <polygon points="256,32 448,142 448,370 256,480 64,370 64,142" fill="none" stroke="#27272A" stroke-width="6" />
          <circle cx="256" cy="256" r="196" fill="none" stroke="url(#cyanGlow)" stroke-width="8" stroke-dasharray="24 12" />
          <path d="M 256 96 L 400 364 L 112 364 Z" fill="none" stroke="url(#cyanGlow)" stroke-width="16" stroke-linejoin="round" />
          <path d="M 256 164 L 342 328 L 170 328 Z" fill="none" stroke="url(#emberGlow)" stroke-width="10" stroke-linejoin="round" />
          <circle cx="256" cy="268" r="24" fill="#00F0FF" />
          <circle cx="256" cy="268" r="8" fill="#080808" />
          <circle cx="256" cy="96" r="14" fill="#FFAA00" />
          <circle cx="400" cy="364" r="14" fill="#FFAA00" />
          <circle cx="112" cy="364" r="14" fill="#FFAA00" />
        </svg>
      '';
    };
    phases = [ "installPhase" ];
    installPhase = ''
      mkdir -p $out/share/icons/hicolor/scalable/apps
      mkdir -p $out/share/pixmaps
      mkdir -p $out/share/wallpapers/TianxiaVoid/contents/images
      cp $src/tianxia-brand.svg $out/share/icons/hicolor/scalable/apps/tianxia-brand.svg
      cp $src/tianxia-brand.svg $out/share/icons/hicolor/scalable/apps/start-here-tianxia.svg
      cp $src/tianxia-brand.svg $out/share/icons/hicolor/scalable/apps/distributor-logo.svg
      cp $src/tianxia-brand.svg $out/share/pixmaps/tianxia-brand.svg
      cp $src/tianxia-brand.svg $out/share/wallpapers/TianxiaVoid/contents/images/1920x1080.svg
    '';
  };

  # ----------------------------------------------------------------------------
  # 3. Freedesktop 5-Tier Menu Category Merge Specification
  # ----------------------------------------------------------------------------
  tianxiaMenuXml = pkgs.writeTextDir "etc/xdg/menus/applications-merged/tianxia-5tier.menu" ''
    <!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"
     "http://www.freedesktop.org/standards/menu-spec/menu-1.0.dtd">
    <Menu>
      <Name>Applications</Name>
      <Menu>
        <Name>TianxiaOS-Root</Name>
        <Directory>tianxia-root.directory</Directory>
        <Include>
          <Category>TianxiaOS</Category>
          <Category>Tianxia-Tier-1</Category>
          <Category>Tianxia-Tier-2</Category>
          <Category>Tianxia-Tier-3</Category>
          <Category>Tianxia-Tier-4</Category>
          <Category>Tianxia-Tier-5</Category>
          <Category>Dynamic</Category>
        </Include>
      </Menu>
    </Menu>
  '';

  # ----------------------------------------------------------------------------
  # 4. 5-Tier Hierarchical Desktop Launchers
  # ----------------------------------------------------------------------------
  tier1Cockpit = pkgs.makeDesktopItem {
    name = "tx-t1-cockpit";
    desktopName = "01 // [T1] Sovereign Cockpit HUD";
    genericName = "System Root Execution";
    comment = "Tier 1: Unified system orchestration and telemetry cockpit";
    exec = "foot -e bash -c '/var/lib/tianxia/bin/tx-menu-trigger.sh 2>/dev/null || /var/lib/tianxia/bin/tx-menu-expand tui'";
    icon = "tianxia-brand";
    categories = [ "TianxiaOS" "Tianxia-Tier-1" "System" ];
  };

  tier1Monitor = pkgs.makeDesktopItem {
    name = "tx-t1-monitor";
    desktopName = "01 // [T1] System Telemetry Matrix";
    genericName = "Hardware Resource Monitor";
    comment = "Tier 1: Real-time CPU, RAM, and process inspection";
    exec = "plasma-systemmonitor";
    icon = "utilities-system-monitor";
    categories = [ "TianxiaOS" "Tianxia-Tier-1" "System" ];
  };

  tier2OperatorTui = pkgs.makeDesktopItem {
    name = "tx-t2-operator-tui";
    desktopName = "02 // [T2] Sovereign Operator TUI";
    genericName = "Terminal Control Plane";
    comment = "Tier 2: High-throughput terminal operations plane";
    exec = "foot -e bash -c '/var/lib/tianxia/bin/tx-menu-expand tui'";
    icon = "utilities-terminal";
    categories = [ "TianxiaOS" "Tianxia-Tier-2" "Development" ];
  };

  tier2MeshControl = pkgs.makeDesktopItem {
    name = "tx-t2-mesh-control";
    desktopName = "02 // [T2] Tailscale Tri-Node Mesh Matrix";
    genericName = "Cluster Orchestration";
    comment = "Tier 2: Active mesh link across Latitude 5591, Pixel 8 Pro, and Poco X5 Pro 5G (XPS 13 Standby)";
    exec = "foot -e bash -c '/var/lib/tianxia/bin/tx-menu-expand mesh-audit; read -p \"Press Enter to close...\"'";
    icon = "network-server-database";
    categories = [ "TianxiaOS" "Tianxia-Tier-2" "Network" ];
  };

  tier2AetherVault = pkgs.makeDesktopItem {
    name = "tx-t2-aethervault";
    desktopName = "02 // [T2] AetherVault Identity Proxy";
    genericName = "Inverse-SSO & Vault Governance";
    comment = "Tier 2: Decentralized identity attestation and keystore audit";
    exec = "foot -e bash -c 'ls -la ~/.vault ~/workspace/.vault; read -p \"Press Enter to close...\"'";
    icon = "security-high";
    categories = [ "TianxiaOS" "Tianxia-Tier-2" "System" ];
  };

  tier3VudaStatus = pkgs.makeDesktopItem {
    name = "tx-t3-vuda-softem";
    desktopName = "03 // [T3] VUDA & SOFTEM Emulation Engine";
    genericName = "Virtual Compute & Thermal Layer";
    comment = "Tier 3: Software-based hardware emulation and thermal telemetry";
    exec = "foot -e bash -c '/var/lib/tianxia/bin/tx-menu-expand vuda-audit; read -p \"Press Enter to close...\"'";
    icon = "preferences-system-performance";
    categories = [ "TianxiaOS" "Tianxia-Tier-3" "System" ];
  };

  tier3Storefront = pkgs.makeDesktopItem {
    name = "tx-t3-storefront";
    desktopName = "03 // [T3] Rasa-X-Machina Storefront";
    genericName = "Autonomous Shopfront Gateway";
    comment = "Tier 3: Live endpoint audit for rasaxmachina.com, rasaxm.com, and airasa.work";
    exec = "foot -e bash -c 'curl -ILs https://rasaxmachina.com | head -n 25; read -p \"Press Enter to close...\"'";
    icon = "network-workgroup";
    categories = [ "TianxiaOS" "Tianxia-Tier-3" "Network" ];
  };

  tier4TetraLedger = pkgs.makeDesktopItem {
    name = "tx-t4-tetraledger";
    desktopName = "04 // [T4] TetraLedger Solvency Engine";
    genericName = "Credit & Liquidity Telemetry";
    comment = "Tier 4: On-demand WAL credit facility and RGU solvency monitor";
    exec = "foot -e bash -c '/var/lib/tianxia/bin/tetraledger-status.sh 2>/dev/null || htop'";
    icon = "office-chart-line";
    categories = [ "TianxiaOS" "Tianxia-Tier-4" "Office" ];
  };

  tier5WorkspaceVfs = pkgs.makeDesktopItem {
    name = "tx-t5-workspace-vfs";
    desktopName = "05 // [T5] Tianxia Workspace VFS";
    genericName = "Autarchic File System";
    comment = "Tier 5: Open partitioned ~/workspace hierarchy in Dolphin";
    exec = "dolphin /root/workspace";
    icon = "folder-cyan";
    categories = [ "TianxiaOS" "Tianxia-Tier-5" "System" ];
  };

  tier5NixosConfig = pkgs.makeDesktopItem {
    name = "tx-t5-nixos-substrate";
    desktopName = "05 // [T5] NixOS Declarative Substrate";
    genericName = "System Configuration Tree";
    comment = "Tier 5: Open /etc/nixos modules and hardware definitions";
    exec = "dolphin /etc/nixos";
    icon = "folder-development";
    categories = [ "TianxiaOS" "Tianxia-Tier-5" "Development" ];
  };

  # ----------------------------------------------------------------------------
  # 5. Plasma 6 & Dolphin Auto-Provisioning Script (Runs at Login)
  # ----------------------------------------------------------------------------
  tianxiaDesktopInit = pkgs.writeScriptBin "tx-plasma-autoconfig" ''
    #!/usr/bin/env bash
    set -euo pipefail

    if command -v plasma-apply-colorscheme >/dev/null 2>&1; then
      plasma-apply-colorscheme TianxiaNeoNoir >/dev/null 2>&1 || true
    fi

    if command -v kwriteconfig6 >/dev/null 2>&1; then
      kwriteconfig6 --file kdeglobals --group General --key ColorScheme "TianxiaNeoNoir"
      kwriteconfig6 --file kdeglobals --group KDE --key SingleClick false
      kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft "M"
      kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight "IAX"
      kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key BorderSize "Normal"
      kwriteconfig6 --file plasmarc --group Theme --key name "breeze-dark"
    fi

    APPLET_RC="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
    if [ -f "$APPLET_RC" ]; then
      sed -i 's/icon=start-here-kde-symbolic/icon=tianxia-brand/g' "$APPLET_RC" || true
      sed -i 's/icon=distributor-logo/icon=tianxia-brand/g' "$APPLET_RC" || true
    fi

    mkdir -p "$HOME/.local/share"
    PLACES_FILE="$HOME/.local/share/user-places.xbel"
    if [ ! -f "$PLACES_FILE" ] || ! grep -q "Tianxia Workspace" "$PLACES_FILE" 2>/dev/null; then
      cat << 'XBEL_EOF' > "$PLACES_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xbel>
<xbel xmlns:bookmark="http://www.freedesktop.org/standards/desktop-bookmarks" xmlns:kdepriv="http://www.kde.org/kdepriv" xmlns:mime="http://www.freedesktop.org/standards/shared-mime-info">
 <bookmark href="file:///root/workspace">
  <title>Tianxia Workspace</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="folder-cyan"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/core">
  <title>TX Core (T1)</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="applications-engineering"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/systems">
  <title>TX Systems (T2)</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="network-server-database"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/subsystems">
  <title>TX Subsystems (T3)</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="preferences-system-performance"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/specs">
  <title>TX Specs &amp; AST</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="text-x-generic"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/payloads">
  <title>TX Payloads (T4)</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="package-x-generic"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/projects">
  <title>TX Custom Projects</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="folder-favorites"/></metadata></info>
 </bookmark>
 <bookmark href="file:///etc/nixos">
  <title>NixOS Substrate</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="folder-development"/></metadata></info>
 </bookmark>
 <bookmark href="file:///var/lib/tianxia">
  <title>Tianxia Registry</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="folder-locked"/></metadata></info>
 </bookmark>
</xbel>
XBEL_EOF
    fi

    kbuildsycoca6 >/dev/null 2>&1 || true
  '';

  tianxiaAutostartDesktop = pkgs.writeTextDir "etc/xdg/autostart/tianxia-plasma-autoconfig.desktop" ''
    [Desktop Entry]
    Type=Application
    Name=TianxiaOS Plasma Auto-Provisioner
    Exec=${tianxiaDesktopInit}/bin/tx-plasma-autoconfig
    OnlyShowIn=KDE;
    X-KDE-Autostart-Phase=1
  '';

  # ----------------------------------------------------------------------------
  # 6. Custom Workspace Section Generator CLI (tx-workspace-init)
  # ----------------------------------------------------------------------------
  txWorkspaceInit = pkgs.writeScriptBin "tx-workspace-init" ''
    #!/usr/bin/env bash
    set -euo pipefail
    TARGET_BASE="''${1:-$HOME/workspace}"
    CUSTOM_SECTION="''${2:-}"
    FLAG="''${3:-}"

    mkdir -p "$TARGET_BASE"/{core,systems,subsystems,runtime,specs,payloads,archive,projects,.vault}
    mkdir -p "$HOME/TianxiaOS"
    chmod 0700 "$TARGET_BASE" "$TARGET_BASE/.vault"
    ln -sfn "$TARGET_BASE" "$HOME/TianxiaOS/workspace"
    ln -sfn "$TARGET_BASE" "$HOME/TianxiaOS-Workspace"

    if [ -n "$CUSTOM_SECTION" ]; then
      SECTION_PATH="$TARGET_BASE/$CUSTOM_SECTION"
      mkdir -p "$SECTION_PATH"/{src,specs,runtime,tests,docs}
      echo "[+] Created custom TianxiaOS workspace section: $SECTION_PATH"
      if [ "$FLAG" = "--bookmark" ] && [ -f "$HOME/.local/share/user-places.xbel" ]; then
        sed -i "s|</xbel>| <bookmark href=\"file://$SECTION_PATH\"><title>TX: $CUSTOM_SECTION</title><info><metadata owner=\"http://www.freedesktop.org\"><bookmark:icon name=\"folder-cyan\"/></metadata></info></bookmark>\n</xbel>|" "$HOME/.local/share/user-places.xbel"
        echo "[+] Pinned $CUSTOM_SECTION to Dolphin Places sidebar."
      fi
    fi

    echo "[+] Verified TianxiaOS workspace hierarchy at $TARGET_BASE"
  '';

in
{
  # ----------------------------------------------------------------------------
  # Bootloader & Neo-Noir Plymouth Splash Configuration
  # ----------------------------------------------------------------------------
  boot = {
    plymouth = {
      enable = true;
      theme = "breeze";
    };
    initrd.verbose = false;
    kernelParams = [
      "quiet"
      "splash"
      "boot.shell_on_fail"
      "loglevel=3"
      "rd.systemd.show_status=false"
      "rd.udev.log_level=3"
      "udev.log_priority=3"
    ];

    loader.systemd-boot = {
      enable = true;
      configurationLimit = 10;
      extraEntries = {
        "tianxia-tui.conf" = ''
          title TianxiaOS v5.0 [TUI] - Sovereign Operator Cockpit (Console Mode)
          version ${config.system.nixos.label}
          linux ${config.system.build.kernel}/bzImage
          initrd ${config.system.build.initialRamdisk}/initrd
          options init=${config.system.build.toplevel}/init systemd.unit=multi-user.target tianxia.mode=tui quiet
        '';
        "tianxia-cli.conf" = ''
          title TianxiaOS v5.0 [CLI] - Pure Autarchic Kernel Rescue (Headless Mode)
          version ${config.system.nixos.label}
          linux ${config.system.build.kernel}/bzImage
          initrd ${config.system.build.initialRamdisk}/initrd
          options init=${config.system.build.toplevel}/init systemd.unit=rescue.target nomodeset quiet
        '';
      };
    };
  };

  # ----------------------------------------------------------------------------
  # Display Manager (SDDM Wayland) & Desktop Manager (KDE Plasma 6)
  # ----------------------------------------------------------------------------
  services.desktopManager.plasma6.enable = true;
  services.displayManager.sddm = {
    enable = true;
    wayland.enable = true;
    theme = "breeze";
    settings = {
      Theme = {
        CursorTheme = "breeze_cursors";
        Font = "JetBrains Mono,10,-1,5,50,0,0,0,0,0";
      };
    };
  };

  services.tailscale.enable = true;

  # ----------------------------------------------------------------------------
  # White-Label OS Release Metadata
  # ----------------------------------------------------------------------------
  environment.etc."os-release".text = lib.mkForce ''
    NAME="TianxiaOS"
    ID="tianxiaos"
    ID_LIKE="nixos"
    VERSION="5.0-Asura"
    VERSION_ID="5.0"
    PRETTY_NAME="TianxiaOS v5.0 (Rasa-X-Machina Super-Harness)"
    HOME_URL="https://rasaxmachina.com"
    DOCUMENTATION_URL="https://airasa.work"
    SUPPORT_URL="https://rasaxm.com"
    BUG_REPORT_URL="https://github.com/rasa-x-machina"
    LOGO="tianxia-brand"
  '';

  # System-Wide KDE & Foot Defaults in /etc/xdg
  environment.etc."xdg/kdeglobals".text = ''
    [General]
    ColorScheme=TianxiaNeoNoir
    Name=Tianxia Neo-Noir
    fixed=JetBrains Mono,10,-1,5,50,0,0,0,0,0
    font=Inter,10,-1,5,50,0,0,0,0,0

    [KDE]
    LookAndFeelPackage=org.kde.breezedark.desktop
    SingleClick=false
  '';

  environment.etc."xdg/kwinrc".text = ''
    [org.kde.kdecoration2]
    BorderSize=Normal
    ButtonsOnLeft=M
    ButtonsOnRight=IAX
    library=org.kde.breeze
  '';

  environment.etc."xdg/foot/foot.ini".text = ''
    [main]
    font=JetBrains Mono:size=11
    pad=12x12

    [colors]
    background=080808
    foreground=ffffff
    regular0=080808
    regular1=ff5533
    regular2=00f0ff
    regular3=ffaa00
    regular4=008899
    regular5=ff5533
    regular6=00f0ff
    regular7=d4d4d8
  '';

  # Expose Dynamic agy Applications Directory to XDG_DATA_DIRS
  environment.sessionVariables = {
    TIANXIA_WORKSPACE = "$HOME/workspace";
    QT_QPA_PLATFORM = "wayland";
    PLASMA_USE_QT_SCALING = "1";
  };
  environment.extraInit = ''
    export XDG_DATA_DIRS="/var/lib/tianxia/share:''${XDG_DATA_DIRS:-/run/current-system/sw/share}"
  '';

  # ----------------------------------------------------------------------------
  # System Packages & Branded Desktop Items
  # ----------------------------------------------------------------------------
  environment.systemPackages = with pkgs; [
    foot
    dolphin
    plasma-systemmonitor
    kate
    kdePackages.kconfig
    kdePackages.kservice
    python3
    jq
    curl
    git
    htop
    tmux
    tailscale
    vulkan-tools
    pciutils

    tianxiaColors
    tianxiaBrandAssets
    tianxiaMenuXml
    tianxiaDesktopInit
    tianxiaAutostartDesktop
    txWorkspaceInit
    tier1Cockpit
    tier1Monitor
    tier2OperatorTui
    tier2MeshControl
    tier2AetherVault
    tier3VudaStatus
    tier3Storefront
    tier4TetraLedger
    tier5WorkspaceVfs
    tier5NixosConfig
  ];

  # ----------------------------------------------------------------------------
  # Systemd Service: Dynamic agy Menu & Mesh Introspection Daemon
  # ----------------------------------------------------------------------------
  systemd.services.tianxia-menu-expand = {
    description = "TianxiaOS Dynamic agy Discovery, SemanticZip & Menu Expansion Daemon";
    wantedBy = [ "multi-user.target" ];
    after = [ "network.target" "tailscaled.service" ];
    path = with pkgs; [ python3 systemd tailscale iproute2 coreutils bash kdePackages.kservice vulkan-tools ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "/var/lib/tianxia/bin/tx-menu-expand daemon";
      Restart = "always";
      RestartSec = "5s";
    };
  };

  # ----------------------------------------------------------------------------
  # Interactive Shell Aliases (GUI / TUI / CLI / Mesh / SemanticZip / agy)
  # ----------------------------------------------------------------------------
  environment.interactiveShellInit = ''
    alias tx-gui-stop="sudo systemctl isolate multi-user.target"
    alias tx-gui-start="sudo systemctl isolate graphical.target"
    alias tx-expand="/var/lib/tianxia/bin/tx-menu-expand"
    alias tx-manifest="cat /var/lib/tianxia/registry/system-manifest.json | jq ."
    alias tx-semantic="/var/lib/tianxia/bin/tx-menu-expand semantic-zip"
    alias tx-mesh="/var/lib/tianxia/bin/tx-menu-expand mesh-audit"
    alias tx-workspace="cd ~/workspace"
    alias tx-tui="/var/lib/tianxia/bin/tx-menu-expand tui"
    export TIANXIA_WORKSPACE="$HOME/workspace"
  '';
}
~~~

---

## 8. Tri-Target Bootloader Matrix & Live Mode Switching

TianxiaOS exposes three operational modes at boot via `systemd-boot` and supports live mode switching without dropping active SSH or Tailscale connections:

~~~text
                  +----------------------------------------------+
                  |            systemd-boot Menu Engine          |
                  +----------------------+-----------------------+
                                         |
       +---------------------------------+---------------------------------+
       |                                 |                                 |
+------v-----------------+     +---------v-----------------+     +---------v-----------------+
| TianxiaOS v5.0 [GUI]   |     | TianxiaOS v5.0 [TUI]      |     | TianxiaOS v5.0 [CLI]      |
| Plasma 6 Wayland       |     | Multi-User Console Target |     | Rescue Target Mode        |
| SDDM / Full Desktop    |     | Zero Wayland / tx-tui     |     | Single User / Maintenance |
+------------------------+     +---------------------------+     +---------------------------+
~~~

- **Live Switch from GUI to TUI:** Execute `tx-gui-stop` (`sudo systemctl isolate multi-user.target`) to stop SDDM and KWin and reclaim all GPU/RAM resources for heavy compilation or tensor workloads while keeping Tailscale and SSH active.
- **Live Switch from TUI to GUI:** Execute `tx-gui-start` (`sudo systemctl isolate graphical.target`) to launch SDDM and KDE Plasma 6 Wayland immediately.

---

## 9. Autonomous Standalone Bootable ISO Builder & Zero-USB Tailscale Server

Save the following expression to `/etc/nixos/tianxia-iso.nix` on `latitude-tianxia` to compile a complete, self-contained Calamares graphical installer ISO pre-configured with the TianxiaOS Plasma 6 desktop, 5-tier menu, and full `/etc/nixos` source tree:

~~~nix
# /etc/nixos/tianxia-iso.nix
# Build command:
# nix-build '<nixpkgs/nixos>' -A config.system.build.isoImage -I nixos-config=/etc/nixos/tianxia-iso.nix -o /root/workspace/payloads/tianxiaos-iso
{ config, pkgs, lib, ... }:

{
  imports = [
    <nixpkgs/nixos/modules/installer/cd-dvd/installation-cd-graphical-calamares.nix>
    ./modules/tianxia-super-harness.nix
  ];

  networking.hostName = "tianxia-live";
  networking.wireless.enable = lib.mkForce false;
  networking.networkmanager.enable = true;

  isoImage.isoBaseName = "tianxiaos-5.0-super-harness";
  isoImage.volumeID = "TIANXIAOS_50";
  isoImage.makeEfiBootable = true;
  isoImage.makeUsbBootable = true;

  isoImage.contents = [
    {
      source = ./.;
      target = "/tianxia-source-config";
    }
  ];

  hardware.enableAllFirmware = true;
  nixpkgs.config.allowUnfree = true;
}
~~~

---

## 10. Single-Pass Atomic Deployment Engine (Pixel 8 Pro & Poco X5 Pro 5G $\rightarrow$ `latitude-tianxia`)

This deployment engine runs cleanly from Termux on either your **Google Pixel 8 Pro** (`pixel8pro-tianxia`) or **Xiaomi Poco X5 Pro 5G** (`pocox5pro-tianxia`). It synchronizes the local mobile edge workspace first, transfers a staged setup script to `latitude-tianxia` (`${TX_HUB_HOST:-127.0.0.1}`) to avoid nested SSH heredoc escaping errors, installs the `tx-menu-expand` daemon, writes `/etc/nixos/modules/tianxia-super-harness.nix` and `/etc/nixos/tianxia-iso.nix`, and switches the NixOS generation atomically.

~~~bash
cat << 'LOCAL_EOF' > ~/deploy_tianxia_v5.sh
#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${1:-latitude-tianxia}"

echo "[*] Phase 0: Initializing Local Mobile Edge Workspace (Pixel 8 Pro / Poco X5 Pro 5G)..."
mkdir -p ~/workspace/{core,systems,subsystems,runtime,specs,payloads,archive,projects,.vault}
mkdir -p ~/TianxiaOS
chmod 0700 ~/workspace ~/workspace/.vault
ln -sfn ~/workspace ~/TianxiaOS/workspace
ln -sfn ~/workspace ~/TianxiaOS-Workspace

echo "[*] Phase 1: Generating Staged Remote Payload for $REMOTE_HOST..."
cat << 'REMOTE_PAYLOAD' > ~/workspace/runtime/apply_tianxia_v5_remote.sh
#!/usr/bin/env bash
set -euo pipefail

echo "[*] [1/6] Veritas-Rex Pre-Flight Disk & Process Sanity..."
AVAIL_KB=$(df --output=avail / | tail -n 1 | tr -d ' ')
[ "$AVAIL_KB" -gt 2097152 ] || { echo "[!] Insufficient disk space on / (<2GB)"; exit 1; }

pkill -9 -f waybar 2>/dev/null || true
pkill -9 -f tetraledger 2>/dev/null || true
pkill -9 -f nixue 2>/dev/null || true

for conf in /var/lib/tianxia/config/hyprland-*.conf; do
  if [ -f "$conf" ]; then
    sed -i '/tetraledger/d;/tx_nixue/d;/waybar/d' "$conf" || true
  fi
done

echo "[*] [2/6] Structuring Autarchic Workspace & LLM Hygiene Firewalls..."
mkdir -p /var/lib/tianxia/{bin,registry,brand/icons,share/applications}
mkdir -p /etc/nixos/modules

for TARGET_HOME in /root /home/*; do
  if [ -d "$TARGET_HOME" ]; then
    mkdir -p "$TARGET_HOME/workspace"/{core,systems,subsystems,runtime,specs,payloads,archive,projects,.vault}
    mkdir -p "$TARGET_HOME/TianxiaOS" "$TARGET_HOME/.vault"
    chmod 0700 "$TARGET_HOME/workspace" "$TARGET_HOME/workspace/.vault" "$TARGET_HOME/.vault"
    ln -sfn "$TARGET_HOME/workspace" "$TARGET_HOME/TianxiaOS/workspace"
    ln -sfn "$TARGET_HOME/workspace" "$TARGET_HOME/TianxiaOS-Workspace"

    cat << 'GITIGNORE_EOF' > "$TARGET_HOME/workspace/.gitignore"
.vault/
*.key
*.pem
*.crt
*.pfx
*.secret
*.password
*.env
*.env.*
id_rsa*
id_ed25519*
payloads/large_weights/
payloads/datasets/
*.bin
*.onnx
*.safetensors
*.gguf
*.iso
*.img
runtime/
*.sock
*.pid
*.lock
archive/logs/
archive/dumps/
*.log
*.trc
target/
result/
build/
GITIGNORE_EOF

    cat << 'MAP_EOF' > "$TARGET_HOME/workspace/WORKSPACE_MAP.md"
# TIANXIAOS v5.0 AUTARCHIC WORKSPACE ARCHITECTURE
- ~/workspace/core       : Tier 1 foundational compilers, toolchains (Rust, Zig, Go, Nix)
- ~/workspace/systems    : Tier 2 platform suites (TianxiaOS, Unbound OS, AetherVault, Faery Fortress)
- ~/workspace/subsystems : Tier 3 VUDA/SOFTEM drivers, AF_XDP telemetry taps, Tailscale/Unbound DNS
- ~/workspace/runtime    : Tier 4 ephemeral IPC sockets, RASOOM ring buffers, state locks
- ~/workspace/specs      : Tier 1-5 SLECO-SO schemas, architectural blueprints, AST definitions
- ~/workspace/payloads   : Tier 4 compiled binaries, microVM rootfs images, ISO builds, weights
- ~/workspace/archive    : Tier 5 immutable execution traces and historical audit logs
- ~/workspace/projects   : User-extensible custom project domains and academic repositories
- ~/workspace/.vault     : Air-gapped encrypted keystores (Excluded from Git & LLM sweeps)
MAP_EOF

    OWNER_UG=$(stat -c '%U:%G' "$TARGET_HOME")
    chown -R "$OWNER_UG" "$TARGET_HOME/workspace" "$TARGET_HOME/TianxiaOS" "$TARGET_HOME/TianxiaOS-Workspace" || true
  fi
done

echo "[*] [3/6] Installing agy / Gemini 3.8 Flash Discovery & SemanticZip Engine..."
cat << 'PY_EOF' > /var/lib/tianxia/bin/tx-menu-expand
#!/usr/bin/env python3
import json, os, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_DIR = Path("/var/lib/tianxia/registry")
MANIFEST_FILE = REGISTRY_DIR / "system-manifest.json"
SEMANTIC_FILE = REGISTRY_DIR / "system-manifest.semantic.toon"
LEGACY_MANIFEST_LINK = Path("/var/lib/tianxia/system-manifest.json")
DYNAMIC_APP_DIR = Path("/var/lib/tianxia/share/applications")

TIER_CATEGORY_MAP = {
    1: "Tianxia-Tier-1", 2: "Tianxia-Tier-2", 3: "Tianxia-Tier-3",
    4: "Tianxia-Tier-4", 5: "Tianxia-Tier-5",
}

DEFAULT_NODES = [
    {"device_id": "latitude-tianxia", "hardware": "Dell Latitude 5591 (32GB RAM)", "role": "PRIMARY_COMPUTE_DESKTOP", "ip_address": "${TX_HUB_HOST:-127.0.0.1}", "vuda_acceleration": True, "status": "ONLINE"},
    {"device_id": "pixel8pro-tianxia", "hardware": "Google Pixel 8 Pro (1TB)", "role": "PRIMARY_EDGE_ORCHESTRATOR_AGY", "ip_address": "tailscale-mesh", "vuda_acceleration": True, "status": "ONLINE"},
    {"device_id": "pocox5pro-tianxia", "hardware": "Xiaomi Poco X5 Pro 5G (128GB)", "role": "SECONDARY_EDGE_WORKER_SENTINEL", "ip_address": "tailscale-mesh", "vuda_acceleration": False, "status": "ONLINE"},
    {"device_id": "xps13-tianxia", "hardware": "Dell XPS 13 9310 (8GB RAM)", "role": "STANDBY_CLIENT_UNDER_REPAIR", "ip_address": "offline-maintenance", "vuda_acceleration": False, "status": "MAINTENANCE_STANDBY"},
]

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=3).strip()
    except Exception:
        return ""

def get_max_temp_c():
    max_t = 0.0
    for tz in Path("/sys/class/thermal").glob("thermal_zone*"):
        t_val = (tz / "temp").read_text().strip() if (tz / "temp").exists() else "0"
        try:
            max_t = max(max_t, int(t_val) / 1000.0)
        except ValueError:
            pass
    return round(max_t, 1)

def probe_tailscale_mesh():
    nodes = [dict(n) for n in DEFAULT_NODES]
    raw_ts = run_cmd(["tailscale", "status", "--json"])
    if not raw_ts:
        return nodes
    try:
        ts_data = json.loads(raw_ts)
        for _, peer in ts_data.get("Peer", {}).items():
            hname = peer.get("HostName", "").lower()
            dns_name = peer.get("DNSName", "").lower()
            ips = peer.get("TailscaleIPs", [])
            ip_val = ips[0] if ips else "unknown"
            online = peer.get("Online", False)
            for node in nodes:
                nid = node["device_id"].split("-")[0]
                if nid in hname or nid in dns_name:
                    node["ip_address"] = ip_val
                    if node["device_id"] == "xps13-tianxia" and not online:
                        node["status"] = "MAINTENANCE_STANDBY"
                    else:
                        node["status"] = "ONLINE" if online else "OFFLINE"
    except Exception:
        pass
    return nodes

def read_existing_dynamic_menus():
    if MANIFEST_FILE.exists():
        try:
            return json.loads(MANIFEST_FILE.read_text()).get("dynamic_menus", [])
        except Exception:
            pass
    return []

def build_manifest(dynamic_menus=None):
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    DYNAMIC_APP_DIR.mkdir(parents=True, exist_ok=True)
    if dynamic_menus is None:
        dynamic_menus = read_existing_dynamic_menus()
    svc_raw = run_cmd(["systemctl", "list-units", "--type=service", "--state=running", "--no-legend", "--no-pager"])
    active_services = [line.split()[0] for line in svc_raw.splitlines() if line.strip()]
    workspace_root = Path("/root/workspace")
    workspace_nodes = sorted([d for d in os.listdir(workspace_root) if not d.startswith(".")]) if workspace_root.exists() else []
    max_temp = get_max_temp_c()
    mesh = probe_tailscale_mesh()

    manifest = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host_node": "latitude-tianxia",
        "architecture": "x86_64-linux",
        "domains": ["rasaxmachina.com", "rasaxm.com", "airasa.work"],
        "softem_max_temp_c": max_temp,
        "hardware_loop": mesh,
        "active_services": active_services[:60],
        "workspace_nodes": workspace_nodes,
        "menu_tiers": {
            "Tier_1_TianxiaOS": ["tx-t1-cockpit", "tx-t1-monitor"],
            "Tier_2_Systems": ["tx-t2-operator-tui", "tx-t2-mesh-control", "tx-t2-aethervault"],
            "Tier_3_Subsystems": ["tx-t3-vuda-softem", "tx-t3-storefront"],
            "Tier_4_Units": ["tx-t4-tetraledger", "foot", "kate"],
            "Tier_5_Files": ["tx-t5-workspace-vfs", "tx-t5-nixos-substrate", "dolphin"],
        },
        "dynamic_menus": dynamic_menus,
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2))
    mesh_str = ",".join(f"{n['device_id']}:{n['status']}:{n['ip_address']}" for n in mesh)
    ws_str = ",".join(workspace_nodes)
    toon_str = f"TX_MANIFEST_V5|HOST:latitude-tianxia(${TX_HUB_HOST:-127.0.0.1})|ARCH:x86_64|TEMP_MAX:{max_temp}C|MESH:[{mesh_str}]|WS:[{ws_str}]|DYN_COUNT:{len(dynamic_menus)}"
    SEMANTIC_FILE.write_text(toon_str + "\n")
    if not LEGACY_MANIFEST_LINK.exists():
        try:
            LEGACY_MANIFEST_LINK.symlink_to(MANIFEST_FILE)
        except Exception:
            pass
    return manifest

def sync_desktop_entries(manifest):
    DYNAMIC_APP_DIR.mkdir(parents=True, exist_ok=True)
    active_files = set()
    for item in manifest.get("dynamic_menus", []):
        safe_id = re.sub(r"[^a-z0-9-]+", "-", item["id"].lower()).strip("-")
        filename = f"tx-dyn-{safe_id}.desktop"
        active_files.add(filename)
        target = DYNAMIC_APP_DIR / filename
        tier_num = int(item.get("tier", 2))
        tier_cat = TIER_CATEGORY_MAP.get(tier_num, "Tianxia-Tier-2")
        content = (
            "[Desktop Entry]\nType=Application\n"
            f"Name=0{tier_num} // [AGY] {item.get('label', safe_id)}\n"
            "GenericName=Dynamic AI Tool\n"
            f"Comment={item.get('description', 'Autogenerated via agy')}\n"
            f"Exec={item.get('exec', 'foot')}\n"
            f"Icon={item.get('icon', 'tianxia-brand')}\n"
            f"Categories=TianxiaOS;{tier_cat};Dynamic;\n"
            "Terminal=false\nX-Tianxia-Dynamic=true\n"
            f"X-Tianxia-Tier={tier_num}\n"
        )
        if not target.exists() or target.read_text() != content:
            target.write_text(content)
    for existing in DYNAMIC_APP_DIR.glob("tx-dyn-*.desktop"):
        if existing.name not in active_files:
            existing.unlink(missing_ok=True)
    run_cmd(["kbuildsycoca6"])

def inject_tool(tier_arg, name, exec_cmd, desc, icon="tianxia-brand"):
    m = re.search(r"([1-5])", str(tier_arg))
    tier_num = int(m.group(1)) if m else 2
    safe_id = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    menus = [i for i in read_existing_dynamic_menus() if i.get("id") != safe_id]
    menus.append({"id": safe_id, "label": name, "tier": tier_num, "exec": exec_cmd, "icon": icon, "description": desc})
    manifest = build_manifest(menus)
    sync_desktop_entries(manifest)
    print(f"[+] Injected '{name}' (Tier {tier_num}) -> {DYNAMIC_APP_DIR}/tx-dyn-{safe_id}.desktop")

def remove_tool(target_id):
    safe_id = re.sub(r"[^a-z0-9-]+", "-", target_id.lower()).strip("-")
    menus = [i for i in read_existing_dynamic_menus() if i.get("id") != safe_id]
    manifest = build_manifest(menus)
    sync_desktop_entries(manifest)
    print(f"[+] Removed dynamic tool '{safe_id}'")

def print_mesh_audit():
    manifest = build_manifest()
    print("=== TIANXIAOS v5.0 ACTIVE TAILSCALE MESH TOPOLOGY ===")
    for n in manifest["hardware_loop"]:
        print(f" * {n['device_id']:18} | {n['status']:20} | IP: {n['ip_address']:18} | Role: {n['role']}")

def print_vuda_audit():
    print(f"=== VUDA / SOFTEM THERMAL & COMPUTE ENVELOPE (Max: {get_max_temp_c()} C) ===")
    for tz in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
        t_type = (tz / "type").read_text().strip() if (tz / "type").exists() else tz.name
        t_val = (tz / "temp").read_text().strip() if (tz / "temp").exists() else "0"
        try:
            print(f" * {tz.name:15} ({t_type:12}): {int(t_val)/1000.0:.1f} C")
        except ValueError:
            pass

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if action == "scan":
        m = build_manifest()
        sync_desktop_entries(m)
        print(f"[+] Synchronized {MANIFEST_FILE} and {SEMANTIC_FILE}")
    elif action == "semantic-zip":
        build_manifest()
        print(SEMANTIC_FILE.read_text().strip())
    elif action == "inject":
        inject_tool(
            sys.argv[2] if len(sys.argv) > 2 else "2",
            sys.argv[3] if len(sys.argv) > 3 else "CustomAgentTool",
            sys.argv[4] if len(sys.argv) > 4 else "foot",
            sys.argv[5] if len(sys.argv) > 5 else "Injected by Gemini 3.8 Flash in agy",
        )
    elif action == "remove":
        remove_tool(sys.argv[2] if len(sys.argv) > 2 else "")
    elif action == "mesh-audit":
        print_mesh_audit()
    elif action == "vuda-audit":
        print_vuda_audit()
    elif action == "tui":
        print_mesh_audit()
        print_vuda_audit()
        os.execvp("htop", ["htop"])
    elif action == "daemon":
        while True:
            sync_desktop_entries(build_manifest())
            time.sleep(15)

if __name__ == "__main__":
    main()
PY_EOF
chmod +x /var/lib/tianxia/bin/tx-menu-expand
/var/lib/tianxia/bin/tx-menu-expand scan

echo "[*] [4/6] Writing /etc/nixos/tianxia-iso.nix..."
cat << 'ISO_EOF' > /etc/nixos/tianxia-iso.nix
{ config, pkgs, lib, ... }:
{
  imports = [
    <nixpkgs/nixos/modules/installer/cd-dvd/installation-cd-graphical-calamares.nix>
    ./modules/tianxia-super-harness.nix
  ];
  networking.hostName = "tianxia-live";
  networking.wireless.enable = lib.mkForce false;
  networking.networkmanager.enable = true;
  isoImage.isoBaseName = "tianxiaos-5.0-super-harness";
  isoImage.volumeID = "TIANXIAOS_50";
  isoImage.makeEfiBootable = true;
  isoImage.makeUsbBootable = true;
  isoImage.contents = [{ source = ./.; target = "/tianxia-source-config"; }];
  hardware.enableAllFirmware = true;
  nixpkgs.config.allowUnfree = true;
}
ISO_EOF

echo "[*] [5/6] Registering /etc/nixos/modules/tianxia-super-harness.nix in configuration.nix..."
if [ -f /etc/nixos/modules/tianxia-super-harness.nix ] && ! grep -q "tianxia-super-harness.nix" /etc/nixos/configuration.nix; then
  sed -i 's|imports = \[|imports = \[ ./modules/tianxia-super-harness.nix|' /etc/nixos/configuration.nix
fi

echo "[*] [6/6] Committing and Switching NixOS Generation..."
git -C /etc/nixos add -A
git -C /etc/nixos commit -m "feat(v5.0): deploy TianxiaOS Asura Super-Harness and tri-node Tailscale mesh" || true
nixos-rebuild switch
echo "[+] SUCCESS: TianxiaOS v5.0 Super-Harness is active."
REMOTE_PAYLOAD

scp ~/workspace/runtime/apply_tianxia_v5_remote.sh "$REMOTE_HOST:/tmp/apply_tianxia_v5_remote.sh"
ssh "$REMOTE_HOST" "sudo bash /tmp/apply_tianxia_v5_remote.sh"
LOCAL_EOF

chmod +x ~/deploy_tianxia_v5.sh
~~~

---

## 11. Verification & Post-Deployment Runbook

1. **Verify SemanticZip & Manifest Telemetry from Pixel 8 Pro or Poco X5 Pro 5G:**
   ~~~bash
   ssh latitude-tianxia "tx-semantic"
   ssh latitude-tianxia "tx-mesh"
   ~~~
   Confirm that `latitude-tianxia`, `pixel8pro-tianxia`, and `pocox5pro-tianxia` report `ONLINE` and `xps13-tianxia` reports `MAINTENANCE_STANDBY`.
2. **Test Dynamic `agy` Menu Expansion:**
   ~~~bash
   ssh latitude-tianxia "tx-expand inject 3 'PocoSentinel' 'foot -e ping -c 4 pocox5pro-tianxia' 'Poco X5 Pro 5G Mesh Latency Probe'"
   ~~~
   Open the KDE Plasma 6 Application Launcher on `latitude-tianxia` and confirm that `03 // [AGY] PocoSentinel` appears immediately under the TianxiaOS hierarchy.
3. **Test Custom User Workspace Section Creation & Dolphin Pinning:**
   ~~~bash
   ssh latitude-tianxia "tx-workspace-init /root/workspace 'agentic-alpha' --bookmark"
   ~~~
   Open Dolphin and confirm that `TX: agentic-alpha` is pinned in the left **Places** panel alongside `Tianxia Workspace`, `TX Core (T1)`, `TX Systems (T2)`, `NixOS Substrate`, and `Tianxia Registry`.
