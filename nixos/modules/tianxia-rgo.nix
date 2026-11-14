# ffp: TX-TIANXIA-RGO declarative nix
# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
{ config, pkgs, lib, ... }:

let
  baseDir = "/var/lib/tianxia";
  venvPython = "${baseDir}/venv/timesfm/bin/python";
  binDir = "${baseDir}/bin";

  mkEngineServiceWith = extraServiceConfig: name: script: args: {
    description = "Tianxia RGO engine: ${name}";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    environment = {
      TX_BASE_DIR = baseDir;
    };
    serviceConfig = {
      Type = "oneshot";
      User = "root";
      WorkingDirectory = baseDir;
      ExecStart = "${venvPython} ${binDir}/${script} ${args}";
      StandardOutput = "journal";
      StandardError = "journal";
      TimeoutStartSec = 600;
      Nice = 10;
      CPUAffinity = "10-11";
      Restart = "no";
    } // extraServiceConfig;
  };

  mkEngineService = mkEngineServiceWith {};

  mkEngineTimer = name: timerConfig: {
    description = "Tianxia RGO timer: ${name}";
    wantedBy = [ "timers.target" ];
    timerConfig = timerConfig // {
      Unit = "tianxia-${name}.service";
    };
  };
in
{
  # Signal feed: hourly ingestion of market signals.
  systemd.services.tianxia-signal-feed =
    mkEngineService "signal-feed" "tx_signal_feed.py" "--once";
  systemd.timers.tianxia-signal-feed = mkEngineTimer "signal-feed" {
    OnCalendar = "hourly";
    Persistent = true;
  };

  # ACAR: adaptive capital allocation, every 30 minutes.
  # Exit 2 (NO_TARGETS) means the batch discovery found no new contracts, a
  # benign no-op rather than a unit failure.
  systemd.services.tianxia-acar =
    mkEngineServiceWith { SuccessExitStatus = [ 2 ]; }
      "acar" "tx_acar.py" "--batch 5";
  systemd.timers.tianxia-acar = mkEngineTimer "acar" {
    OnBootSec = "5min";
    OnUnitActiveSec = "30min";
    Persistent = true;
  };

  # Keeper crank: profit-gated, safe to run every 5 minutes.
  systemd.services.tianxia-keeper-crank =
    mkEngineService "keeper-crank" "tx_keeper_crank.py" "--once --live";
  systemd.timers.tianxia-keeper-crank = mkEngineTimer "keeper-crank" {
    OnBootSec = "5min";
    OnUnitActiveSec = "5min";
    Persistent = true;
  };

  # Merkle watch: daily integrity sweep.
  systemd.services.tianxia-merkle-watch =
    mkEngineService "merkle-watch" "tx_merkle_watch.py" "--once";
  systemd.timers.tianxia-merkle-watch = mkEngineTimer "merkle-watch" {
    OnCalendar = "daily";
    Persistent = true;
  };

  # Sustained evidence: daily RGO report (report + metrics + ledger row).
  systemd.services.tianxia-rgo-report =
    mkEngineService "rgo-report" "tx_rgo_report.py" "--once";
  systemd.timers.tianxia-rgo-report = mkEngineTimer "rgo-report" {
    OnCalendar = "daily";
    Persistent = true;
  };

  # RGU lifecycle engine: hourly evaluation of the five registered RGUs from
  # real evidence (EARNINGS.json, rgu_revenue_events, engine logs). State
  # transitions are written back to rgo_registry.json and the ledger.
  systemd.services.tianxia-rgu-engine =
    mkEngineService "rgu-engine" "tx_rgu_engine.py" "--tick";
  systemd.timers.tianxia-rgu-engine = mkEngineTimer "rgu-engine" {
    OnCalendar = "hourly";
    Persistent = true;
  };

  # Flash-arb hunter: scans Base pairs/venues every 2 minutes; executes the
  # atomic arb only when the eth_call simulation succeeds AND net exceeds the
  # profit floor (sim-first, kill-switch aware, signer-gated via tx_evm_exec).
  systemd.services.tianxia-flash-scan = {
    description = "Tianxia RGO engine: flash-scan (continuous watch)";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    environment.TX_BASE_DIR = baseDir;
    serviceConfig = {
      Type = "simple";
      User = "root";
      WorkingDirectory = baseDir;
      ExecStart = "${venvPython} ${binDir}/tx_flash_scanner.py --watch --live --interval 10";
      StandardOutput = "journal";
      StandardError = "journal";
      Restart = "always";
      RestartSec = "5s";
      TimeoutStartSec = "infinity";
      Nice = 10;
      CPUAffinity = "10-11";
    };
  };
}
