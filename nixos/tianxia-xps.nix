# ffp: TX-TIANXIA-XPS declarative nix
{ config, pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    python3
    curl
    jq
  ];

  systemd.services.tianxia-xps13-sync = {
    description = "Tianxia Tier-0 XPS 13 Mesh Forwarder & Heartbeat Daemon";
    after = [ "network.target"  ];
    wantedBy = [ "multi-user.target" ];
    environment = {
      LATITUDE_IP = "latitude-tianxia.tail7a45a7.ts.net";
    };
    path = with pkgs; [ python3 coreutils ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/services/tx_xps13_sync_daemon.py";
      Restart = "always";
      RestartSec = "3s";
      LimitNOFILE = 65536;
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
