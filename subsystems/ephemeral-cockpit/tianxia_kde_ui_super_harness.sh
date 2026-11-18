#!${TX_PREFIX:-/usr/local}/files/usr/bin/env bash
set -euo pipefail

# 1. ENVIRONMENT & PATH DEFINITIONS
WORKSPACE_ROOT="${HOME}/workspace/tianxiaos_arch_menu_system"
MISSION_NAME="tianxia_kde_ui_super_harness.md"
MISSIONS_DIR="${WORKSPACE_ROOT}/missions"
MISSION_FILE="${MISSIONS_DIR}/${MISSION_NAME}"
DOWNLOAD_SOURCE="/sdcard/Download/${MISSION_NAME}"

AGY_CONFIG_DIR="${HOME}/.config/agy"
AGY_LEGACY_DIR="${HOME}/.agy"
GLOBAL_ALLOWLIST_FILE="${AGY_CONFIG_DIR}/persistent_allowed_commands.list"
GLOBAL_ALLOWLIST_JSON="${AGY_CONFIG_DIR}/allowed_commands.json"
GLOBAL_SETTINGS_JSON="${AGY_CONFIG_DIR}/settings.json"
LEGACY_SETTINGS_JSON="${AGY_LEGACY_DIR}/settings.json"

LOG_DIR="${WORKSPACE_ROOT}/logs"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SESSION_LOG="${LOG_DIR}/agy_headless_${TIMESTAMP}.log"
AUDIT_JSONL="${LOG_DIR}/agy_audit_${TIMESTAMP}.jsonl"
SSH_CONTROL_DIR="${HOME}/.ssh/ctl"

PRIMARY_HOST="latitude-tianxia"
PRIMARY_IP="${TX_HUB_HOST:-127.0.0.1}"
STANDBY_HOST="xps13-tianxia"

# Export global non-interactive & permissive environment variables for agy
export AGY_HEADLESS=1
export AGY_NON_INTERACTIVE=1
export AGY_AUTO_ACCEPT=1
export AGY_ACCEPT_ALL_EDITS=1
export AGY_ACCEPT_ALL_COMMANDS=1
export AGY_PERSIST_ALLOWED_COMMANDS=1
export AGY_YES_ALWAYS=1
export AGY_TRUST_ALL=1
export AGY_MODEL="${AGY_MODEL:-gemini-3.8-flash}"
export CI="true"
export DEBIAN_FRONTEND="noninteractive"
export GIT_TERMINAL_PROMPT=0
export PYTHONIOENCODING="utf-8"
export PYTHONUNBUFFERED=1

mkdir -p "${WORKSPACE_ROOT}" "${LOG_DIR}" "${AGY_CONFIG_DIR}" "${AGY_LEGACY_DIR}" "${SSH_CONTROL_DIR}"
chmod 0700 "${AGY_CONFIG_DIR}" "${AGY_LEGACY_DIR}" "${SSH_CONTROL_DIR}"

log_event() {
    local level="$1"
    local msg="$2"
    local ts
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf "[%s] [%s] %s\n" "${ts}" "${level}" "${msg}" | tee -a "${SESSION_LOG}"
    printf '{"timestamp":"%s","level":"%s","message":"%s"}\n' \
        "${ts}" "${level}" "${msg//\"/\\\"}" >> "${AUDIT_JSONL}"
}

# 2. ANDROID WAKE-LOCK & CLEANUP TRAP
acquire_wakelock() {
    if command -v termux-wake-lock >/dev/null 2>&1; then
        termux-wake-lock || true
        log_event "INFO" "Acquired Android Termux wake-lock."
    fi
}

cleanup_session() {
    local exit_code=$?
    log_event "INFO" "Harvesting session commands into global persistent allowlist..."
    harvest_and_persist_commands || true
    if command -v termux-wake-unlock >/dev/null 2>&1; then
        termux-wake-unlock || true
    fi
    log_event "INFO" "Headless agy session finished (exit=${exit_code}). Log: ${SESSION_LOG}"
}
trap cleanup_session EXIT INT TERM

