# ffp: TX-TIANXIA-AUTONOMY declarative nix
{ config, pkgs, lib, ... }:
{
  # DASAVIDYAYANA-governed autonomous operations core.
  # Runs the self-healing cycle on an interval; remediation is explicitly
  # enabled here (the Bhairavi capability gate is satisfied by the flag and
  # the root-only unit). Kill-switch: touch /var/lib/tianxia/AUTONOMY_PAUSED.
  systemd.services.tianxia-autonomy = {
    description = "Tianxia Dasavidyayana Autonomy Core (self-healing cycle)";
    after = [ "network-online.target" "tianxia-uds-gateway.service" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];

    environment = {
      TX_BASE_DIR = "/var/lib/tianxia";
      TX_LOG_DIR = "/var/lib/tianxia/logs";
    };

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_autonomy_core.py loop --interval 300 --allow-remediate";
      Restart = "always";
      RestartSec = "10s";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
