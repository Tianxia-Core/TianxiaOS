# ffp: TX-NETWORK declarative nix
{ config, pkgs, ... }:
{
  networking.firewall = {
    enable = true;
    trustedInterfaces = [ "tailscale0" ];
    allowedUDPPorts = [ 51820 ];
    allowPing = false;
  };

  

  # Tailscale: relay-capable overlay for hostile-network and cellular access.
  # the current path away. DERP relay fallback is the property the
  # hostile-network requirement actually needs.
  services.tailscale = {
    enable = true;
    openFirewall = true;
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
