#!/usr/bin/env bash
# TIANXIAOS // Ephemeral Cockpit & Sovereign Menu Deployment Engine
# Target: latitude-tianxia (${TX_HUB_HOST:-127.0.0.1})
set -euo pipefail

DEST_HOST="${TX_HUB_HOST:-127.0.0.1}"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== [TIANXIAOS] Ephemeral Cockpit & Sovereign Menu Deployment ==="
echo "Host: ${DEST_HOST}"
echo "Source: ${BASE_DIR}"

# 1. Sync source tree to Latitude
echo "[1/6] Syncing source tree to /var/lib/tianxia/tianxiaos_arch_menu_system..."
ssh root@${DEST_HOST} "mkdir -p /var/lib/tianxia/tianxiaos_arch_menu_system /var/lib/tianxia/bin /var/lib/tianxia/lib /var/lib/tianxia/logs /run/tianxia"
rsync -avz --exclude='.git' "${BASE_DIR}/" root@${DEST_HOST}:/var/lib/tianxia/tianxiaos_arch_menu_system/

# 2. Install executable binaries and scripts
echo "[2/6] Staging binaries and scripts in /var/lib/tianxia/bin..."
ssh root@${DEST_HOST} "bash -s" << 'EOF'
set -euo pipefail

# Copy binaries
cp -f /var/lib/tianxia/tianxiaos_arch_menu_system/src/tx-menu-ast/tx_menu_ast /var/lib/tianxia/bin/tx-menu-ast
chmod +x /var/lib/tianxia/bin/tx-menu-ast

cp -f /var/lib/tianxia/tianxiaos_arch_menu_system/bin/tx-elastic-exec /var/lib/tianxia/bin/tx-elastic-exec
chmod +x /var/lib/tianxia/bin/tx-elastic-exec

cp -f /var/lib/tianxia/tianxiaos_arch_menu_system/bin/tx-zygote-resume /var/lib/tianxia/bin/tx-zygote-resume
chmod +x /var/lib/tianxia/bin/tx-zygote-resume

cp -f /var/lib/tianxia/tianxiaos_arch_menu_system/bin/tx-menu-trigger.sh /var/lib/tianxia/bin/tx-menu-trigger.sh
chmod +x /var/lib/tianxia/bin/tx-menu-trigger.sh

# Verify core binaries exist in /var/lib/tianxia/bin
ls -lh /var/lib/tianxia/bin/tx-ephemeral-hud /var/lib/tianxia/bin/tx-menu-broker /var/lib/tianxia/bin/tx-menu-ast /var/lib/tianxia/bin/tx-virtwl-proxy /var/lib/tianxia/lib/libtx_manas_cpu.so
EOF

# 3. Populate /dev/shm/tx_menu_ast with DSS-14.2 verified AST
echo "[3/6] Initializing /dev/shm/tx_menu_ast via Nim AST engine..."
ssh root@${DEST_HOST} "/var/lib/tianxia/bin/tx-menu-ast"

# 4. Install NixOS module and systemd units
echo "[4/6] Installing NixOS module and systemd runtime units..."
ssh root@${DEST_HOST} "bash -s" << 'EOF'
set -euo pipefail
mkdir -p /etc/nixos/modules /run/systemd/system
cp -f /var/lib/tianxia/tianxiaos_arch_menu_system/nix/tianxia-ephemeral-menu.nix /etc/nixos/modules/tianxia-ephemeral-menu.nix

cat << 'UNIT' > /run/systemd/system/tx-menu-broker.service
[Unit]
Description=TianxiaOS Polyglot Menu AST & CoW MicroVM Broker
After=network.target

[Service]
Type=simple
ExecStart=/var/lib/tianxia/bin/tx-menu-broker
Restart=always
RestartSec=100ms
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

cat << 'UNIT' > /run/systemd/system/tx-wayland-virtwl-proxy.service
[Unit]
Description=TianxiaOS OCaml Cross-VM Wayland Capability Proxy
After=network.target

[Service]
Type=simple
ExecStart=/var/lib/tianxia/bin/tx-virtwl-proxy
Restart=always
RestartSec=500ms
MemoryMax=64M
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl restart tx-menu-broker.service
systemctl restart tx-wayland-virtwl-proxy.service
EOF

# 5. Wire Hyprland keybindings for instant HUD summon
echo "[5/6] Injecting sovereign HUD keybindings into Hyprland configs..."
ssh root@${DEST_HOST} "python3 -s" << 'EOF'
import re

configs = [
    "/var/lib/tianxia/config/hyprland-tv.conf",
    "/var/lib/tianxia/config/hyprland-tx.conf"
]

hud_binds = """
# TianxiaOS Sovereign Ephemeral Cockpit HUD
bind = $mod, Space, exec, /var/lib/tianxia/bin/tx-menu-trigger.sh
bind = $mod, M, exec, /var/lib/tianxia/bin/tx-menu-trigger.sh
bind = ALT, 1, exec, python3 -c "import socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect('/run/tianxia/broker.sock'); s.send(bytes([0x54, 0x58, 0x4F, 0x53, 31, 0, 0, 0, 1, 0, 0, 0]) + b'Alt+1 Enforce Lock'.ljust(128, b'\\x00'))"
bind = ALT, 2, exec, python3 -c "import socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect('/run/tianxia/broker.sock'); s.send(bytes([0x54, 0x58, 0x4F, 0x53, 41, 0, 0, 0, 0, 0, 0, 0]) + b'Alt+2 Adjust Holdback'.ljust(128, b'\\x00'))"
bind = ALT, 3, exec, python3 -c "import socket; s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.connect('/run/tianxia/broker.sock'); s.send(bytes([0x54, 0x58, 0x4F, 0x53, 12, 0, 0, 0, 0, 0, 0, 0]) + b'Alt+3 Inspect AF_XDP'.ljust(128, b'\\x00'))"

# Layer-shell blur rules for Ephemeral HUD
layerrule = blur 1, match:namespace ^(tianxia-ephemeral-hud)$
layerrule = ignore_alpha 0.15, match:namespace ^(tianxia-ephemeral-hud)$
"""

for path in configs:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if "tx-menu-trigger.sh" not in content:
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n" + hud_binds)
            print(f"[HYPR_BIND] Successfully injected HUD bindings into {path}")
        else:
            print(f"[HYPR_BIND] HUD bindings already present in {path}")
    except Exception as e:
        print(f"[HYPR_BIND] Error updating {path}: {e}")
EOF

# 6. Verification & Health Check
echo "[6/6] Verifying systemd unit status and shared memory..."
ssh root@${DEST_HOST} "bash -s" << 'EOF'
set -euo pipefail
echo "=== Systemd Services Status ==="
systemctl status tx-menu-broker.service --no-pager
systemctl status tx-wayland-virtwl-proxy.service --no-pager

echo "=== Shared Memory Verification ==="
ls -lh /dev/shm/tx_menu_ast
ls -lh /run/tianxia/broker.sock /run/tianxia/virtwl.sock

echo "=== Hyprland Debounced Reload ==="
if [ -x /var/lib/tianxia/bin/hypr-verify-reload ]; then
    /var/lib/tianxia/bin/hypr-verify-reload || true
fi
EOF

echo "=== [TIANXIAOS] Deployment Completed Successfully ==="
