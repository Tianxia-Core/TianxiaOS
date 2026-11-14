# ffp: TX-TIANXIA-HOSTS declarative nix
{ config, pkgs, ... }:
{
  networking.extraHosts = ''
    10.0.99.254 hud.rasaxmachina.com git.rasaxmachina.com
  '';
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
