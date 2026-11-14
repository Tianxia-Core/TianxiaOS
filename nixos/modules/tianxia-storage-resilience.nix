# ffp: TX-TIANXIA-STORAGE-RESILIENCE declarative nix
{ config, pkgs, lib, ... }:
{
  environment.systemPackages = with pkgs; [ age sops rsync zstd ];
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
