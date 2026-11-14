# ffp: TX-TIANXIA-GUI declarative nix
{ config, lib, pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    # Compositor & UI
    sway
    wayvnc
    swaybg
    foot
    fuzzel
    chromium
    jq

    # Development & Workflow
    tmux
    zellij
    neovim
    git
    fzf
    ripgrep
    htop

    # NixOS Package Inspection & Management Suite
    nh                  # Fast, modern NixOS CLI helper
    nix-tree            # Interactive visual dependency & closure inspector
    nix-output-monitor  # Pretty build tree viewer (nom)
    nurl                # Nix fetcher generator
  ];

  # Allow unfree packages & experimental flakes
  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  systemd.services.tianxia-cockpit = {
    description = "Tianxia Sovereign Wayland Cockpit (DP-1)";
    after = [ "network.target"  "tianxia-gui-bridge.service" ];
    wants = [ "tianxia-gui-bridge.service" ];
    wantedBy = [ "multi-user.target" ];
    path = with pkgs; [
      bash
      coreutils
      procps
      findutils
      sway
      wayvnc
    swaybg
      foot
      fuzzel
      chromium
      jq
      tmux
      neovim
      fzf
      nh
      nix-tree
      nix
    ];
    environment = {
      XDG_RUNTIME_DIR = "/run/user/0";
      WLR_BACKENDS = "drm,libinput";
      WLR_RENDERER = "pixman";
      _JAVA_AWT_WM_NONREPARENTING = "1";
    };
    serviceConfig = {
   
      CPUQuota = "40%";
      CPUWeight = 50;   Type = "simple";
      User = "root";
      WorkingDirectory = "/var/lib/tianxia";
      ExecStart = "${pkgs.bash}/bin/bash /var/lib/tianxia/bin/tx_tv_sway_launch.sh";
      Restart = "always";
      RestartSec = 3;
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
