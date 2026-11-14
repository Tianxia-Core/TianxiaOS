# ffp: TX-TIANXIA-MESH-SURFACE declarative nix
{ config, lib, pkgs, ... }:

{
  # ────────────────────────────────────────────────────────────────────────────
  # The MESH SURFACE: the services that make the mesh one system.
  #
  #   8792  tx-workspace-bus   ONE workspace bus across the mesh: every node
  #                            publishes its workspaces and any node can switch a
  #                            workspace on another node.
  #   8793  tx-pointer-bridge   ONE cursor across the mesh: a pointer that
  #                            leaves the edge of one screen continues on the
  #                            other, so the cockpit and the workhorse are
  #                            driven by the same mouse.
  #   5900  wayvnc              the cockpit's screen feed (the TV mirrors it).
  #
  # All three are opened on tailscale0 ONLY: they are mesh services and must
  # not be exposed on the LAN.
  #
  # They are MANAGED SERVICES, not transient units: a nohup job started from an
  # ssh session is reaped when logind tears the session scope down, so the bus
  # kept "vanishing" until it was given a unit of its own.
  # ────────────────────────────────────────────────────────────────────────────
  networking.firewall.interfaces."tailscale0".allowedTCPPorts = [ 8792 8793 5900 ];

  systemd.services.tx-workspace-bus = {
    description = "Tianxia workspace bus (one bus across the mesh)";
    after = [ "network-online.target" "tianxia-cockpit.service" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_workspace_bus.py --serve";
      Restart = "on-failure";
      RestartSec = "10s";
      # The bus needs the compositor: it publishes the local Hyprland
      # workspaces and needs the instance signature to find it.
      # A LIST: repeating `Environment = ...` in one attrset is a duplicate
      # attribute definition and the file will not even parse.
      Environment = [
        "XDG_RUNTIME_DIR=/run/tx-cockpit-runtime"
        "WAYLAND_DISPLAY=wayland-1"
        "PATH=/run/current-system/sw/bin:/usr/bin:/bin"
      ];
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  systemd.services.tx-pointer-bridge = {
    description = "Tianxia pointer bridge (one cursor across the mesh)";
    after = [ "network-online.target" "tianxia-cockpit.service" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_pointer_bridge.py --serve";
      Restart = "on-failure";
      RestartSec = "10s";
      # A LIST: repeating `Environment = ...` in one attrset is a duplicate
      # attribute definition and the file will not even parse.
      Environment = [
        "XDG_RUNTIME_DIR=/run/tx-cockpit-runtime"
        "WAYLAND_DISPLAY=wayland-1"
        "PATH=/run/current-system/sw/bin:/usr/bin:/bin"
      ];
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
}
