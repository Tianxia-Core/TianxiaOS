# ffp: FFP-NIXOS-HW-INPUT-BACKLIGHT declarative nix
# TianxiaOS Dell Latitude 5591 Sovereign Input, External Mouse Maximizer, ALPS DualPoint & Backlight Module
{ config, pkgs, lib, ... }:

let
  dellPegLcdSsdt = pkgs.runCommand "dell-latitude-5591-peglcd-ssdt" {
    nativeBuildInputs = [ pkgs.acpica-tools ];
  } ''
    cp ${../src/hw-input/dell_peglcd_fix.asl} dell_peglcd_fix.asl
    iasl -tc dell_peglcd_fix.asl
    mkdir -p $out/share/acpi
    cp dell_peglcd_fix.aml $out/share/acpi/dell_peglcd_fix.aml
  '';

  txHwInputSuite = pkgs.stdenv.mkDerivation {
    pname = "tx-hw-input-suite";
    version = "1.0.0";
    dontUnpack = true;
    buildPhase = ''
      $CC -std=c11 -O2 -Wall -Wextra -Werror \
        ${../src/hw-input/tx_alps_dualpoint_init.c} \
        -o tx-alps-dualpoint-init
      $CC -std=c11 -O2 -Wall -Wextra -Werror \
        ${../src/hw-input/tx_mouse_maximizer.c} \
        -o tx-mouse-maximizer
    '';
    installPhase = ''
      mkdir -p $out/bin
      install -m 0755 tx-alps-dualpoint-init $out/bin/tx-alps-dualpoint-init
      install -m 0755 tx-mouse-maximizer $out/bin/tx-mouse-maximizer
    '';
  };

  txBacklightCtl = pkgs.writeShellScriptBin "tx-backlight-ctl" ''
    # ffp: FFP-BACKLIGHT-CTL glue bash
    set +e
    set +u

    ACTION="''${1:-status}"
    ARG="''${2:-5%}"
    BL_DIR="/sys/class/backlight/intel_backlight"
    KBD_DIR="/sys/class/leds/dell::kbd_backlight"

    notify_powerdevil() {
      local target_kde="$1"
      if [ -S "/run/user/1000/bus" ]; then
        if [ "$(${pkgs.coreutils}/bin/id -u)" -eq 1000 ]; then
          env DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus" \
            ${pkgs.systemd}/bin/busctl --user call \
            org.kde.Solid.PowerManagement \
            /org/kde/Solid/PowerManagement/Actions/BrightnessControl \
            org.kde.Solid.PowerManagement.Actions.BrightnessControl \
            setBrightness i "$target_kde" >/dev/null 2>&1
          return $?
        elif [ "$(${pkgs.coreutils}/bin/id -u)" -eq 0 ]; then
          ${pkgs.util-linux}/bin/runuser -u tianxia -- \
            env DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus" \
            ${pkgs.systemd}/bin/busctl --user call \
            org.kde.Solid.PowerManagement \
            /org/kde/Solid/PowerManagement/Actions/BrightnessControl \
            org.kde.Solid.PowerManagement.Actions.BrightnessControl \
            setBrightness i "$target_kde" >/dev/null 2>&1
          return $?
        fi
      fi
      return 1
    }

    if [ ! -d "$BL_DIR" ]; then
      printf '%s\n' "[tx-backlight-ctl] warn: intel_backlight not present" >&2
      exit 0
    fi

    MAX=$(cat "$BL_DIR/max_brightness" 2>/dev/null)
    CUR=$(cat "$BL_DIR/brightness" 2>/dev/null)
    MAX="''${MAX:-120000}"
    CUR="''${CUR:-96000}"
    MIN_SAFE=$(( MAX * 5 / 100 ))

    case "$ACTION" in
      status)
        PCT=$(( CUR * 100 / MAX ))
        KBD_CUR=$(cat "$KBD_DIR/brightness" 2>/dev/null)
        printf 'screen_brightness=%s/%s (%s%%) kbd_backlight=%s\n' "$CUR" "$MAX" "$PCT" "''${KBD_CUR:-n/a}"
        ;;
      up)
        STEP_NUM="''${ARG%%%}"
        DELTA=$(( MAX * STEP_NUM / 100 ))
        NEW=$(( CUR + DELTA ))
        [ "$NEW" -gt "$MAX" ] && NEW="$MAX"
        KDE_VAL=$(( NEW * 10000 / MAX ))
        notify_powerdevil "$KDE_VAL" || ${pkgs.brightnessctl}/bin/brightnessctl -d intel_backlight set "$NEW" >/dev/null 2>&1
        printf '%s\n' "$NEW" > "$BL_DIR/brightness" 2>/dev/null
        ;;
      down)
        STEP_NUM="''${ARG%%%}"
        DELTA=$(( MAX * STEP_NUM / 100 ))
        NEW=$(( CUR - DELTA ))
        [ "$NEW" -lt "$MIN_SAFE" ] && NEW="$MIN_SAFE"
        KDE_VAL=$(( NEW * 10000 / MAX ))
        notify_powerdevil "$KDE_VAL" || ${pkgs.brightnessctl}/bin/brightnessctl -d intel_backlight set "$NEW" >/dev/null 2>&1
        printf '%s\n' "$NEW" > "$BL_DIR/brightness" 2>/dev/null
        ;;
      set)
        PCT_NUM="''${ARG%%%}"
        NEW=$(( MAX * PCT_NUM / 100 ))
        [ "$NEW" -lt "$MIN_SAFE" ] && NEW="$MIN_SAFE"
        [ "$NEW" -gt "$MAX" ] && NEW="$MAX"
        KDE_VAL=$(( NEW * 10000 / MAX ))
        notify_powerdevil "$KDE_VAL" || ${pkgs.brightnessctl}/bin/brightnessctl -d intel_backlight set "$NEW" >/dev/null 2>&1
        printf '%s\n' "$NEW" > "$BL_DIR/brightness" 2>/dev/null
        ;;
      kbd)
        if [ -d "$KBD_DIR" ]; then
          KMAX=$(cat "$KBD_DIR/max_brightness" 2>/dev/null)
          KCUR=$(cat "$KBD_DIR/brightness" 2>/dev/null)
          KMAX="''${KMAX:-2}"
          KCUR="''${KCUR:-1}"
          if [ "$ARG" = "cycle" ]; then
            KNEW=$(( (KCUR + 1) % (KMAX + 1) ))
          else
            KNEW="$ARG"
          fi
          printf '%s\n' "$KNEW" > "$KBD_DIR/brightness" 2>/dev/null
        fi
        ;;
      *)
        printf 'Usage: tx-backlight-ctl [status|up [pct%%]|down [pct%%]|set <pct%%>|kbd <0|1|2|cycle>]\n' >&2
        exit 2
        ;;
    esac
    exit 0
  '';

  txKwinInputSync = pkgs.writeShellScriptBin "tx-kwin-input-sync" ''
    # ffp: FFP-KWIN-INPUT-SYNC glue bash
    set +e
    set +u

    USER_CFG="/home/tianxia/.config/kcminputrc"
    if [ -d "/home/tianxia/.config" ]; then
      cp /etc/xdg/kcminputrc "$USER_CFG.tmp" 2>/dev/null
      chown tianxia:users "$USER_CFG.tmp" 2>/dev/null
      chmod 0644 "$USER_CFG.tmp" 2>/dev/null
      mv -f "$USER_CFG.tmp" "$USER_CFG" 2>/dev/null
    fi

    if [ ! -S "/run/user/1000/bus" ]; then
      exit 0
    fi

    kwin_set() {
      local obj="$1"
      local prop="$2"
      local sig="$3"
      local val="$4"
      ${pkgs.util-linux}/bin/runuser -u tianxia -- \
        env DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus" \
        ${pkgs.systemd}/bin/busctl --user set-property \
        org.kde.KWin "$obj" org.kde.KWin.InputDevice "$prop" "$sig" "$val" >/dev/null 2>&1
    }

    for sysdev in /sys/class/input/event*; do
      [ -e "$sysdev/device/name" ] || continue
      ev="''${sysdev##*/}"
      dname=$(cat "$sysdev/device/name" 2>/dev/null)
      obj="/org/kde/KWin/InputDevice/$ev"
      case "$dname" in
        *"044E:121F Touchpad"*)
          kwin_set "$obj" enabled b true
          kwin_set "$obj" tapToClick b true
          kwin_set "$obj" tapAndDrag b true
          kwin_set "$obj" lmrTapButtonMap b false
          kwin_set "$obj" naturalScroll b true
          kwin_set "$obj" scrollTwoFinger b true
          kwin_set "$obj" disableWhileTyping b true
          kwin_set "$obj" disableEventsOnExternalMouse b false
          kwin_set "$obj" pointerAccelerationProfileAdaptive b true
          kwin_set "$obj" pointerAcceleration d 0.2
          ;;
        *"044E:121F Mouse"*)
          kwin_set "$obj" enabled b true
          kwin_set "$obj" middleEmulation b true
          kwin_set "$obj" scrollOnButtonDown b true
          kwin_set "$obj" scrollButton u 274
          kwin_set "$obj" naturalScroll b false
          kwin_set "$obj" pointerAccelerationProfileAdaptive b true
          kwin_set "$obj" pointerAcceleration d 0.2
          ;;
        *"Shinetek Technology USB Composite Device"*|*"Logitech USB Receiver Mouse"*)
          kwin_set "$obj" enabled b true
          kwin_set "$obj" pointerAccelerationProfileFlat b true
          kwin_set "$obj" pointerAcceleration d 0.0
          kwin_set "$obj" naturalScroll b false
          kwin_set "$obj" scrollFactor d 1.0
          ;;
      esac
    done
    exit 0
  '';