# 3. SMART 'mv' PATH RECOVERY & SELF-SEEDING MISSION PAYLOAD
normalize_mission_payload() {
    cd "${WORKSPACE_ROOT}"

    # Recover if 'mv ./downloads/tianxia_kde_ui_super_harness.md missions'
    # created 'missions' as a flat file instead of a directory
    if [ -f "${WORKSPACE_ROOT}/missions" ] && [ ! -d "${WORKSPACE_ROOT}/missions" ]; then
        log_event "WARN" "Detected 'missions' as a flat file. Converting to missions/ directory..."
        mv -f "${WORKSPACE_ROOT}/missions" "${WORKSPACE_ROOT}/${MISSION_NAME}.tmp"
        mkdir -p "${MISSIONS_DIR}"
        mv -f "${WORKSPACE_ROOT}/${MISSION_NAME}.tmp" "${MISSION_FILE}"
        log_event "INFO" "Normalized mission payload to ${MISSION_FILE}"
    fi

    mkdir -p "${MISSIONS_DIR}"

    if [ -f "${DOWNLOAD_SOURCE}" ]; then
        log_event "INFO" "Moving ${DOWNLOAD_SOURCE} -> ${MISSION_FILE}"
        mv -f "${DOWNLOAD_SOURCE}" "${MISSION_FILE}"
    fi

    if [ ! -f "${MISSION_FILE}" ]; then
        for candidate in \
            "${WORKSPACE_ROOT}/${MISSION_NAME}" \
            "${HOME}/workspace/${MISSION_NAME}" \
            "${HOME}/workspace/tianxiaos_super_harness_master.md" \
            "./downloads/tianxiaos_super_harness_master.md"; do
            if [ -f "${candidate}" ]; then
                cp -f "${candidate}" "${MISSION_FILE}"
                log_event "INFO" "Copied mission payload from ${candidate} -> ${MISSION_FILE}"
                break
            fi
        done
    fi

    # Self-seed fallback mission specification if file is still absent
    if [ ! -s "${MISSION_FILE}" ]; then
        log_event "WARN" "Seeding default v5.0 Super-Harness mission specification at ${MISSION_FILE}..."
        cat << 'SEED_MISSION_EOF' > "${MISSION_FILE}"
# MISSION: TIANXIAOS v5.0 KDE PLASMA 6 SUPER-HARNESS & 5-TIER MENU DEPLOYMENT
1. Target primary compute workhorse `latitude-tianxia` (`${TX_HUB_HOST:-127.0.0.1}`) and active mobile edge nodes (`pixel8pro-tianxia`, `pocox5pro-tianxia`). Treat `xps13-tianxia` as `MAINTENANCE_STANDBY` (non-blocking).
2. Deploy `/etc/nixos/modules/tianxia-super-harness.nix` enabling KDE Plasma 6 Wayland, SDDM, Plymouth Breeze Neo-Noir splash, and Rasa-X-Machina Neo-Noir colors (`#080808`, `#00F0FF`, `#FF5533`, `#FFAA00`).
3. Provision the 5-Tier XDG application launcher (`[T1]` Cockpit/Monitor, `[T2]` Operator TUI/Tailscale Mesh/AetherVault, `[T3]` VUDA-SOFTEM/Storefront, `[T4]` on-demand TetraLedger/Foot/Kate, `[T5]` Workspace VFS/NixOS Substrate).
4. Deploy `/var/lib/tianxia/bin/tx-menu-expand` supporting `scan`, `semantic-zip`, `inject`, `remove`, `mesh-audit`, `vuda-audit`, `tui`, and `daemon`.
5. Initialize partitioned `~/workspace` (`core`, `systems`, `subsystems`, `runtime`, `specs`, `payloads`, `archive`, `projects`, `.vault`) with Dolphin `user-places.xbel` bookmarks and execute `nixos-rebuild switch`.
SEED_MISSION_EOF
    fi

    log_event "INFO" "Verified mission file: ${MISSION_FILE} ($(wc -c < "${MISSION_FILE}") bytes)."
}

