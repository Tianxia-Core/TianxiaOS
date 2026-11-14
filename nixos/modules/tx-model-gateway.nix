# ffp: TX-MODEL-GATEWAY declarative nix
#
# The gateway script resolves its bind address at start-up (tx_mesh_addr.py).
# It must NEVER be pinned to a literal mesh IP: the old WireGuard subnet
# (10.0.99.0/24) was replaced by a Tailscale tailnet, and a pinned stale address
# still binds successfully because net.ipv4.ip_nonlocal_bind=1 is set -- the
# unit then looks healthy while nothing can reach it.
#
# This unit is separate from tianxia-secenhan.nix, which only supplies the
# hardening drop-in. The previous definition was dropped when tianxia-net-guard
# was rewritten, leaving a [Service] with no ExecStart; systemd refused it with
# "Service has no ExecStart=, ExecStop=, or SuccessAction=", which is the
# rebuild exit-4 failure this module fixes.
{ config, lib, pkgs, ... }:
{
  systemd.services.tx-model-gateway = {
    description = "Tianxia model gateway (mesh-facing, loopback-only backends)";
    wantedBy = [ "multi-user.target" ];
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_model_gateway.py";
      Restart = "on-failure";
      RestartSec = "5s";
      StartLimitBurst = 5;
      Environment = [
        "TX_GATEWAY_PORT=8790"
        "TX_GATEWAY_MESH=100.64.0.0/10"
      ];
      # Optional vault-managed bearer token for non-mesh clients. The leading
      # '-' means "ignore when absent"; an absent token keeps the gateway
      # fail-closed for everything outside loopback/tailnet.
      EnvironmentFile = "-/etc/tianxia/model-gateway.env";
      WorkingDirectory = "/var/lib/tianxia";
    };
    startLimitIntervalSec = 900;
  };
}
