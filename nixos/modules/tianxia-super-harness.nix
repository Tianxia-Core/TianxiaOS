# ffp: FFP-NIXOS-SUPER-HARNESS declarative nix
{ config, pkgs, lib, ... }:
let
  txPython = pkgs.python3.withPackages (ps: with ps; [
    pyqt6
    dbus-python
    nats-py
    requests
    urllib3
  ]);
in
{
  environment.systemPackages = with pkgs; [
    foot
    kdePackages.dolphin
    kdePackages.plasma-systemmonitor
    kdePackages.kate
    kdePackages.kconfig
    kdePackages.kservice
    (lib.setPrio (-100) txPython)
    jq
    curl
    git
    htop
    tmux
    tailscale
    vulkan-tools
    pciutils
    openssl

    # Passwordless Hardware & FIDO2 Infrastructure (Option D + YubiKey 5C NFC)
    pam_u2f
    libfido2
    yubikey-manager
    yubikey-personalization
  ];

  # KDE Connect Integration (Option B - Pixel 8 Pro cryptographic link & remote unlock)
  programs.kdeconnect.enable = true;

  # Smartcard & YubiKey 5C NFC Infrastructure
  services.pcscd.enable = true;
  services.udev.packages = with pkgs; [
    yubikey-personalization
    libfido2
  ];

  # Passwordless FIDO2 / U2F PAM Authentication (Option D + YubiKey 5C NFC)
  security.pam.u2f = {
    enable = true;
    control = "sufficient";
    settings = {
      cue = true;
      cue_prompt = "🔑 Tap YubiKey 5C NFC or approve on Pixel 8 Pro...";
      authfile = "/etc/u2f_keys";
    };
  };

  
  # Strict Passwordless PAM Authentication & Root Access Guard (Titan M2 + YubiKey 5C NFC)
  # Disables unix shadow password authentication; hardware or mesh approval strictly required for both desktop and root!
  security.pam.services = let
    meshAuthRule = {
      order = 10950;
      control = "sufficient";
      modulePath = "${pkgs.linux-pam}/lib/security/pam_exec.so";
      settings = {
        quiet = false;
      };
      args = [ "/var/lib/tianxia/bin/tx-pam-mesh-verify" ];
    };
  in {
    kde = {
      unixAuth = false;
      rules.auth.meshAuth = meshAuthRule;
    };
    sudo = {
      unixAuth = false;
      rules.auth.meshAuth = meshAuthRule;
    };
    su = {
      unixAuth = false;
      rules.auth.meshAuth = meshAuthRule;
    };
    polkit-1 = {
      unixAuth = false;
      rules.auth.meshAuth = meshAuthRule;
    };
    login = {
      unixAuth = false;
      rules.auth.meshAuth = meshAuthRule;
    };
  };

  # 1000Hz (1ms) USB Polling Rate for Ultra-Low Latency Mouse Tracking
  boot.kernelParams = [ "usbhid.mousepoll=1" ];

  # Redragon Griffin Ultra M602U-KS Hardware Database Entry
  services.udev.extraHwdb = ''
    # Redragon Griffin Ultra M602U-KS Gaming Mouse (1a2c:8fff)
    mouse:usb:v1a2cp8fff:*
     MOUSE_DPI=800@1000 1200@1000 1600@1000 2400@1000 7200@1000
     MOUSE_WHEEL_CLICK_ANGLE=15
     MOUSE_WHEEL_CLICK_COUNT=24
  '';

  # System-wide Input Profiles: Redragon M602U-KS, Logitech Lightspeed, and Dell Latitude 5591 ALPS DualPoint
  environment.etc."xdg/kcminputrc".text = lib.mkForce ''
    [Mouse]
    AccelerationProfile=flat
    PointerAcceleration=0.0
    PointerAccelerationProfile=1
    NaturalScroll=false
    ScrollFactor=1.0
    MiddleButtonEmulation=false

    [Libinput][6700][36863][Shinetek Technology USB Composite Device]
    Enabled=true
    LeftHanded=false
    MiddleButtonEmulation=false
    NaturalScroll=false
    PointerAcceleration=0.000
    PointerAccelerationProfile=1
    ScrollFactor=1.0

    [Libinput][1133][50493][Logitech USB Receiver Mouse]
    Enabled=true
    LeftHanded=false
    MiddleButtonEmulation=false
    NaturalScroll=false
    PointerAcceleration=0.000
    PointerAccelerationProfile=1
    ScrollFactor=1.0

    [Libinput][1102][4639][DELL0819:00 044E:121F Touchpad]
    ClickMethod=2
    DisableEventsOnExternalMouse=false
    DisableWhileTyping=true
    Enabled=true
    LeftHanded=false
    LmrTapButtonMap=false
    MiddleButtonEmulation=true
    NaturalScroll=true
    PointerAcceleration=0.200
    PointerAccelerationProfile=2
    ScrollFactor=1.0
    ScrollMethod=1
    TapAndDrag=true
    TapDragLock=false
    TapToClick=true

    [Libinput][1102][4639][DELL0819:00 044E:121F Mouse]
    Enabled=true
    LeftHanded=false
    MiddleButtonEmulation=true
    NaturalScroll=false
    PointerAcceleration=0.200
    PointerAccelerationProfile=2
    ScrollButton=274
    ScrollFactor=1.0
    ScrollMethod=4
  '';

  # Bind KWin Wayland directly to Intel UHD 630 on card1
  environment.sessionVariables = {
    KWIN_DRM_DEVICES = "/dev/dri/card1";
  };

  # Declarative symlinks, directories, and permissions
  systemd.tmpfiles.rules = [
    "L+ /var/lib/tianxia/bin/python3 - - - - ${txPython}/bin/python3"
    "d /var/lib/tianxia 0755 root root -"
    "d /var/lib/tianxia/bin 0755 root root -"
    "d /var/lib/tianxia/share 0755 root root -"
    "d /var/lib/tianxia/share/applications 0755 root root -"
    "d /var/lib/tianxia/share/desktop-directories 0755 root root -"
    "d /var/lib/tianxia/registry 0755 root root -"
    "Z /var/lib/tianxia/bin 0755 root root -"
    "Z /var/lib/tianxia/share 0755 root root -"
  ];

  environment.etc."xdg/foot/foot.ini".text = lib.mkForce ''
    [main]
    font=JetBrains Mono:size=11
    pad=12x12

    [colors-dark]
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

  # Disable conflicting headless Sway cockpit service on DRM card1
  systemd.services.tianxia-cockpit.enable = lib.mkForce false;

  # Eliminate DrKonqi coredump fork bombs & Baloo indexer loops
  systemd.coredump.enable = false;
  systemd.services."drkonqi-coredump-processor@".enable = false;
  systemd.user.services."drkonqi-coredump-launcher@".enable = false;
  systemd.user.services."kde-baloo".enable = false;

  
  # TianxiaOS Sovereign Mesh Auth Daemon (Titan M2 Validator)
  systemd.services.tianxia-mesh-auth = {
    description = "TianxiaOS Sovereign Mesh Authentication & Titan M2 Validator Daemon";
    wantedBy = [ "multi-user.target" ];
    after = [ "network.target" "tailscaled.service" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "/var/lib/tianxia/bin/tx-mesh-auth-receiver";
      Restart = "always";
      RestartSec = "2s";
      LimitNOFILE = 65536;
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };

  # Wakeup and Input Device Persistence
  services.udev.extraRules = lib.mkAfter ''
    # Enable wakeup for all USB root hubs, host controllers, and USB devices (keyboards, mice, YubiKeys)
    ACTION=="add", SUBSYSTEM=="usb", ATTR{power/wakeup}="enabled"
    # Enable wakeup for all input devices (touchpad, keyboard, external mouse)
    ACTION=="add", SUBSYSTEM=="input", ATTR{power/wakeup}="enabled"
    # Enable wakeup for serio and platform devices (i8042 keyboard / touchpad)
    ACTION=="add", SUBSYSTEM=="serio", ATTR{power/wakeup}="enabled"
    ACTION=="add", SUBSYSTEM=="platform", KERNEL=="i8042", ATTR{power/wakeup}="enabled"
    ACTION=="add", SUBSYSTEM=="i2c", ATTR{power/wakeup}="enabled"
    ACTION=="add", SUBSYSTEM=="pci", DRIVER=="xhci_hcd", ATTR{power/wakeup}="enabled"
    # Grant video-group control over screen & keyboard backlights on add/change (never override user brightness!)
    ACTION=="add|change", SUBSYSTEM=="backlight", RUN+="${pkgs.coreutils}/bin/chgrp video /sys/class/backlight/%k/brightness", RUN+="${pkgs.coreutils}/bin/chmod 0664 /sys/class/backlight/%k/brightness"
    ACTION=="add|change", SUBSYSTEM=="leds", KERNEL=="*kbd_backlight", RUN+="${pkgs.coreutils}/bin/chgrp video /sys/class/leds/%k/brightness", RUN+="${pkgs.coreutils}/bin/chmod 0664 /sys/class/leds/%k/brightness"
  '';

  # Persistent Wakeup and Unblank Safeguard on boot and post-resume (preserves non-zero user brightness)
  systemd.services.tianxia-power-wakeup = {
    description = "Tianxia Persistent Wakeup and Display Unblank Safeguard";
    wantedBy = [ "multi-user.target" "post-resume.target" ];
    after = [ "systemd-udev-settle.service" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${pkgs.bash}/bin/bash -c 'for w in /sys/bus/usb/devices/*/power/wakeup /sys/class/input/input*/device/power/wakeup /sys/bus/i2c/devices/*/power/wakeup /sys/devices/platform/i8042/power/wakeup; do [ -f \"$w\" ] && echo enabled > \"$w\" 2>/dev/null || true; done; if [ -f /sys/class/backlight/intel_backlight/brightness ]; then echo 0 > /sys/class/backlight/intel_backlight/bl_power 2>/dev/null || true; cur=$(cat /sys/class/backlight/intel_backlight/brightness 2>/dev/null || echo 0); max=$(cat /sys/class/backlight/intel_backlight/max_brightness 2>/dev/null || echo 120000); if [ \"\${cur:-0}\" -le 0 ]; then echo $(( max * 80 / 100 )) > /sys/class/backlight/intel_backlight/brightness 2>/dev/null || true; fi; fi'";
    };
  };

  # Systemd Logind Power Management (longer wake times, no aggressive sleep on AC)
  services.logind = {
    settings.Login = {
      HandleLidSwitch = "ignore";
      HandleLidSwitchExternalPower = "ignore";
      HandlePowerKey = "suspend";
      HandleSuspendKey = "suspend";
      IdleAction = "ignore";
    };
  };

  # System-wide XDG Defaults for KDE PowerDevil & ScreenLocker (AC plugged-in persistence)
  environment.etc."xdg/powerdevilrc".text = lib.mkForce ''
    [AC][Display]
    dimDisplayWhenIdle=false
    dimDisplayIdleTimeoutSec=7200
    turnOffDisplayWhenIdle=false
    turnOffDisplayIdleTimeoutSec=14400

    [AC][SuspendAndShutdown]
    autoSuspendAction=0
    autoSuspendIdleTimeoutSec=14400
    lidAction=0
    powerButtonAction=1
    sleepAction=1

    [Battery][Display]
    dimDisplayWhenIdle=true
    dimDisplayIdleTimeoutSec=300
    turnOffDisplayWhenIdle=true
    turnOffDisplayIdleTimeoutSec=600

    [Battery][SuspendAndShutdown]
    autoSuspendAction=1
    autoSuspendIdleTimeoutSec=1800
    lidAction=1
    powerButtonAction=1
    sleepAction=1

    [General]
    pausePlayersOnSuspend=true
  '';

  environment.etc."xdg/kscreenlockerrc".text = lib.mkForce ''
    [Daemon]
    Autolock=false
    LockOnResume=false
    Timeout=120
  '';

  environment.extraInit = ''
    export XDG_DATA_DIRS="/var/lib/tianxia/share:''${XDG_DATA_DIRS:-/run/current-system/sw/share}"
  '';
}