in
{
  # 1. Kernel Modules & Parameters for Native Backlight, ACPI Hotkeys, HID++ & Low-Latency 1000Hz Input
  boot.kernelModules = [
    "acpi_configfs"
    "uinput"
    "i2c-dev"
    "hid-logitech-hidpp"
    "hid-logitech-dj"
    "snd-ctl-led"
  ];

  boot.kernelParams = [
    "acpi_backlight=native"
    "video.brightness_switch_enabled=0"
    "video.report_key_events=1"
  ];

  # 2. Sovereign Peripheral, Mouse Customization, Backlight & Firmware Tooling
  environment.systemPackages = with pkgs; [
    txHwInputSuite
    txBacklightCtl
    txKwinInputSync
    brightnessctl
    ddcutil
    acpi
    libinput
    evtest
    solaar
    libratbag
    piper
    mouse_m908
    input-remapper
    libsmbios
    powertop
  ];

  # 3. Peripheral Daemons, Real-Time Input/Audio Scheduling, I2C, Firmware & Bluetooth 5.1
  services.ratbagd.enable = true;
  services.input-remapper.enable = true;
  services.fwupd.enable = lib.mkDefault true;
  services.upower.enable = lib.mkDefault true;
  hardware.i2c.enable = true;
  security.rtkit.enable = true;

  hardware.bluetooth = {
    enable = true;
    powerOnBoot = true;
    settings = {
      General = {
        FastConnectable = true;
        Experimental = true;
      };
    };
  };

  services.udev.packages = with pkgs; [
    solaar
    libratbag
    brightnessctl
  ];

  # Ensure Sovereign Desktop Operator has full non-root access to input, HID, backlight, and DDC/I2C buses
  users.users.tianxia.extraGroups = [
    "input"
    "plugdev"
    "i2c"
    "lp"
  ];

  # 4. Libinput Local Device Quirks for Dell Latitude 5591 ALPS DualPoint Stick
  environment.etc."libinput/local-overrides.quirks".text = ''
    [Dell Latitude 5591 ALPS DualPoint Stick]
    MatchName=DELL0819:00 044E:121F Mouse
    MatchVendor=0x044E
    MatchProduct=0x121F
    AttrPointingStickIntegration=internal
  '';

  # 5. Hardware Database & udev Rules: PointingStick Tagging, Zero-Lag USB HID, ALPS Storm Guard & MX130 D3cold
  services.udev.extraHwdb = lib.mkAfter ''
    # Dell Latitude 5591 ALPS DualPoint TrackStick sensitivity calibration
    libinput:name:DELL0819:00 044E:121F Mouse:*
     LIBINPUT_ATTR_TRACKPOINT_RANGE=20
  '';

  services.udev.extraRules = lib.mkAfter ''
    # Tag DELL0819:00 044E:121F Mouse (Report ID 1) as internal PointingStick so Top 3 Buttons + Middle-Button Scroll + dwtp link cleanly
    ACTION=="add|change", SUBSYSTEM=="input", KERNEL=="event*", ATTRS{name}=="DELL0819:00 044E:121F Mouse", ENV{ID_INPUT_POINTINGSTICK}="1"

    # Trigger ALPS 044E:121F hardware self-test & stuck-switch fault isolator on hidraw bind
    ACTION=="add|change", SUBSYSTEM=="hidraw", KERNELS=="*044E:121F*", RUN+="${txHwInputSuite}/bin/tx-alps-dualpoint-init"

    # Keep Intel LPSS I2C #1 controller & DELL0819 touchpad bus powered on to prevent runtime-PM cursor jump
    ACTION=="add", SUBSYSTEM=="pci", KERNEL=="0000:00:15.1", ATTR{power/control}="on"
    ACTION=="add", SUBSYSTEM=="i2c", KERNEL=="i2c-DELL0819:00", ATTR{power/control}="on"

    # Disable USB autosuspend on Redragon M602U-KS (1a2c:8fff), Logitech Lightspeed (046d:c53d), and USB HID mice
    ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="1a2c", ATTR{idProduct}=="8fff", ATTR{power/control}="on"
    ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="046d", ATTR{idProduct}=="c53d", ATTR{power/control}="on"
    ACTION=="add", SUBSYSTEM=="usb", ATTR{bInterfaceClass}=="03", ATTR{bInterfaceProtocol}=="02", TEST=="../power/control", ATTR{../power/control}="on"

    # Grant plugdev/input non-root access to Redragon M602U-KS vendor HID configuration interface (mouse_m908)
    ACTION=="add", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1a2c", ATTRS{idProduct}=="8fff", MODE="0660", GROUP="plugdev"

    # Enable PCIe runtime power management (D3cold) on unused discrete NVIDIA GeForce MX130 (saves ~6W heat/fan load)
    ACTION=="add", SUBSYSTEM=="pci", ATTR{vendor}=="0x10de", ATTR{power/control}="auto"
  '';

  # Silence PowerDevil xdg-desktop-portal registration warning
  systemd.tmpfiles.rules = [
    "d /run/tianxia 0755 root root -"
    "f /var/lib/tianxia/share/applications/org.kde.org_kde_powerdevil.desktop 0644 root root - [Desktop Entry]\\nType=Application\\nName=KDE PowerDevil\\nExec=org_kde_powerdevil\\nNoDisplay=true\\n"
  ];

  # 6. Early-Boot Dell Latitude 5591 DSDT BRT6 (PEG0.PEGP.LCD) ACPI Hotfix Loader
  systemd.services.tianxia-acpi-dell-brt6-fix = {
    description = "Load Dell Latitude 5591 PEGP.LCD ACPI SSDT Brightness Hotkey Fix";
    wantedBy = [ "multi-user.target" ];
    after = [ "systemd-modules-load.service" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      MemoryMax = "32M";
      TasksMax = 16;
      ExecStart = pkgs.writeShellScript "load-dell-peglcd-ssdt" ''
        set +e
        set +u
        ${pkgs.kmod}/bin/modprobe acpi_configfs 2>/dev/null
        TBL_DIR="/sys/kernel/config/acpi/table/dell_peglcd_fix"
        if [ -d "/sys/kernel/config/acpi/table" ]; then
          mkdir -p "$TBL_DIR" 2>/dev/null
          if [ -f "$TBL_DIR/aml" ] && [ "$(wc -c < "$TBL_DIR/aml" 2>/dev/null)" -eq 0 ]; then
            cat ${dellPegLcdSsdt}/share/acpi/dell_peglcd_fix.aml > "$TBL_DIR/aml" 2>/dev/null
          fi
        fi
        exit 0
      '';
    };
  };

  # 7. Boot & Post-Resume ALPS DualPoint Self-Test + KWin Live Input Profile Enforcer
  systemd.services.tianxia-alps-dualpoint-init = {
    description = "Initialize Dell Latitude 5591 ALPS DualPoint PTP & Isolate Stuck Switches";
    wantedBy = [ "multi-user.target" "post-resume.target" ];
    after = [ "systemd-udev-settle.service" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      MemoryMax = "32M";
      TasksMax = 16;
      ExecStart = pkgs.writeShellScript "run-alps-dualpoint-init" ''
        set +e
        set +u
        ${txHwInputSuite}/bin/tx-alps-dualpoint-init
        ${txKwinInputSync}/bin/tx-kwin-input-sync
        exit 0
      '';
    };
  };

  # 8. Zero-Latency External Mouse Extra-Button Maximizer Daemon (Buttons 6/7/8 -> Plasma Overview/Expose/KRunner)
  systemd.services.tianxia-mouse-maximizer = {
    description = "TianxiaOS Zero-Latency External Mouse Extra-Button Maximizer";
    wantedBy = [ "multi-user.target" ];
    after = [ "systemd-udev-settle.service" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${txHwInputSuite}/bin/tx-mouse-maximizer";
      Restart = "always";
      RestartSec = "2s";
      MemoryMax = "32M";
      TasksMax = 16;
      CPUQuota = "5%";
      NoNewPrivileges = true;
      ProtectHome = true;
      ProtectSystem = "strict";
    };
  };
}
