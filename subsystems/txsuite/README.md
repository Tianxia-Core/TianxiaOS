<div align="center">

# TXSUITE

### Fourteen sovereign Rust binaries. One polyglot fleet, compiled.

**The compute, wire, mesh, and market layer of the Tianxia substrate — rewritten from a Python fleet into a single static Rust suite. Same behavior. 31–123× faster. 8× smaller resident memory.**

![Rust](https://img.shields.io/badge/rust-stable-orange?logo=rust&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue)
![Platform](https://img.shields.io/badge/platform-x86__64%20Linux-lightgrey?logo=linux&logoColor=white)
![Standard](https://img.shields.io/badge/DSS--14-ADMITTED-brightgreen)

</div>

---

## Why txsuite exists

Every substrate eventually hits the same wall: the control plane written in a scripting
language starts to cost more than it earns. Hash a payload, frame a telemetry packet, lock a
state vector, sweep fourteen cores — each operation is small, each one runs constantly, and
each one pays the interpreter tax on every single call.

txsuite is the answer. Fourteen operational binaries, each rewritten in Rust from a verified
Python implementation, each compiled with `opt-level = 3`, link-time optimization, and symbol
stripping. No runtime, no interpreter startup, no GC pauses — just static executables that do
one job and exit in microseconds.

The migration discipline was strict: **no behavior was allowed to change.** Each Rust binary
was validated against the Python original it replaced — same inputs, same outputs, same
failure modes — before the Python process was retired. The result is a suite that is faster,
lighter, and *more predictable* than the fleet it replaced.

Why contributors gravitate to it:

- **Small, sharp binaries.** Each `src/bin/*.rs` is a self-contained tool. Read one file, understand one capability.
- **Real performance work.** Hash cracking, wire codecs, Unix-socket sweeps, WebSocket feeds — honest systems programming, measurable wins.
- **No framework religion.** `sha3`, `rusqlite`, `tungstenite`, `serde_json`, `ureq` — the smallest dependency surface that does the job.
- **Governed by construction.** Every source file carries an FFP declaration and passes the DSS-14 machine gate before it ships.

---

## The suite

All fourteen flagship binaries ship in `txsuite-v1.0.0-x86_64-linux.tar.gz`.

| Binary | Class | Purpose |
|---|---|---|
| `payload_hash` | compute-kernel | Keccak-256 canonical chain-op payload hasher — **123× faster** than the Python it replaced. |
| `njvm_frame` | wire-codec | 32-byte NJ wire-frame codec with magic `0x4E4A` and CRC32 integrity — **31× faster**. |
| `state_sentinel` | compute-kernel | SQLite vector state-lock integrity sentinel — **34× faster**. |
| `supply_authority` | concurrent-daemon | Single-pass full-system audit snapshot — **4.2× faster**. |
| `scale_anchor` | wire-codec | SCALE-codec encoder + Blake2b substrate extrinsic anchor. |
| `ghost_sweep` | compute-kernel | Owner-controlled wallet/chain fork-ghost balance scanner with vault scan. |
| `sweep_14core` | compute-kernel | Full 14-core Dasavidyayana telemetry sweep over the UDS fast-path. |
| `auxiliary_daemons` | concurrent-daemon | Tiny HTTP sidecar serving neural-substrate telemetry. |
| `hussar_patrol` | concurrent-daemon | Mesh core-patrol daemon walking the fastpath Unix socket. |
| `wss_feed` | concurrent-daemon | TLS WebSocket depth feed (Coinbase WSS) augmenting REST snapshots. |
| `signature_blacklist` | crypto-signer | Compiles trap intelligence into signature blacklists + Suricata perimeter rules. |
| `worker_autoscaler` | concurrent-daemon | NATS elastic worker autoscaler with thermal throttling. |
| `replicate_signatures` | concurrent-daemon | Signature-set fanout across the sovereign mesh. |
| `sync_signatures` | concurrent-daemon | Intelligence compile + distribute across mesh nodes. |

Four auxiliary binaries are also included in the source crate — `hw_probe`, `market_cron`,
`mesh_watchdog`, and `nowwallet_probe` — small utilities for hardware telemetry, market
snapshots, mesh liveness, and wallet probes. Build them with `cargo build --release`.

### Binary-by-binary

<details>
<summary><b>payload_hash</b> — the fastest hash in the suite</summary>

Reads a canonical payload from stdin or argv, produces its Keccak-256 digest, writes it to
stdout. That is the whole tool. It replaced a Python script that imported a general-purpose
crypto library and paid for a process start on every invocation. At 0.6 ms per call it is now
faster than the filesystem cache miss that feeds it.
</details>

<details>
<summary><b>njvm_frame</b> — 32 bytes, magic-prefixed, CRC-checked</summary>

The NJ-VM telemetry frame is exactly 32 bytes: 2-byte magic (`0x4E4A`), versioned header,
payload, CRC32 trailer. `njvm_frame` encodes and verifies frames without allocation thrash,
making it safe to call from the hot path of any telemetry producer.
</details>

<details>
<summary><b>state_sentinel</b> — integrity for a living state vector</summary>

Walks the SQLite-backed state store, hashes each vector, and verifies the state lock. When
the state drifts, it says so — fast. A 53 ms Python integrity pass became a 1.6 ms native one.
</details>

<details>
<summary><b>supply_authority</b> — the whole system, one pass</summary>

Produces a single-pass snapshot of every registered supply surface: files, hashes, sizes,
permissions, and ledger-facing metadata. Output is JSON, ready for diffing between runs. What
used to take 97 ms now takes 23 ms — and it runs on every audit cycle.
</details>

<details>
<summary><b>scale_anchor</b> — substrate-grade wire framing</summary>

Implements SCALE-style compact encoding for substrate payloads and anchors the result with a
Blake2b digest bound to a timestamp. Use it when an extrinsic needs a verifiable anchor that
fits on a wire, not a paragraph of JSON.
</details>

<details>
<summary><b>ghost_sweep</b> — fork-ghost recovery, owner-controlled</summary>

Scans descendant chains of BTC/ETH hard forks for unclaimed balances belonging to addresses
the owner lawfully controls. The pipeline is evacuation-first: parent chain cleared before
descendant keys are ever exposed; air-gapped derivation; offline signing. Recovery-as-a-service
only — the client holds the key. No key extraction. Ever.
</details>

<details>
<summary><b>sweep_14core</b> — fourteen cores in one pass</summary>

Walks all fourteen Dasavidyayana core sockets over the Unix-domain fast-path and returns a
consolidated telemetry snapshot. Built for the moment when you need to know what every core is
thinking *right now*.
</details>

<details>
<summary><b>auxiliary_daemons</b> — a sidecar, not a framework</summary>

A tiny threaded HTTP server that exposes auxiliary telemetry as JSON. No router tree, no
middleware stack — just a listener that answers. Everything unnecessary was deleted.
</details>

<details>
<summary><b>hussar_patrol</b> — the mesh walks itself</summary>

Patrol daemon that probes each mesh core over its Unix socket, checks liveness, and reports
anomalies. The mesh does not wait to be asked whether it is healthy.
</details>

<details>
<summary><b>wss_feed</b> — market depth over TLS WebSocket</summary>

Maintains a live Coinbase WebSocket depth subscription with rustls, feeding the market layer
faster-than-REST snapshots. TLS roots are pinned via `webpki-roots` — no system trust store
required.
</details>

<details>
<summary><b>signature_blacklist</b> — trap intel in, perimeter rules out</summary>

Reads trap intelligence from the ledger and compiles it into two artifacts: a signature
blacklist for runtime matching, and Suricata rules for the perimeter. Defense that regenerates
itself from observed reality.
</details>

<details>
<summary><b>worker_autoscaler</b> — elastic, but thermal-aware</summary>

Watches NATS work queues and scales the worker pool elastically — while respecting thermal
headroom. Throughput is a goal; a melted node is not.
</details>

<details>
<summary><b>replicate_signatures</b> — fanout without drama</summary>

Replicates signature sets across the sovereign mesh with bounded retries and deterministic
ordering. One source of truth, many witnesses.
</details>

<details>
<summary><b>sync_signatures</b> — compile, then distribute</summary>

The other half of the pair: compiles raw signature intelligence into distributable form, then
pushes it to every mesh node in a single coordinated pass.
</details>

---

## Benchmarks

Measured on the x86_64 hub, same workload, Python implementation vs. compiled Rust binary.
Times are wall-clock per operation; RSS is resident set size at steady state.

| Operation | Python baseline | Rust | Speedup |
|---|---:|---:|---:|
| `payload_hash` — Keccak-256 payload hash | 74.6 ms | **0.6 ms** | **123×** |
| `njvm_frame` — 32-byte frame encode + CRC | 17.1 ms | **0.56 ms** | **31×** |
| `state_sentinel` — state-lock integrity pass | 53.3 ms | **1.6 ms** | **34×** |
| `supply_authority` — full audit snapshot | 97 ms | **23 ms** | **4.2×** |
| Resident memory (daemon steady state) | 19.2 MB | **2.3 MB** | **8.3× less** |

**Methodology.** Each binary was built with:

```toml
[profile.release]
opt-level = 3
lto = true
strip = true
```

The Python baselines were taken from the production processes they replaced, under identical
workloads on the same host. No warm-up tricks, no cached results — the numbers are what you
get when you run the tool.

Why the wins are this large: process startup, interpreter initialization, and dynamic dispatch
dominate short-lived operations. Eliminate them and a "small script" becomes a
hundred-times-faster executable.

---

## Install

### From the release tarball

```bash
curl -LO https://github.com/collinstaken525-cloud/txsuite/releases/download/v1.0.0/txsuite-v1.0.0-x86_64-linux.tar.gz
curl -LO https://github.com/collinstaken525-cloud/txsuite/releases/download/v1.0.0/checksums.txt

# verify before you run anything
sha256sum -c checksums.txt

tar xzf txsuite-v1.0.0-x86_64-linux.tar.gz
cd txsuite-v1.0.0-x86_64-linux
chmod +x *
./payload_hash "hello, sovereign mesh"
```

The tarball contains all fourteen compiled executables, this README, and a `checksums.txt`
for offline verification.

### From source

```bash
git clone https://github.com/collinstaken525-cloud/txsuite.git
cd txsuite

# stable Rust toolchain required (2021 edition)
cargo build --release

# eighteen binaries land in target/release/
ls target/release/ | grep -v '\.d$'
```

Individual binaries:

```bash
cargo build --release --bin payload_hash
```

The suite has no system dependencies beyond libc. Rustls uses pinned roots, SQLite is bundled,
and everything else is pure Rust.

> **Compatibility note.** The pre-built `v1.0.0` release binaries were compiled on the
> sovereign NixOS hub (x86_64, glibc 2.42 runtime interpreter). On NixOS they run directly; on
> other distributions, either build from source — nothing required but a Rust toolchain — or
> provide a compatible loader (`nix-ld`, or `patchelf --set-interpreter`). Aarch64 builds are
> a welcome contribution.

---

## Quickstart

```bash
# 1. hash a canonical payload
./payload_hash '{"op":"anchor","seq":4821}'
# -> 0x9f2c...  (Keccak-256)

# 2. frame it for the wire
./njvm_frame encode --payload '{"op":"anchor"}'
# -> 32-byte frame, magic 4E4A, CRC32 verified

# 3. lock the state vector
./state_sentinel --db /var/lib/state/vector.db
# -> OK  state lock verified (1.6 ms)

# 4. take the audit snapshot
./supply_authority --out /tmp/supply.json
# -> snapshot written: N surfaces, 23 ms

# 5. sweep the cores
./sweep_14core --json
# -> 14/14 cores reported
```

Each binary supports `--help`. All are designed to compose: hash it, frame it, anchor it,
snapshot it, patrol it.

---

## Architecture

```
                          ┌──────────────────────────────────────────┐
                          │             TXSUITE v1.0.0               │
                          │      fourteen sovereign rust bins        │
                          └──────────────────────────────────────────┘
                                           │
        ┌────────────────┬─────────────────┼─────────────────┬────────────────┐
        │                │                 │                 │                │
  ┌─────▼─────┐   ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐  ┌──────▼──────┐
  │  COMPUTE  │   │    WIRE     │   │    MESH     │   │   MARKET    │  │  INTEGRITY  │
  │           │   │             │   │             │   │             │  │             │
  │ payload_  │   │ njvm_frame  │   │ hussar_     │   │ wss_feed    │  │ state_      │
  │   hash    │   │ scale_anchor│   │   patrol    │   │ worker_     │  │   sentinel  │
  │ ghost_    │   │             │   │ replicate_  │   │   autoscaler│  │ supply_     │
  │   sweep   │   │             │   │   signatures│   │             │  │   authority │
  │ sweep_    │   │             │   │ sync_       │   │             │  │ signature_  │
  │   14core  │   │             │   │   signatures│   │             │  │   blacklist │
  └───────────┘   └─────────────┘   └──────┬──────┘   └─────────────┘  └─────────────┘
                                           │
                                    Unix-domain fast-path
                                           │
                          ┌────────────────▼────────────────┐
                          │        sovereign mesh            │
                          │   (self-hosted, NixOS hub +      │
                          │    heterogeneous edge nodes)     │
                          └──────────────────────────────────┘
```

**Reading the diagram.** Compute binaries are pure functions over data. Wire binaries own
framing discipline. Mesh binaries keep every node honest. Market binaries move live data.
Integrity binaries verify that what should be true still is.

The UDS fast-path is the spine: telemetry, patrols, and sweeps all traverse Unix sockets
instead of TCP, because the mesh is local-first by design.

---

## Design principles

1. **One capability per binary.** If a tool needs a subcommand tree, it probably wants to be
   two tools.
2. **Static and small.** LTO, strip, opt-level 3 — every release binary is self-contained.
3. **Deterministic I/O.** JSON in, JSON out where it matters; exit codes are meaningful.
4. **No ambient authority.** Binaries read explicit paths; nothing assumes a working directory.
5. **Fail loud, fail fast.** A CRC failure is an error, not a warning.
6. **Measured, not claimed.** Every performance number in this README came from a real
   before/after run.

---

## Built under the DSS-14 polyglot standard

txsuite is the flagship migration of the **DSS-14 Unified Polyglot Standard** — the
FFP-First rule that every Function-Feature Pair is implemented in the language with the
best fitness for its workload.

- **`concurrent-daemon` and `compute-kernel` classes → Rust.** The fitness matrix ranks Rust
  first for daemons and compute kernels; these fourteen binaries are that ranking made real.
- **Every source file carries an FFP marker.** Open any `src/bin/*.rs` and the first line
  declares the FFP id, the fitness class, and the language.
- **The gate is machine-enforced.** `tx_ds_gate.py` validates declarations and language
  fitness; the hourly ratchet applies it to every changed file. Nothing ships non-ADMITTED.
- **Baselines are sealed.** `BASELINE.json` is a sha256 manifest; drift is gated automatically.

Full standard: see the Tianxia repository (`docs/faery_fortress/DSS14_UNIFIED_STANDARD.md`).

---

## Contributing

The suite is deliberately approachable.

- **Good first issue material:** add a `--json` output mode to a binary that lacks one; add
  input validation; improve `--help` text.
- **Meatier work:** bench harnesses (`criterion`), property tests for the frame codec,
  cross-compilation targets (aarch64-linux), structured logging.
- **House rules:** keep binaries single-purpose; no async runtime unless a workload demands
  it; declare your FFP; follow the existing error style (loud and explicit).

```bash
cargo fmt
cargo clippy --all-targets
cargo test
```

Open an issue with a benchmark or a bug — both are equally welcome.

---

## License

MIT — see [LICENSE](LICENSE).

Verdict: **ADMITTED.**

<div align="center">

*Built by the sovereign mesh. Compile once, patrol forever.*

</div>
