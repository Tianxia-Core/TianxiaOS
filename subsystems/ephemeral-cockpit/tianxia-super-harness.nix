# /etc/nixos/modules/tianxia-super-harness.nix
{ config, pkgs, lib, ... }:

let
  # ----------------------------------------------------------------------------
  # 1. Rasa-X-Machina Neo-Noir KDE Color Scheme
  # ----------------------------------------------------------------------------
  tianxiaColors = pkgs.writeTextDir "share/color-schemes/TianxiaNeoNoir.colors" ''
    [General]
    ColorScheme=TianxiaNeoNoir
    Name=Tianxia Neo-Noir

    [Colors:Window]
    BackgroundNormal=8,8,8
    BackgroundAlternate=16,18,22
    ForegroundNormal=255,255,255
    ForegroundInactive=156,163,175
    ForegroundActive=0,240,255
    ForegroundLink=0,240,255
    ForegroundNegative=255,85,51
    ForegroundNeutral=255,170,0

    [Colors:View]
    BackgroundNormal=16,18,22
    BackgroundAlternate=22,25,32
    ForegroundNormal=255,255,255
    ForegroundInactive=156,163,175
    ForegroundActive=0,240,255
    ForegroundLink=0,240,255

    [Colors:Button]
    BackgroundNormal=24,27,36
    BackgroundAlternate=32,36,48
    ForegroundNormal=255,255,255
    ForegroundActive=0,240,255

    [Colors:Selection]
    BackgroundNormal=0,240,255
    ForegroundNormal=8,8,8

    [Colors:Tooltip]
    BackgroundNormal=16,18,22
    ForegroundNormal=255,255,255

    [Colors:Complementary]
    BackgroundNormal=8,8,8
    ForegroundNormal=255,255,255

    [WM]
    activeBackground=8,8,8
    activeForeground=0,240,255
    inactiveBackground=16,18,22
    inactiveForeground=156,163,175
  '';

  # ----------------------------------------------------------------------------
  # 2. Harmonized 512x512 Neo-Noir Brandmark & Wallpaper Package
  # ----------------------------------------------------------------------------
  tianxiaBrandAssets = pkgs.stdenv.mkDerivation {
    name = "tianxia-brand-assets-5.0";
    src = pkgs.writeTextFile {
      name = "tianxia-brand.svg";
      destination = "/tianxia-brand.svg";
      text = ''
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
          <defs>
            <linearGradient id="cyanGlow" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#00F0FF" stop-opacity="1.0" />
              <stop offset="100%" stop-color="#008899" stop-opacity="0.85" />
            </linearGradient>
            <linearGradient id="emberGlow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#FF5533" />
              <stop offset="100%" stop-color="#FFAA00" />
            </linearGradient>
          </defs>
          <rect width="512" height="512" rx="96" fill="#080808" />
          <polygon points="256,32 448,142 448,370 256,480 64,370 64,142" fill="none" stroke="#27272A" stroke-width="6" />
          <circle cx="256" cy="256" r="196" fill="none" stroke="url(#cyanGlow)" stroke-width="8" stroke-dasharray="24 12" />
          <path d="M 256 96 L 400 364 L 112 364 Z" fill="none" stroke="url(#cyanGlow)" stroke-width="16" stroke-linejoin="round" />
          <path d="M 256 164 L 342 328 L 170 328 Z" fill="none" stroke="url(#emberGlow)" stroke-width="10" stroke-linejoin="round" />
          <circle cx="256" cy="268" r="24" fill="#00F0FF" />
          <circle cx="256" cy="268" r="8" fill="#080808" />
          <circle cx="256" cy="96" r="14" fill="#FFAA00" />
          <circle cx="400" cy="364" r="14" fill="#FFAA00" />
          <circle cx="112" cy="364" r="14" fill="#FFAA00" />
        </svg>
      '';
    };
    phases = [ "installPhase" ];
    installPhase = ''
      mkdir -p $out/share/icons/hicolor/scalable/apps
      mkdir -p $out/share/pixmaps
      mkdir -p $out/share/wallpapers/TianxiaVoid/contents/images
      cp $src/tianxia-brand.svg $out/share/icons/hicolor/scalable/apps/tianxia-brand.svg
      cp $src/tianxia-brand.svg $out/share/icons/hicolor/scalable/apps/start-here-tianxia.svg
      cp $src/tianxia-brand.svg $out/share/icons/hicolor/scalable/apps/distributor-logo.svg
      cp $src/tianxia-brand.svg $out/share/pixmaps/tianxia-brand.svg
      cp $src/tianxia-brand.svg $out/share/wallpapers/TianxiaVoid/contents/images/1920x1080.svg
    '';
  };

  # ----------------------------------------------------------------------------
  # 3. Freedesktop 5-Tier Menu Category Merge Specification
  # ----------------------------------------------------------------------------
  tianxiaMenuXml = pkgs.writeTextDir "etc/xdg/menus/applications-merged/tianxia-5tier.menu" ''
    <!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"
     "http://www.freedesktop.org/standards/menu-spec/menu-1.0.dtd">
    <Menu>
      <Name>Applications</Name>
      <Menu>
        <Name>TianxiaOS-Root</Name>
        <Directory>tianxia-root.directory</Directory>
        <Include>
          <Category>X-TianxiaOS</Category>
          <Category>X-Tianxia-Tier-1</Category>
          <Category>X-Tianxia-Tier-2</Category>
          <Category>X-Tianxia-Tier-3</Category>
          <Category>X-Tianxia-Tier-4</Category>
          <Category>X-Tianxia-Tier-5</Category>
          <Category>X-Dynamic</Category>
          <Category>TianxiaOS</Category>
          <Category>Tianxia-Tier-1</Category>
          <Category>Tianxia-Tier-2</Category>
          <Category>Tianxia-Tier-3</Category>
          <Category>Tianxia-Tier-4</Category>
          <Category>Tianxia-Tier-5</Category>
          <Category>Dynamic</Category>
        </Include>
      </Menu>
    </Menu>
  '';

  # ----------------------------------------------------------------------------
  # 4. Helper Launchers & 5-Tier Hierarchical Desktop Items
  # ----------------------------------------------------------------------------
  txCockpitLaunch = pkgs.writeScriptBin "tx-cockpit-launch" ''
    #!/usr/bin/env bash
    foot -e bash -c '/var/lib/tianxia/bin/tx-menu-trigger.sh 2>/dev/null || /var/lib/tianxia/bin/tx-menu-expand tui'
  '';

  txOperatorTuiLaunch = pkgs.writeScriptBin "tx-operator-tui-launch" ''
    #!/usr/bin/env bash
    foot -e bash -c '/var/lib/tianxia/bin/tx-menu-expand tui'
  '';

  txMeshControlLaunch = pkgs.writeScriptBin "tx-mesh-control-launch" ''
    #!/usr/bin/env bash
    foot -e bash -c '/var/lib/tianxia/bin/tx-menu-expand mesh-audit; read -p "Press Enter to close..."'
  '';

  txAetherVaultLaunch = pkgs.writeScriptBin "tx-aethervault-launch" ''
    #!/usr/bin/env bash
    foot -e bash -c 'ls -la ~/.vault ~/workspace/.vault 2>/dev/null; read -p "Press Enter to close..."'
  '';

  txVudaLaunch = pkgs.writeScriptBin "tx-vuda-launch" ''
    #!/usr/bin/env bash
    foot -e bash -c '/var/lib/tianxia/bin/tx-menu-expand vuda-audit; read -p "Press Enter to close..."'
  '';

  txStorefrontLaunch = pkgs.writeScriptBin "tx-storefront-launch" ''
    #!/usr/bin/env bash
    foot -e bash -c 'curl -ILs https://rasaxmachina.com 2>/dev/null | head -n 25; read -p "Press Enter to close..."'
  '';

  txTetraLedgerLaunch = pkgs.writeScriptBin "tx-tetraledger-launch" ''
    #!/usr/bin/env bash
    foot -e bash -c '/var/lib/tianxia/bin/tetraledger-status.sh 2>/dev/null || htop'
  '';

  tier1Cockpit = pkgs.makeDesktopItem {
    name = "tx-t1-cockpit";
    desktopName = "01 // [T1] Sovereign Cockpit HUD";
    genericName = "System Root Execution";
    comment = "Tier 1: Unified system orchestration and telemetry cockpit";
    exec = "tx-cockpit-launch";
    icon = "tianxia-brand";
    categories = [ "X-TianxiaOS" "X-Tianxia-Tier-1" "System" ];
  };

  tier1Monitor = pkgs.makeDesktopItem {
    name = "tx-t1-monitor";
    desktopName = "01 // [T1] System Telemetry Matrix";
    genericName = "Hardware Resource Monitor";
    comment = "Tier 1: Real-time CPU, RAM, and process inspection";
    exec = "plasma-systemmonitor";
    icon = "utilities-system-monitor";
    categories = [ "X-TianxiaOS" "X-Tianxia-Tier-1" "System" ];
  };

  tier2OperatorTui = pkgs.makeDesktopItem {
    name = "tx-t2-operator-tui";
    desktopName = "02 // [T2] Sovereign Operator TUI";
    genericName = "Terminal Control Plane";
    comment = "Tier 2: High-throughput terminal operations plane";
    exec = "tx-operator-tui-launch";
    icon = "utilities-terminal";
    categories = [ "X-TianxiaOS" "X-Tianxia-Tier-2" "Development" ];
  };

  tier2MeshControl = pkgs.makeDesktopItem {
    name = "tx-t2-mesh-control";
    desktopName = "02 // [T2] Tailscale Tri-Node Mesh Matrix";
    genericName = "Cluster Orchestration";
    comment = "Tier 2: Active mesh link across Latitude 5591, Pixel 8 Pro, and Poco X5 Pro 5G (XPS 13 Standby)";
    exec = "tx-mesh-control-launch";
    icon = "network-server-database";
    categories = [ "X-TianxiaOS" "X-Tianxia-Tier-2" "Network" ];
  };

  tier2AetherVault = pkgs.makeDesktopItem {
    name = "tx-t2-aethervault";
    desktopName = "02 // [T2] AetherVault Identity Proxy";
    genericName = "Inverse-SSO & Vault Governance";
    comment = "Tier 2: Decentralized identity attestation and keystore audit";
    exec = "tx-aethervault-launch";
    icon = "security-high";
    categories = [ "X-TianxiaOS" "X-Tianxia-Tier-2" "System" ];
  };

  tier3VudaStatus = pkgs.makeDesktopItem {
    name = "tx-t3-vuda-softem";
    desktopName = "03 // [T3] VUDA & SOFTEM Emulation Engine";
    genericName = "Virtual Compute & Thermal Layer";
    comment = "Tier 3: Software-based hardware emulation and thermal telemetry";
    exec = "tx-vuda-launch";
    icon = "preferences-system-performance";
    categories = [ "X-TianxiaOS" "X-Tianxia-Tier-3" "System" ];
  };

  tier3Storefront = pkgs.makeDesktopItem {
    name = "tx-t3-storefront";
    desktopName = "03 // [T3] Rasa-X-Machina Storefront";
    genericName = "Autonomous Shopfront Gateway";
    comment = "Tier 3: Live endpoint audit for rasaxmachina.com, rasaxm.com, and airasa.work";
    exec = "tx-storefront-launch";
    icon = "network-workgroup";
    categories = [ "X-TianxiaOS" "X-Tianxia-Tier-3" "Network" ];
  };

  tier4TetraLedger = pkgs.makeDesktopItem {
    name = "tx-t4-tetraledger";
    desktopName = "04 // [T4] TetraLedger Solvency Engine";
    genericName = "Credit & Liquidity Telemetry";
    comment = "Tier 4: On-demand WAL credit facility and RGU solvency monitor";
    exec = "tx-tetraledger-launch";
    icon = "office-chart-line";
    categories = [ "X-TianxiaOS" "X-Tianxia-Tier-4" "Office" ];
  };

  tier5WorkspaceVfs = pkgs.makeDesktopItem {
    name = "tx-t5-workspace-vfs";
    desktopName = "05 // [T5] Tianxia Workspace VFS";
    genericName = "Autarchic File System";
    comment = "Tier 5: Open partitioned ~/workspace hierarchy in Dolphin";
    exec = "dolphin /root/workspace";
    icon = "folder-cyan";
    categories = [ "X-TianxiaOS" "X-Tianxia-Tier-5" "System" ];
  };

  tier5NixosConfig = pkgs.makeDesktopItem {
    name = "tx-t5-nixos-substrate";
    desktopName = "05 // [T5] NixOS Declarative Substrate";
    genericName = "System Configuration Tree";
    comment = "Tier 5: Open /etc/nixos modules and hardware definitions";
    exec = "dolphin /etc/nixos";
    icon = "folder-development";
    categories = [ "X-TianxiaOS" "X-Tianxia-Tier-5" "Development" ];
  };

  # ----------------------------------------------------------------------------
  # 5. Plasma 6 & Dolphin Auto-Provisioning Script (Runs at Login)
  # ----------------------------------------------------------------------------
  tianxiaDesktopInit = pkgs.writeScriptBin "tx-plasma-autoconfig" ''
    #!/usr/bin/env bash
    set -euo pipefail

    if command -v plasma-apply-colorscheme >/dev/null 2>&1; then
      plasma-apply-colorscheme TianxiaNeoNoir >/dev/null 2>&1 || true
    fi

    if command -v kwriteconfig6 >/dev/null 2>&1; then
      kwriteconfig6 --file kdeglobals --group General --key ColorScheme "TianxiaNeoNoir"
      kwriteconfig6 --file kdeglobals --group KDE --key SingleClick false
      kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnLeft "M"
      kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key ButtonsOnRight "IAX"
      kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key BorderSize "Normal"
      kwriteconfig6 --file plasmarc --group Theme --key name "breeze-dark"
    fi

    APPLET_RC="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
    if [ -f "$APPLET_RC" ]; then
      sed -i 's/icon=start-here-kde-symbolic/icon=tianxia-brand/g' "$APPLET_RC" || true
      sed -i 's/icon=distributor-logo/icon=tianxia-brand/g' "$APPLET_RC" || true
    fi

    mkdir -p "$HOME/.local/share"
    PLACES_FILE="$HOME/.local/share/user-places.xbel"
    if [ ! -f "$PLACES_FILE" ] || ! grep -q "Tianxia Workspace" "$PLACES_FILE" 2>/dev/null; then
      cat << 'XBEL_EOF' > "$PLACES_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xbel>
