{ pkgs, lib, ... }: {
  # 1. Udev rules for RTL2832U devices (RTL-SDR v3/v4 / generic)
  #
  #    NOTE: no SYSTEMD_WANTS=rtl-tcp.service here any more. The SDR CLIENT
  #    (tx_sdr_client.py) owns the dongle and starts its own IQ server when
  #    the device appears; the old rule started a second claimant on plug-in,
  #    which took the device away from the arbiter (usb_claim_interface
  #    error -6) and left the stack "running but decoding nothing".
  services.udev.extraRules = ''
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", MODE="0666", SYMLINK+="rtl_sdr", TAG+="systemd"
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2832", MODE="0666", SYMLINK+="rtl_sdr", TAG+="systemd"
  '';

  # 2. Bind rtl-tcp strictly to physical device presence
  systemd.services.rtl-tcp = {
    # Eradicate multi-user target dependency so it never starts without hardware
    wantedBy = lib.mkForce [ ];

    unitConfig = {
      ConditionPathExists = "/dev/rtl_sdr";
      StopWhenUnneeded = true;
    };

    bindsTo = [ "dev-rtl_sdr.device" ];
    after = [ "dev-rtl_sdr.device" ];

    serviceConfig = {
      Restart = lib.mkForce "no";
    };
  };
}
