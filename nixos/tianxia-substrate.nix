# ffp: TX-TIANXIA-SUBSTRATE declarative nix
{ pkgs, ... }:

{
  # 1. Hardware Graphics Acceleration & Drivers
  hardware.graphics = {
    enable = true;
    enable32Bit = true;
    extraPackages = with pkgs; [
      intel-media-driver
      intel-vaapi-driver
      mesa
      libvdpau-va-gl
    ];
  };

  # 2. Kernel Modules & Ingress Hardening
  boot.kernelModules = [ "uinput" "i915" ];

  # 3. Global System Packages for Cockpit & Kiosk
  environment.systemPackages = with pkgs; [
    chromium
    cage
    lan-mouse
    waypipe
    wl-clipboard
    sqlite
    zig
  ];

  # 4. Hardware HID Udev Rules (Logitech G613 & Redragon M602-KS)
  services.udev.extraRules = ''
    KERNEL=="uinput", GROUP="input", MODE="0660"
    SUBSYSTEMS=="usb", ATTRS{idVendor}=="046d", GROUP="input", MODE="0660"
    SUBSYSTEMS=="hid", ATTRS{idVendor}=="046d", GROUP="input", MODE="0660"
    SUBSYSTEMS=="usb", ATTRS{idVendor}=="0c45", GROUP="input", MODE="0660"
    SUBSYSTEMS=="usb", ATTRS{idVendor}=="258a", GROUP="input", MODE="0660"
    SUBSYSTEMS=="hid", GROUP="input", MODE="0660"
  '';

  # 5. Dedicated Substrate System Users and Groups
  
  # Mesh Firewall & Substrate Port Lock
  
  # Systemd Daemon Stabilizers & Active Cluster Engines
  systemd.services.tianxia-clip-sync = {
    enable = true;
    description = "Tianxia Clipboard Synchronizer Daemon";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    path = [ pkgs.wl-clipboard pkgs.python3 ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia";
      Environment = [
        "TX_BASE_DIR=/var/lib/tianxia"
        "WAYLAND_DISPLAY=wayland-0"
        "XDG_RUNTIME_DIR=/run/user/0"
      ];
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_clip_sync.py";
      Restart = "always";
      RestartSec = "5s";
    };
  };

  systemd.services.tianxia-hussar-patrol = {
    enable = true;
    description = "Tianxia Hussar Autonomous Patrol & Orchestration Daemon";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    path = [ pkgs.python3 pkgs.curl pkgs.jq ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia";
      Environment = "TX_BASE_DIR=/var/lib/tianxia";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_hussar.py selftest";
      Restart = "always";
      RestartSec = "30s";
    };
  };

  systemd.services.tianxia-lan-mouse = {
    enable = true;
    description = "Tianxia LAN-Mouse KVM Service";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia";
      Environment = [
        "HOME=/var/lib/tianxia"
        "XDG_CONFIG_HOME=/var/lib/tianxia/.config"
        "XDG_DATA_HOME=/var/lib/tianxia/.local/share"
        "XDG_RUNTIME_DIR=/run/user/0"
        "WAYLAND_DISPLAY=wayland-1"
      ];
      ReadWritePaths = [ "/var/lib/tianxia" "/run/user/0" ];
      ExecStartPre = "-/run/current-system/sw/bin/rm -f /run/user/0/lan-mouse-socket.sock";
      ExecStart = "${pkgs.lan-mouse}/bin/lan-mouse daemon";
      Restart = "always";
      RestartSec = "10s";
    };
  };

  systemd.services.tianxia-typec-power = {
    enable = true;
    description = "Tianxia Type-C Power Role Enforcer (Source power to downstream peers)";
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = pkgs.writeShellScript "tx-typec-power" ''
        if [ -w /sys/class/typec/port0/power_role ]; then
          echo source > /sys/class/typec/port0/power_role 2>/dev/null || true
        fi
      '';
    };
  };

  systemd.services.tianxia-nimue = {
    enable = true;
    description = "Tianxia Nimue Autonomous Underwriting & Enforcement Engine (:8090)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia";
      ExecStart = "/var/lib/tianxia/bin/tx_nimue";
      Restart = "always";
      RestartSec = "5s";
      LimitNOFILE = 65536;
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-tetraledger-sync = {
    enable = true;
    description = "TetraLedger WAL Checkpoint & Integrity Sync";
    serviceConfig = {
      Type = "oneshot";
      ExecStart = pkgs.writeShellScript "tx-tetraledger-sync" ''
        if [ -f /var/lib/tetraledger/tetraledger.db ]; then
          ${pkgs.sqlite}/bin/sqlite3 /var/lib/tetraledger/tetraledger.db "PRAGMA wal_checkpoint(TRUNCATE); PRAGMA integrity_check;"
        fi
      '';
    };
  };

  systemd.timers.tianxia-tetraledger-sync = {
    enable = true;
    description = "Hourly TetraLedger WAL Checkpoint Timer";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "hourly";
      Persistent = true;
    };
  };

  
  # Declarative WireGuard Interface (Mesh Subnet: 10.0.99.0/24)
  # Declarative WireGuard Interface (Mesh Subnet: 10.0.99.0/24)
  

  
  systemd.services.tianxia-gui-bridge = {
    enable = true;
    description = "Tianxia Foveal GUI Hot-Reload SSE Telemetry Bridge";
    serviceConfig = {
      ExecStart = "/var/lib/tianxia/venv/timesfm/bin/python /var/lib/tianxia/bin/tx_gui_bridge.py";
      Environment = "TX_BASE_DIR=/var/lib/tianxia";
      EnvironmentFile = "/var/lib/tianxia/secrets/bridge.env";
      Restart = "always";
      RestartSec = "3s";
    };
    wantedBy = [ "multi-user.target" ];
  };

  systemd.services.tianxia-gumroad-reconcile = {
    enable = true;
    description = "Faery Fortress Legio Mercator — Gumroad poll-to-ledger reconciliation (REAL revenue)";
    serviceConfig = {
      Type = "oneshot";
      WorkingDirectory = "/var/lib/tianxia";
      ExecStart = "/var/lib/tianxia/venv/timesfm/bin/python /var/lib/tianxia/bin/tx_gumroad_reconcile.py";
    };
  };

  systemd.timers.tianxia-gumroad-reconcile = {
    enable = true;
    description = "5-min Gumroad revenue reconciliation";
    timerConfig = {
      OnCalendar = "*:0/5";
      Persistent = true;
      Unit = "tianxia-gumroad-reconcile.service";
    };
    wantedBy = [ "timers.target" ];
  };

  systemd.services.tianxia-stripe-reconcile = {
    enable = true;
    description = "Faery Fortress Lakshmi Rail — Stripe poll-to-ledger reconciliation (REAL revenue)";
    serviceConfig = {
      Type = "oneshot";
      WorkingDirectory = "/var/lib/tianxia";
      ExecStart = "/var/lib/tianxia/venv/timesfm/bin/python /var/lib/tianxia/bin/tx_stripe_reconcile.py";
    };
  };

  systemd.timers.tianxia-stripe-reconcile = {
    enable = true;
    description = "5-min Stripe revenue reconciliation";
    timerConfig = {
      OnCalendar = "*:0/5";
      Persistent = true;
      Unit = "tianxia-stripe-reconcile.service";
    };
    wantedBy = [ "timers.target" ];
  };

  systemd.services.tianxia-telegram-herald = {
    enable = true;
    description = "Faery Fortress RGO-ALPHA Herald — autonomous Telegram signal publisher";
    serviceConfig = {
      ExecStart = "/var/lib/tianxia/venv/timesfm/bin/python /var/lib/tianxia/bin/tx_telegram_herald.py --loop --interval 900";
      Environment = "TX_BASE_DIR=/var/lib/tianxia";
      EnvironmentFile = "/var/lib/tianxia/secrets/bridge.env";
      Restart = "always";
      RestartSec = "30s";
    };
    wantedBy = [ "multi-user.target" ];
  };

  systemd.services.tianxia-fortress-gate = {
    enable = true;
    description = "Faery Fortress Lady Naga Lifecycle Gate (72h/7d/14d enforcement)";
    serviceConfig = {
      Type = "oneshot";
      WorkingDirectory = "/var/lib/tianxia";
      ExecStart = "/var/lib/tianxia/venv/timesfm/bin/python /var/lib/tianxia/bin/tx_faery_fortress.py enforce";
    };
  };

  systemd.services.tianxia-campaign = {
    enable = true;
    description = "Hussar campaign cycle (kill-switch aware)";
    serviceConfig = {
      Type = "oneshot";
      WorkingDirectory = "/var/lib/tianxia";
      Environment = "TX_BASE_DIR=/var/lib/tianxia";
      ExecStartPre = "-/run/current-system/sw/bin/bash -c 'test ! -f /var/lib/tianxia/HUSSAR_PAUSED'";
      ExecStart = "/var/lib/tianxia/venv/timesfm/bin/python /var/lib/tianxia/bin/tx_hussar_campaign.py once";
    };
  };

  systemd.timers.tianxia-campaign = {
    enable = true;
    description = "Hussar campaign every 6 hours";
    timerConfig = {
      OnBootSec = "10min";
      OnUnitActiveSec = "6h";
      Persistent = true;
      Unit = "tianxia-campaign.service";
    };
    wantedBy = [ "timers.target" ];
  };

  systemd.services.tx-base-watch = {
    enable = true;
    description = "Base PairCreated radar (read-only)";
    serviceConfig = {
      Type = "oneshot";
      WorkingDirectory = "/var/lib/tianxia";
      Environment = "TX_BASE_DIR=/var/lib/tianxia";
      ExecStartPre = "-/run/current-system/sw/bin/bash -c 'test ! -f /var/lib/tianxia/HUSSAR_PAUSED'";
      ExecStart = "/var/lib/tianxia/venv/timesfm/bin/python /var/lib/tianxia/bin/tx_base_watch.py";
    };
  };

  systemd.timers.tx-base-watch = {
    enable = true;
    description = "Base radar every 10 minutes";
    timerConfig = {
      OnBootSec = "5min";
      OnUnitActiveSec = "10min";
      Persistent = true;
      Unit = "tx-base-watch.service";
    };
    wantedBy = [ "timers.target" ];
  };

  systemd.timers.tianxia-fortress-gate = {
    enable = true;
    description = "Hourly Faery Fortress gate enforcement";
    timerConfig = {
      OnCalendar = "hourly";
      Persistent = true;
      Unit = "tianxia-fortress-gate.service";
    };
    wantedBy = [ "timers.target" ];
  };

  networking.firewall = {
    enable = true;
    trustedInterfaces = [ "tailscale0" ];
    allowedTCPPorts = [ 22 8791 ];  # LAN: SSH only
    allowedUDPPorts = [ 51820 ];  # LAN: WireGuard only
  };

  users.groups.tianxia-hud = {};
  users.users.tianxia-hud = {
    isSystemUser = true;
    group = "tianxia-hud";
    extraGroups = [ "input" "video" ];
    home = "/var/lib/tianxia";
  };

  systemd.services.tianxia-etamanga = {
    description = "ETAMANGA solo chain node (:9944)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "/var/lib/tianxia/etamanga-build/polkadot-sdk/target/release/minimal-template-node --base-path /var/lib/tianxia/etamanga-chain --chain etamanga --validator --rpc-port 9944 --rpc-cors all --rpc-methods Safe --rpc-max-connections 100 --name latitude-etamanga --port 30333";
      Restart = "always";
      RestartSec = "10s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tianxia-trigger-watch = {
    enable = true;
    description = "Second-chain $3k/mo build-gate monitor (trailing-30d chain revenue)";
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "/var/lib/tianxia/venv/timesfm/bin/python /var/lib/tianxia/bin/tx_trigger_watch.py check --herald";
      WorkingDirectory = "/var/lib/tianxia";
      Environment = "TX_BASE_DIR=/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.timers.tianxia-trigger-watch = {
    enable = true;
    description = "Monthly second-chain build-gate check";
    timerConfig = {
      OnCalendar = "monthly";
      Persistent = true;
      Unit = "tianxia-trigger-watch.service";
    };
    wantedBy = [ "timers.target" ];
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
