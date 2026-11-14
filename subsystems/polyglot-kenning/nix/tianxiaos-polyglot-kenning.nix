# ffp: FFP-NIX-002 polyglot-kenning-module nix
# TianxiaOS Core 11 (Nimbus-Flake) - NixOS Systemd Service Module

{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.tianxiaos-polyglot-kenning;
in {
  options.services.tianxiaos-polyglot-kenning = {
    enable = mkEnableOption "TianxiaOS Polyglot Kenning Suite";
    package = mkOption {
      type = types.package;
      description = "The package to use for TianxiaOS Polyglot Kenning.";
    };
  };

  config = mkIf cfg.enable {
    systemd.services.tx-kenning-daemon = {
      description = "TianxiaOS Artificial Kenning Daemon";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];
      serviceConfig = {
        ExecStart = "${cfg.package}/bin/tx_kenning_daemon";
        Restart = "always";
        RestartSec = "5s";
        MemoryMax = "256M";
        TasksMax = 128;
      };
    };
  };
}
