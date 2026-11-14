# ffp: FFP-EDGE-FORWARDER-SVC declarative nix
# Tianxia Edge Ingress Forwarder: bridges Cloudflare Tunnel ingress ports
# (10.0.99.2:{8082,8081,8791,8790}) to tx_gui_bridge (:9199) across reboots.
{ config, lib, pkgs, ... }:
{
  systemd.services.tx-edge-forwarder = {
    description = "Tianxia Cloudflare Tunnel Edge Ingress Forwarder (:8082/:8081/:8791/:8790 -> :9199)";
    after = [ "network-online.target" "tianxia-gui-bridge.service" ];
    wants = [ "network-online.target" "tianxia-gui-bridge.service" ];
    wantedBy = [ "multi-user.target" ];
    path = [ pkgs.iproute2 pkgs.coreutils ];
    startLimitIntervalSec = 900;
    serviceConfig = {
      Type = "simple";
      Restart = "always";
      RestartSec = "3";
      StartLimitBurst = 10;
      WorkingDirectory = "/var/lib/tianxia";
      MemoryMax = "128M";
      TasksMax = 512;
      CPUQuota = "50%";
      AmbientCapabilities = [ "CAP_NET_ADMIN" ];
      CapabilityBoundingSet = [ "CAP_NET_ADMIN" ];
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_edge_forwarder.py";
    };
  };
}
