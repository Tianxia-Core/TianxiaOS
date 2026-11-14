# ffp: TX-TIANXIA-EXPORTER declarative nix
{ config, pkgs, lib, ... }:
{

  systemd.services.tianxia-workqueue-exporter = {
    description = "Tianxia JetStream WorkQueue Prometheus Exporter";
    after = [ "network.target" "nats.service" ];
    wantedBy = [ "multi-user.target" ];

    environment = {
      PYTHONPATH = "/var/lib/tianxia/bin";
    };

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_workqueue_exporter.py";
      Restart = "always";
      RestartSec = "3s";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # Configure Prometheus Scrape Target
  services.prometheus = {
    scrapeConfigs = [
      {
        job_name = "tianxia_workqueue";
        static_configs = [
          {
            targets = [ "127.0.0.1:9102" ];
            labels = {
              service = "tianxia-workqueue";
              environment = "sovereign-mesh";
            };
          }
        ];
        scrape_interval = "2s";
      }
    ];
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
