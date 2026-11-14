# ffp: TX-NETWORK-TUNING declarative nix
{ config, pkgs, lib, ... }:
{
  boot.kernelModules = [ "tcp_bbr" ];
  boot.kernel.sysctl = {
    "net.core.default_qdisc" = lib.mkDefault "fq";
    "net.ipv4.tcp_congestion_control" = lib.mkDefault "bbr";
    "net.ipv4.tcp_fastopen" = lib.mkDefault 3;
    "net.ipv4.ip_nonlocal_bind" = lib.mkDefault 1;
    "net.core.rmem_max" = lib.mkDefault 16777216;
    "net.core.wmem_max" = lib.mkDefault 16777216;
    "net.ipv4.tcp_rmem" = lib.mkDefault "4096 87380 16777216";
    "net.ipv4.tcp_wmem" = lib.mkDefault "4096 65536 16777216";
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
