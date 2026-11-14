# ffp: TX-TIANXIA-ORCHESTRATOR declarative nix
{ config, pkgs, lib, ... }:
let
  vaultDir = "/var/lib/tianxia";
in
{
  imports = [ ./forgejo.nix ];

  services.nats.enable = lib.mkForce false;

  systemd.targets.tianxia-core = {
    description = "Tianxia Unbound OS Core Subsystem Target";
    after = [ "network-online.target"  ];
    wants = [ "network-online.target"  ];
    wantedBy = [ "multi-user.target" ];
  };

  # 1. Unconfined NATS JetStream Engine (:4222, :6222, :8222)
  systemd.services.nats = {
    description = "Tianxia NATS JetStream Engine";
    after = [ "network.target" ];
    bindsTo = [ "tianxia-core.target" ];
    wantedBy = [ "tianxia-core.target" ];
    path = with pkgs; [ nats-server coreutils procps ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.nats-server}/bin/nats-server -c ${vaultDir}/nats.conf";
      Restart = "always";
      RestartSec = "2s";
      User = "root";
      LimitNOFILE = 1048576;
    };
  };

  # 2. Forgejo Source Control (:3000)
  systemd.services.forgejo = {
    after = [  "nats.service" ];
    wants = [ "nats.service" ];
    bindsTo = [ "tianxia-core.target" ];
    wantedBy = [ "tianxia-core.target" ];
  };

  # 3. Telemetry Collector Agent
  systemd.services.tianxia-telemetry = {
    description = "Tianxia Fractal Lattice Real-Time Telemetry Collector";
    after = [ "nats.service"  ];
    bindsTo = [ "tianxia-core.target" ];
    wantedBy = [ "tianxia-core.target" ];
    path = with pkgs; [ python3 coreutils curl ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u ${vaultDir}/bin/tx_telemetry_agent.py";
      Restart = "always";
      RestartSec = "2s";
      User = "root";
    };
  };

  # 4. Autonomous Unikernel Dispatch Worker
  systemd.services.tianxia-unikernel-worker = {
    description = "Tianxia Unikernel Dispatch & Sandbox Execution Worker";
    after = [ "nats.service"  ];
    bindsTo = [ "tianxia-core.target" ];
    wantedBy = [ "tianxia-core.target" ];
    path = with pkgs; [ python3 coreutils procps ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u ${vaultDir}/bin/tx_unikernel_worker.py";
      Restart = "always";
      RestartSec = "2s";
      User = "root";
      LimitNOFILE = 1048576;
    };
  };

  # 5. Prometheus Sovereign Mesh Latency Exporter (:9100)
  systemd.services.tianxia-prometheus-exporter = {
    description = "Tianxia Prometheus Sovereign Mesh Latency Exporter";
    after = [ "nats.service"  ];
    bindsTo = [ "tianxia-core.target" ];
    wantedBy = [ "tianxia-core.target" ];
    path = with pkgs; [ python3 coreutils ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${(pkgs.python3.withPackages (ps: with ps; [ prometheus-client requests psutil urllib3 ]))}/bin/python3 /var/lib/tianxia/bin/tx_prometheus_exporter.py";
      Restart = "always";
      RestartSec = "2s";
      User = "root";
    };
  };

  # 6. Continuous Mesh Latency Probe Oneshot Service
  systemd.services.tianxia-mesh-probe = {
    description = "Tianxia Multi-Node Continuous IPC Mesh Prober";
    after = [ "nats.service"  ];
    requires = [ "nats.service" ];
    path = with pkgs; [ python3 coreutils ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${pkgs.python3}/bin/python3 -u ${vaultDir}/bin/tx_mesh_probe_runner.py";
      User = "root";
    };
  };

  # 7. Declarative Systemd Timer for Periodic Sampling (Every 15s)
  systemd.timers.tianxia-mesh-probe = {
    description = "Tianxia Multi-Node Continuous Mesh Probe Timer (45s, cadence>=runtime per KAI3-101)";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "5s";
      OnUnitActiveSec = "45s";
      AccuracySec = "5s";
    };
  };

  # 8. Persistent Local Mesh Echo Responder
  systemd.services.tianxia-echo-responder = {
    description = "Tianxia Persistent Local Mesh Echo Responder";
    after = [ "nats.service"  ];
    bindsTo = [ "tianxia-core.target" ];
    wantedBy = [ "tianxia-core.target" ];
    path = with pkgs; [ python3 coreutils ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u ${vaultDir}/bin/tx_mesh_bench.py --mode echo --node latitude --server 127.0.0.1";
      Restart = "always";
      RestartSec = "2s";
      User = "root";
    };
  };

  # 9. Alertmanager to NATS Bridge Daemon (:9095)
  systemd.services.tianxia-alert-nats-bridge = {
    description = "Tianxia Alertmanager to NATS JetStream Bridge";
    after = [ "nats.service"  ];
    requires = [ "nats.service" ];
    bindsTo = [ "tianxia-core.target" ];
    wantedBy = [ "tianxia-core.target" ];
    path = with pkgs; [ python3 coreutils ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u ${vaultDir}/bin/tx_alert_nats_bridge.py";
      Restart = "always";
      RestartSec = "2s";
      User = "root";
    };
  };

  # 10. Autonomous Mesh Failover Router Engine
  systemd.services.tianxia-mesh-failover = {
    description = "Tianxia Autonomous Mesh Failover Router";
    after = [ "nats.service"  ];
    requires = [ "nats.service" ];
    bindsTo = [ "tianxia-core.target" ];
    wantedBy = [ "tianxia-core.target" ];
    path = with pkgs; [ python3 coreutils ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u ${vaultDir}/bin/tx_mesh_failover.py";
      Restart = "always";
      RestartSec = "2s";
      User = "root";
    };
  };

  # 11. Declarative Alertmanager Server (:9093)
  services.prometheus.alertmanager = {
    enable = true;
    port = 9093;
    listenAddress = "0.0.0.0";
    configuration = {
      global = {
        resolve_timeout = "30s";
      };
      route = {
        receiver = "nats-bridge";
        group_by = [ "alertname" "node" ];
        group_wait = "2s";
        group_interval = "5s";
        repeat_interval = "15m";
        routes = [
          {
            receiver = "nats-bridge";
            matchers = [ "severity =~ \"critical|warning\"" ];
            continue = false;
          }
        ];
      };
      receivers = [
        {
          name = "nats-bridge";
          webhook_configs = [
            {
              url = "http://127.0.0.1:9095/alert";
              send_resolved = true;
              max_alerts = 10;
            }
          ];
        }
      ];
    };
  };

  # 12. Prometheus Engine (:9090) with Latency & Reachability Alerting Rules
  services.prometheus = {
    enable = true;
    port = 9090;
    listenAddress = "0.0.0.0";
    alertmanagers = [
      {
        static_configs = [
          { targets = [ "127.0.0.1:9093" ]; }
        ];
      }
    ];
    scrapeConfigs = [
        {
          job_name = "tianxia-dasavidyayana";
          scrape_interval = "2s";
          static_configs = [
            {
              targets = [ "127.0.0.1:9198" ];
              labels = {
                subsystem = "dasavidyayana-14core";
                node = "latitude-tianxia";
              };
            }
          ];
        }
      {
        job_name = "tianxia-mesh-latency";
        scrape_interval = "5s";
        static_configs = [
          { targets = [ "127.0.0.1:9100" ]; }
        ];
      }
    ];
    rules = [
      ''
        groups:
          - name: tianxia_mesh_alerts
            rules:
              - alert: TianxiaMeshNodeOffline
                expr: tianxia_mesh_reachable == 0
                for: 15s
                labels:
                  severity: critical
                annotations:
                  summary: "Tianxia Mesh Node {{ $labels.node }} is OFFLINE"
                  description: "Node {{ $labels.node }} failed NATS IPC ping responses for >15s over WireGuard."

              - alert: TianxiaMeshHighLatencyP99
                expr: tianxia_mesh_latency_microseconds{quantile="0.99"} > 5000
                for: 30s
                labels:
                  severity: warning
                annotations:
                  summary: "Tianxia Mesh Node {{ $labels.node }} P99 latency degraded"
                  description: "Node {{ $labels.node }} P99 RTT latency is {{ $value }}µs (>5.0ms) for >30s."

              - alert: TianxiaMeshCriticalLatencyP50
                expr: tianxia_mesh_latency_microseconds{quantile="0.5"} > 10000
                for: 15s
                labels:
                  severity: critical
                annotations:
                  summary: "Tianxia Mesh Node {{ $labels.node }} Median Latency CRITICAL"
                  description: "Node {{ $labels.node }} median RTT latency is {{ $value }}µs (>10.0ms)."
      ''
    ];
  };

  # 13. Native Grafana Visualization Engine (:3001)
      services.grafana = {
    enable = true;
    settings = {
      server = {
        http_addr = "0.0.0.0";
        http_port = 3001;
        domain = "latitude-tianxia.tail7a45a7.ts.net";
        root_url = "http://latitude-tianxia.tail7a45a7.ts.net:3001/";
        serve_from_sub_path = false;
      };
      security = {
        admin_user = "admin";
        admin_password = "$__file{/var/lib/tianxia/secrets/grafana_admin.password}";
        secret_key = "$__file{/var/lib/tianxia/secrets/grafana_secret.key}";
        allow_embedding = true;
      };
      "auth.anonymous" = {
        enabled = true;
        org_name = "Main Org.";
        org_role = "Viewer";
      };
    };
  };

}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
