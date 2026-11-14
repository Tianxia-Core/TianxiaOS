# ffp: TX-TIANXIA-AMDI-HUB declarative nix
{ config, pkgs, ... }:

{
  systemd.services.tianxia-amdi-hub = {
    description = "Tianxia KAI3 AMDI Zero-I/O UDS Gateway Daemon";
    after = [ "network.target" "local-fs.target" ];
    wantedBy = [ "multi-user.target" ];

    path = with pkgs; [ python3 coreutils ];

    serviceConfig = {
      Type = "simple";
      User = "root";
      Group = "root";
      WorkingDirectory = "/var/lib/tianxia/amdi_staging";
      ExecStartPre = pkgs.writeShellScript "amdi-hub-prestart" ''
        mkdir -p /var/lib/tianxia/amdi_staging/logs
        rm -f /var/lib/tianxia/amdi_staging/amdi_gateway.sock
      '';
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/amdi_staging/amdi_uds_hub.py";
      ExecStopPost = "${pkgs.coreutils}/bin/rm -f /var/lib/tianxia/amdi_staging/amdi_gateway.sock";

      Restart = "always";
      RestartSec = "2s";
      StandardOutput = "append:/var/lib/tianxia/amdi_staging/logs/amdi_service.log";
      StandardError = "append:/var/lib/tianxia/amdi_staging/logs/amdi_service.log";
      KillMode = "process";
      MemoryMax = "512M";
      LimitNOFILE = 65535;
    };
  };

  system.activationScripts.tianxiaAmdiStaging = ''
    mkdir -p /var/lib/tianxia/amdi_staging/logs
  '';
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
