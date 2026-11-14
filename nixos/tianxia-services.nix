{ config, pkgs, ... }:

let
  tianxiaUnits = pkgs.runCommand "tianxia-systemd-units" {} ''
    mkdir -p $out/lib/systemd/system
    cp -v ${./units}/*.service $out/lib/systemd/system/
  '';
in
{
  # Runtime state and socket directories
  systemd.tmpfiles.rules = [
    "d /run/tianxia 0755 root root -"
    "d /run/tx 0755 root root -"
    "d /var/lib/tianxia 0755 root root -"
    "d /var/lib/tianxia/bin 0755 root root -"
    "d /var/lib/tianxia/murua/bin 0755 root root -"
  ];

  # Ingest unit files into system-units derivation via systemd.packages
  systemd.packages = [ tianxiaUnits ];

  # Declaratively link into multi-user.target for boot autostart
  systemd.targets.multi-user.wants = [
    "tx-srm-apex.service"
    "tx-crownforge-daemon.service"
    "tx-murua.service"
    "tx-tetraledger-aurum.service"
    "tx-biomimetic-orchestrator.service"
    "tx-kenning-daemon.service"
    "tx-oracular-arsi.service"
    "tx-rasoom-mesh.service"
    "tx-tremor-pheromone.service"
    "tx-hussar-mesh.service"
  ];
}
