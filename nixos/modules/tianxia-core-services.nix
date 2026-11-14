# ffp: TX-TIANXIA-CORE-SERVICES declarative nix
{ pkgs, ... }:

{
  systemd.services.tianxia-rpc-broker = {
    description = "Tianxia Nixyr Swarm RPC Broker";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_rpc_broker.py";
      Restart = "always";
      RestartSec = "2s";
      MemoryMax = "64M";
    };
  };

  systemd.services.tianxia-ireb-sync = {
    description = "Tianxia IREB Memory State-Lock Persistence";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_ireb_sync.py";
      Restart = "always";
      RestartSec = "5s";
      MemoryMax = "32M";
    };
  };

  systemd.services.tianxia-inference = {
    description = "Tianxia Autarchic Local Inference Router";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_inference_router.py";
      Restart = "always";
      RestartSec = "3s";
      MemoryMax = "128M";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
