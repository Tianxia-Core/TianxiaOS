# ffp: TX-TIANXIA-ALERTS declarative nix
{ config, pkgs, lib, ... }:
{
  # 1. Alertmanager Service (Force 0.0.0.0 bind)
  services.prometheus.alertmanager = {
    enable = true;
    listenAddress = lib.mkForce "0.0.0.0";
    port = lib.mkDefault 9093;
    configuration = {
      global = {
        resolve_timeout = "30s";
      };
      route = {
        receiver = "nats-bridge";
        group_by = [ "alertname" "severity" ];
        group_wait = "3s";
        group_interval = "15s";
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
              url = "http://127.0.0.1:9095/alerts";
              send_resolved = true;
            }
          ];
        }
      ];
    };
  };

  # 2. Attach Alertmanager to Prometheus
  services.prometheus.alertmanagers = [
    {
      static_configs = [
        {
          targets = [ "127.0.0.1:9093" ];
        }
      ];
    }
  ];

  # 3. Declarative Alerting Rule Files (Isolated Derivation)
  services.prometheus.ruleFiles = [
    (pkgs.writeText "tianxia-mesh-workqueue-alerts.yml" ''
      groups:
        - name: tianxia_mesh_workqueue_alerts
          rules:
            - alert: TianxiaWorkQueueBacklogCritical
              expr: tianxia_workqueue_pending_tasks > 100
              for: 20s
              labels:
                severity: critical
                environment: sovereign-mesh
              annotations:
                summary: "JetStream WorkQueue backlog critical ({{ $value }} pending tasks)"
                description: "WorkQueue backlog has exceeded 100 pending tasks for >20s on {{ $labels.instance }}."

            - alert: TianxiaWorkerProcessingStalled
              expr: tianxia_workqueue_inflight_tasks > 5 and rate(tianxia_workqueue_tasks_completed_total[30s]) == 0
              for: 30s
              labels:
                severity: warning
                environment: sovereign-mesh
              annotations:
                summary: "Worker execution stalled on in-flight tasks"
                description: "Tasks are remaining un-ACKed in-flight with zero task completion rate."

            - alert: TianxiaWorkerLatencyElevated
              expr: tianxia_workqueue_worker_latency_ms{quantile="0.9"} > 50
              for: 20s
              labels:
                severity: warning
                environment: sovereign-mesh
              annotations:
                summary: "Worker {{ $labels.worker }} P90 latency elevated ({{ $value }}ms)"
                description: "Task processing execution latency on {{ $labels.worker }} exceeds 50ms."

            - alert: TianxiaMeshNodeDown
              expr: tianxia_mesh_reachable == 0
              for: 10s
              labels:
                severity: critical
                environment: sovereign-mesh
              annotations:
                summary: "Mesh Node '{{ $labels.node }}' is unreachable"
                description: "Node '{{ $labels.node }}' has failed heartbeat and reachability probes."
    '')
  ];

  # 4. Systemd Service for Alert Bridge
  systemd.services.tianxia-alert-bridge = {
    description = "Tianxia Alertmanager to NATS Event Bridge";
    after = [ "network.target" "nats.service" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_alert_bridge.py";
      Restart = "always";
      RestartSec = "3s";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
