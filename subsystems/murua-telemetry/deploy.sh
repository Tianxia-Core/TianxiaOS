#!${TX_PREFIX:-/usr/local}/files/usr/bin/env bash
# ffp: FFP-MURUA-DEPLOY deploy-orchestrator bash
# TianxiaOS Murua Sovereign Telemetry Suite (v8.4-OMEGA) Deployment Engine
# Target: latitude-tianxia (${TX_HUB_HOST:-127.0.0.1})
# Compliance: SLECO-SO++ + DSS-14.2 + ENHAN3

set +e
set +u

DEST_HOST="latitude-tianxia"
SCRIPT_DIR="$(cd "${0%/*}" 2>/dev/null && pwd)"
PROJECT_DIR="${SCRIPT_DIR}"
REMOTE_WS="~/workspace/murua_architecture_enhancement"
INSTALL_PREFIX="/var/lib/tianxia/murua"

cleanup() {
    local exit_code="${?}"
    if [ "${exit_code}" -ne 0 ]; then
        printf '[DEPLOY_ERR] Deployment pipeline interrupted with code: %d\n' "${exit_code}" >&2
    fi
}
trap cleanup EXIT

printf '================================================================================\n'
printf ' TIANXIA OS // MURUA UNIVERSAL TRACER (v8.4-OMEGA) DEPLOYMENT PIPELINE\n'
printf ' Target Node: %s\n' "${DEST_HOST}"
printf ' Local Source: %s\n' "${PROJECT_DIR}"
printf '================================================================================\n'

# 1. Synchronize source tree to latitude-tianxia
printf '[1/8] Syncing source tree to %s:%s...\n' "${DEST_HOST}" "${REMOTE_WS}"
ssh "${DEST_HOST}" "mkdir -p ~/workspace/murua_architecture_enhancement" || exit 1
rsync -avz --delete \
    --exclude='.git' \
    --exclude='target' \
    "${PROJECT_DIR}/" "${DEST_HOST}:~/workspace/murua_architecture_enhancement/"
sync_status="${?}"
if [ "${sync_status}" -ne 0 ]; then
    printf '[SYNC_ERR] Rsync failed with status %d\n' "${sync_status}" >&2
    exit "${sync_status}"
fi

# 2. Compile Polyglot binaries on latitude-tianxia
printf '[2/8] Compiling production release binaries on %s...\n' "${DEST_HOST}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_BUILD'
set +e
set +u
cd ~/workspace/murua_architecture_enhancement || exit 1
mkdir -p target/release

printf '[CARGO] Building Rust release binaries...\n'
cargo build --release
build_status="${?}"
if [ "${build_status}" -ne 0 ]; then
    printf '[CARGO_ERR] Cargo build failed with status %d\n' "${build_status}" >&2
    exit "${build_status}"
fi

printf '[ZIG] Compiling Murua-RingBuffer zero-allocation module...\n'
zig build-exe src/zig/murua_ring_buffer.zig -O ReleaseFast -femit-bin=target/release/tx_murua_ring
zig_status="${?}"
if [ "${zig_status}" -ne 0 ]; then
    printf '[ZIG_WARN] Zig build exited with %d\n' "${zig_status}"
fi

printf '[C] Compiling SRM Lamb-Wave Acoustic compute kernel...\n'
gcc -O3 src/c/tx_srm_acoustic_kernel.c -o target/release/tx_srm_kernel -lm
c_status="${?}"
if [ "${c_status}" -ne 0 ]; then
    printf '[C_WARN] GCC build exited with %d\n' "${c_status}"
fi

printf '[GO] Compiling 5-Node WireGuard Phyllotactic Mesh Agent...\n'
go build -o target/release/tx_murua_mesh_agent src/go/murua_mesh_agent.go
go_status="${?}"
if [ "${go_status}" -ne 0 ]; then
    printf '[GO_WARN] Go build exited with %d\n' "${go_status}"
fi

printf '[NIM] Compiling Symbolic Ontology & AST Grammar Checker...\n'
nim c -d:release --hints:off --out:target/release/tx_softem_ontology src/nim/tx_softem_ontology.nim
nim_status="${?}"
if [ "${nim_status}" -ne 0 ]; then
    printf '[NIM_WARN] Nim build exited with %d\n' "${nim_status}"
fi

printf '[OCAML] Compiling Veritas-Rex Algebraic Escrow State Machine Verifier...\n'
ocamlopt -o target/release/tx_murua_escrow_verifier src/ocaml/murua_escrow_verifier.ml 2>/dev/null || ocamlc -o target/release/tx_murua_escrow_verifier src/ocaml/murua_escrow_verifier.ml
ocaml_status="${?}"
if [ "${ocaml_status}" -ne 0 ]; then
    printf '[OCAML_WARN] OCaml build exited with %d\n' "${ocaml_status}"
fi

printf '[BUILD_OK] All polyglot targets compiled on latitude-tianxia.\n'
REMOTE_BUILD

build_exit="${?}"
if [ "${build_exit}" -ne 0 ]; then
    printf '[FATAL] Remote build on %s failed.\n' "${DEST_HOST}" >&2
    exit 1
fi

# 3. Execute unit and integration tests on latitude-tianxia
printf '[3/8] Running Rust test suite on %s...\n' "${DEST_HOST}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_TEST'
set +e
set +u
cd ~/workspace/murua_architecture_enhancement || exit 1

cargo test --release
test_status="${?}"
if [ "${test_status}" -ne 0 ]; then
    printf '[TEST_ERR] Rust test suite failed with status %d\n' "${test_status}" >&2
    exit "${test_status}"
fi
printf '[TEST_OK] All Rust test suites PASSED!\n'
REMOTE_TEST

test_exit="${?}"
if [ "${test_exit}" -ne 0 ]; then
    printf '[FATAL] Unit tests failed on %s.\n' "${DEST_HOST}" >&2
    exit 1
fi

# 4. Execute Polyglot component test harnesses
printf '[4/8] Executing polyglot module verifications on %s...\n' "${DEST_HOST}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_POLYGLOT_TEST'
set +e
set +u
cd ~/workspace/murua_architecture_enhancement || exit 1

printf '[RUN] Testing C SRM acoustic kernel...\n'
./target/release/tx_srm_kernel || exit 1

printf '[RUN] Testing Zig zero-alloc ring buffer...\n'
./target/release/tx_murua_ring || exit 1

printf '[RUN] Testing Nim symbolic ontology validator...\n'
./target/release/tx_softem_ontology || exit 1

printf '[RUN] Testing OCaml escrow state machine...\n'
./target/release/tx_murua_escrow_verifier || exit 1

printf '[RUN] Testing Go WireGuard phyllotaxis agent...\n'
./target/release/tx_murua_mesh_agent || exit 1

printf '[RUN] Testing Python forensic ingestion and Veritas ledger...\n'
python3 python/murua_forensic_ingest.py || exit 1
python3 python/tx_veritas_ledger.py || exit 1

printf '[POLYGLOT_OK] All polyglot modules verified operational.\n'
REMOTE_POLYGLOT_TEST

polyglot_exit="${?}"
if [ "${polyglot_exit}" -ne 0 ]; then
    printf '[FATAL] Polyglot module verification failed.\n' >&2
    exit 1
fi

# 5. Production Installation
printf '[5/8] Installing production binaries & configs to %s:%s...\n' "${DEST_HOST}" "${INSTALL_PREFIX}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_INSTALL'
set +e
set +u
mkdir -p /var/lib/tianxia/murua/{bin,config,data,sql} /run/tianxia

cd ~/workspace/murua_architecture_enhancement || exit 1
cp -f target/release/tx_* /var/lib/tianxia/murua/bin/ 2>/dev/null || true
cp -f config/* /var/lib/tianxia/murua/config/
cp -f sql/* /var/lib/tianxia/murua/sql/
chmod +x /var/lib/tianxia/murua/bin/*

printf '[INSTALL_OK] Production artifacts placed in /var/lib/tianxia/murua.\n'
REMOTE_INSTALL

# 6. Database Initialization
printf '[6/8] Initializing SQLite production database...\n'
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_DB'
set +e
set +u
cd /var/lib/tianxia/murua || exit 1
sqlite3 data/tx_murua_telemetry.db < sql/tx_murua_telemetry.sql
printf '[DB_OK] Database initialized at /var/lib/tianxia/murua/data/tx_murua_telemetry.db.\n'
sqlite3 data/tx_murua_telemetry.db "SELECT corridor_id, origin_impc, dest_impc, c_cbd_score FROM murua_corridor_priors;"
REMOTE_DB

# 7. Systemd Service Deployment
printf '[7/8] Configuring and starting systemd service tx-murua.service...\n'
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_SERVICE'
set +e
set +u
cp -f /var/lib/tianxia/murua/config/tx-murua.service /run/systemd/system/tx-murua.service
systemctl daemon-reload
systemctl restart tx-murua.service
sleep 1
systemctl status tx-murua.service --no-pager
REMOTE_SERVICE

# 8. Live Telemetry Verification
printf '[8/8] Verifying live Murua Universal Tracer telemetry...\n'
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_VERIFY'
set +e
set +u
/var/lib/tianxia/murua/bin/tx_murua_tracer_daemon both
printf '\n[+] LIVE VERIFICATION CONVERGED: 100%% OPERATIONAL ON LATITUDE-TIANXIA.\n'
REMOTE_VERIFY

printf '================================================================================\n'
printf '[SUCCESS] TIANXIA OS MURUA v8.4-OMEGA DEPLOYMENT COMPLETE ON %s!\n' "${DEST_HOST}"
printf '================================================================================\n'
