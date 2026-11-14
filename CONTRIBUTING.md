# Contributing to TianxiaOS

Thank you for contributing to **TianxiaOS**, engineered by **Collins Takem** under the **Rasa-X-Machina** sovereign engineering initiative (*proposed Estonian entity `RASA-X-MACHINA OÜ` to be incorporated in Tallinn upon Estonian Startup Committee approval under § 100¹ of the Estonian Aliens Act, Dealum Application `#179423`*).

All contributions are governed by the immutable [**TianxiaOS Build Law (`BUILD_LAW.md`)**](BUILD_LAW.md).

## 1. Mandatory Pre-Submission Checklist

Before opening a Pull Request, every new or modified file must satisfy:

1. **FFP-First Header Declaration (`Pillar 2.1`)**:
   - Every source file must carry its explicit Function-Feature Pair header on lines 1–3:
     - Rust / Zig / Go / TypeScript / C: `// ffp: FFP-<MODULE> <ffp_class> <lang>`
     - Nix / Python / Shell: `# ffp: FFP-<MODULE> <ffp_class> <lang>`
     - HTML: `<!-- ffp: FFP-<MODULE> frontend html -->`
2. **Polyglot Fitness Alignment (`Pillar 2.2–2.3`)**:
   - Match the language to the workload (`Rust` / `Zig` / `C` for compute, crypto, wire codecs, and edge tooling; `Go` / `Rust` for concurrent relays; `Nix` for declarative OS modules; `TypeScript` / `JS` for sandboxed Cockpit PWAs). Python is never used as a lazy default for latency-critical daemons.
3. **Zero Stubs & Zero `eval` (`Daśavidyāyāna NL` Lenses)**:
   - No `TODO`/`FIXME` placeholders, mock-only handlers, `eval`, or unguarded shell-string execution.
   - Shell scripts must follow **SLECO-SO++** (`set +e`, explicit `trap`, bounded timeouts, parameter expansion).
4. **Zero Secrets & Full Localization Compatibility**:
   - Never commit credentials, tokens, private keys, or build caches (`target/`, `node_modules/`, `__pycache__/`).
   - Client-facing UI surfaces must support 100% full-copy localization across all 42 markets and 29 single-currency views, and must never expose internal conversion metrics.

## 2. Local Verification Gate

Run the local verification suite prior to pushing:

```bash
# 1. Secret Shield zero-leak audit
python3 mcp/secret_shield.py

# 2. Build Law Merkle + HMAC seal verification
python3 ../tianxia/bin/tx_build_law_sentinel.py --verify

# 3. Rust workspace check & unit tests
cargo test --workspace
```

## 3. Commit Convention

Use Conventional Commits:
- `feat(<scope>): ...`
- `fix(<scope>): ...`
- `security(<scope>): ...`
- `docs(<scope>): ...`
- `ci(<scope>): ...`
