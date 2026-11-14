# ffp: NIMBUS2-DAS-WATCH declarative nix
{ config, lib, ... }:
{
  systemd.services.nimbus2-das-watch = {
    description = "Nimbus2-DAS burn-elimination watch (spend guard)";
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "/run/current-system/sw/bin/python3 /var/lib/tianxia/bin/nimbus2_das.py watch";
    };
  };
  systemd.timers.nimbus2-das-watch = {
    description = "Nimbus2-DAS watch every 15min";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnCalendar = "*:0/15"; Persistent = true; };
  };
}
