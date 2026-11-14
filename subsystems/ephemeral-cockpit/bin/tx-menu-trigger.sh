#!/run/current-system/sw/bin/bash
# TIANXIAOS // Toggle Ephemeral Cockpit HUD
# Conforms to SLECO-SO++ and TianxiaOS Build Law
set +e
set +u

if [ -z "${XDG_RUNTIME_DIR:-}" ]; then
    if [ -S /run/tx-cockpit-runtime/wayland-1 ]; then
        export XDG_RUNTIME_DIR="/run/tx-cockpit-runtime"
    else
        export XDG_RUNTIME_DIR="/run/user/0"
    fi
fi
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"

# Ensure /dev/shm/tx_menu_ast exists and is initialized
if [ ! -f /dev/shm/tx_menu_ast ] || [ ! -s /dev/shm/tx_menu_ast ]; then
    if [ -x /var/lib/tianxia/bin/tx-menu-ast ]; then
        /var/lib/tianxia/bin/tx-menu-ast >/dev/null 2>&1
    fi
fi

# Ensure broker daemon is running
if ! pgrep -f '[t]x-menu-broker' >/dev/null 2>&1; then
    if [ -x /var/lib/tianxia/bin/tx-menu-broker ]; then
        /var/lib/tianxia/bin/tx-menu-broker >/var/lib/tianxia/logs/broker.log 2>&1 &
        sleep 0.1
    fi
fi

# Toggle HUD: if already running, dismiss
HUD_PID=$(pgrep -f '[t]x-ephemeral-hud' | head -1)
if [ -n "${HUD_PID:-}" ]; then
    kill "${HUD_PID}" 2>/dev/null
    exit 0
fi

# Launch HUD on active Wayland layer
exec /var/lib/tianxia/bin/tx-ephemeral-hud
