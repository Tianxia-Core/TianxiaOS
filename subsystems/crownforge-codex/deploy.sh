#!/usr/bin/env bash
# ffp: FFP-SH-003 crownforge-deploy-orchestrator bash
# TianxiaOS Crownforge Codex (V8.6.0) Production Deployment Engine
# Target: latitude-tianxia (${TX_HUB_HOST:-127.0.0.1})
# Compliance: SLECO-SO++ + DSS-14.2 + ENHAN3 Tri-Vector

set +e
set +u

DEST_HOST="latitude-tianxia"
SCRIPT_DIR="$(cd "${0%/*}" 2>/dev/null && pwd)"
PROJECT_DIR="${SCRIPT_DIR}"
REMOTE_WS="~/workspace/tianxiaos_crownforge_codex"
INSTALL_PREFIX="/var/lib/tianxia"

cleanup() {
    local exit_code="${?}"
    if [ "${exit_code}" -ne 0 ]; then
        printf '[DEPLOY_ERR] Deployment pipeline interrupted with code: %d\n' "${exit_code}" >&2
    fi
}
trap cleanup EXIT

printf '=== [TIANXIAOS // CROWNFORGE CODEX v8.6.0] Production Deployment ===\n'
printf 'Host: %s\n' "${DEST_HOST}"
printf 'Source Tree: %s\n' "${PROJECT_DIR}"

# 1. Sync local tree to latitude-tianxia
printf '[1/7] Syncing source tree to %s:%s...\n' "${DEST_HOST}" "${REMOTE_WS}"
ssh "${DEST_HOST}" "mkdir -p ~/workspace/tianxiaos_crownforge_codex" || exit 1
rsync -avz --delete \
    --exclude='.git' \
    --exclude='target' \
    "${PROJECT_DIR}/" "${DEST_HOST}:~/workspace/tianxiaos_crownforge_codex/" || exit 1

# 2. Compile Polyglot binaries on latitude-tianxia
printf '[2/7] Compiling production release binaries on %s...\n' "${DEST_HOST}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_BUILD'
set +e
set +u
cd ~/workspace/tianxiaos_crownforge_codex || exit 1
mkdir -p target/release

printf '[CARGO] Building Rust release binaries...\n'
cargo build --release
build_status="${?}"
if [ "${build_status}" -ne 0 ]; then
    printf '[CARGO_ERR] Cargo build failed with status %d\n' "${build_status}" >&2
    exit "${build_status}"
fi

printf '[ZIG] Compiling Ego-AVX2 Verifier...\n'
zig build-exe src/zig/tx_ego_avx2_verifier.zig -O ReleaseFast -femit-bin=target/release/tx_ego_avx2_verifier
zig_status="${?}"
if [ "${zig_status}" -ne 0 ]; then
    printf '[ZIG_WARN] Zig build exited with %d\n' "${zig_status}"
fi

printf '[C++] Compiling WAV-KAN SIMD/AVX2 Resonance Kernel...\n'
g++ -O3 -mavx2 -mfma src/cpp/tx_wav_kan_resonance.cpp -o target/release/tx_wav_kan_resonance 2>/dev/null || g++ -O3 src/cpp/tx_wav_kan_resonance.cpp -o target/release/tx_wav_kan_resonance

printf '[C] Compiling Tremor VFS Inode Modulator...\n'
gcc -O3 src/c/tx_tremor_vfs_modulator.c -o target/release/tx_tremor_vfs_modulator

printf '[GO] Compiling Hussar Swarm Honeycomb Mesh...\n'
go build -o target/release/tx_hussar_mesh src/go/tx_hussar_swarm_mesh.go

printf '[NIM] Compiling Maha Madpie AST Principle Extractor...\n'
nim c -d:release --hints:off --out:target/release/tx_madpie_ast src/nim/tx_madpie_hoard_ast.nim

printf '[OCAML] Compiling Veritas Triple-Helix Gate...\n'
ocamlopt -o target/release/tx_veritas_gate src/ocaml/tx_veritas_helix_gate.ml 2>/dev/null || ocamlc -o target/release/tx_veritas_gate src/ocaml/tx_veritas_helix_gate.ml

printf '[BUILD_OK] All polyglot targets compiled successfully.\n'
REMOTE_BUILD

if [ "${?}" -ne 0 ]; then
    printf '[FATAL] Polyglot compilation on %s failed.\n' "${DEST_HOST}" >&2
    exit 1
fi

# 3. Execute unit and integration tests on latitude-tianxia
printf '[3/7] Running full test suite on %s...\n' "${DEST_HOST}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_TEST'
set +e
set +u
cd ~/workspace/tianxiaos_crownforge_codex || exit 1

printf '[REMOTE_TEST] Running cargo test --release...\n'
cargo test --release
test_status="${?}"
if [ "${test_status}" -ne 0 ]; then
    printf '[TEST_ERR] Cargo test failed with status %d\n' "${test_status}" >&2
    exit "${test_status}"
fi
printf '[REMOTE_TEST] All Rust tests passed successfully!\n'
REMOTE_TEST

if [ "${?}" -ne 0 ]; then
    printf '[FATAL] Tests on %s failed.\n' "${DEST_HOST}" >&2
    exit 1
fi

# 4. Verify Python, TypeScript, and Julia scripts
printf '[4/7] Verifying Python, TypeScript, and Julia workers on %s...\n' "${DEST_HOST}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_SCRIPTS'
set +e
set +u
cd ~/workspace/tianxiaos_crownforge_codex || exit 1

printf '[PYTHON] Testing tx_omphalos_madpie_naga_engine.py...\n'
python3 python/tx_omphalos_madpie_naga_engine.py || exit 1

printf '[PYTHON] Testing tx_jivascriptocle_vision.py...\n'
python3 python/tx_jivascriptocle_vision.py || exit 1

printf '[PYTHON] Testing tx_jot_151k_nullspace.py...\n'
python3 python/tx_jot_151k_nullspace.py || exit 1

printf '[JULIA] Testing tx_omni_lattice_simulator.jl...\n'
julia src/julia/tx_omni_lattice_simulator.jl || exit 1

printf '[NODE] Testing tx_crownforge_hud.ts...\n'
node --experimental-strip-types src/ts/tx_crownforge_hud.ts || exit 1

printf '[SCRIPTS_OK] All polyglot script workers verified.\n'
REMOTE_SCRIPTS

if [ "${?}" -ne 0 ]; then
    printf '[FATAL] Polyglot worker verification failed.\n' >&2
    exit 1
fi

# 5. SQLite TetraLedger Verification
printf '[5/7] Initializing and verifying SQLite Crownforge TetraLedger schema...\n'
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_SQL'
set +e
set +u
cd ~/workspace/tianxiaos_crownforge_codex || exit 1
mkdir -p /var/lib/tianxia/db

sqlite3 /var/lib/tianxia/db/crownforge_tetraledger.db < sql/crownforge_schema.sql
sql_status="${?}"
if [ "${sql_status}" -ne 0 ]; then
    printf '[SQL_ERR] SQLite schema initialization failed.\n' >&2
    exit 1
fi
printf '[SQL_OK] Crownforge TetraLedger schema verified in WAL mode.\n'
REMOTE_SQL

# 6. Staging binaries & systemd service units
printf '[6/7] Staging binaries in %s/bin and configuring systemd...\n' "${INSTALL_PREFIX}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_INSTALL'
set +e
set +u
mkdir -p /var/lib/tianxia/bin /var/lib/tianxia/python /run/systemd/system

cd ~/workspace/tianxiaos_crownforge_codex || exit 1

# Copy compiled Rust binaries
cp -f target/release/tx_crownforge_daemon /var/lib/tianxia/bin/
cp -f target/release/tx_omphalos_orw22 /var/lib/tianxia/bin/
cp -f target/release/tx_noetic_kenning /var/lib/tianxia/bin/
cp -f target/release/tx_tremor_pheromone /var/lib/tianxia/bin/
cp -f target/release/tx_ego_naga /var/lib/tianxia/bin/
cp -f target/release/tx_maha_madpie /var/lib/tianxia/bin/

# Copy polyglot compiled binaries
[ -f target/release/tx_ego_avx2_verifier ] && cp -f target/release/tx_ego_avx2_verifier /var/lib/tianxia/bin/
[ -f target/release/tx_wav_kan_resonance ] && cp -f target/release/tx_wav_kan_resonance /var/lib/tianxia/bin/
[ -f target/release/tx_tremor_vfs_modulator ] && cp -f target/release/tx_tremor_vfs_modulator /var/lib/tianxia/bin/
[ -f target/release/tx_hussar_mesh ] && cp -f target/release/tx_hussar_mesh /var/lib/tianxia/bin/
[ -f target/release/tx_madpie_ast ] && cp -f target/release/tx_madpie_ast /var/lib/tianxia/bin/
[ -f target/release/tx_veritas_gate ] && cp -f target/release/tx_veritas_gate /var/lib/tianxia/bin/

chmod +x /var/lib/tianxia/bin/tx_*

# Copy Python modules
cp -rf python/* /var/lib/tianxia/python/
chmod +x /var/lib/tianxia/python/*.py

# Install systemd service units
cp -f config/systemd/*.service /run/systemd/system/

systemctl daemon-reload
systemctl restart tx-crownforge-daemon.service
systemctl restart tx-tremor-pheromone.service
systemctl restart tx-hussar-mesh.service

printf '[SYSTEMD_OK] Crownforge systemd services deployed and restarted.\n'
REMOTE_INSTALL

# 7. Live smoke verification across all targets
printf '[7/7] Running live smoke test suite on target...\n'
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_VERIFY'
set +e
set +u

printf '\n--- [SMOKE 1: CROWNFORGE DAEMON] ---\n'
CROWNFORGE_CONTINUOUS=0 /var/lib/tianxia/bin/tx_crownforge_daemon

printf '\n--- [SMOKE 2: OMPHALOS ORW-22 CLI] ---\n'
/var/lib/tianxia/bin/tx_omphalos_orw22 TRADING "High-frequency contrarian liquidity capture"

printf '\n--- [SMOKE 3: NOETIC KENNING SENTIENCE] ---\n'
/var/lib/tianxia/bin/tx_noetic_kenning

printf '\n--- [SMOKE 4: TREMOR PHEROMONE BUS] ---\n'
/var/lib/tianxia/bin/tx_tremor_pheromone

printf '\n--- [SMOKE 5: EGO NAGA HUSSAR REGISTRY] ---\n'
/var/lib/tianxia/bin/tx_ego_naga

printf '\n--- [SMOKE 6: MAHA MADPIE SOLVER] ---\n'
/var/lib/tianxia/bin/tx_maha_madpie

printf '\n--- [SMOKE 7: ZIG FAST AVX2 VERIFIER] ---\n'
/var/lib/tianxia/bin/tx_ego_avx2_verifier

printf '\n--- [SMOKE 8: C++ WAV-KAN RESONANCE KERNEL] ---\n'
/var/lib/tianxia/bin/tx_wav_kan_resonance

printf '\n--- [SMOKE 9: C TREMOR VFS MODULATOR] ---\n'
/var/lib/tianxia/bin/tx_tremor_vfs_modulator

printf '\n--- [SMOKE 10: GO HUSSAR SWARM MESH] ---\n'
/var/lib/tianxia/bin/tx_hussar_mesh

printf '\n--- [SMOKE 11: NIM MADPIE AST PRINCIPLE] ---\n'
/var/lib/tianxia/bin/tx_madpie_ast

printf '\n--- [SMOKE 12: OCAML VERITAS TRIPLE-HELIX GATE] ---\n'
/var/lib/tianxia/bin/tx_veritas_gate

printf '\n--- [SYSTEMD STATUS] ---\n'
systemctl status tx-crownforge-daemon.service --no-pager
systemctl status tx-tremor-pheromone.service --no-pager
systemctl status tx-hussar-mesh.service --no-pager
REMOTE_VERIFY

printf '\n=== [TIANXIAOS // CROWNFORGE CODEX] Deployment & Verification Succeeded ===\n'
exit 0
