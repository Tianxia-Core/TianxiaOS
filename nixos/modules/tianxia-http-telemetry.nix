# ffp: TX-TIANXIA-HTTP-TELEMETRY declarative nix
{ config, pkgs, lib, ... }:
{
  systemd.services.tianxia-http-telemetry = {
    enable = lib.mkForce false;
    wantedBy = lib.mkForce [ ];
    serviceConfig = {
      ExecStart = lib.mkForce "${pkgs.coreutils}/bin/true";
      Restart = lib.mkForce "no";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
