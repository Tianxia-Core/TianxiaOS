# ffp: TX-TIANXIA-NET-BRIDGE declarative nix
{ config, pkgs, ... }:

{
  systemd.services.tianxia-net-bridge = {
    description = "Tianxia AMDI WireGuard Mesh Frame Router Bridge";
    after = [ "network.target"  "tianxia-amdi-hub.service" ];
    wantedBy = [ "multi-user.target" ];

    path = with pkgs; [ python3 coreutils ];

    serviceConfig = {
      Type = "simple";
      User = "root";
      Group = "root";
      WorkingDirectory = "/var/lib/tianxia";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_net_bridge.py";
      Restart = "always";
      RestartSec = "2s";
      StandardOutput = "journal";
      StandardError = "journal";
      KillMode = "process";
      MemoryMax = "256M";
      LimitNOFILE = 65535;
    };
  };

  # Allow bridge port on WireGuard mesh
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
