#!/usr/bin/env bash
# ffp: FFP-SH-001 enterprise-deploy-orchestrator bash
# TianxiaOS & Ndimmôrwyn: Enterprise Production-Grade Architecture Deployment Engine
# Target: latitude-tianxia (${TX_HUB_HOST:-127.0.0.1})
# Compliance: SLECO-SO++ + DSS-14 + ENHAN3

set +e
set +u

DEST_HOST="latitude-tianxia"
SCRIPT_DIR="$(cd "${0%/*}" 2>/dev/null && pwd)"
PROJECT_DIR="${SCRIPT_DIR}"
REMOTE_WS="~/workspace/tianxiaos_ndimmorwyn_enterprise"
INSTALL_PREFIX="/var/lib/tianxia"

cleanup() {
    local exit_code="${?}"
    if [ "${exit_code}" -ne 0 ]; then
        printf '[DEPLOY_ERR] Deployment pipeline interrupted with code: %d\n' "${exit_code}" >&2
    fi
}
trap cleanup EXIT

printf '=== [TIANXIAOS // NDIMMÔRWYN] Enterprise Production Suite Deployment ===\n'
printf 'Host: %s\n' "${DEST_HOST}"
printf 'Source Tree: %s\n' "${PROJECT_DIR}"

# 1. Sync local tree to latitude-tianxia
printf '[1/6] Syncing source tree to %s:%s...\n' "${DEST_HOST}" "${REMOTE_WS}"
ssh "${DEST_HOST}" "mkdir -p ~/workspace/tianxiaos_ndimmorwyn_enterprise" || exit 1
rsync -avz --delete \
    --exclude='.git' \
    --exclude='target' \
    "${PROJECT_DIR}/" "${DEST_HOST}:~/workspace/tianxiaos_ndimmorwyn_enterprise/" || exit 1

# 2. Compile Rust binaries on latitude-tianxia
printf '[2/6] Compiling production release binaries on %s...\n' "${DEST_HOST}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_BUILD'
set +e
set +u
cd ~/workspace/tianxiaos_ndimmorwyn_enterprise || exit 1

printf '[REMOTE_CARGO] Building release binaries...\n'
cargo build --release
build_status="${?}"
if [ "${build_status}" -ne 0 ]; then
    printf '[CARGO_ERR] Cargo build failed with status %d\n' "${build_status}" >&2
    exit "${build_status}"
fi
printf '[REMOTE_CARGO] Build successful!\n'
REMOTE_BUILD

if [ "${?}" -ne 0 ]; then
    printf '[FATAL] Build on %s failed.\n' "${DEST_HOST}" >&2
    exit 1
fi

# 3. Execute unit and integration tests on latitude-tianxia
printf '[3/6] Running full test suite on %s...\n' "${DEST_HOST}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_TEST'
set +e
set +u
cd ~/workspace/tianxiaos_ndimmorwyn_enterprise || exit 1

printf '[REMOTE_TEST] Running cargo test...\n'
cargo test --release
test_status="${?}"
if [ "${test_status}" -ne 0 ]; then
    printf '[TEST_ERR] Cargo test failed with status %d\n' "${test_status}" >&2
    exit "${test_status}"
fi
printf '[REMOTE_TEST] All Rust tests passed!\n'
REMOTE_TEST

if [ "${?}" -ne 0 ]; then
    printf '[FATAL] Tests on %s failed.\n' "${DEST_HOST}" >&2
    exit 1
fi

# 4. Run DSS-14 static gate compiler
printf '[4/6] Executing DSS-14 static gate compiler...\n'
ssh "${DEST_HOST}" "cd ~/workspace/tianxiaos_ndimmorwyn_enterprise && python3 python/tx_ds_gate.py"
if [ "${?}" -ne 0 ]; then
    printf '[FATAL] DSS-14 static gate audit failed.\n' >&2
    exit 1
fi

# 5. Staging binaries & systemd service units
printf '[5/6] Staging binaries in %s/bin and configuring systemd...\n' "${INSTALL_PREFIX}"
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_INSTALL'
set +e
set +u
mkdir -p /var/lib/tianxia/bin /var/lib/tianxia/python /var/lib/tianxia/config/matrices /run/systemd/system

cd ~/workspace/tianxiaos_ndimmorwyn_enterprise || exit 1

# Copy compiled binaries
cp -f target/release/tx_spear_and_meter /var/lib/tianxia/bin/
cp -f target/release/tx_srm_apex_daemon /var/lib/tianxia/bin/
cp -f target/release/tx_tetraledger_aurum /var/lib/tianxia/bin/
cp -f target/release/tx_void_shadow_lsp /var/lib/tianxia/bin/
cp -f target/release/tx_biomimetic_router /var/lib/tianxia/bin/
cp -f target/release/tx_dss14_validator /var/lib/tianxia/bin/
chmod +x /var/lib/tianxia/bin/tx_*

# Copy Python modules
cp -rf python/* /var/lib/tianxia/python/
chmod +x /var/lib/tianxia/python/*.py

# Copy matrices
cp -rf config/matrices/* /var/lib/tianxia/config/matrices/

# Install systemd service units
cp -f config/systemd/*.service /run/systemd/system/

systemctl daemon-reload
systemctl restart tx-srm-apex.service
systemctl restart tx-tetraledger-aurum.service
systemctl restart tx-biomimetic-orchestrator.service

printf '[SYSTEMD_OK] Services restarted successfully.\n'
REMOTE_INSTALL

# 6. Live verification smoke tests
printf '[6/6] Verifying live operation and executing smoke suite...\n'
ssh "${DEST_HOST}" "bash -s" << 'REMOTE_VERIFY'
set +e
set +u
printf '\n--- [SMOKE TEST 1: SRM APEX DAEMON] ---\n'
/var/lib/tianxia/bin/tx_srm_apex_daemon

printf '\n--- [SMOKE TEST 2: TETRALEDGER AURUM BUS] ---\n'
/var/lib/tianxia/bin/tx_tetraledger_aurum

printf '\n--- [SMOKE TEST 3: CAREER SPEAR & OUTCOME METER] ---\n'
/var/lib/tianxia/bin/tx_spear_and_meter "Paid.ai"

printf '\n--- [SMOKE TEST 4: BIOMIMETIC ROUTER] ---\n'
/var/lib/tianxia/bin/tx_biomimetic_router

printf '\n--- [SMOKE TEST 5: DSS-14 UNIVERSAL VALIDATOR] ---\n'
/var/lib/tianxia/bin/tx_dss14_validator

printf '\n--- [SYSTEMD STATUS] ---\n'
systemctl status tx-srm-apex.service --no-pager
systemctl status tx-tetraledger-aurum.service --no-pager
systemctl status tx-biomimetic-orchestrator.service --no-pager
REMOTE_VERIFY

printf '\n=== [TIANXIAOS // NDIMMÔRWYN] Deployment & Verification Completed Successfully ===\n'
exit 0
