# ffp: FFP-NIX-002 enterprise-nixos-module declarative
{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.tianxiaosEnterprise;
in {
  options.services.tianxiaosEnterprise = {
    enable = mkEnableOption "TianxiaOS & Ndimmôrwyn Enterprise Production-Grade Suite";

    package = mkOption {
      type = types.package;
      default = pkgs.callPackage ./default.nix {};
      description = "The tianxiaos_ndimmorwyn_enterprise binary package.";
    };

    wireguardInterface = mkOption {
      type = types.str;
      default = "wg0";
      description = "The sovereign mesh WireGuard interface.";
    };
  };

  config = mkIf cfg.enable {
    # Systemd Services with Cgroup v2 Containment & SO_PEERCRED Hardening
    systemd.services.tx-srm-apex = {
      description = "TianxiaOS SRM Apex Lamb-Wave & MagPrint Biometric Gate";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "simple";
        ExecStart = "${cfg.package}/bin/tx_srm_apex_daemon";
        Restart = "always";
        RestartSec = "100ms";
        MemoryMax = "64M";
        TasksMax = 16;
        ProtectSystem = "strict";
        ProtectHome = "read-only";
        NoNewPrivileges = true;
      };
    };

    systemd.services.tx-tetraledger-aurum = {
      description = "TianxiaOS TetraLedger OpenReserve & Ubyx Clearing Bus";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "simple";
        ExecStart = "${cfg.package}/bin/tx_tetraledger_aurum";
        Restart = "always";
        RestartSec = "200ms";
        MemoryMax = "128M";
        TasksMax = 32;
        ProtectSystem = "strict";
        NoNewPrivileges = true;
      };
    };

    systemd.services.tx-biomimetic-orchestrator = {
      description = "TianxiaOS Biomimetic Filippov Router & TreasuryEscrow Waterfall";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "simple";
        ExecStart = "${pkgs.python3}/bin/python3 ${cfg.package}/python/tx_biomimetic_orchestrator.py";
        Restart = "always";
        RestartSec = "500ms";
        MemoryMax = "128M";
      };
    };
  };
}
