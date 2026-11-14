{ config, pkgs, lib, ... }:

{
  # 1. Bimodal Silicon Lock: Intel UHD 630 for Display Scanout, NVIDIA MX130 for Headless CUDA sm_50
  hardware.graphics = {
    enable = true;
    extraPackages = with pkgs; [
      intel-media-driver
      intel-vaapi-driver
      libvdpau-va-gl
    ];
  };

  environment.sessionVariables = {
    WLR_DRM_DEVICES = "/dev/dri/by-path/pci-0000:00:02.0-card";
    GBM_BACKEND = "drm";
    __GLX_VENDOR_LIBRARY_NAME = "mesa";
  };

  # 2. Kernel KVM, VSOCK & Shared Memory Ring-Buffer Provisioning
  boot.kernelModules = [ "kvm-intel" "vhost-vsock" "tun" ];

  systemd.tmpfiles.rules = [
    "f /dev/shm/tx_menu_ast 0660 root wheel -"
    "d /run/tianxia 0755 root wheel -"
    "d /dev/shm/tx_vm_zygote 0750 root wheel -"
  ];

  # 3. Immutable Hyprland Layer Rules (Conforming to Hyprlang 0.56.2+)
  environment.etc."tianxia/hyprland-layer-rules.conf".text = ''
    # Autonomous Hyprland Layer Rules - TianxiaOS Sovereign Cockpit
    layerrule = blur 1, match:namespace ^(waybar|tianxia-ephemeral-hud|tianxia-dispatcher|tianxia-cockpit|notifications)$
    layerrule = ignorealpha 0.15, match:namespace ^(waybar|tianxia-ephemeral-hud|tianxia-dispatcher|tianxia-cockpit|notifications)$
    layerrule = blur_popups 1, match:namespace ^(waybar|tianxia-ephemeral-hud|tianxia-dispatcher|tianxia-cockpit|notifications)$
    layerrule = xray 1, match:namespace ^(tianxia-ephemeral-hud|tianxia-cockpit)$
  '';

  # 4. Zig Zero-Copy AST & SO_PEERCRED MicroVM Broker Daemon
  systemd.services.tx-menu-broker = {
    description = "TianxiaOS Polyglot Menu AST & CoW MicroVM Broker";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    environment = {
      CUDA_VISIBLE_DEVICES = "0"; # Dedicated Headless GeForce MX130
      TX_MANAS_PORT = "3109";
    };
    serviceConfig = {
      Type = "simple";
      ExecStart = "/var/lib/tianxia/bin/tx-menu-broker";
      Restart = "always";
      RestartSec = "100ms";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # 5. OCaml Cross-VM Wayland Capability Security Proxy
  systemd.services.tx-wayland-virtwl-proxy = {
    description = "TianxiaOS OCaml Cross-VM Wayland Capability Proxy";
    after = [ "tx-menu-broker.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "/var/lib/tianxia/bin/tx-virtwl-proxy";
      Restart = "always";
      RestartSec = "500ms";
      MemoryMax = "64M";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
}
