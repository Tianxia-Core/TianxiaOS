# ffp: TX-MODEL-BACKUP-SVC declarative nix
# Offsite model warehouse (TX-MODEL-BACKUP).
#
# The original queue item was "R2 model warehouse 761G (keys vaulted)". As
# written that was unachievable:
#   * the Cloudflare token in the vault returns HTTP 401, so no R2 remote can be
#     minted;
#   * the GCS remote fails with "billing account for the owning project is
#     disabled";
#   * the relay has 9 GB free against a 590 GB estate.
# R2 IS the warehouse: it already holds ~375 GiB (cold lattice + pilot) and the
# vault carries working S3 keys. An earlier conclusion that R2 was dead was based
# on the api_token in the LOCAL vault (a different credential); the hub vault has
# r2_endpoint / r2_access_key_id / r2_secret_access_key and they work.
#
# The S3 config is rendered from the vault by tx_rclone_conf.py at service start
# rather than committed, because it contains live secrets. Drive remains
# configured as a secondary offsite copy.
#
# Backups the in-service tier (the models the gateway actually serves, ~38 GiB)
# and by default EXCLUDES models/quarantine (106 GB of superseded .prev /
# -id-bad / BADNAME files). Pass --include-quarantine to sweep that too.
{ config, lib, pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    rclone
  ];

  systemd.services.tx-model-backup = {
    description = "Offsite model warehouse backup -> Cloudflare R2 (TX-MODEL-BACKUP)";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    # wantedBy = [ "multi-user.target" ]; # triggered by timer
    serviceConfig = {
      Type = "oneshot";
      WorkingDirectory = "/var/lib/tianxia";
      Environment = [
        "TX_BACKUP_REMOTE=tianxia-r2"
        "TX_BACKUP_DEST=cold/hot-tier"
        "TX_BACKUP_SRC=/var/lib/tianxia/models"
        "TX_BACKUP_MANIFEST=/var/lib/tianxia/log/model_backup_manifest.json"
        "TX_VAULT_DIR=/var/lib/tianxia/secrets"
        "TX_RCLONE_CONF_OUT=/var/lib/tianxia/etc/rclone-r2.conf"
        "TX_R2_BUCKET=tianxia-models"
        # rclone locates its config dir via glibc getent(1) for $HOME, and a
        # systemd unit has a minimal PATH with no getent. Without these it
        # silently falls back to "config in current directory" and every remote
        # then reads as unreachable. Name both the binary and the config file
        # absolutely so nothing depends on PATH or $HOME.
        "TX_RCLONE_BIN=${pkgs.rclone}/bin/rclone"
        "TX_RCLONE_CONFIG=/var/lib/tianxia/etc/rclone-r2.conf"
      ];
      # Hashing ~38 GiB of GGUF dominates runtime; allow generous headroom.
      # Render the R2 S3 config from the vault first; it holds live secrets so it
      # is generated 0600 at run time and never committed.
      ExecStartPre = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_rclone_conf.py";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_model_backup.py --run";
      TimeoutStartSec = 32400;   # 9h: in-service tier is ~38 GiB at ~4.8 MiB/s
      # The vault holds the R2 keys; the unit only ever reads it.
      ReadWritePaths = [ "/var/lib/tianxia/models" "/var/lib/tianxia/log" "/var/lib/tianxia/etc" ];
    };
  };

  systemd.timers.tx-model-backup = {
    description = "Daily offsite model warehouse backup";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "daily";
      Persistent = true;
      RandomizedDelaySec = 1800;
    };
  };
}
