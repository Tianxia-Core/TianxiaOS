# /etc/nixos/tianxia-iso.nix
# Build command:
# nix-build '<nixpkgs/nixos>' -A config.system.build.isoImage -I nixos-config=/etc/nixos/tianxia-iso.nix -o /root/workspace/payloads/tianxiaos-iso
{ config, pkgs, lib, ... }:

{
  imports = [
    <nixpkgs/nixos/modules/installer/cd-dvd/installation-cd-graphical-calamares.nix>
    ./modules/tianxia-super-harness.nix
  ];

  networking.hostName = "tianxia-live";
  networking.wireless.enable = lib.mkForce false;
  networking.networkmanager.enable = true;

  isoImage.isoBaseName = lib.mkForce "tianxiaos-5.0-super-harness";
  isoImage.volumeID = "TIANXIAOS_50";
  isoImage.makeEfiBootable = true;
  isoImage.makeUsbBootable = true;

  isoImage.contents = [
    {
      source = ./.;
      target = "/tianxia-source-config";
    }
  ];

  hardware.enableAllFirmware = true;
  nixpkgs.config.allowUnfree = true;
}
