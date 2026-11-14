# ffp: TX-TIANXIA-MESH declarative nix
{ config, pkgs, lib, ... }:
{
  environment.systemPackages = with pkgs; [
    python3
    wireguard-tools
    nats-server
    tmux
    netcat-openbsd
    jq
    curl
    git
  ];

  # Disable legacy conflicting units on 9097/9102
  systemd.services.tianxia-alerts.enable = lib.mkForce false;
  systemd.services.tianxia-webhook.enable = lib.mkForce false;
  systemd.services.tianxia-exporter.enable = lib.mkForce false;
  systemd.services.tianxia-benchmark-exporter.enable = lib.mkForce false;

  # 1. Thermal Broadcaster Daemon
  systemd.services.tianxia-thermal-broadcaster = lib.mkForce {
    description = "Tianxia Thermal State Broadcaster";
    after = [ "network.target" "nats.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_thermal_broadcaster.py";
      Restart = "always";
      RestartSec = "3s";
      User = "root";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # 2. Local Compute Worker
  systemd.services.tianxia-compute-worker = lib.mkForce {
    description = "Tianxia Local Compute Worker (Latitude)";
    after = [ "network.target" "nats.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_compute_router.py --mode worker --node latitude-w1 --server 127.0.0.1 --batch-size 50";
      Restart = "always";
      RestartSec = "3s";
      User = "root";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # 3. Alertmanager to NATS Event Bridge (Port 9097)
  systemd.services.tianxia-alert-bridge = lib.mkForce {
    description = "Tianxia Alertmanager to NATS Event Bridge";
    after = [ "network.target" "nats.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_alert_bridge.py";
      Restart = "always";
      RestartSec = "3s";
      User = "root";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # 4. WorkQueue Prometheus Exporter (Port 9102)
  systemd.services.tianxia-workqueue-exporter = lib.mkForce {
    description = "Tianxia JetStream WorkQueue Prometheus Exporter";
    after = [ "network.target" "nats.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_workqueue_exporter.py";
      Restart = "always";
      RestartSec = "3s";
      User = "root";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # 5. Daily Git State Snapshot
  systemd.services.tianxia-nixos-snapshot = {
    description = "Tianxia Automated /etc/nixos Git State Snapshot";
    path = with pkgs; [ bash coreutils git nix ];
    serviceConfig = {
      Type = "oneshot";
      User = "root";
      WorkingDirectory = "/etc/nixos";
      ExecStart = pkgs.writeShellScript "tx-nixos-snapshot" ''
        set -eu
        cd /etc/nixos
        [ -d .git ] || exit 0
        git add -A
        if ! git diff-index --quiet HEAD -- 2>/dev/null; then
          TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%SZ")
          git commit -m "[AUTO-SNAPSHOT] Daily configuration state @ $TIMESTAMP"
        fi
      '';
    };
  };

  systemd.timers.tianxia-nixos-snapshot = {
    description = "Daily Timer for Tianxia /etc/nixos Git Snapshots";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "*-*-* 03:00:00 UTC";
      Persistent = true;
      Unit = "tianxia-nixos-snapshot.service";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
