# ffp: TX-TIANXIA-RGU-DISPATCHER declarative nix
{ config, pkgs, lib, ... }:
{
  systemd.services.tianxia-rgu-dispatcher = {
    description = "Tianxia Autonomous RGU Swarm Dispatcher";
    after = [ "network-online.target"  ];
    wants = [ "network-online.target"  ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      Restart = "always";
      RestartSec = "5s";
      ExecStart = "${pkgs.python3.withPackages (ps: [ ps.nats-py ps.requests ps.urllib3 ])}/bin/python3 /etc/tianxia/scripts/rgu-swarm-dispatcher.py";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
