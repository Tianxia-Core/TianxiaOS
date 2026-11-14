# ffp: TX-TIANXIA-TV-HYPRLAND declarative nix
{ config, lib, pkgs, ... }:

{
  # ────────────────────────────────────────────────────────────────────────────
  # 1. GRAPHICS — the nouveau dGPU drives NO connector on this host.
  #
  #    lspci on latitude-tianxia (CoffeeLake-H, 6th-10th gen):
  #      00:02.0  Intel  CoffeeLake-H GT2 UHD 630   -> i915   -> card1
  #      01:00.0  NVIDIA GM108M (GeForce MX130)     -> nouveau -> card0
  # ────────────────────────────────────────────────────────────────────────────
  boot.blacklistedKernelModules = [
    "nouveau"
    "nvidia"
    "nvidia_drm"
    "nvidia_modeset"
  ];

  boot.kernelParams = [
    "nouveau.modeset=0"
    "i915.enable_guc=3"
    "i915.enable_fbc=1"
  ];

  boot.kernelModules = [ "i915" ];

  hardware.graphics = {
    enable = true;
    enable32Bit = true;
    extraPackages = with pkgs; [
      intel-media-driver
      intel-vaapi-driver
      ocl-icd
      libvdpau-va-gl
    ];
  };

  # ────────────────────────────────────────────────────────────────────────────
  # 2. TV SESSION — Hyprland + greetd/tuigreet.
  # ────────────────────────────────────────────────────────────────────────────
  programs.hyprland = {
    enable = true;
    xwayland.enable = true;
    package = pkgs.hyprland;
  };

  services.greetd = {
    enable = true;
    settings = {
      initial_session = {
        command = "/var/lib/tianxia/bin/tx_hyprland_session.sh";
        user = "root";
      };
      default_session = {
        command = "/var/lib/tianxia/bin/tx_hyprland_session.sh";
        user = "root";
      };
    };
  };

  environment.sessionVariables = {
    NIXOS_OZONE_WL = "1";
    LIBVA_DRIVER_NAME = "iHD";
  };

  environment.systemPackages = with pkgs; [
    hyprland
    greetd
    tuigreet
    waybar
    wofi
    foot
    wlvncc
    wlr-randr

    # Tianxia Sovereign Astal (AGS v2) Desktop Shell Stack
    ags
    gjs
    gtk4
    libadwaita
    graphene
    pango
    gdk-pixbuf
    astal.astal4
    astal.battery
    astal.hyprland
    astal.apps
    astal.wireplumber
    astal.network
    astal.notifd
    astal.io
    dart-sass
    esbuild
  ];

  # ────────────────────────────────────────────────────────────────────────────
  # 3. The TV session launcher.
  # ────────────────────────────────────────────────────────────────────────────
  systemd.services.tianxia-cockpit = {
    path = with pkgs; [
      hyprland
      waybar
      wofi
      tuigreet
      wlr-randr
      ags
      gjs
      gtk4
      dart-sass
      esbuild
    ];
    serviceConfig.ExecStart = lib.mkForce [
      "${pkgs.bash}/bin/bash /var/lib/tianxia/bin/tx_tv_session_launch.sh"
    ];
  };

  # ────────────────────────────────────────────────────────────────────────────
  # 4. Tianxia Astal Desktop Shell Service
  # ────────────────────────────────────────────────────────────────────────────
  systemd.services.tianxia-shell = {
    description = "TianxiaOS Sovereign Astal Wayland Desktop Shell";
    after = [ "tianxia-cockpit.service" ];
    wants = [ "tianxia-cockpit.service" ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [
      bash
      coreutils
      procps
      gnugrep
      hyprland
      ags
      gjs
      gtk4
      dart-sass
      esbuild
      sqlite
      iputils
      python3
    ];
    environment = {
      HOME = "/var/lib/tianxia";
      XDG_RUNTIME_DIR = "/run/user/0";
      WAYLAND_DISPLAY = "wayland-1";
    };
    serviceConfig = {
      Type = "simple";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia/tianxia-shell";
      ExecStart = "/var/lib/tianxia/tianxia-shell/scripts/run.sh";
      Restart = "always";
      RestartSec = 2;
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # ────────────────────────────────────────────────────────────────────────────
  # 5. Hyprland Configuration Watch & Debounced Reloader
  # ────────────────────────────────────────────────────────────────────────────
  systemd.paths.tianxia-hyprland-watch = {
    description = "Watch Hyprland Configuration for Atomic Reload";
    after = [ "tianxia-shell.service" ];
    wantedBy = [ "multi-user.target" ];
    pathConfig = {
      PathModified = "/var/lib/tianxia/config/hyprland-tx.conf";
      Unit = "tianxia-hyprland-watch.service";
    };
  };

  systemd.services.tianxia-hyprland-watch = {
    description = "Tianxia Debounced Hyprland Configuration Reload";
    after = [ "tianxia-shell.service" ];
    path = with pkgs; [ bash python3 coreutils hyprland procps ];
    environment = {
      HOME = "/var/lib/tianxia";
      XDG_RUNTIME_DIR = "/run/user/0";
    };
    serviceConfig = {
      Type = "oneshot";
      User = "root";
      ExecStart = "/var/lib/tianxia/bin/hypr-debounced-reload.sh";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # ────────────────────────────────────────────────────────────────────────────
  # 6. Declarative Hyprlang AST Pre-Flight Sanity Assertion
  # ────────────────────────────────────────────────────────────────────────────
  system.activationScripts.hyprland-tx-check = {
    supportsDryActivation = true;
    text = ''
      if [ -f /var/lib/tianxia/bin/hypr-verify-reload ]; then
        ${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/hypr-verify-reload --check-only || {
          echo "FATAL: /var/lib/tianxia/config/hyprland-tx.conf failed AST syntax validation!" >&2
          exit 1
        }
      fi
    '';
  };

  # ────────────────────────────────────────────────────────────────────────────
  # 7. Dual-Display WayVNC Server for Mobile Mesh Nodes (eDP-1 on :5901)
  # ────────────────────────────────────────────────────────────────────────────
  systemd.services.tx-wayvnc-edp = {
    description = "Tianxia Sovereign WayVNC Server (eDP-1 on :5901)";
    after = [ "network.target" "greetd.service" ];
    wants = [ "greetd.service" ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [ wayvnc coreutils ];
    environment = {
      XDG_RUNTIME_DIR = "/run/user/0";
      WAYLAND_DISPLAY = "wayland-1";
    };
    serviceConfig = {
      Type = "simple";
      User = "root";
      ExecStart = "${pkgs.wayvnc}/bin/wayvnc -o eDP-1 -S /run/user/0/wayvncctl-edp1 0.0.0.0:5901";
      Restart = "always";
      RestartSec = 3;
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
}
