# ffp: FFP-MURUA-NIXOS nixos-module declarative
{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.tianxiaos.murua;
in {
  options.services.tianxiaos.murua = {
    enable = mkEnableOption "TianxiaOS Murua Universal Tracer Suite";

    package = mkOption {
      type = types.package;
      description = "Murua tracer binary package";
    };

    nodeIp = mkOption {
      type = types.str;
      default = "10.77.0.3";
      description = "WireGuard mesh node IP address";
    };

    port = mkOption {
      type = types.port;
      default = 8089;
      description = "Telemetry and metrics port";
    };
  };

  config = mkIf cfg.enable {
    systemd.services.tx-murua = {
      description = "TianxiaOS Murua Sovereign Telemetry & Actuation Daemon";
      after = [ "network.target" "wireguard-wg0.service" ];
      wantedBy = [ "multi-user.target" ];

      serviceConfig = {
        ExecStart = "${cfg.package}/bin/tx_murua_tracer_daemon both";
        Restart = "always";
        RestartSec = "5s";
        MemoryMax = "512M";
        TasksMax = 64;
        ProtectSystem = "strict";
        ProtectHome = "read-only";
        ReadWritePaths = [ "/var/lib/tianxia/murua" "/run/tianxia" ];
        PrivateTmp = true;
        NoNewPrivileges = true;
      };

      environment = {
        MURUA_NODE_IP = cfg.nodeIp;
        RUST_BACKTRACE = "1";
      };
    };
  };
}
