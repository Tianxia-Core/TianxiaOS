# DASAVIDYAYANA NL — The Natural-Language Release & Market Doctrine

**Authority:** derived from the DSS-14 Unified Polyglot Standard (Dasavidyayana × SLECO-SO++)
and the Shanmukha-Kala-Vidhi (Eleven Eternal Script Stipulations). This document is the
human-readable rendering of Dasavidyayana for **product-release and market strategy**:
it tells a sovereign operator *which kind of product, in which language, for which market,
at which moment* — guided by evidence, not aspiration.

**Companion artifacts (machine-readable):** `strategy_rules.jsonl` (nodes of kind
`strategy_rule`), `language_nodes.jsonl` (nodes of kind `language`), ingested into
`docs/faery_fortress/registries/tianxia_registry.db` where each rule is linked to the
domains, niches, languages and RGUs it governs.

---

## I. The Fourteen Lenses

Dasavidyayana judges every artifact through fourteen lenses. In natural language they are:

1. **KALI — Severance.** Cut what cannot be defended. A file, a service, or a product that
   cannot pass the gate does not ship; it is severed or rewritten, never excused.
2. **BHAIRAVI — Containment.** Anything that can mutate a protected surface (files, keys,
   networks, money) must stand behind a capability gate. Read-only diagnostics are free.
3. **PRATYANGIRA — Innocence.** No dynamic evaluation, no shell-string execution, no hidden
   interpretation. Code says exactly what it does.
4. **BAGALAMUKHI — Loop Discipline.** Any loop that never ends must carry a kill-switch and
   a shutdown path. Nothing runs because "it always has."
5. **TARA — Graceful Failure.** Errors are logged and survived, not swallowed. `set +e`,
   `except` with logging, no bare throws into the void.
6. **TRIPURA — Three Cities.** Three independent ways to fetch, three ways to build, three
   ways to verify. Single points of failure are design errors.
7. **BHUVANESVARI — Environment Humility.** Never assume the machine; ask it. Defaults
   from the environment (`${VAR:-}`, `os.environ`), detection over declaration.
8. **CHHINNAMASTA — Decapitation of Stale Systems.** When a component is proven harmful,
   cut its head cleanly: remove it, archive it, note it. No zombie services.
9. **DHUMAVATI — Truthful Logging.** Every action leaves an auditable trace in a durable
   ledger. If it was not written down, it did not happen.
10. **MATANGI — Polyglot Fitness.** Language follows workload. No default language; the
    fittest tongue speaks.
11. **ANNAPURNA — Nourishing Provision.** Idempotent creation, resumable downloads,
    self-healing state files. Systems feed themselves.
12. **MAHASARASVATI — Polyglot Wisdom.** The ten preferred languages form one voice; the
    choice among them is strategic, not tribal.
13. **FFP — Function-Feature Pairing.** Every function is registered as an FFP with its
    fitness declaration (`# ffp: ID class lang`). If it is not paired, it is not real.
14. **KAMALA — Value Extraction.** Revenue hooks are constitutional, not incidental; and
    every claim of value must point at a ledger row.

**PARAMASIVA** is the gate: an artifact passes only when all fourteen lenses agree.

---

## II. Language–Market Resonance

Each language carries an engineering character that resonates with a market archetype.
This table governs which toolchain fronts which product class:

| Language | Class fitness | Market archetype it earns trust with |
|---|---|---|
| Rust | compute-kernel, crypto-signer, wire-codec, edge-agent | Infrastructure & security buyers — arbitrage engines, keepers, signers, daemons |
| TypeScript | frontend, chain-tooling, io-edge | Portal & dashboard buyers — operator cockpits, merchant consoles, monitors |
| Python | data-science, ml-inference, glue, chain-tooling | Research & integration buyers — analytics, backtests, API bridges |
| Go | concurrent-daemon, io-edge | Service buyers — proxies, relays, network utilities |
| Nix | declarative | Sovereign-infrastructure buyers — reproducible deployment, immutability |
| Zig | wire-codec, edge-agent | Systems buyers — minimal binaries, embedded and edge agents |
| Nim | edge-agent, concurrent-daemon | Compact-service buyers — low-footprint daemons |
| Julia | data-science | Quant buyers — numerical research, signal mathematics |
| Mojo | ml-inference | AI buyers — inference kernels, model serving |
| F# | data-science, contract-adjacent | Enterprise-data buyers — typed data transforms, audit pipelines |
| Bash | content-pipeline, glue | Orchestration only — never the product surface |

