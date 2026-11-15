# ffp: FFP-NIXOS-KDE-BRAND declarative nix
# RASA-X-MACHINA · tianxiaOS Declarative KDE Plasma 6, Plymouth Boot Splash & Brand Identity Module
{ config, pkgs, lib, ... }:

let
  tianxiaPlymouthPkg = pkgs.runCommand "tianxiaos-plymouth-theme" {} ''
    mkdir -p $out/share/plymouth/themes/tianxiaos
    if [ -d /var/lib/tianxia/brand-theme/plymouth/tianxiaos ]; then
      cp -r /var/lib/tianxia/brand-theme/plymouth/tianxiaos/* $out/share/plymouth/themes/tianxiaos/
    fi
    substituteInPlace $out/share/plymouth/themes/tianxiaos/tianxiaos.plymouth \
      --replace-quiet "/etc/plymouth/themes/tianxiaos" "$out/share/plymouth/themes/tianxiaos" || true
  '';
in
{
  # 1. Sovereign OS Identity (/etc/os-release + KDE About This System)
  system.nixos.distroName = lib.mkDefault "tianxiaOS";
  system.nixos.label = lib.mkDefault "Crownforge";

  environment.etc."xdg/kcm-about-distrorc".text = ''
    [General]
    LogoPath=/var/lib/tianxia/brand-theme/icons/hicolor/512x512/apps/tianxiaos-logo.png
    Website=https://rasaxmachina.com
    Variant=v8.7.0 Crownforge · RASA-X-MACHINA Sovereign Substrate
    UseOSReleaseVersion=false
    Version=8.7.0 (NixOS 26.11 Wayland)
  '';

  # 2. Plymouth Boot Splash ("RASA-X-MACHINA · tianxiaOS")
  boot.plymouth = {
    enable = lib.mkDefault true;
    theme = lib.mkDefault "tianxiaos";
    themePackages = [ tianxiaPlymouthPkg ];
  };
  boot.kernelParams = [ "quiet" "splash" ];

  # 3. Canonical Brand Kit Typography (Zero Inter/Roboto/Arial)
  fonts.fontDir.enable = true;
  fonts.packages =
    (lib.optional (pkgs ? jetbrains-mono) pkgs.jetbrains-mono)
    ++ (lib.optional (pkgs ? space-grotesk) pkgs.space-grotesk)
    ++ (lib.optional (pkgs ? syne) pkgs.syne)
    ++ (lib.optional (pkgs ? plus-jakarta-sans) pkgs.plus-jakarta-sans);

  # 4. SDDM Wayland Dark Breeze + Ethereal Space Background
  services.displayManager.sddm.theme = lib.mkDefault "breeze";

  # 5. Idempotent Boot/Session Enforcement of RASA-X-MACHINA · tianxiaOS Desktop Suite
  systemd.services.tianxia-kde-brand-sync = {
    description = "Enforce RASA-X-MACHINA · tianxiaOS Ethereal Glass KDE Plasma 6 Brand Kit";
    wantedBy = [ "multi-user.target" ];
    after = [ "local-fs.target" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${pkgs.bash}/bin/bash /var/lib/tianxia/brand-theme/apply_kde_brand_suite.sh --boot-sync";
      MemoryMax = "256M";
      TasksMax = 64;
    };
  };
}
