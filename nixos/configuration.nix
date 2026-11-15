# ffp: TX-CONFIGURATION declarative nix
{ config, pkgs, lib, ... }:

{
  imports = [ ./modules/tianxia-autologin.nix ./modules/tianxia-super-harness.nix ./modules/tianxia-desktop-ui.nix ./modules/tianxia-kde-brand.nix ./modules/tianxia-hardware-input-backlight.nix
    ./embed-service.nix
    ./tianxia-services.nix
    ./ncm-service.nix
    # nix-ld: unpatched pip wheels (torch) need libstdc++.so.6, which is not in
    # the default linker path on NixOS.
    # (see programs.nix-ld below)
    ./qdrant.nix
    ./modules/tianxia-pq-rosenpass.nix
    ./modules/tianxia-net-guard.nix
    ./modules/tianxia-cgroups-slices.nix
    ./modules/tianxia-secrets-ramfs.nix
    ./modules/tx-model-gateway.nix
      ./modules/tianxia-sdr-client.nix
    ./tianxia-gui.nix
    # ./modules/tianxia-tv-hyprland.nix
    ./modules/tianxia-ephemeral-menu.nix
    ./tianxia-substrate.nix
    ./tianxia-kernel-armor.nix
    ./substrate-hardening.nix
    ./model-forest-services.nix
    ./network.nix
    ./modules/tianxia-mesh.nix
    ./modules/tianxia-compute.nix
    ./modules/tianxia-autoscaler.nix
    ./modules/tianxia-remediation.nix
    ./modules/tianxia-alerts.nix
    ./modules/tianxia-grafana-dashboards.nix
    ./modules/tianxia-exporter.nix
    ./modules/tianxia-freebuff-probe.nix
    ./modules/tianxia-secenhan.nix
    ./modules/rtl-sdr-services.nix
    ./modules/mcp-reserve-svc.nix
    ./modules/nimbus2-das-watch.nix
    ./modules/tianxia-worker.nix
    ./modules/tianxia-consensus.nix
    ./modules/wireguard.nix
    ./modules/forgejo.nix
    ./hardware-configuration.nix
      ./wireguard-mesh.nix
      ./rtl-sdr-udev.nix
    ./hardware-peripherals.nix
    ./modules/network-tuning.nix
    ./modules/tianxia-amdi-hub.nix
    ./modules/tianxia-autodoc.nix
    ./modules/tianxia-backup.nix
    ./modules/tianxia-benchmark-exporter.nix
    ./modules/tianxia-cli.nix
    ./modules/tianxia-core-services.nix
    ./modules/tx-cockpit-svc.nix
    ./modules/tx-edge-forwarder.nix
    ./modules/tx-model-backup-svc.nix
    ./modules/tx-hardening-svc.nix
    ./modules/tianxia-x402.nix
    ./modules/tianxia-defense-matrix.nix
    ./modules/tianxia-edge-defense.nix
    ./modules/tianxia-forgejo-runner.nix
    ./modules/tianxia-hosts.nix
    ./modules/tianxia-http-telemetry.nix
    
    ./modules/tianxia-net-bridge.nix
    ./modules/tianxia-rgo-allocator.nix
    ./modules/tianxia-rgu-dispatcher.nix
    ./modules/tianxia-spoke.nix
    ./modules/tianxia-storage-resilience.nix
    
    ./modules/tianxia-thermal-mitigation.nix
    ./modules/tianxia-watchdog.nix
    ./modules/tianxia-webhook.nix
  
    ./modules/tianxia-orchestrator.nix
    ./modules/tianxia-autonomy.nix
    ./modules/tianxia-plane-engine.nix
      ./modules/tianxia-thermal.nix
      ./modules/tianxia-mesh-surface.nix
    ./modules/tianxia-langpacks.nix
    ./modules/tianxia-dss-ratchet.nix
    ./modules/tianxia-dss14.nix
    ./modules/tianxia-revenue.nix
    ./modules/tx-graph-vec-svc.nix
    ./modules/tianxia-rgo.nix
  ];

  nixpkgs.config.allowUnfree = true;

  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  boot.loader.efi.efiSysMountPoint = "/boot";

  boot.kernelPackages = pkgs.linuxPackages_latest;
  boot.kernelModules = [ "thunderbolt" "thunderbolt-net" ];
  boot.kernelParams = [
    "transparent_hugepage=always"
    "zswap.enabled=0"
    "mitigations=off"
    "intel_pstate=active"
  ];

  

  zramSwap = {
    enable = true;
    algorithm = "zstd";
    memoryPercent = 85;
    priority = 32767;
  };

  hardware.graphics = {
    extraPackages = with pkgs; [
      intel-media-driver
      intel-vaapi-driver
      ocl-icd
    ];
  };

  networking = {
    hostName = "latitude-tianxia";
    networkmanager.enable = true;
    firewall = {
      enable = true;
      trustedInterfaces = [ "tailscale0" "thunderbolt0" "lo" ];
      allowedTCPPorts = [ 22 8081 8090 8099 8790 8791 9199 ];
      allowedUDPPorts = [ 51820 41641 ];
    };
    interfaces.thunderbolt0.ipv4.addresses = [{
      address = "10.99.0.2";
      prefixLength = 30;
    }];
  };

  # Resolver independence (2026-09-13): bypass home-router DNS caches.
  # Quad9 primary (malware blocklists + DNSSEC), Cloudflare fallback; native v6.
  networking.resolvconf.enable = false;
  # Pin /etc/resolv.conf after NM (Quad9 primary + Cloudflare fallback).
  systemd.services.tianxia-resolv-pin = {
    description = "Pin resolvers (Quad9 + Cloudflare)";
    after = [ "NetworkManager.service" ];
    wants = [ "NetworkManager.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = { Type = "oneshot"; RemainAfterExit = true; };
    script = ''
      printf "nameserver 9.9.9.9\nnameserver 1.1.1.1\nnameserver 2620:fe::fe\nnameserver 2606:4700:4700::1111\noptions edns0\n" > /etc/resolv.conf
    '';
  };

  networking.networkmanager.dns = "none";
  networking.nameservers = [
    "9.9.9.9"
    "1.1.1.1"
    "2620:fe::fe"
    "2606:4700:4700::1111"
  ];

  

  
  services.openssh.enable = true;
  
  services.openssh = {
    settings = {
      PermitRootLogin = "prohibit-password";
      PasswordAuthentication = false;
      KbdInteractiveAuthentication = false;
      MaxAuthTries = 4;
    };
  };
  users.users.root.openssh.authorizedKeys.keys = [
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINAFT0AhBjvO55+S6j5JpgOX797lOgPeetB9PBtuC7Om root@tianxia-relay"
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJ94PB+dtFDHwviVleBvLTHWQpGaCOV0BYYdSWPgyllp root@xps13-tianxia"
  
      "ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBO76c2I8+hjeY/fUkRA5R1vPc1aiCIzwtBoNZl1kfXQAqvVvurphC1hJhDe9zLar7odI/YxiXlPcYM/KcKOXtdM= #SSH ID - @pixel8pro-tianxia"
    ];

  environment.systemPackages = with pkgs; [
    android-tools
    # (python3.withPackages (ps: [ ps.nats-py ps.requests ps.urllib3 ]))
    git curl wget jq aria2 htop tmux btrfs-progs pciutils usbutils
    wireguard-tools util-linux procps openssh bolt
    # python3
  ];

  services.hardware.bolt.enable = true;

  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  
  systemd.services.tianxia-vector-cache = {
    description = "Tianxia Tier-1 Shared Memory Vector Cache Daemon";
    wantedBy = [ "multi-user.target" ];
    after = [ "network.target" ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/vector_cache/cache_daemon.py";
      Restart = "always";
      RestartSec = "3s";
    };
  };

  
  systemd.services.tianxia-telemetry-sink = {
    description = "Tianxia Telemetry In-Memory SQLite Sink";
    wantedBy = [ "multi-user.target" ];
    after = [ "network.target" ];
    serviceConfig = {
      Type = "simple";
      User = "root";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/telemetry/telemetry_sink.py";
      Restart = "always";
      RestartSec = "3s";
    };
  };

  system.stateVersion = "24.05";

  

  boot.devShmSize = "50%";

  # Disable failing Gitea runner unit
  systemd.services."gitea-runner-latitude-tianxia-runner".enable = false;

  # Force disable gitea actions runner instances
  services.gitea-actions-runner.instances = pkgs.lib.mkForce {};
  services.journald.extraConfig = "SystemMaxUse=500M\nMaxRetentionSec=30day\n";

  # >>> TX-RTLSDR-BEGIN >>>
  services.udev.extraRules = ''
    # ffp: TX-RTLSDR ops config nix
    # Realtek RTL2838 DVB-T (0bda:2838) - allow rtl_tcp to claim the device.
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", MODE="0660", GROUP="plugdev"
    KERNEL=="rtlsdr", MODE="0660", GROUP="plugdev"
  '';
  # <<< TX-RTLSDR-END <<<


  # Compatibility linker for unpatched binaries (pip wheels such as torch).
  programs.nix-ld.enable = true;
  # The MESH surface, tailnet only: 8792 is the workspace bus (one bus across
  # the mesh) and 5900 is the cockpit feed the TV mirrors. Scoped to
  # tailscale0 so these are NOT exposed on the LAN.
  networking.firewall.interfaces."tailscale0".allowedTCPPorts = [ 8792 5900 ];
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
