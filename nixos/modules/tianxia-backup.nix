# ffp: TX-TIANXIA-BACKUP declarative nix
{ config, pkgs, ... }:

{
  systemd.services.tianxia-snapshot-backup = {
    description = "Tianxia Fractal Lattice Daily State Snapshot Backup";
    after = [ "local-fs.target" ];
    wantedBy = [ ]; # Triggered exclusively via systemd timer

    path = with pkgs; [
      bash
      gawk
      gnutar
      zstd
      coreutils
      findutils
      iproute2
    ];

    serviceConfig = {
      Type = "oneshot";
      User = "root";
      Group = "root";
      WorkingDirectory = "/var/lib/tianxia";
      ExecStart = "${pkgs.bash}/bin/bash /var/lib/tianxia/bin/tx_snapshot_backup.sh";
      StandardOutput = "journal";
      StandardError = "journal";
      # Low-priority I/O and CPU scheduling for background compression
      CPUSchedulingPolicy = "idle";
      IOSchedulingClass = "idle";
    };
  };

  systemd.timers.tianxia-snapshot-backup = {
    description = "Tianxia State Snapshot 24-Hour Timer";
    wantedBy = [ "timers.target" ];

    timerConfig = {
      OnCalendar = "*-*-* 04:00:00 UTC";
      Persistent = true;
      RandomizedDelaySec = "10m";
      Unit = "tianxia-snapshot-backup.service";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
