# ffp: TX-TIANXIA-WATCHDOG declarative nix
{ config, pkgs, ... }:

{
  systemd.services.tianxia-watchdog = {
    description = "Tianxia Fractal Lattice Cluster Self-Healing Watchdog";
    after = [ "network.target" "tianxia-amdi-hub.service" "tianxia-net-bridge.service" ];
    wantedBy = [ "multi-user.target" ];

    path = with pkgs; [ python3 coreutils systemd iproute2 wireguard-tools ];

    serviceConfig = {
      Type = "simple";
      User = "root";
      Group = "root";
      WorkingDirectory = "/var/lib/tianxia";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_cluster_watchdog.py";
      Restart = "always";
      RestartSec = "3s";
      StandardOutput = "journal";
      StandardError = "journal";
      KillMode = "process";
      MemoryMax = "128M";
      LimitNOFILE = 65535;
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