<xbel xmlns:bookmark="http://www.freedesktop.org/standards/desktop-bookmarks" xmlns:kdepriv="http://www.kde.org/kdepriv" xmlns:mime="http://www.freedesktop.org/standards/shared-mime-info">
 <bookmark href="file:///root/workspace">
  <title>Tianxia Workspace</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="folder-cyan"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/core">
  <title>TX Core (T1)</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="applications-engineering"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/systems">
  <title>TX Systems (T2)</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="network-server-database"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/subsystems">
  <title>TX Subsystems (T3)</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="preferences-system-performance"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/specs">
  <title>TX Specs &amp; AST</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="text-x-generic"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/payloads">
  <title>TX Payloads (T4)</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="package-x-generic"/></metadata></info>
 </bookmark>
 <bookmark href="file:///root/workspace/projects">
  <title>TX Custom Projects</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="folder-favorites"/></metadata></info>
 </bookmark>
 <bookmark href="file:///etc/nixos">
  <title>NixOS Substrate</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="folder-development"/></metadata></info>
 </bookmark>
 <bookmark href="file:///var/lib/tianxia">
  <title>Tianxia Registry</title>
  <info><metadata owner="http://www.freedesktop.org"><bookmark:icon name="folder-locked"/></metadata></info>
 </bookmark>