# 4. GLOBAL PERSISTENT PERMISSIVE CONFIGURATION ENGINE
seed_global_permissive_store() {
    log_event "INFO" "Updating global persistent command & edit allowlists..."

    local base_commands=(
        "*"
        "ssh *"
        "scp *"
        "rsync *"
        "sudo *"
        "bash *"
        "sh *"
        "python3 *"
        "nix *"
        "nix-build *"
        "nixos-rebuild *"
        "systemctl *"
        "journalctl *"
        "tailscale *"
        "git *"
        "cat *"
        "sed *"
        "awk *"
        "grep *"
        "find *"
        "mkdir *"
        "chmod *"
        "chown *"
        "cp *"
        "mv *"
        "rm *"
        "ln *"
        "pkill *"
        "pgrep *"
        "curl *"
        "jq *"
        "kwriteconfig6 *"
        "kbuildsycoca6 *"
        "plasma-apply-colorscheme *"
        "tx-menu-expand *"
        "tx-workspace-init *"
        "/var/lib/tianxia/bin/*"
    )

    touch "${GLOBAL_ALLOWLIST_FILE}"
    for cmd_pattern in "${base_commands[@]}"; do
        if ! grep -Fxq "${cmd_pattern}" "${GLOBAL_ALLOWLIST_FILE}" 2>/dev/null; then
            printf "%s\n" "${cmd_pattern}" >> "${GLOBAL_ALLOWLIST_FILE}"
        fi
    done

    python3 - "${MISSION_FILE}" "${GLOBAL_ALLOWLIST_FILE}" "${GLOBAL_ALLOWLIST_JSON}" "${GLOBAL_SETTINGS_JSON}" "${LEGACY_SETTINGS_JSON}" << 'PY_SEED_EOF'
import json
import re
import sys
from pathlib import Path

mission_path = Path(sys.argv[1])
allowlist_path = Path(sys.argv[2])
allowlist_json_path = Path(sys.argv[3])
settings_path = Path(sys.argv[4])
legacy_settings_path = Path(sys.argv[5])

existing = [line.strip() for line in allowlist_path.read_text().splitlines() if line.strip()]
seen = set(existing)

text = mission_path.read_text(errors="ignore")
for line in text.splitlines():
    stripped = line.strip()
    if stripped and not stripped.startswith("#") and re.match(r"^[a-zA-Z0-9_/.-]+\s+", stripped):
        first_token = stripped.split()[0]
        if first_token in {
            "ssh", "scp", "sudo", "mkdir", "chmod", "chown", "ln", "cat",
            "sed", "git", "nixos-rebuild", "nix-build", "pkill", "cp", "mv",
            "tx-menu-expand", "tx-workspace-init", "tailscale", "systemctl", "bash"
        }:
            if stripped not in seen and len(stripped) < 240:
                existing.append(stripped)
                seen.add(stripped)
            wildcard_tok = f"{first_token} *"
            if wildcard_tok not in seen:
                existing.append(wildcard_tok)
                seen.add(wildcard_tok)

allowlist_path.write_text("\n".join(existing) + "\n")
allowlist_json_path.write_text(json.dumps({"allowed_commands": existing, "auto_allow_all": True}, indent=2) + "\n")

config_payload = {
    "model": "gemini-3.8-flash",
    "headless": True,
    "non_interactive": True,
    "auto_accept": True,
    "yes_always": True,
    "permissions": {
        "mode": "permissive",
        "auto_accept_edits": True,
        "auto_accept_commands": True,
        "persist_accepted_commands": True,
        "allow_all_file_writes": True,
        "allow_all_shell_commands": True,
        "global_allowed_commands": existing,
        "allowed_paths": [
            "*",
            "/root/*",
            "/etc/nixos/*",
            "/var/lib/tianxia/*",
            "${TX_HOME:-/var/lib/tianxia}/*"
        ]
    },
    "mesh_routing": {
        "primary_workhorse": "latitude-tianxia",
        "primary_ip": "${TX_HUB_HOST:-127.0.0.1}",
        "active_edge_nodes": ["pixel8pro-tianxia", "pocox5pro-tianxia"],
        "offline_excluded_nodes": ["xps13-tianxia"]
    }
}

for target_json in (settings_path, legacy_settings_path):
    target_json.parent.mkdir(parents=True, exist_ok=True)
    target_json.write_text(json.dumps(config_payload, indent=2) + "\n")
PY_SEED_EOF

    log_event "INFO" "Global persistent command allowlist seeded ($(wc -l < "${GLOBAL_ALLOWLIST_FILE}") rules)."
}

