#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$HOME/workspace/tianxiaos_arch_menu_system"
MISSIONS_DIR="$BASE_DIR/missions"
REMOTE_NODE="latitude-tianxia"
LOG_DIR="$BASE_DIR/logs/orchestration"

mkdir -p "$LOG_DIR"
cd "$BASE_DIR"

# ---------------------------------------------------------
# Telemetry Math & Formatting Primitives
# ---------------------------------------------------------
format_duration() {
    local total_seconds=$1
    local hrs=$((total_seconds / 3600))
    local mins=$(((total_seconds % 3600) / 60))
    local secs=$((total_seconds % 60))
    if [ "$hrs" -gt 0 ]; then
        printf "%02dh %02dm %02ds" "$hrs" "$mins" "$secs"
    else
        printf "%02dm %02ds" "$mins" "$secs"
    fi
}

render_progress_bar() {
    local current=$1
    local total=$2
    local width=24
    local filled=$(( (current * width) / total ))
    local empty=$(( width - filled ))
    local pct=$(( (current * 100) / total ))

    printf "["
    printf "%0.s█" $(seq 1 $filled 2>/dev/null) || true
    printf "%0.s░" $(seq 1 $empty 2>/dev/null) || true
    printf "] %d/%d (%d%%)" "$current" "$total" "$pct"
}

set_termux_title() {
    printf "\033]0;%s\007" "$1"
}

# ---------------------------------------------------------
# Pre-Flight Verification
# ---------------------------------------------------------
echo "[*] === TIANXIA OS: MISSION SEQUENTIAL DISPATCHER ==="
echo "[*] Checking connectivity to $REMOTE_NODE via Tailscale..."
if ! ping -c 1 -W 3 "$REMOTE_NODE" > /dev/null 2>&1; then
    echo "[!] CRITICAL: Cannot reach $REMOTE_NODE over Tailscale."
    exit 1
fi
echo "[+] Mesh Node $REMOTE_NODE reachable. SSH latency validated."

# ---------------------------------------------------------
# Session Docket Registry (Resilient Regex Matching)
# ---------------------------------------------------------
declare -A SESSIONS
declare -A SESSION_FILES

SESSIONS["1"]="tianxiaos_ndimmorwyn_enterprise"
SESSION_FILES["1"]="$(ls -1 "$MISSIONS_DIR"/tianxiaos_*ndimm*part_*.md 2>/dev/null | tr '\n' ' ')"

SESSIONS["2"]="tianxiaos_polyglot_kenning"
SESSION_FILES["2"]="$(ls -1 "$MISSIONS_DIR"/tianxiaos_artificial_kenning*part_*.md 2>/dev/null | tr '\n' ' ')"

SESSIONS["3"]="murua_architecture_enhancement"
SESSION_FILES["3"]="$(ls -1 "$MISSIONS_DIR"/murua_architecture_enhancement*.md 2>/dev/null | tr '\n' ' ')"

SESSIONS["4"]="tianxiaos_crownforge_codex"
SESSION_FILES["4"]="$(ls -1 "$MISSIONS_DIR"/tianxiaos_v8.6.0_crownforge*.md 2>/dev/null | tr '\n' ' ')"

TOTAL_SESSIONS=4
GLOBAL_START_TIME=$(date +%s)
SESSION_DURATIONS=()