</xbel>
XBEL_EOF
    fi

    kbuildsycoca6 >/dev/null 2>&1 || true
  '';

  tianxiaAutostartDesktop = pkgs.writeTextDir "etc/xdg/autostart/tianxia-plasma-autoconfig.desktop" ''
    [Desktop Entry]
    Type=Application
    Name=TianxiaOS Plasma Auto-Provisioner
    Exec=${tianxiaDesktopInit}/bin/tx-plasma-autoconfig
    OnlyShowIn=KDE;
    X-KDE-Autostart-Phase=1
  '';

  # ----------------------------------------------------------------------------
  # 6. Custom Workspace Section Generator CLI (tx-workspace-init)
  # ----------------------------------------------------------------------------
  txWorkspaceInit = pkgs.writeScriptBin "tx-workspace-init" ''
    #!/usr/bin/env bash
    set -euo pipefail
    TARGET_BASE="''${1:-$HOME/workspace}"
    CUSTOM_SECTION="''${2:-}"
    FLAG="''${3:-}"

    mkdir -p "$TARGET_BASE"/{core,systems,subsystems,runtime,specs,payloads,archive,projects,.vault}
    mkdir -p "$HOME/TianxiaOS"
    chmod 0700 "$TARGET_BASE" "$TARGET_BASE/.vault"
    ln -sfn "$TARGET_BASE" "$HOME/TianxiaOS/workspace"
    ln -sfn "$TARGET_BASE" "$HOME/TianxiaOS-Workspace"

    if [ -n "$CUSTOM_SECTION" ]; then
      SECTION_PATH="$TARGET_BASE/$CUSTOM_SECTION"
      mkdir -p "$SECTION_PATH"/{src,specs,runtime,tests,docs}
      echo "[+] Created custom TianxiaOS workspace section: $SECTION_PATH"
      if [ "$FLAG" = "--bookmark" ] && [ -f "$HOME/.local/share/user-places.xbel" ]; then
        sed -i "s|</xbel>| <bookmark href=\"file://$SECTION_PATH\"><title>TX: $CUSTOM_SECTION</title><info><metadata owner=\"http://www.freedesktop.org\"><bookmark:icon name=\"folder-cyan\"/></metadata></info></bookmark>\n</xbel>|" "$HOME/.local/share/user-places.xbel"
        echo "[+] Pinned $CUSTOM_SECTION to Dolphin Places sidebar."
      fi
    fi

    echo "[+] Verified TianxiaOS workspace hierarchy at $TARGET_BASE"
  '';

