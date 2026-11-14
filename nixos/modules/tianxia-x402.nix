# ffp: TX-TIANXIA-X402 declarative nix
{ config, pkgs, lib, ... }:
{
  systemd.services.tianxia-x402-gateway = {
    description = "Tianxia x402 Payment-Gated Inference Gateway (M2M revenue)";
    after = [ "network-online.target" "tianxia-inference.service" ];
    wants = [ "network-online.target" "tianxia-inference.service" ];
    wantedBy = [ "multi-user.target" ];
    environment = {
      TX_BASE_DIR = "/var/lib/tianxia";
      TX_X402_PORT = "9196";
      TX_X402_PRICE_EFM = "1000000000000000";
    };
    serviceConfig = {
      Type = "simple";
      User = "root";
      Restart = "always";
      RestartSec = "3s";
      CPUAffinity = "10-11";
      MemoryMax = "256M";
      ExecStart = "${pkgs.python3}/bin/python3 -u /var/lib/tianxia/bin/tx_x402_gateway.py --serve";
    };
  };
  # Mesh bridge: expose the loopback gateway to the WG mesh only.
  # (The gateway fails closed on any non-loopback bind by design.)
  systemd.services.tianxia-x402-bridge = {
    description = "Tianxia x402 tailnet bridge (:9196 -> 127.0.0.1:9196)";
    after = [  "tianxia-x402-gateway.service" ];
    wants = [ "tianxia-x402-gateway.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      ExecStart = "/var/lib/tianxia/bin/tx_mesh_bind.sh ${pkgs.socat}/bin/socat TCP-LISTEN:9196,bind=@MESH_BIND@,fork,reuseaddr TCP:127.0.0.1:9196";
      Restart = "always";
      RestartSec = "3s";
      User = "root";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
