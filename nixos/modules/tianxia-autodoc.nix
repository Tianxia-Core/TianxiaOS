# ffp: TX-TIANXIA-AUTODOC declarative nix
{ config, pkgs, lib, ... }:
{
  systemd.services.tianxia-autodoc-agent = {
    description = "Tianxia AutoDoc Markdown Generator & Forgejo Syncer";
    after = [ "network-online.target"  ];
    wants = [ "network-online.target"  ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ git openssh ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia-autodoc";
      Restart = "always";
      RestartSec = "5s";
      ExecStart = "${pkgs.python3.withPackages (ps: [ ps.nats-py ps.requests ps.urllib3 ])}/bin/python3 /etc/tianxia/scripts/nats-autodoc-agent.py";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
