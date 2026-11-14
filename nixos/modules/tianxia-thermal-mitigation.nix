# ffp: TX-TIANXIA-THERMAL-MITIGATION declarative nix
{ config, pkgs, lib, ... }:
{
  systemd.services.tianxia-thermal-mitigation = {
    description = "Tianxia P0 Thermal Alert Automated Mitigation Controller";
    after = [ "network-online.target"  "nats.service" ];
    wants = [ "network-online.target"  "nats.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      Restart = "always";
      RestartSec = "3s";
      LimitNOFILE = 65536;
      ExecStart = "${pkgs.python3.withPackages (ps: [ ps.nats-py ps.requests ])}/bin/python3 /etc/tianxia/scripts/tianxia-thermal-mitigation-daemon.py";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
