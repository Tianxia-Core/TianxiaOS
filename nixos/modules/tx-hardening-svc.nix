# ffp: TX-HARDENING-SVC declarative nix
# Host hardening: bounded logs + declared SSH key-only auth.
#
# Found while remediating storage pressure:
#   * no tianxia log was ever rotated, so the three large logs (762 MB flash
#     scanner, 374 MB mini_eval, 168 MB rpc_xs) could only grow;
#   * journald had no size cap and had reached 455.7 MB;
#   * sshd auth posture was implicit rather than declared.
#
# Notes on this nixpkgs, learned the slow way:
#   * the logrotate option is services.logrotate, NOT environment.logRotate;
#   * services.journald exposes no sizing options at all (SystemMaxUse,
#     SystemKeepFree, MaxRetentionSec are all absent), so every knob goes
#     through extraConfig, which lands verbatim in journald.conf;
#   * services.logrotate.settings accepted a tianxia block that evaluated
#     correctly but was never rendered into the generated logrotate.conf, and
#     that module emits no `include /etc/logrotate.d`. So rotation for these
#     logs is driven by a self-contained unit instead. It is deliberately named
#     tianxia-logrotate so it cannot collide with the distribution's own
#     logrotate.service/ExecStart.
{ config, lib, pkgs, ... }:
{
  # ---- bounded journald ------------------------------------------------
  services.journald.extraConfig = ''
    SystemMaxUse=512M
    SystemKeepFree=2G
    MaxRetentionSec=14day
  '';

  # ---- rotate the tianxia file logs ------------------------------------
  environment.etc."tianxia-logrotate.conf".text = ''
    /var/lib/tianxia/logs/*.log
    /var/lib/tianxia/etamanga-build/*.log
    {
      daily
      rotate 14
      maxsize 100M
      compress
      delaycompress
      missingok
      notifempty
      create 0640 root root
      su root root
    }
  '';

  systemd.services.tianxia-logrotate = {
    description = "Rotate and compress the tianxia logs (TX-HARDENING)";
    path = with pkgs; [ coreutils gnugrep findutils gzip ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${pkgs.logrotate}/bin/logrotate /etc/tianxia-logrotate.conf";
    };
  };

  systemd.timers.tianxia-logrotate = {
    description = "Daily rotation of the tianxia logs";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "daily";
      Persistent = true;
      RandomizedDelaySec = 1200;
    };
  };

  # ---- SSH: declare key-only auth --------------------------------------
  # mkDefault throughout: this host already sets MaxAuthTries=4,
  # PermitRootLogin=prohibit-password and PasswordAuthentication=no, and a
  # hardening module must not silently override a deliberate host decision.
  # This states the invariant where the host would otherwise be silent.
  services.openssh.settings = {
    PasswordAuthentication = lib.mkDefault false;
    KbdInteractiveAuthentication = lib.mkDefault false;
    PermitRootLogin = lib.mkDefault "prohibit-password";
    MaxAuthTries = lib.mkDefault 3;
    LoginGraceTime = lib.mkDefault 30;
  };
}