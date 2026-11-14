# ffp: RTL-SDR-SERVICES declarative nix
# Tianxia RF plane: RTL2838 IQ server, hourly wideband sweep, ADS-B Mode-S
# decode (dump1090-fa), feeding the TX-RTL-ML classifier.
#
# Dongle exclusivity: the RTL2838 is a single-radio device and exactly one
# process may hold it at a time.
#   * rtl-tcp  owns it by default and serves loopback IQ at :1234, which
#     tx_rf_sweep.sh consumes for the hourly wideband sweep.
#   * adsb-dump takes the device DIRECTLY (dump1090 is itself an RTLSDR app);
#     its ExecStartPre stops rtl-tcp and ExecStopPost restores it, so ADS-B
#     decode and the sweep never collide.
#
# Verified against dump1090-fa 11.1: the binary is named `dump1090` (not
# `dump1090-fa`), the Mode A/C switch is `--modeac` (not `--mode ac`), `--fix` is
# a boolean, and there is neither `--net-heard` nor `--iq`. Beast OUTPUT defaults
# to :30005, which is exactly what bin/tx_adsb_ingest.py consumes.
{ config, lib, pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    dump1090-fa
  ];

  systemd.services.rtl-tcp = {
    description = "rtl_tcp IQ server (canon node 67)";
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      ExecStart = "/run/current-system/sw/bin/rtl_tcp -a 127.0.0.1 -p 1234";
      Restart = "on-failure";
      # A missing dongle must not become a journal-flooding crash loop:
      # back off and wait for the operator to replug the RTL2838.
      RestartSec = "120";
      StartLimitBurst = 5;
    };
    startLimitIntervalSec = 900;
  };

  systemd.services.rf-sweep = {
    description = "Hourly wideband RF sweep (RTL2838)";
    serviceConfig = {
      Type = "oneshot";
      # The RTL2838 is hot-pluggable. When it is absent the sweep is
      # OPPORTUNISTIC, not broken: ExecCondition makes systemd record the
      # unit as skipped instead of failed, so a missing dongle no longer
      # turns every hourly timer tick into a red rebuild result.
      ExecCondition = "${pkgs.coreutils}/bin/test -e /dev/rtl_sdr";
      ExecStart = "/var/lib/tianxia/bin/tx_rf_sweep.sh";
      TimeoutStartSec = "15s";
    };
  };
  systemd.timers.rf-sweep = {
    description = "Hourly RF sweep";
    wantedBy = [ "timers.target" ];
    timerConfig = { OnCalendar = "hourly"; Persistent = true; };
  };

  # ---- ADS-B / Mode-S decode (dump1090-fa) --------------------------------
  systemd.services.adsb-dump = {
    # Retired: dump1090 took the device DIRECTLY and fought the SDR
    # client for it. The client now runs dump1090 in an EXCLUSIVE
    # window, and the ingest it feeds (tx_adsb_ingest.py, Beast on
    # :30005) is unchanged.
    enable = false;
    description = "dump1090-fa ADS-B decode (RTL2838) -> Beast binary at :30005";
    after = [ "rf-sweep.service" ];
    serviceConfig = {
      Type = "simple";
      Restart = "on-failure";
      RestartSec = "120";
      # Single-radio dongle: hand it from rtl-tcp to dump1090 and take it back.
      ExecStartPre = "-${pkgs.systemd}/bin/systemctl stop rtl-tcp.service";
      ExecStart = "${pkgs.dump1090-fa}/bin/dump1090 --net --net-bind-address 127.0.0.1 --modeac --device-index 0 --freq 109000000 --fix";
      ExecStopPost = "-${pkgs.systemd}/bin/systemctl start rtl-tcp.service";
      StartLimitBurst = 5;
    };
    startLimitIntervalSec = 900;
  };

  systemd.services.adsb-parse = {
    description = "ADS-B ingest -> TX-RTL-ML classifier (beast :30005)";
    after = [ "adsb-dump.service" ];
    # bindsTo propagates STOPS; wantedBy propagates STARTS. Both are required:
    # bindsTo alone left the classifier inactive after any dump1090 restart.
    bindsTo = [ "adsb-dump.service" ];
    wantedBy = [ "adsb-dump.service" ];
    serviceConfig = {
      Type = "simple";
      # always: the ingest exits 0 when the Beast socket closes, and
      # Restart=on-failure would leave the classifier dead after any dump1090
      # restart (observed: ran 55 min, 7 frames, then "Deactivated
      # successfully" and stayed down).
      Restart = "always";
      RestartSec = "60";
      # systemd units have no nix profile PATH: use an absolute interpreter.
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_adsb_ingest.py";
      StartLimitBurst = 5;
    };
    startLimitIntervalSec = 900;
  };
}
