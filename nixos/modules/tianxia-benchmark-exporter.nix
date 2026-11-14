# ffp: TX-TIANXIA-BENCHMARK-EXPORTER declarative nix
{ config, pkgs, lib, ... }:
{

  systemd.services.tianxia-benchmark-exporter = {
    description = "Tianxia Prometheus Benchmark Exporter";
    after = [ "network-online.target"  ];
    wants = [ "network-online.target"  ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      Restart = "always";
      RestartSec = "5s";
      ExecStart = "${pkgs.python3.withPackages (ps: [ ps.nats-py ps.requests ps.urllib3 ])}/bin/python3 /etc/tianxia/scripts/tianxia-benchmark-exporter.py";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