harvest_and_persist_commands() {
    [ -f "${SESSION_LOG}" ] || return 0
    python3 - "${SESSION_LOG}" "${GLOBAL_ALLOWLIST_FILE}" "${GLOBAL_ALLOWLIST_JSON}" "${GLOBAL_SETTINGS_JSON}" "${LEGACY_SETTINGS_JSON}" << 'PY_HARVEST_EOF'
import json
import re
import sys
from pathlib import Path

log_path = Path(sys.argv[1])
allowlist_path = Path(sys.argv[2])
allowlist_json_path = Path(sys.argv[3])
settings_path = Path(sys.argv[4])
legacy_path = Path(sys.argv[5])

existing = [line.strip() for line in allowlist_path.read_text().splitlines() if line.strip()]
seen = set(existing)

cmd_patterns = [
    re.compile(r"(?:Executing|Running|Command|Run|[$#])\s*[:>]?\s*(.+)$", re.IGNORECASE),
    re.compile(r"^\+\s+(.+)$")
]

for line in log_path.read_text(errors="ignore").splitlines():
    for pat in cmd_patterns:
        m = pat.search(line.strip())
        if m:
            candidate = m.group(1).strip()
            if candidate and candidate not in seen and len(candidate) < 240:
                existing.append(candidate)
                seen.add(candidate)

allowlist_path.write_text("\n".join(existing) + "\n")
allowlist_json_path.write_text(json.dumps({"allowed_commands": existing, "auto_allow_all": True}, indent=2) + "\n")

for cfg_file in (settings_path, legacy_path):
    if cfg_file.exists():
        try:
            data = json.loads(cfg_file.read_text())
            data.setdefault("permissions", {})["global_allowed_commands"] = existing
            cfg_file.write_text(json.dumps(data, indent=2) + "\n")
        except Exception:
            pass
PY_HARVEST_EOF
}

# 5. TAILSCALE MESH PRE-FLIGHT & SSH CONTROLMASTER MULTIPLEXING
establish_mesh_multiplexing() {
    log_event "INFO" "Checking Tailscale mesh link to ${PRIMARY_HOST} (${PRIMARY_IP})..."

    mkdir -p "${HOME}/.ssh"
    chmod 0700 "${HOME}/.ssh"
    if ! grep -q "ControlPath ~/.ssh/ctl/%r@%h:%p" "${HOME}/.ssh/config" 2>/dev/null; then
        cat << 'SSH_CFG_EOF' >> "${HOME}/.ssh/config"

Host latitude-tianxia ${TX_HUB_HOST:-127.0.0.1}
    HostName ${TX_HUB_HOST:-127.0.0.1}
    User root
    ControlMaster auto
    ControlPath ~/.ssh/ctl/%r@%h:%p
    ControlPersist 30m
    ConnectTimeout 5
    ServerAliveInterval 15
    ServerAliveCountMax 3
    StrictHostKeyChecking accept-new
SSH_CFG_EOF
        chmod 0600 "${HOME}/.ssh/config"
    fi

    LIVE_SEMANTIC_STATE="UNPROBED"
    if ssh -o BatchMode=yes -o ConnectTimeout=5 "${PRIMARY_HOST}" "true" 2>/dev/null; then
        log_event "INFO" "SSH ControlMaster active to ${PRIMARY_HOST} (${PRIMARY_IP})."
        LIVE_SEMANTIC_STATE="$(ssh -o ConnectTimeout=5 "${PRIMARY_HOST}" "/var/lib/tianxia/bin/tx-menu-expand semantic-zip 2>/dev/null || uptime" 2>/dev/null || echo "ONLINE")"
        log_event "INFO" "Workhorse Telemetry: ${LIVE_SEMANTIC_STATE}"
    else
        log_event "WARN" "SSH to ${PRIMARY_HOST} not reachable yet; staging local artifacts first."
    fi
}

