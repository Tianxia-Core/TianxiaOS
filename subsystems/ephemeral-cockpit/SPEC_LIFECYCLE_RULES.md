# TianxiaOS Architecture & Specification Lifecycle Protocol

> **MANDATORY GOVERNANCE DIRECTIVE FOR ALL LLM AGENTS, INSTANCES, AND BUILD RUNTIMES**
> *Active Standard: SLECO-SO++ · Polyglot FFP-First · DSS-14.2 Immutable Build Law*

This document establishes the unyielding, deterministic lifecycle protocol for all architectural specifications, feature sheets, and design documents residing within `tianxiaos_arch_menu_system`.

---

## 1. Directory Structure & Partition Topology

```
tianxiaos_arch_menu_system/
├── missions/        # Stage 1: Backlog / Pending Dispatch (Undeployed)
├── yet/             # Stage 2: Active Session / Ongoing Implementation
└── accomplished/    # Stage 3: Fully Verified & Deployed to Relevant Node(s)
```

| Partition | Directory | Description & Entry Condition | Exit Condition |
| :--- | :--- | :--- | :--- |
| **Stage 1** | `missions/` | **Pending / Unclaimed Backlog.** New specifications awaiting analysis, architectural decomposition, polyglot compilation, or cluster deployment. | Claimed by an LLM instance or engineer for active session execution. |
| **Stage 2** | `yet/` | **Active Implementation / Ongoing Build Session.** Specifications currently being analyzed, scaffolded, compiled, debugged, or tested. | 100% full implementation, multi-language build, zero-stub deployment, and verified live node activation. |
| **Stage 3** | `accomplished/` | **Fully Deployed & Verified.** Specifications where **every single aspect** has been analyzed, built, implemented, and deployed to all relevant mesh node(s). | Permanent archive of sovereign system implementations. |

---

## 2. Universal Agent State Transition Rules

Every LLM instance (including Antigravity, Claude Code, Gemini CLI, Agy, and subagents) MUST adhere to the following 6 inviolable rules:

### RULE 1: Initial Ingestion (`missions/`)
* Any newly drafted, ingested, or proposed architecture specification must be initially placed into `tianxiaos_arch_menu_system/missions/`.
* No specification may bypass `missions/` or `yet/` directly into `accomplished/`.

### RULE 2: Session Claim & In-Flight Staging (`yet/`)
* When an LLM instance begins analyzing, decomposing, or implementing a specification from `missions/`, it **MUST immediately move** the specification document into `tianxiaos_arch_menu_system/yet/`.
* Staging in `yet/` signals to all parallel agents and human operators that the specification is actively undergoing build execution.

### RULE 3: Strict Zero-Stub & TianxiaOS Build Law Gate (`accomplished/`)
* An LLM instance is **STRICTLY PROHIBITED** from moving a specification document from `yet/` to `accomplished/` until **ALL** of the following conditions are verified with exit code `0`:
  1. **100% Section Coverage:** Every requirement, algorithm, data structure, and wire format described in the specification is completely implemented.
  2. **DSS-14.2 Universal Domain Compliance:** The design and implementation satisfy all applicable Mahāvidyā domains (Kālī through Paramaśiva) as codified in `AGENTS.md`.
  3. **Polyglot FFP-First Compliance (Function-Feature Pair):** No lazy default to Python. Every constituent Function-Feature Pair (FFP) is implemented in the language ranked highest in its Architectural Fitness Class under the FFP Fitness Matrix (e.g. Rust for concurrent-daemons/HUDs, Zig for wire-codecs/brokers, Nim for AST gates, OCaml for capability proxies, C/CUDA for compute kernels, Nix for declarative OS modules). Python is strictly banned as a lazy default.
  4. **SLECO-SO++ Execution Compliance:** All shell/system runners adhere to anti-fail-fast resilience, deterministic $O(1)$/linear velocity, process cgroup containment, pure parameter expansion, linear file synthesis, and atomic state synchronization.
  5. **Zero Stubs / Zero Mocking:** All polyglot source code is fully written, compiled into production-grade release binaries, and verified. No `TODO`, `FIXME`, or dummy fallbacks.
  6. **Target Node Deployment:** All generated binaries, shared libraries, IPC sockets, configuration files, and systemd units/NixOS modules are deployed and active on their designated mesh node(s) (e.g. `latitude-tianxia`).
  7. **Live Verification Telemetry:** System services are confirmed active, IPC sockets respond correctly (`broker.sock`, `virtwl.sock`, etc.), and layer-shell / display renders are validated in real time.

### RULE 4: Partial Failure Containment
* If any subcomponent, compiler gate, or node deployment fails or is partially incomplete during a session, the specification **MUST REMAIN in `yet/`**.
* The LLM instance must document the blocker and current completion status in the session handoff log before exiting.

### RULE 5: Dual-Surface Mesh Synchronization
* All moves between `missions/` $\rightarrow$ `yet/` $\rightarrow$ `accomplished/` must be mirrored across:
  1. The local workspace staging tree (`${TX_WORKSPACE:-/var/lib/tianxia}/tianxiaos_arch_menu_system/`)
  2. The cluster anchor node (`/var/lib/tianxia/tianxiaos_arch_menu_system/` on `latitude-tianxia`)

### RULE 6: Immutability & Non-Bypass Clause
* These rules and the underlying TianxiaOS Build Law (`AGENTS.md`) are absolute and permanent. No LLM instance has the authority to soften, waive, or bypass these verification gates.

---

## 3. Current Inventory

* `accomplished/`:
  - `TianxiaOS Polyglot Ephemeral Cockpit & Sovereign Menu Master Specification.md` *(Fully implemented in Rust, Zig, Nim, OCaml, C AVX2, BPF, and Nix; deployed to `latitude-tianxia` under systemd units `tx-menu-broker.service` and `tx-wayland-virtwl-proxy.service`; verified live on seat0 `eDP-1`).*
* `yet/`: *(Empty — no ongoing specification sessions currently in-flight)*
* `missions/`: *(Empty — awaiting next specification intake)*
