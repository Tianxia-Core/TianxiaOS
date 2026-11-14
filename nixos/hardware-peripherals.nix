# ffp: TX-HARDWARE-PERIPHERALS declarative nix
{ config, lib, pkgs, ... }:

{
  # 1. RTL-SDR: Enables udev rules & blacklists blocking DVB kernel modules
  hardware.rtl-sdr.enable = true;

  # Blacklist TV tuner modules explicitly to prevent kernel lockup
  boot.blacklistedKernelModules = [
    "dvb_usb_rtl28xxu"
    "rtl2832"
    "rtl2830"
    "r820t"
  ];

  # 2. Add SDR, Audio & Video packages (using canonical rtl-sdr package)
  environment.systemPackages = with pkgs; [
    rtl-sdr
    v4l-utils
    alsa-utils
    pavucontrol
    usbutils
    soapysdr-with-plugins

    # ── the FULL-FEATURED SDR CLIENT STACK (2026-10-22) ────────────────────
    # One dongle, many consumers. The set was CHOSEN BY SCOUR, not by memory:
    # `tx_scour github` topic:rtlsdr + "rtl-sdr spectrum radio receiver" and
    # then checked against nixpkgs availability. What the scour surfaced and
    # what each piece adds:
    #   readsb        ADS-B decoder + web UI (supersedes dump1090; 1939* tar1090
    #                 is the same lineage)                      -> aviation
    #   rtl_433       433/868 MHz ISM sensors (weather stations, remotes,
    #                 doorbells, TPMS)                          -> the "sensors" panel
    #   rtl_ais       maritime AIS                               -> ship traffic
    #   rtlamr        AMR / cellular voice decoding             -> a new radio class
    #   rtl_fm_streamer  FM broadcast streaming                -> the radio panel
    #   gnss-sdr      software-defined GNSS (GPS from the dongle)-> position fix
    #   csdr          signal decoding                           -> misc decoders
    #   multimon-ng   ADS-B + POCSAG/AFSK from the shared IQ stream -> aviation
    #                 (readsb is the better decoder but needs the RAW device,
    #                  so it would re-create the contention this removes)
    #   kalibrate-rtl  RTL433 decoder calibration                -> better sensors
    #   (sdrplay is DROPPED: its nixpkgs derivation downloads an upstream
    #    .run that now 404s. The multi-vendor path is already covered by
    #    SoapySDR's airspy/bladerf/hackrf plugins, which are installed.)
    #   prometheus-rtl_433-exporter  sensor metrics             -> the existing
    #                                                             prometheus stack
    # The heavy GUIs (gqrx / sdrangel / gnuradio) are deliberately NOT here:
    # they pull a multi-GB GNU Radio build for a windowed console the cockpit
    # does not need -- the cockpit consumes the DECODERS over rtl_tcp instead.
    readsb
    rtl_433
    rtl-ais
    rtlamr
    rtl_fm_streamer
    gnss-sdr
    csdr
    multimon-ng
    kalibrate-rtl
    prometheus-rtl_433-exporter
  ];

  # 3. Ensure root user has access to peripheral device nodes
  users.users.root.extraGroups = [ "video" "audio" "plugdev" ];
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
