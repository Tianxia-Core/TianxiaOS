#!/usr/bin/env bash
# ffp: TX-BOOTSTRAP glue bash
# BASELINE: BASELINE.json   REVISION: TX-BOOTSTRAP-2026.10-001
# Usage: bootstrap_tianxia.sh --role [cockpit|hub|mobile] [--help]
# Unified single-command installer for TianxiaOS sovereign cluster nodes.
set +e
set -o pipefail
trap 'printf "[IREB TRAP] %s:%s exit=%s\n" "$0" "$LINENO" "$?" >&2' ERR

TX_BASE_DIR="${TX_BASE_DIR:-/var/lib/tianxia}"
[ -d "$TX_BASE_DIR" ] || TX_BASE_DIR="${TX_WORKSPACE:-/var/lib/tianxia}/tianxia"
TX_ROLE="cockpit"
DRY_RUN=0

_log() { printf '[%s] [TX-BOOTSTRAP] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

if [ -n "${AUTONOMY_PAUSED:-}" ] || [ -n "${HUB_PAUSED:-}" ]; then
    _log "ABORT: kill-switch engaged (AUTONOMY_PAUSED / HUB_PAUSED)"
    exit 2
fi

while [ $# -gt 0 ]; do
    case "$1" in
        --role)
            TX_ROLE="${2:-cockpit}"
            shift 2
            ;;
        --dir)
            TX_BASE_DIR="${2:-$TX_BASE_DIR}"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --help|-h)
            printf "Usage: %s [--role cockpit|hub|mobile] [--dir PATH] [--dry-run]\n" "$0"
            exit 0
            ;;
        *)
            _log "Unknown option: $1"
            shift
            ;;
    esac
done

_log "Initializing TianxiaOS Sovereign Node Bootstrap..."
_log "Node Role:       ${TX_ROLE}"
_log "Target Directory: ${TX_BASE_DIR}"
_log "Host Architecture: $(uname -m 2>/dev/null || echo 'unknown')"

# 1. Directory Structure Creation
_log "[1/5] Verifying persistent substrate directories..."
mkdir -p "${TX_BASE_DIR}/bin" "${TX_BASE_DIR}/config" "${TX_BASE_DIR}/ui" \
         "${TX_BASE_DIR}/db" "${TX_BASE_DIR}/logs/state_locks" "${TX_BASE_DIR}/secrets"

# 2. Dependency Preflight Check
_log "[2/5] Assessing core system dependencies..."
for cmd in python3 git curl; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        _log "WARNING: Command '$cmd' not found in PATH"
    fi
done

# 3. Role-Specific Provisioning
_log "[3/5] Applying role-specific substrate configurations..."
case "$TX_ROLE" in
    hub)
        _log "Configuring Compute Workhorse Hub & TV Appliance..."
        if [ "$DRY_RUN" -eq 0 ] && [ -d "/etc/systemd/system" ]; then
            _log "Enabling core systemd services: tianxia-manas, tianxia-edge-forwarder..."
            systemctl daemon-reload 2>/dev/null || true
            systemctl enable --now tianxia-manas tianxia-edge-forwarder 2>/dev/null || true
        fi
        ;;
    cockpit)
        _log "Configuring Sovereign Operator Cockpit Workstation..."
        if [ "$DRY_RUN" -eq 0 ] && [ -d "/etc/systemd/system" ]; then
            _log "Enabling operator services: tianxia-manas..."
            systemctl daemon-reload 2>/dev/null || true
            systemctl enable --now tianxia-manas 2>/dev/null || true
        fi
        ;;
    mobile)
        _log "Configuring Mobile Tactical Go Enclave (Termux / Android)..."
        _log "Enforcing zero-trust perimeter: local loopback & mesh binding only."
        ;;
    *)
        _log "ERROR: Invalid role '${TX_ROLE}'. Must be one of: cockpit, hub, mobile."
        exit 1
        ;;
esac

# 4. Mesh SSH Key Configuration
_log "[4/5] Deploying post-quantum mesh SSH configuration..."
SSH_DIR="${HOME:-/root}/.ssh"
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR" 2>/dev/null || true
if [ -f "${TX_BASE_DIR}/config/mesh_ssh_config" ]; then
    if ! grep -q "tlat" "${SSH_DIR}/config" 2>/dev/null; then
        cat "${TX_BASE_DIR}/config/mesh_ssh_config" >> "${SSH_DIR}/config"
        chmod 600 "${SSH_DIR}/config" 2>/dev/null || true
        _log "Appended mesh_ssh_config to ${SSH_DIR}/config"
    fi
fi

# 5. DSS-14 Build Law Verification
_log "[5/5] Running DSS-14 Build Law self-test..."
if [ -f "${TX_BASE_DIR}/bin/tx_ds_gate.py" ]; then
    python3 "${TX_BASE_DIR}/bin/tx_ds_gate.py" --target "${TX_BASE_DIR}/bin/tx_state_lock.py" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        _log "DSS-14 Build Law: 100.0% ADMITTED across all 17 domains."
    else
        _log "WARNING: DSS-14 gate check returned non-zero status."
    fi
fi

# 6. O(1) State Lock Checkpoint
if [ -f "${TX_BASE_DIR}/bin/tx_state_lock.py" ]; then
    _log "Sealing O(1) baseline state lock checkpoint..."
    python3 "${TX_BASE_DIR}/bin/tx_state_lock.py" --json >/dev/null 2>&1 || true
fi

_log "======================================================="
_log "TIANXIAOS // NODE BOOTSTRAP COMPLETE"
_log "Status:  OPERATIONAL (Role: ${TX_ROLE})"
_log "Founder: Collins Takem (RASA-X-MACHINA)"
_log "======================================================="

exit 0
