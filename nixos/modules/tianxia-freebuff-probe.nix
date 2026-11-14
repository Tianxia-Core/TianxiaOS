# ffp: TX-FREEBUFF-PROBE-MODULE declarative nix
{ config, lib, ... }:
{
  systemd.services.tianxia-freebuff-probe = {
    description = "Tianxia freebuff ws recovery probe";
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "/var/lib/tianxia/bin/tx_freebuff_probe.sh";
    };
  };
  systemd.timers.tianxia-freebuff-probe = {
    description = "Tianxia freebuff probe hourly";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "hourly";
      Persistent = true;
    };
  };
}
