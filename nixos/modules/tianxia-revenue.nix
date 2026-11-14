# ffp: TX-TIANXIA-REVENUE declarative nix
{ config, pkgs, lib, ... }:
{
  # Autonomous revenue watcher: x402 receipts + Base EFM + Solana ETMA
  # settlements -> idempotent rgu_revenue_events booking + EARNINGS.json
  # merge + PROOF_OF_EARNING.md. Read-only chain access via stdlib urllib;
  # no curl, no keys. Flywheel hook is dry-mode only (never --live).
  systemd.services.tianxia-revenue-watcher = {
    description = "Tianxia autonomous revenue watcher (x402/EFM/ETMA observer)";
    path = [ pkgs.coreutils pkgs.python3 ];
    serviceConfig = {
      Type = "oneshot";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_revenue_watcher.py --once";
      Nice = 10;
      CPUAffinity = "10-11";
      TimeoutStartSec = "10min";
    };
  };
  systemd.timers.tianxia-revenue-watcher = {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "3min";
      OnUnitActiveSec = "5min";
      Persistent = true;
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
