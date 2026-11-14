# ffp: TX-TIANXIA-DSS-RATCHET declarative nix
{ config, pkgs, lib, ... }:
{
  # DSS-14 ratchet: hourly baseline-drift verification + changed-file gating.
  systemd.services.tianxia-dss-ratchet = {
    description = "DSS-14 baseline drift verify + changed-file gate";
    path = [ pkgs.bash pkgs.coreutils pkgs.gnugrep pkgs.gawk pkgs.gnused pkgs.procps pkgs.findutils ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${pkgs.bash}/bin/bash /var/lib/tianxia/bin/tx_dss_ratchet.sh";
      CPUAffinity = "10-11";
      Nice = 10;
    };
  };
  systemd.timers.tianxia-dss-ratchet = {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "hourly";
      Persistent = true;
      RandomizedDelaySec = 120;
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
