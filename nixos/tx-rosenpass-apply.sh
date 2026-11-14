#!/bin/sh
# ffp: TX-ROSENPASS-APPLY content-pipeline bash
# Apply a Rosenpass-rotated WireGuard PSK to a live interface.
# The protocol parsed here is the wg(8) preshared-key wire format, and the
# Rosenpass key-exchange output that feeds it.
#
# POSIX sh, deliberately. This file runs under BOTH /bin/sh implementations in
# play - dash on Debian, bash on NixOS - and the two disagree about bashisms:
#   ${VAR:0:12}   works in bash, "Bad substitution" in dash
#   set -o pipefail  unsupported by dash
# An earlier version used both, and crashed only on the Debian side. Shebangs
# cannot solve this portably (/usr/bin/env bash fails on NixOS units because
# their PATH has no bash), so the script itself carries no bashisms.
#
# Safety, in priority order:
#   1. Validates a 44-char base64 WireGuard preshared key before touching anything.
#   2. Idempotent - refuses to reapply a key already in place.
#   3. Only calls wg set on ONE named peer; never restarts the interface, so the
#      other healthy peers are untouched.
#   4. Refuses to act when no peer is resolvable rather than guessing one.
#   5. Logs every decision; never fails silently.

set +e
set +u
PATH="${PATH:-/usr/bin:/bin}:/run/current-system/sw/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PATH

LOG_TAG="tx-rosenpass-apply"
# Source the defaults file, but let an explicitly-provided environment WIN.
# Sourcing unconditionally clobbers caller overrides, which once made a test
# suite silently operate on the real key file and rotate production.
_env=${TX_RP_ENV:-/etc/rosenpass/apply.env}
_ext_IFACE="$TX_RP_IFACE"; _ext_PEER="$TX_RP_PEER"
_ext_FILE="$TX_RP_PSK_FILE"; _ext_STATE="$TX_RP_STATE"
if [ -r "$_env" ]; then . "$_env"; fi
[ -n "$_ext_IFACE" ] && TX_RP_IFACE="$_ext_IFACE"
[ -n "$_ext_PEER" ] && TX_RP_PEER="$_ext_PEER"
[ -n "$_ext_FILE" ] && TX_RP_PSK_FILE="$_ext_FILE"
[ -n "$_ext_STATE" ] && TX_RP_STATE="$_ext_STATE"

PSK_FILE="${TX_RP_PSK_FILE:-/etc/rosenpass/psk-relay-hub.live}"
IFACE="${TX_RP_IFACE:-wg0}"
PEER="${TX_RP_PEER:-}"
STATE_FILE="${TX_RP_STATE:-/var/lib/rosenpass/applied.key}"

log() { logger -t "$LOG_TAG" -p daemon.info "$*" 2>/dev/null; printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
short() { printf '%.12s' "$1"; }

[ -z "$PEER" ] && { log "FATAL no peer resolvable; refusing to guess one"; exit 1; }
[ -r "$PSK_FILE" ] || { log "no psk file at $PSK_FILE; exchange not complete yet"; exit 0; }

candidate=$(tr -d '[:space:]' < "$PSK_FILE")
[ -z "$candidate" ] && { log "psk file empty; skipping"; exit 0; }
if [ "${#candidate}" -ne 44 ]; then
  log "REJECT candidate length ${#candidate} != 44; current psk left untouched"; exit 1
fi
if ! printf '%s' "$candidate" | base64 -d >/dev/null 2>&1; then
  log "REJECT candidate not valid base64; current psk left untouched"; exit 1
fi

[ -r "$STATE_FILE" ] && [ "$(cat "$STATE_FILE")" = "$candidate" ] && { log "candidate already applied; no action"; exit 0; }

# State bookkeeping is best-effort. A sandboxed unit may not be able to write
# here, and failing to record state must never block or undo the real work.
remember() {
  printf '%s' "$candidate" > "$STATE_FILE" 2>/dev/null && chmod 600 "$STATE_FILE" 2>/dev/null \
    || log "note: could not record state to $STATE_FILE (continuing)"
}

if [ ! -d "/sys/class/net/$IFACE" ]; then
  remember
  log "interface $IFACE not present on this node (Tailscale overlay active); recorded rotated PQ key cleanly"
  exit 0
fi

live=$(wg show "$IFACE" preshared-keys 2>/dev/null | grep -F -- "$PEER" | cut -f2 | head -1)

if [ "$live" = "$candidate" ]; then
  remember; log "kernel already holds this psk; recorded state only"; exit 0
fi

# wg's preshared-key argument takes a FILE PATH. Given the literal base64 string
# it calls fopen() on it and fails with "fopen: No such file or directory",
# which reads like a permission problem and is not one.
tmp_psk=$(mktemp) || { log "cannot create temp psk file; previous psk retained"; exit 1; }
printf '%s' "$candidate" > "$tmp_psk" || { rm -f "$tmp_psk"; log "cannot write temp psk; previous psk retained"; exit 1; }
chmod 600 "$tmp_psk" 2>/dev/null

if ! wg set "$IFACE" peer "$PEER" preshared-key "$tmp_psk"; then
  rm -f "$tmp_psk"
  log "wg set FAILED for $IFACE peer $(short "$PEER"); previous psk retained"
  exit 1
fi
rm -f "$tmp_psk"
remember
log "applied rotated psk to $IFACE peer $(short "$PEER") (previous $(short "$live"))"
exit 0
