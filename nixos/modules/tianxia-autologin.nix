{ config, pkgs, lib, ... }:
{
  # 1. Sovereign Desktop User
  users.users.tianxia = {
    isNormalUser = true;
    uid = 1000;
    description = "Tianxia Sovereign Operator";
    extraGroups = [ "wheel" "networkmanager" "video" "audio" "dialout" "render" ];
    initialPassword = "tianxia";
    home = "/home/tianxia";
  };

  # 2. Passwordless sudo for wheel
  security.sudo.wheelNeedsPassword = true;

  # 3. Plasma 6 & SDDM Wayland autologin targeting UID 1000
  services.xserver.enable = lib.mkForce true;
  services.desktopManager.plasma6.enable = lib.mkForce true;

  services.displayManager.autoLogin = {
    enable = true;
    user = "tianxia";
  };

  services.displayManager.defaultSession = "plasma";

  services.displayManager.sddm = {
    enable = true;
    wayland.enable = true;
  };

  # Suppress Baloo and broken services
  environment.etc."xdg/baloofilerc".text = ''
    [Basic Settings]
    Indexing-Enabled=false
  '';
  services.grafana.enable = lib.mkForce false;
  systemd.services."gitea-runner-latitude-tianxia-runner".enable = lib.mkForce false;

  # GPU Driver Guard (disable faulting nouveau on GM108 / MX130)
  boot.blacklistedKernelModules = [ "nouveau" ];
  boot.kernelParams = [ "i915.enable_psr=0" "nouveau.modeset=0" ];
}
