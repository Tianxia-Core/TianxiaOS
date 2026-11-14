# ffp: TX-TIANXIA-MESH-WORKER declarative nix
{ config, pkgs, lib, ... }:

with lib;

let
  cfg = config.services.tianxia-mesh-worker;
in
{
  options.services.tianxia-mesh-worker = {
    enable = mkEnableOption "Tianxia Mesh Compute Worker Service";
    nodeName = mkOption {
      type = types.str;
      default = config.networking.hostName;
      description = "Identifier for the node in the Tianxia mesh";
    };
    coordinatorUrl = mkOption {
      type = types.str;
      default = "http://${TX_HUB_HOST:-127.0.0.1}:8081";
      description = "URL of the primary Tianxia mesh coordinator";
    };
  };

  config = mkIf cfg.enable {
    systemd.services.tianxia-mesh-worker = {
      description = "Tianxia Distributed Mesh Worker Daemon";
      after = [ "network-online.target" "tailscaled.service" ];
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      path = [ pkgs.curl pkgs.jq pkgs.coreutils pkgs.procps ];
      environment = {
        NODE_NAME = cfg.nodeName;
        COORDINATOR_URL = cfg.coordinatorUrl;
      };
      serviceConfig = {
        Type = "simple";
        User = "root";
        Restart = "always";
        RestartSec = "10s";
        ExecStart = pkgs.writeShellScript "tx-mesh-worker-run" ''
          set -euo pipefail
          echo "[tx-mesh-worker] Starting worker on node ${NODE_NAME}..."
          while true; do
            LOAD=$(cat /proc/loadavg | awk "{print \$1}")
            MEM_AVAIL=$(awk "/MemAvailable/ {print int(\$2/1024)}" /proc/meminfo)
            TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
            echo "[tx-mesh-worker] Heartbeat at ${TIMESTAMP} - load: ${LOAD}, mem_avail: ${MEM_AVAIL}MB"
            sleep 30
          done
        '';
      };
    };
  };
}
