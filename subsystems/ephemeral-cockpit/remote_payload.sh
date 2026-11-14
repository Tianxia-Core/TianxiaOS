#!/usr/bin/env bash
set -euo pipefail

echo "[*] [1/6] Veritas-Rex Pre-Flight Disk & Process Sanity..."
AVAIL_KB=$(df --output=avail / | tail -n 1 | tr -d ' ')
[ "$AVAIL_KB" -gt 2097152 ] || { echo "[!] Insufficient disk space on / (<2GB)"; exit 1; }

pkill -9 -f waybar 2>/dev/null || true
pkill -9 -f tetraledger 2>/dev/null || true
pkill -9 -f nixue 2>/dev/null || true

for conf in /var/lib/tianxia/config/hyprland-*.conf; do
  if [ -f "$conf" ]; then
    sed -i '/tetraledger/d;/tx_nixue/d;/waybar/d' "$conf" || true
  fi
done

echo "[*] [2/6] Structuring Autarchic Workspace & LLM Hygiene Firewalls..."
mkdir -p /var/lib/tianxia/{bin,registry,brand/icons,share/applications}
mkdir -p /etc/nixos/modules

for TARGET_HOME in /root /home/*; do
  if [ -d "$TARGET_HOME" ]; then
    mkdir -p "$TARGET_HOME/workspace"/{core,systems,subsystems,runtime,specs,payloads,archive,projects,.vault}
    mkdir -p "$TARGET_HOME/TianxiaOS" "$TARGET_HOME/.vault"
    chmod 0700 "$TARGET_HOME/workspace" "$TARGET_HOME/workspace/.vault" "$TARGET_HOME/.vault"
    ln -sfn "$TARGET_HOME/workspace" "$TARGET_HOME/TianxiaOS/workspace"
    ln -sfn "$TARGET_HOME/workspace" "$TARGET_HOME/TianxiaOS-Workspace"

    cat << 'GITIGNORE_EOF' > "$TARGET_HOME/workspace/.gitignore"
.vault/
*.key
*.pem
*.crt
*.pfx
*.secret
*.password
*.env
*.env.*
id_rsa*
id_ed25519*
payloads/large_weights/
payloads/datasets/
*.bin
*.onnx
*.safetensors
*.gguf
*.iso
*.img
runtime/
*.sock
*.pid
*.lock
archive/logs/
archive/dumps/
*.log
*.trc
target/
result/
build/
GITIGNORE_EOF

    cat << 'MAP_EOF' > "$TARGET_HOME/workspace/WORKSPACE_MAP.md"
# TIANXIAOS v5.0 AUTARCHIC WORKSPACE ARCHITECTURE
- ~/workspace/core       : Tier 1 foundational compilers, toolchains (Rust, Zig, Go, Nix)
- ~/workspace/systems    : Tier 2 platform suites (TianxiaOS, Unbound OS, AetherVault, Faery Fortress)
- ~/workspace/subsystems : Tier 3 VUDA/SOFTEM drivers, AF_XDP telemetry taps, Tailscale/Unbound DNS
- ~/workspace/runtime    : Tier 4 ephemeral IPC sockets, RASOOM ring buffers, state locks
- ~/workspace/specs      : Tier 1-5 SLECO-SO schemas, architectural blueprints, AST definitions
- ~/workspace/payloads   : Tier 4 compiled binaries, microVM rootfs images, ISO builds, weights
- ~/workspace/archive    : Tier 5 immutable execution traces and historical audit logs
- ~/workspace/projects   : User-extensible custom project domains and academic repositories
- ~/workspace/.vault     : Air-gapped encrypted keystores (Excluded from Git & LLM sweeps)
MAP_EOF

    OWNER_UG=$(stat -c '%U:%G' "$TARGET_HOME")
    chown -R "$OWNER_UG" "$TARGET_HOME/workspace" "$TARGET_HOME/TianxiaOS" "$TARGET_HOME/TianxiaOS-Workspace" || true
  fi
done

echo "[*] [3/6] Deploying tx-menu-expand..."
cp /tmp/tx-menu-expand /var/lib/tianxia/bin/tx-menu-expand
chmod +x /var/lib/tianxia/bin/tx-menu-expand
/var/lib/tianxia/bin/tx-menu-expand scan

echo "[*] [4/6] Installing /etc/nixos/modules/tianxia-super-harness.nix and /etc/nixos/tianxia-iso.nix..."
cp /tmp/tianxia-super-harness.nix /etc/nixos/modules/tianxia-super-harness.nix
cp /tmp/tianxia-iso.nix /etc/nixos/tianxia-iso.nix

echo "[*] [5/6] Registering /etc/nixos/modules/tianxia-super-harness.nix in configuration.nix..."
if ! grep -q "tianxia-super-harness.nix" /etc/nixos/configuration.nix; then
  sed -i 's|imports = \[|imports = \[ ./modules/tianxia-super-harness.nix|' /etc/nixos/configuration.nix
fi

echo "[*] [6/6] Committing and Switching NixOS Generation..."
git -C /etc/nixos add -A
git -C /etc/nixos commit -m "feat(v5.0): deploy TianxiaOS Asura Super-Harness and tri-node Tailscale mesh" || true
nixos-rebuild switch
echo "[+] SUCCESS: TianxiaOS v5.0 Super-Harness is active."