in
{
  # ----------------------------------------------------------------------------
  # Bootloader & Neo-Noir Plymouth Splash Configuration
  # ----------------------------------------------------------------------------
  boot = {
    plymouth = {
      enable = true;
      theme = "breeze";
    };
    initrd.verbose = false;
    kernelParams = [
      "quiet"
      "splash"
      "boot.shell_on_fail"
      "loglevel=3"
      "rd.systemd.show_status=false"
      "rd.udev.log_level=3"
      "udev.log_priority=3"
    ];

    loader.systemd-boot = {
      enable = true;
      configurationLimit = 10;
      extraEntries = {
        "tianxia-tui.conf" = ''
          title TianxiaOS v5.0 [TUI] - Sovereign Operator Cockpit (Console Mode)
          version ${config.system.nixos.label}
          linux ${config.system.build.kernel}/bzImage
          initrd ${config.system.build.initialRamdisk}/initrd
          options init=/nix/var/nix/profiles/system/init systemd.unit=multi-user.target tianxia.mode=tui quiet
        '';
        "tianxia-cli.conf" = ''
          title TianxiaOS v5.0 [CLI] - Pure Autarchic Kernel Rescue (Headless Mode)
          version ${config.system.nixos.label}
          linux ${config.system.build.kernel}/bzImage
          initrd ${config.system.build.initialRamdisk}/initrd
          options init=/nix/var/nix/profiles/system/init systemd.unit=rescue.target nomodeset quiet
        '';
      };
    };
  };

  # ----------------------------------------------------------------------------
  # Display Manager (SDDM Wayland) & Desktop Manager (KDE Plasma 6)
  # ----------------------------------------------------------------------------
  services.desktopManager.plasma6.enable = true;
  services.displayManager.sddm = {
    enable = true;
    wayland.enable = true;
    theme = "breeze";
    settings = {
      Theme = {
        CursorTheme = "breeze_cursors";
        Font = "JetBrains Mono,10,-1,5,50,0,0,0,0,0";
      };
    };
  };

  services.tailscale.enable = true;

  # ----------------------------------------------------------------------------
  # White-Label OS Release Metadata
  # ----------------------------------------------------------------------------
  environment.etc."os-release".text = lib.mkForce ''
    NAME="TianxiaOS"
    ID="tianxiaos"
    ID_LIKE="nixos"
    VERSION="5.0-Asura"
    VERSION_ID="5.0"
    PRETTY_NAME="TianxiaOS v5.0 (Rasa-X-Machina Super-Harness)"
    HOME_URL="https://rasaxmachina.com"
    DOCUMENTATION_URL="https://airasa.work"
    SUPPORT_URL="https://rasaxm.com"
    BUG_REPORT_URL="https://github.com/rasa-x-machina"
    LOGO="tianxia-brand"
  '';

  # System-Wide KDE & Foot Defaults in /etc/xdg
  environment.etc."xdg/kdeglobals".text = ''
    [General]
    ColorScheme=TianxiaNeoNoir
    Name=Tianxia Neo-Noir
    fixed=JetBrains Mono,10,-1,5,50,0,0,0,0,0
    font=Inter,10,-1,5,50,0,0,0,0,0

    [KDE]
    LookAndFeelPackage=org.kde.breezedark.desktop
    SingleClick=false
  '';

  environment.etc."xdg/kwinrc".text = ''
    [org.kde.kdecoration2]
    BorderSize=Normal
    ButtonsOnLeft=M
    ButtonsOnRight=IAX
    library=org.kde.breeze
  '';

  environment.etc."xdg/foot/foot.ini".text = ''
    [main]
    font=JetBrains Mono:size=11
    pad=12x12

    [colors]
    background=080808
    foreground=ffffff
    regular0=080808
    regular1=ff5533
    regular2=00f0ff
    regular3=ffaa00
    regular4=008899
    regular5=ff5533
    regular6=00f0ff
    regular7=d4d4d8
  '';

  # Expose Dynamic agy Applications Directory to XDG_DATA_DIRS
  environment.sessionVariables = {
    TIANXIA_WORKSPACE = "$HOME/workspace";
    QT_QPA_PLATFORM = "wayland";
    PLASMA_USE_QT_SCALING = "1";
  };
  environment.extraInit = ''
    export XDG_DATA_DIRS="/var/lib/tianxia/share:''${XDG_DATA_DIRS:-/run/current-system/sw/share}"
  '';

  # ----------------------------------------------------------------------------
  # System Packages & Branded Desktop Items
  # ----------------------------------------------------------------------------
  environment.systemPackages = with pkgs; [
    foot
    kdePackages.dolphin
    kdePackages.plasma-systemmonitor
    kdePackages.kate
    kdePackages.kconfig
    kdePackages.kservice
    python3
    jq
    curl
    git
    htop
    tmux
    tailscale
    vulkan-tools
    pciutils

    tianxiaColors
    tianxiaBrandAssets
    tianxiaMenuXml
    tianxiaDesktopInit
    tianxiaAutostartDesktop
    txWorkspaceInit
    txCockpitLaunch
    txOperatorTuiLaunch
    txMeshControlLaunch
    txAetherVaultLaunch
    txVudaLaunch
    txStorefrontLaunch
    txTetraLedgerLaunch
    tier1Cockpit
    tier1Monitor
    tier2OperatorTui
    tier2MeshControl
    tier2AetherVault
    tier3VudaStatus
    tier3Storefront
    tier4TetraLedger
    tier5WorkspaceVfs
    tier5NixosConfig
  ];

  # ----------------------------------------------------------------------------
  # Systemd Service: Dynamic agy Menu & Mesh Introspection Daemon
  # ----------------------------------------------------------------------------
  systemd.services.tianxia-menu-expand = {
    description = "TianxiaOS Dynamic agy Discovery, SemanticZip & Menu Expansion Daemon";
    wantedBy = [ "multi-user.target" ];
    after = [ "network.target" "tailscaled.service" ];
    path = with pkgs; [ python3 systemd tailscale iproute2 coreutils bash kdePackages.kservice vulkan-tools ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "/var/lib/tianxia/bin/tx-menu-expand daemon";
      Restart = "always";
      RestartSec = "5s";
    };
  };

  # ----------------------------------------------------------------------------
  # Interactive Shell Aliases (GUI / TUI / CLI / Mesh / SemanticZip / agy)
  # ----------------------------------------------------------------------------
  environment.interactiveShellInit = ''
    alias tx-gui-stop="sudo systemctl isolate multi-user.target"
    alias tx-gui-start="sudo systemctl isolate graphical.target"
    alias tx-expand="/var/lib/tianxia/bin/tx-menu-expand"
    alias tx-manifest="cat /var/lib/tianxia/registry/system-manifest.json | jq ."
    alias tx-semantic="/var/lib/tianxia/bin/tx-menu-expand semantic-zip"
    alias tx-mesh="/var/lib/tianxia/bin/tx-menu-expand mesh-audit"
    alias tx-workspace="cd ~/workspace"
    alias tx-tui="/var/lib/tianxia/bin/tx-menu-expand tui"
    export TIANXIA_WORKSPACE="$HOME/workspace"
  '';
}