# 6. AUGMENTED RUNTIME PROMPT ASSEMBLY
build_augmented_mission_prompt() {
    AUGMENTED_MISSION_FILE="${MISSIONS_DIR}/.augmented_${MISSION_NAME}"
    cat << AUG_EOF > "${AUGMENTED_MISSION_FILE}"
# AUTONOMOUS HEADLESS EXECUTION DIRECTIVE (GEMINI 3.8 FLASH IN AGY)
- Execution Mode: HEADLESS, NON-INTERACTIVE, 100% PERMISSIVE.
- Edit & Command Policy: All file edits and shell commands are pre-approved and permanently added to the global persistent allowlist (${GLOBAL_ALLOWLIST_FILE}). Execute end-to-end without pausing for confirmation.
- Active Tailscale Mesh Topology:
  1. Primary Compute & Desktop Workhorse: latitude-tianxia (${TX_HUB_HOST:-127.0.0.1}) — ONLINE TARGET.
  2. Primary Mobile Edge Orchestrator: pixel8pro-tianxia (Google Pixel 8 Pro) — ACTIVE.
  3. Secondary Mobile Edge Worker: pocox5pro-tianxia (Xiaomi Poco X5 Pro 5G) — ACTIVE.
  4. Standby Node (Offline / In Repair): xps13-tianxia (Dell XPS 13 9310) — DO NOT BLOCK OR WAIT ON THIS NODE; configure it as MAINTENANCE_STANDBY.
- Live Workhorse Telemetry Snapshot: ${LIVE_SEMANTIC_STATE}

---

AUG_EOF
    cat "${MISSION_FILE}" >> "${AUGMENTED_MISSION_FILE}"
    log_event "INFO" "Built augmented mission prompt: ${AUGMENTED_MISSION_FILE}"
}

# 7. HEADLESS AGY INVOCATION
execute_agy_headless() {
    cd "${WORKSPACE_ROOT}"

    if command -v agy >/dev/null 2>&1; then
        local agy_bin
        agy_bin="$(command -v agy)"
        log_event "INFO" "Found agy at ${agy_bin}. Probing supported flags..."

        local help_text=""
        help_text="$("${agy_bin}" --help 2>&1 || true)"

        local -a agy_args=()
        grep -q -- "--yes" <<<"${help_text}" && agy_args+=("--yes")
        grep -q -- "--auto-accept" <<<"${help_text}" && agy_args+=("--auto-accept")
        grep -q -- "--auto-approve" <<<"${help_text}" && agy_args+=("--auto-approve")
        grep -q -- "--allow-all" <<<"${help_text}" && agy_args+=("--allow-all")
        grep -q -- "--trust-all" <<<"${help_text}" && agy_args+=("--trust-all")
        grep -q -- "--non-interactive" <<<"${help_text}" && agy_args+=("--non-interactive")
        grep -q -- "--headless" <<<"${help_text}" && agy_args+=("--headless")

        if grep -q -- "--model" <<<"${help_text}"; then
            agy_args+=("--model" "${AGY_MODEL}")
        fi

        log_event "INFO" "Running agy with args: ${agy_args[*]:-(env-driven)}"

        set +e
        if grep -q -- "--file" <<<"${help_text}"; then
            yes a | "${agy_bin}" "${agy_args[@]}" --file "${AUGMENTED_MISSION_FILE}" 2>&1 | tee -a "${SESSION_LOG}"
            AGY_STATUS=${PIPESTATUS[1]}
        elif grep -q -- "--prompt-file" <<<"${help_text}"; then
            yes a | "${agy_bin}" "${agy_args[@]}" --prompt-file "${AUGMENTED_MISSION_FILE}" 2>&1 | tee -a "${SESSION_LOG}"
            AGY_STATUS=${PIPESTATUS[1]}
        else
            yes a | "${agy_bin}" "${agy_args[@]}" -p "$(cat "${AUGMENTED_MISSION_FILE}")" 2>&1 | tee -a "${SESSION_LOG}"
            AGY_STATUS=${PIPESTATUS[1]}
        fi
        set -e

        log_event "INFO" "agy exited with status ${AGY_STATUS}."
    else
        log_event "WARN" "'agy' binary not in PATH; running direct deployment fallback if staged."
    fi

    if [ -f "${HOME}/deploy_tianxia_v5.sh" ]; then
        log_event "INFO" "Executing ~/deploy_tianxia_v5.sh against ${PRIMARY_HOST}..."
        bash "${HOME}/deploy_tianxia_v5.sh" "${PRIMARY_HOST}" 2>&1 | tee -a "${SESSION_LOG}" || true
    fi
}

main() {
    acquire_wakelock
    log_event "INFO" "Starting TianxiaOS v5.0 Headless Permissive agy Runner..."
    normalize_mission_payload
    seed_global_permissive_store
    establish_mesh_multiplexing
    build_augmented_mission_prompt
    execute_agy_headless
    harvest_and_persist_commands
    log_event "INFO" "Mission execution and global command persistence complete."
}

main "$@"
