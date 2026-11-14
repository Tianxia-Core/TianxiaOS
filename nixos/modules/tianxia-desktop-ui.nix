{ config, pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    waybar
    font-awesome
  ];
}
