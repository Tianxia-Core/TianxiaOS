# ffp: TX-TIANXIA-TUNING declarative nix
{ pkgs, lib, ... }:

{
  boot.kernelModules = [ "thunderbolt" "thunderbolt-net" "zram" ];
  services.hardware.bolt.enable = lib.mkForce true;

  boot.kernel.sysctl = {
    "net.core.default_qdisc" = lib.mkForce "fq";
    "net.ipv4.tcp_congestion_control" = lib.mkForce "bbr";
    "net.core.rmem_max" = lib.mkForce 33554432;
    "net.core.wmem_max" = lib.mkForce 33554432;
    "net.ipv4.tcp_rmem" = lib.mkForce "4096 87380 33554432";
    "net.ipv4.tcp_wmem" = lib.mkForce "4096 65536 33554432";
    "net.core.netdev_max_backlog" = lib.mkForce 10000;
    "vm.swappiness" = lib.mkForce 100;
    "vm.watermark_boost_factor" = lib.mkForce 0;
    "vm.watermark_scale_factor" = lib.mkForce 125;
    "vm.page-cluster" = lib.mkForce 0;
  };

  networking.interfaces.thunderbolt0 = {
    useDHCP = false;
    ipv4.addresses = [ {
      address = "10.0.98.2";
      prefixLength = 30;
    } ];
  };

  environment.systemPackages = with pkgs; [
    bolt pciutils usbutils jq curl sqlite iperf3 ethtool
  ];
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
