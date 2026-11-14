# ffp: TX-TIANXIA-AUTOSCALER declarative nix
{ config, pkgs, lib, ... }:
{
  # Disable static single worker in favor of dynamic autoscaler
  systemd.services.tianxia-worker.enable = lib.mkForce false;

  systemd.services.tianxia-worker-autoscaler = {
    description = "Tianxia JetStream Autonomous Worker Elastic Autoscaler";
    after = [ "network.target" "nats.service" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      ExecStart = "/var/lib/tianxia/src/rust/txsuite/target/release/worker_autoscaler";
      Restart = "always";
      RestartSec = "3s";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
      KillMode = "mixed";
      TimeoutStopSec = "10s";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
