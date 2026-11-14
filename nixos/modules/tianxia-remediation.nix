# ffp: TX-TIANXIA-REMEDIATION declarative nix
{ config, pkgs, lib, ... }:
{
  systemd.services.tianxia-auto-remediator = {
    description = "Tianxia Autonomous Self-Healing & Remediation Daemon";
    after = [ "network.target" "nats.service" "tianxia-alert-bridge.service" ];
    wantedBy = [ "multi-user.target" ];

    environment = {
      PYTHONPATH = "/var/lib/tianxia/bin";
    };

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_auto_remediator.py";
      Restart = "always";
      RestartSec = "3s";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
