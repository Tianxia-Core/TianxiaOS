# ffp: TX-TIANXIA-WORKER declarative nix
{ config, pkgs, lib, ... }:
{
  systemd.services.tianxia-worker = {
    description = "Tianxia JetStream Autonomous WorkQueue Consumer Daemon";
    after = [ "network.target" "nats.service" ];
    wantedBy = [ "multi-user.target" ];

    environment = {
      PYTHONPATH = "/var/lib/tianxia/bin";
    };

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_workqueue_engine.py --mode worker --worker-id latitude --server 127.0.0.1";
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