**Rule of resonance:** the language that *demonstrates* the value best for the buyer's own
workload is the language the product ships in. A frontend sold to operators is TypeScript;
the engine behind it is Rust; the report generator may be Python; the deployment is Nix.

---

## III. The Priority Calculus

Every candidate release is ranked by five measured terms, in this order:

1. **Proximity to earning (P).** Distance between today's state and a first real receipt.
   Lower is better. A 3-step path beats a 30-step path regardless of scale.
2. **Capital efficiency (C).** Receipt per dollar of gas/API/infrastructure spend. The
   flash-arbitrage engine (principal-free) ranks above anything requiring inventory.
3. **Permissionlessness (A).** How few humans, approvals, or counterparties stand between
   the engine and revenue. Zero-human paths outrank partnership-dependent ones.
4. **Evidence compounding (E).** Does running it produce ledger rows that strengthen the
   next release? Measured engines compound; speculative builds do not.
5. **Perimeter fit (F).** Does it fit the deployed substrate (models, timers, registry,
   rails) without new fragility?

Rank score = **P + C + A + E + F**, with proximity-to-earning holding veto weight: any
candidate requiring unknown capital is deferred to the capital-gated tier no matter how
large its theoretical market.

---

## IV. The Release Ladder (Earning Before Selling)

1. **Engine proves itself.** An RGU runs unattended and produces a real receipt or a
   verifiable on-chain outcome. Evidence lands in `EARNINGS.json` and the ledger.
2. **Evidence sustains.** Receipts repeat across a sliding window (SLA-dependent).
3. **Productization becomes honest.** Only then may a SKU, catalog entry, or marketplace
   listing be created from the proven mechanism — the demo is the engine's own history.
4. **Language-guided packaging.** The SKU speaks in the language of its buyer's workload
   (see §II), wrapped in the deployment form its market trusts (Nix modules for
   infrastructure, hosted endpoints for services, dashboards on top of APIs).
5. **Scale or sever.** Underperforming releases are severed by the KALI lens, not kept
   alive by hope.

The catalog remains **shelved** until step 1 has actually occurred. This is doctrine, not
preference: seeing is believing; earning is confirming.

---

## V. Language-Guided Release Rules (governable)

Each rule below exists as a `strategy_rule` node in the registry with machine-readable
condition/action/weight fields:

- **SR-001 (Resonance First).** Package each release in the language whose class fitness
  matches the buyer's workload; never ship a frontend in a kernel language or a kernel in
  a scripting language.
- **SR-002 (Proximity Veto).** No capital-gated build may be promoted above a zero-capital
  build with a shorter path to first receipt.
- **SR-003 (Engine Before SKU).** Product listings are forbidden until the underlying RGU
  shows a real receipt (Release Ladder step 1).
- **SR-004 (Mechanism Classes).** Portfolio expansion proceeds by mechanism class
  (arbitrage, keeper, signal, attestation, inference, memory) — not by market fashion.
- **SR-005 (Evidence Density).** Prefer releases whose execution continuously emits
  evidence (signals, receipts, attestations) over releases that emit only a final invoice.
- **SR-006 (Language Leap).** A new language enters a product only when its class fitness
  genuinely beats the incumbent for that workload, demonstrated by benchmark FFP.
- **SR-007 (Market Resonance).** Select the first market for a release by the ICP whose
  pain points the mechanism removes directly — not by the ICP with the largest budget.
- **SR-008 (Sovereign Surface).** Every release exposes at least one sovereigninterface:
  an x402-payable endpoint, a self-hosted dashboard, or a verifiable on-chain artifact.
- **SR-009 (Zero-Human Default).** Automate to zero human touches before adding a second
  market; manual steps are treated as defects.
- **SR-010 (Capability Honesty).** Never announce a capability the ledger cannot prove;
  claims without rows are severed on sight.
- **SR-011 (Amortized Rails).** Prefer mechanisms that reuse existing rails (gateway,
  ledger, registry, treasury) over those requiring new infrastructure.
- **SR-012 (Ratchet Amendment).** This doctrine amends only through the DSS-14 ratchet:
  proposed rule → 14-lens review → gate → registry ingest → hourly enforcement.

---

## VI. Enforcement

- Rules are nodes; their edges bind them to languages, domains, niches, and RGUs.
- `tx_registry_sync.py` (hourly) verifies the links never rot.
- `tx_ds_gate.py` enforces code-level lenses; this document enforces strategy-level
  congruence.
- Amendments are additive: rules are superseded, never silently deleted.

*Drafted under the fourteen lenses; every sentence above must eventually be backed by a
ledger row that proves it was lived, not merely written.*