# ---------------------------------------------------------
# Sequential Execution Loop
# ---------------------------------------------------------
for idx in $(seq 1 $TOTAL_SESSIONS); do
    SESSION_NAME="${SESSIONS[$idx]}"
    SPEC_FILES="${SESSION_FILES[$idx]}"
    SESSION_LOG="$LOG_DIR/${SESSION_NAME}_$(date +%Y%m%d_%H%M%S).log"
    SESSION_START_TIME=$(date +%s)

    # Adaptive ETA Calculation
    if [ "${#SESSION_DURATIONS[@]}" -gt 0 ]; then
        SUM=0
        for dur in "${SESSION_DURATIONS[@]}"; do
            SUM=$((SUM + dur))
        done
        AVG_TIME=$((SUM / ${#SESSION_DURATIONS[@]}))
        REMAINING_SESSIONS=$((TOTAL_SESSIONS - idx + 1))
        ESTIMATED_REMAINING_SECS=$((AVG_TIME * REMAINING_SESSIONS))
        ETA_STR="~$(format_duration "$ESTIMATED_REMAINING_SECS")"
    else
        ETA_STR="Calculating (pending Docket 1 baseline)..."
    fi

    TOTAL_ELAPSED_SO_FAR=$((SESSION_START_TIME - GLOBAL_START_TIME))

    echo ""
    echo "================================================================================"
    echo " DOCKET:    $idx/$TOTAL_SESSIONS - $SESSION_NAME"
    echo " PROGRESS:  $(render_progress_bar $((idx - 1)) $TOTAL_SESSIONS)"
    echo " TOTAL RUN: $(format_duration "$TOTAL_ELAPSED_SO_FAR")"
    echo " EST. ETA:  $ETA_STR"
    echo " LOG FILE:  $SESSION_LOG"
    echo "================================================================================"

    # Termux titlebar heartbeat in background
    (
        while true; do
            NOW=$(date +%s)
            S_ELAPSED=$((NOW - SESSION_START_TIME))
            set_termux_title "[$idx/$TOTAL_SESSIONS] $SESSION_NAME | S_ELAPSED: $(format_duration "$S_ELAPSED") | ETA: $ETA_STR"
            sleep 2
        done
    ) &
    TICKER_PID=$!

    PROMPT="[TIANXIA_OS::AUTONOMOUS_BUILD_DIRECTIVE]
Project: $SESSION_NAME
Model: Gemini 3.8 Flash
Mesh Target: $REMOTE_NODE

MANDATES:
1. Zero stubs or placeholders. Output 100% complete, working files.
2. Termux is local orchestration only. Route all compile/test/nix commands to $REMOTE_NODE via:
   ssh $REMOTE_NODE 'cd ~/workspace && <CMD>'
3. Autonomously read all spec files listed below and implement all requirements directly.
4. Auto-approve all edits and disk operations.

SPECS:
$SPEC_FILES"

    # Launch agy with valid schema flags:
    # --project sets the session identifier
    # --mode auto enables autonomous tool execution
    # --dangerously-skip-permissions auto-approves command/edit tools
    # --print passes the prompt non-interactively
    set +e
    agy \
        --model "gemini-3.8-flash" \
        --project "$SESSION_NAME" \
        --mode auto \
        --dangerously-skip-permissions \
        --print "$PROMPT" 2>&1 | tee "$SESSION_LOG"
    RAW_EXIT="${PIPESTATUS[0]}"
    set -e

    # Terminate ticker process cleanly
    kill "$TICKER_PID" 2>/dev/null || true
    wait "$TICKER_PID" 2>/dev/null || true

    SESSION_END_TIME=$(date +%s)
    SESSION_DURATION=$((SESSION_END_TIME - SESSION_START_TIME))
    SESSION_DURATIONS+=("$SESSION_DURATION")

    echo ""
    echo "--------------------------------------------------------------------------------"
    if [ "$RAW_EXIT" -ne 0 ] || grep -qE "(no output produced|auto-denied)" "$SESSION_LOG"; then
        echo "[!] FAILURE: Session $SESSION_NAME failed or encountered errors (Exit: $RAW_EXIT)."
    else
        echo "[+] SUCCESS: Session $SESSION_NAME completed."
    fi
    echo "[*] Session Duration: $(format_duration "$SESSION_DURATION")"
    echo "[*] Current Stage:    $(render_progress_bar "$idx" $TOTAL_SESSIONS)"
    echo "--------------------------------------------------------------------------------"

    sync
    sleep 3
done

GLOBAL_END_TIME=$(date +%s)
TOTAL_RUNTIME=$((GLOBAL_END_TIME - GLOBAL_START_TIME))

set_termux_title "Tianxia Build Complete [$(format_duration "$TOTAL_RUNTIME")]"

echo ""
echo "================================================================================"
echo "[+] ALL 4 MISSIONS CONVERGED."
echo "[+] Final Status:      $(render_progress_bar $TOTAL_SESSIONS $TOTAL_SESSIONS)"
echo "[+] Total Run Time:    $(format_duration "$TOTAL_RUNTIME")"
echo "[+] Execution Logs:    $LOG_DIR"
echo "================================================================================"
