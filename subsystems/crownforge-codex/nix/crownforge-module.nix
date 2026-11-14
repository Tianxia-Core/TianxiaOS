# ffp: FFP-NIX-002 crownforge-nixos-module declarative
{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.tianxiaCrownforge;
in {
  options.services.tianxiaCrownforge = {
    enable = mkEnableOption "TianxiaOS Crownforge Codex Daemon";
    package = mkOption {
      type = types.package;
      default = pkgs.callPackage ./default.nix {};
      description = "The Crownforge Codex binary package";
    };
  };

  config = mkIf cfg.enable {
    systemd.services.tx-crownforge-daemon = {
      description = "TianxiaOS Crownforge Codex Master Daemon";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];
      serviceConfig = {
        ExecStart = "${cfg.package}/bin/tx_crownforge_daemon";
        Restart = "always";
        RestartSec = "3s";
        MemoryMax = "512M";
        TasksMax = 128;
        CPUQuota = "100%";
        ProtectSystem = "full";
        RuntimeDirectory = "tianxia";
        StateDirectory = "tianxia";
      };
    };
  };
}
