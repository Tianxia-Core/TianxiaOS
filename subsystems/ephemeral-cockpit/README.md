# TianxiaOS Polyglot Ephemeral Cockpit & Sovereign Menu System

## Architectural Overview
This subsystem implements the **$5 \times 3 \times 3$ Sovereign Hyper-Lattice** architecture specified in `accomplished/TianxiaOS Polyglot Ephemeral Cockpit & Sovereign Menu Master Specification.md`:
* **5 Structural Tiers:** Miller Column Lattice (`TianxiaOS` $\rightarrow$ `System` $\rightarrow$ `Subsystem` $\rightarrow$ `Unit` $\rightarrow$ `File & Atomic State`).
* **3 Execution Planes:** Keychord Router (`Plane A: Native Zero-Copy Inspect`, `Plane B: Elastic Semi-Containerized Namespace`, `Plane C: Sovereign Ephemeral MicroVM`).
* **3 Ephemeral Modalities:** Spatial Muscle-Memory Spine, `SOFTEM` Huber-Boosted Ephemeral Hot-Nodes, and Port `3109` `MANAS` Bimodal Intent Bar.

---

## Specification Lifecycle Governance

All architectural specifications follow the mandatory 3-stage protocol defined in [`SPEC_LIFECYCLE_RULES.md`](./SPEC_LIFECYCLE_RULES.md):

* **`missions/`**: Ingestion queue for newly proposed or backlogged specifications awaiting architectural analysis, compilation, and deployment.
* **`yet/`**: Active session working directory for specifications currently being analyzed, built, tested, or debugged.
* **`accomplished/`**: Permanent archive for specifications where **every single aspect** has been 100% analyzed, built, implemented with zero stubs, deployed, and live-verified across target nodes.

---

## 7-Language Polyglot Components

| Component | Language | Source Directory | Binary Target | Description |
| :--- | :--- | :--- | :--- | :--- |
| **GPU HUD Renderer** | Rust | `src/tx-ephemeral-hud/` | `/var/lib/tianxia/bin/tx-ephemeral-hud` | Zero-dependency Wayland layer-shell HUD (`smithay-client-toolkit`, seqlock mmap, 5x7 bitmapped font, 697 KB release binary). |
| **Telemetry & VM Broker** | Zig | `src/tx-menu-broker/` | `/var/lib/tianxia/bin/tx-menu-broker` | Populates `/dev/shm/tx_menu_ast`, listens on `/run/tianxia/broker.sock`, validates `SO_PEERCRED`, dispatches Plane A/B/C actions. |
| **AST & Gate Compiler** | Nim | `src/tx-menu-ast/` | `/var/lib/tianxia/bin/tx-menu-ast` | Enforces DSS-14.2 Mahavidya compile-time gates, validates node invariants, and serializes the 5-tier Miller binary lattice to `/dev/shm/tx_menu_ast`. |
| **Wayland VM Proxy** | OCaml | `src/tx-virtwl-proxy/` | `/var/lib/tianxia/bin/tx-virtwl-proxy` | Enforces capability security over `/run/tianxia/virtwl.sock`, isolates clipboard/keystrokes, and tags MicroVMs with `#ff5533` Ember alert borders. |
| **System-1 Intent Scorer** | CUDA / C | `src/tx-cuda-manas/` | `/var/lib/tianxia/lib/libtx_manas_cpu.so` & `.cu` | Maxwell `GM108` (`sm_50`) INT8 dot product + AVX2 CPU fallback with SOFTEM Huber-loss anomaly prior boosting. |
| **Scheduler Priority** | BPF C | `src/scx-tianxia/` | `scx_tianxia.bpf.c` | Linux `sched_ext` priority preemption maps for `tx-hud.scope` ensuring zero frame drops. |
| **Declarative Substrate** | Nix | `nix/` | `/etc/nixos/modules/tianxia-ephemeral-menu.nix` | Declarative NixOS module configuring tmpfiles rules, graphics drivers, and systemd units. |

---

## Keybindings & Interaction

* **Summon / Dismiss HUD:** `$mod + Space` or `$mod + M` (or click off / press `Escape`).
* **Miller Column Navigation:**
  * `Left` / `Right`: Navigate between Tiers (Tier 0 to Tier 4).
  * `Up` / `Down`: Navigate rows within active Tier.
* **Plane Execution Keychords:**
  * `Enter`: **Plane A** (Native Zero-Copy Inspection).
  * `Shift + Enter`: **Plane B** (Elastic Semi-Containerized Namespace via `systemd-run`).
  * `Ctrl + Enter`: **Plane C** (Hardware-Isolated MicroVM via CoW Zygote Resume).
* **Ephemeral Hot-Node Deck:**
  * `Alt + 1`: Enforce Lock on Delinquent Facility (`FAC-LEASE-002`).
  * `Alt + 2`: Adjust Holdback (`+250 BPS SPLIT`).
  * `Alt + 3`: Inspect AF_XDP 11.4 Mpps RingBuf Telemetry.

---

## Live System Verification
* Node: `latitude-tianxia` (`${TX_HUB_HOST:-127.0.0.1}`)
* Active Display Output: `eDP-1` (1920x1080@60Hz) & `DP-1` (1920x1080@60Hz)
* Layer-Shell Geometry: `1280x480` centered at `x: 320, y: 70` on Overlay Layer
* Live Sockets: `/run/tianxia/broker.sock`, `/run/tianxia/virtwl.sock`
* Shared Memory: `/dev/shm/tx_menu_ast` (70,688 bytes, 18 validated nodes)
* Active Services: `tx-menu-broker.service` (PID 2206408), `tx-wayland-virtwl-proxy.service` (PID 2189907)
