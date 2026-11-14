# ffp: TX-TIANXIA-THERMAL declarative nix
{ config, lib, pkgs, ... }:

{
  # ────────────────────────────────────────────────────────────────────────────
  # THERMAL CONTROL for the workhorse.
  #
  # The Latitude is a LAPTOP doing server work, and the heat was unacceptable:
  # x86_pkg_temp sat at 92 C with a load average of 6+ on 8 threads. The cause
  # was in this tree, not in the hardware: the plane engine asks for
  # `performance` (it pins the model forest to cores 2-7 so inference planes
  # stay free), and thermald was ENABLED but had NO POLICY -- so nothing
  # capped the package power, the turbo ran unpinned (max_perf_pct=100), and
  # the only visible symptom was a hot chassis.
  #
  # The reconciliation: keep the governor (the plane engine needs the
  # responsiveness) but CAP the turbo, and give thermald a real policy with
  # trip points that throttle instead of merely reporting. tx_thermal_guard.py
  # then watches the package temperature and sheds load (and holds the SDR
  # client down) while the machine is hot.
  # ────────────────────────────────────────────────────────────────────────────
  # A hard turbo ceiling. NixOS has no `powerManagement.maxPerformancePercentage`
  # in this release (the option does not exist -- the build says so), so the cap
  # is the intel_pstate module parameter: it scales the whole frequency range,
  # so 65% keeps the fast bins for latency-sensitive work while cutting the
  # package power that makes the chassis hot. thermald's adaptive mode then
  # moves the cap dynamically, and tx_thermal_guard.py tightens it further.
  boot.kernelParams = [ "intel_pstate.max_perf_pct=65" ];

  # thermald's OWN policy file. This NixOS release exposes almost nothing
  # under services.thermald (no temperatureThresholds, no adaptive, no
  # indulgence -- the build says so), so the policy is written where thermald
  # actually reads it instead of fighting the option set. thermald was ENABLED
  # but had NO policy at all, which is why nothing capped the package power.
  environment.etc."thermald/thermald.conf" = { text = ''
    [pch-cannonlake]
    TSensorName = TSKN

    [cpu]
    # 80 C: start pulling the turbo down. 92 C is what the box actually sat
    # at, so the critical point is not academic.
    TripPoint0Temperature = 80000
    TripPoint0Type = cputemp
    TripPoint0Speed = 65
    TripPoint1Temperature = 92000
    TripPoint1Type = cputemp
    TripPoint1Speed = 35

    [gpu]
    TripPoint0Temperature = 78000
    TripPoint0Type = gputemp
    TripPoint0Speed = 40

    [pch-cannonlake]
    TripPoint0Temperature = 85000
    TripPoint0Type = pchcannonlakecputemp
    TripPoint0Speed = 50
  ''; };

  # The lid must NOT suspend the machine: the cockpit session (and the
  # workhorse services) have to keep running with the lid shut, on AC.
  # Written as a systemd drop-in rather than services.logind.extraConfig
  # (deprecated in this release -- the build says "use
  # services.logind.settings.Login instead") or a settings.Login option
  # (whose exact key set varies by release): a plain file that systemd
  # definitely reads, and that cannot fail to build.
  environment.etc."systemd/logind.conf.d/10-tianxia-lid.conf" = { text = ''
    [Login]
    HandleLidSwitch=ignore
    HandlePowerKey=ignore
  ''; };

  # The thermal guard: the adaptive, project-native half of the control loop.
  systemd.services.tx-thermal-guard = {
    description = "Tianxia thermal guard (cap the turbo, shed load, hold the SDR down when hot)";
    after = [ "network.target" "thermald.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_thermal_guard.py --serve";
      Restart = "on-failure";
      RestartSec = "15s";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
}
