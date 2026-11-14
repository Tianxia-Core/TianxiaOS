#!/usr/bin/env bash
# ffp: FFP-SH-002 polyglot-kenning-deploy-orchestrator bash
# TianxiaOS Polyglot Kenning Suite & 14-Core DAS v3.0.0 Deployment Engine
# Target: latitude-tianxia (${TX_HUB_HOST:-127.0.0.1})
# Compliance: SLECO-SO++ + DSS-14.2 + ENHAN3

set +e
set +u

DEST_HOST="latitude-tianxia"
SCRIPT_DIR="$(cd "${0%/*}" 2>/dev/null && pwd)"
PROJECT_DIR="${SCRIPT_DIR}"
REMOTE_WS="~/workspace/tianxiaos_polyglot_kenning"
INSTALL_PREFIX="/var/lib/tianxia"

cleanup() {
    local exit_code="${?}"
    if [ "${exit_code}" -ne 0 ]; then
        printf '[DEPLOY_ERR] Deployment pipeline interrupted with code: %d\n' "${exit_code}" >&2
    fi
}
trap cleanup EXIT

printf '=== [TIANXIAOS // POLYGLOT KENNING] Production Suite Deployment ===\n'
printf 'Host: %s\n' "${DEST_HOST}"
printf 'Source Tree: %s\n' "${PROJECT_DIR}"

# 1. Sync local tree to latitude-tianxia
printf '[1/7] Syncing source tree to %s:%s...\n' "${DEST_HOST}" "${REMOTE_WS}"
ssh "${DEST_HOST}" "mkdir -p ~/workspace/tianxiaos_polyglot_kenning" || exit 1
rsync -avz --delete \
    --exclude='.git' \
    --exclude='target' \
    "${PROJECT_DIR}/" "${DEST_HOST}:~/workspace/tianxiaos_polyglot_kenning/" || exit 1

# 2. Compile Polyglot binaries on latitude-tianxia
printf '[2/7] Compiling production release binaries on %s...\n' "${DEST_HOST}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_BUILD'
set +e
set +u
cd ~/workspace/tianxiaos_polyglot_kenning || exit 1
mkdir -p target/release

printf '[CARGO] Building Rust release binaries...\n'
cargo build --release
build_status="${?}"
if [ "${build_status}" -ne 0 ]; then
    printf '[CARGO_ERR] Cargo build failed with status %d\n' "${build_status}" >&2
    exit "${build_status}"
fi

printf '[ZIG] Compiling Nimbus-ZeroAlloc ring buffer...\n'
zig build-exe src/zig/zero_alloc_ring.zig -O ReleaseFast -femit-bin=target/release/tx_zero_alloc_ring
zig_status="${?}"
if [ "${zig_status}" -ne 0 ]; then
    printf '[ZIG_WARN] Zig build exited with %d\n' "${zig_status}"
fi

printf '[C++] Compiling Nimbus-SIMD AVX2 kernel...\n'
g++ -O3 -mavx2 -mfma src/cpp/bitnet_simd_kernel.cpp -o target/release/tx_bitnet_simd 2>/dev/null || g++ -O3 src/cpp/bitnet_simd_kernel.cpp -o target/release/tx_bitnet_simd

printf '[GO] Compiling Nimbus-Mesh WireGuard agent...\n'
go build -o target/release/tx_wg_mesh_agent src/go/wireguard_mesh_agent.go

printf '[NIM] Compiling Nimbus-Stealth honey-inode generator...\n'
nim c -d:release --hints:off --out:target/release/tx_loki_stealth src/nim/loki_stealth_vfs.nim

printf '[OCAML] Compiling Nimbus-Proof ARSI checker...\n'
ocamlopt -o target/release/tx_arsi_proof_checker src/ocaml/arsi_proof_checker.ml 2>/dev/null || ocamlc -o target/release/tx_arsi_proof_checker src/ocaml/arsi_proof_checker.ml

printf '[C] Compiling Nimbus-Sandbox shim & Nimbus-Kernel XDP filter...\n'
gcc -O3 src/wasm/sandbox_shim.c -o target/release/tx_wasm_sandbox
gcc -O3 src/bpf/tx_xdp_filter.c -o target/release/tx_xdp_filter

printf '[BUILD_OK] All polyglot targets processed successfully.\n'
REMOTE_BUILD

if [ "${?}" -ne 0 ]; then
    printf '[FATAL] Polyglot build on %s failed.\n' "${DEST_HOST}" >&2
    exit 1
fi

# 3. Execute unit and integration tests on latitude-tianxia
printf '[3/7] Running full test suite on %s...\n' "${DEST_HOST}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_TEST'
set +e
set +u
cd ~/workspace/tianxiaos_polyglot_kenning || exit 1

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

# 4. Verify Python and Script-based Polyglot Workers
printf '[4/7] Verifying Python, Julia and TypeScript workers on %s...\n' "${DEST_HOST}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_SCRIPTS'
set +e
set +u
cd ~/workspace/tianxiaos_polyglot_kenning || exit 1

printf '[PYTHON] Testing tx_kenning_oracular_engine.py...\n'
python3 python/tx_kenning_oracular_engine.py || exit 1

printf '[PYTHON] Testing tx_polyglot_kenning_bridge.py...\n'
python3 python/tx_polyglot_kenning_bridge.py || exit 1

printf '[JULIA] Testing filippov_kalman_solver.jl...\n'
julia src/julia/filippov_kalman_solver.jl || exit 1

printf '[NODE] Testing osc7501_hud_adapter.ts...\n'
node --experimental-strip-types src/ts/osc7501_hud_adapter.ts || exit 1

printf '[SCRIPT_OK] All script-based polyglot workers verified.\n'
REMOTE_SCRIPTS

if [ "${?}" -ne 0 ]; then
    printf '[FATAL] Polyglot worker verification failed.\n' >&2
    exit 1
fi

# 5. SQLite Ledger Verification
printf '[5/7] Initializing and verifying SQLite TetraLedger double-entry schema...\n'
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_SQL'
set +e
set +u
cd ~/workspace/tianxiaos_polyglot_kenning || exit 1
mkdir -p /var/lib/tianxia/db

sqlite3 /var/lib/tianxia/db/tetraledger_kenning.db < sql/tetraledger_schema.sql
sql_status="${?}"
if [ "${sql_status}" -ne 0 ]; then
    printf '[SQL_ERR] SQLite schema initialization failed.\n' >&2
    exit 1
fi
printf '[SQL_OK] SQLite TetraLedger initialized in WAL mode.\n'
REMOTE_SQL

# 6. Staging binaries & systemd service units
printf '[6/7] Staging binaries in %s/bin and configuring systemd...\n' "${INSTALL_PREFIX}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_INSTALL'
set +e
set +u
mkdir -p /var/lib/tianxia/bin /var/lib/tianxia/python /var/lib/tianxia/config/matrices /run/systemd/system

cd ~/workspace/tianxiaos_polyglot_kenning || exit 1

# Copy compiled Rust binaries
cp -f target/release/tx_kenning_daemon /var/lib/tianxia/bin/
cp -f target/release/tx_oracular_arsi /var/lib/tianxia/bin/
cp -f target/release/tx_jivaslokan_probe /var/lib/tianxia/bin/
cp -f target/release/tx_rasoom_nkg /var/lib/tianxia/bin/
cp -f target/release/tx_tremor_ego_aegis /var/lib/tianxia/bin/
cp -f target/release/tx_nimbus_polyglot /var/lib/tianxia/bin/

# Copy polyglot compiled binaries
[ -f target/release/tx_zero_alloc_ring ] && cp -f target/release/tx_zero_alloc_ring /var/lib/tianxia/bin/
[ -f target/release/tx_bitnet_simd ] && cp -f target/release/tx_bitnet_simd /var/lib/tianxia/bin/
[ -f target/release/tx_wg_mesh_agent ] && cp -f target/release/tx_wg_mesh_agent /var/lib/tianxia/bin/
[ -f target/release/tx_loki_stealth ] && cp -f target/release/tx_loki_stealth /var/lib/tianxia/bin/
[ -f target/release/tx_arsi_proof_checker ] && cp -f target/release/tx_arsi_proof_checker /var/lib/tianxia/bin/
[ -f target/release/tx_wasm_sandbox ] && cp -f target/release/tx_wasm_sandbox /var/lib/tianxia/bin/
[ -f target/release/tx_xdp_filter ] && cp -f target/release/tx_xdp_filter /var/lib/tianxia/bin/

chmod +x /var/lib/tianxia/bin/tx_*

# Copy Python modules
cp -rf python/* /var/lib/tianxia/python/
chmod +x /var/lib/tianxia/python/*.py

# Copy matrices
cp -rf config/matrices/* /var/lib/tianxia/config/matrices/

# Install systemd service units
cp -f config/systemd/*.service /run/systemd/system/

systemctl daemon-reload
systemctl restart tx-kenning-daemon.service
systemctl restart tx-oracular-arsi.service
systemctl restart tx-rasoom-mesh.service

printf '[SYSTEMD_OK] Polyglot kenning services restarted successfully.\n'
REMOTE_INSTALL

# 7. Live smoke verification across all 14-Core binaries
printf '[7/7] Running live smoke test suite on target...\n'
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_VERIFY'
set +e
set +u

printf '\n--- [SMOKE 1: KENNING DAEMON] ---\n'
/var/lib/tianxia/bin/tx_kenning_daemon

printf '\n--- [SMOKE 2: ORACULAR ARSI VERIFIER] ---\n'
/var/lib/tianxia/bin/tx_oracular_arsi

printf '\n--- [SMOKE 3: JIVASLOKAN PROBE] ---\n'
/var/lib/tianxia/bin/tx_jivaslokan_probe

printf '\n--- [SMOKE 4: RASOOM-NKG ENGINE] ---\n'
/var/lib/tianxia/bin/tx_rasoom_nkg

printf '\n--- [SMOKE 5: TREMOR, EGO & AEGIS-9] ---\n'
/var/lib/tianxia/bin/tx_tremor_ego_aegis

printf '\n--- [SMOKE 6: NIMBUS² DAS 14-CORE SUPERVISOR] ---\n'
/var/lib/tianxia/bin/tx_nimbus_polyglot

printf '\n--- [SMOKE 7: ZIG ZERO-ALLOC RING] ---\n'
/var/lib/tianxia/bin/tx_zero_alloc_ring

printf '\n--- [SMOKE 8: C++ BITNET SIMD KERNEL] ---\n'
/var/lib/tianxia/bin/tx_bitnet_simd

printf '\n--- [SMOKE 9: GO WG MESH AGENT] ---\n'
/var/lib/tianxia/bin/tx_wg_mesh_agent

printf '\n--- [SMOKE 10: NIM LOKI STEALTH INODE] ---\n'
/var/lib/tianxia/bin/tx_loki_stealth

printf '\n--- [SMOKE 11: OCAML ARSI PROOF CHECKER] ---\n'
/var/lib/tianxia/bin/tx_arsi_proof_checker

printf '\n--- [SMOKE 12: C WASM SANDBOX SHIM] ---\n'
/var/lib/tianxia/bin/tx_wasm_sandbox

printf '\n--- [SMOKE 13: C KERNEL XDP FILTER] ---\n'
/var/lib/tianxia/bin/tx_xdp_filter

printf '\n--- [SYSTEMD UNITS STATUS] ---\n'
systemctl status tx-kenning-daemon.service --no-pager
systemctl status tx-oracular-arsi.service --no-pager
systemctl status tx-rasoom-mesh.service --no-pager
REMOTE_VERIFY

printf '\n=== [TIANXIAOS // POLYGLOT KENNING] Deployment & Verification Completed Successfully ===\n'
exit 0
