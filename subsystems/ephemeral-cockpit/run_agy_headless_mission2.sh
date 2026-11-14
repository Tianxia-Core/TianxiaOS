#!${TX_PREFIX:-/usr/local}/files/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="${HOME}/workspace/tianxiaos_arch_menu_system"
MISSIONS_DIR="${WORKSPACE_ROOT}/missions"
MISSION_FILE="${MISSIONS_DIR}/tianxia_kde_ui_super_harness.md"
LOG_DIR="${WORKSPACE_ROOT}/logs"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SESSION_LOG="${LOG_DIR}/agy_headless_${TIMESTAMP}.log"

PRIMARY_HOST="latitude-tianxia"
PRIMARY_IP="${TX_HUB_HOST:-127.0.0.1}"

mkdir -p "${WORKSPACE_ROOT}" "${MISSIONS_DIR}" "${LOG_DIR}"

log() {
  local level="$1"
  local msg="$2"
  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf "[%s] [%s] %s\n" "${ts}" "${level}" "${msg}" | tee -a "${SESSION_LOG}"
}

# 1. Android Termux wake-lock
if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock || true
  log "INFO" "Termux wake-lock active."
fi

cleanup() {
  local exit_code=$?
  if command -v termux-wake-unlock >/dev/null 2>&1; then
    termux-wake-unlock || true
  fi
  log "INFO" "Session finished (exit code ${exit_code}). Log: ${SESSION_LOG}"
}
trap cleanup EXIT INT TERM

# 2. Path normalization & auto-discovery
if [ -f "${WORKSPACE_ROOT}/missions" ] && [ ! -d "${WORKSPACE_ROOT}/missions" ]; then
  mv -f "${WORKSPACE_ROOT}/missions" "/tmp/mission_rescue.tmp"
  mkdir -p "${MISSIONS_DIR}"
  mv -f "/tmp/mission_rescue.tmp" "${MISSION_FILE}"
fi

if [ ! -s "${MISSION_FILE}" ]; then
  for candidate in \
    "/sdcard/Download/tianxia_kde_ui_super_harness.md" \
    "${WORKSPACE_ROOT}/tianxia_kde_ui_super_harness.md" \
    "${HOME}/workspace/tianxia_kde_ui_super_harness.md" \
    "${MISSIONS_DIR}/.augmented_"*.md; do
    if [ -s "${candidate}" ]; then
      cp -f "${candidate}" "${MISSION_FILE}"
      log "INFO" "Discovered and restored payload from ${candidate}"
      break
    fi
  done
fi

if [ ! -s "${MISSION_FILE}" ]; then
  log "ERROR" "Mission file not found or empty at: ${MISSION_FILE}"
  exit 1
fi

log "INFO" "Target payload confirmed: ${MISSION_FILE} ($(wc -c < "${MISSION_FILE}") bytes)."

# 3. Pre-seed agy permissive tool configuration
python3 - << 'PYEOF'
import json
from pathlib import Path
for cfg in [Path.home() / ".config" / "agy" / "settings.json", Path.home() / ".agy" / "settings.json"]:
    cfg.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text())
        except Exception:
            data = {}
    perms = data.setdefault("permissions", {})
    rules = set(perms.get("allow", []))
    rules.update(["command(*)", "edit(*)", "read(*)", "write(*)", "glob(*)", "grep(*)", "list_directory(*)"])
    perms["allow"] = sorted(list(rules))
    cfg.write_text(json.dumps(data, indent=2))
PYEOF

# 4. Tailscale reachability check
log "INFO" "Checking Tailscale connectivity to ${PRIMARY_HOST} (${PRIMARY_IP})..."
if ! ping -c 1 -W 2 "${PRIMARY_IP}" >/dev/null 2>&1; then
  log "WARN" "ICMP ping to ${PRIMARY_IP} dropped; Tailscale SSH socket will negotiate directly."
fi

# 5. Build execution prompt & dispatch
AGY_BIN="$(command -v agy || echo "${HOME}/../usr/bin/agy")"
AUGMENTED_PROMPT="${WORKSPACE_ROOT}/missions/.augmented_${TIMESTAMP}.md"

cat << 'PROMPT_HEADER' > "${AUGMENTED_PROMPT}"
# AUTONOMOUS HEADLESS EXECUTION DIRECTIVE (GEMINI 3.8 FLASH IN AGY)
- Execution Mode: HEADLESS, NON-INTERACTIVE, 100% PERMISSIVE.
- Tool Permissions: Auto-approved via --dangerously-skip-permissions.
- Primary Workhorse: latitude-tianxia (${TX_HUB_HOST:-127.0.0.1}).
- XPS 13 Status: MAINTENANCE_STANDBY (non-blocking).
- Primary Deliverable: Deploy /etc/nixos/modules/tianxia-super-harness.nix and run nixos-rebuild switch on latitude-tianxia via SSH.

---

PROMPT_HEADER

cat "${MISSION_FILE}" >> "${AUGMENTED_PROMPT}"

log "INFO" "Executing agy (gemini-3.8-flash) with --dangerously-skip-permissions..."

export AGY_HEADLESS=1
export AGY_NON_INTERACTIVE=1
export AGY_AUTO_ACCEPT=1
export AGY_ACCEPT_ALL_EDITS=1
export AGY_ACCEPT_ALL_COMMANDS=1

"${AGY_BIN}" \
  --model gemini-3.8-flash \
  --dangerously-skip-permissions \
  -p "$(cat "${AUGMENTED_PROMPT}")" 2>&1 | tee -a "${SESSION_LOG}"

rm -f "${AUGMENTED_PROMPT}"
log "INFO" "Headless execution pipeline finished."
