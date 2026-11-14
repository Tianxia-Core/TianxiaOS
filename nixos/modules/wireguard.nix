# ffp: TX-WIREGUARD declarative nix
{ config, pkgs, lib, ... }:
{
  networking.firewall.allowedUDPPorts = [ 51820 ];

  
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
