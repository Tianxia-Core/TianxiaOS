# ffp: TX-TIANXIA-SDR-CLIENT declarative nix
{ config, lib, pkgs, ... }:

{
  # The SDR CLIENT: one owner for the dongle, many consumers.
  #
  # A single RTL2832U cannot be opened by several programs at once, and the
  # hub had three claimants (adsb-dump claimed the device DIRECTLY, rtl-tcp
  # wanted it as the shared IQ server, and the RF sweep "borrowed" it back and
  # forth) -- so they raced and crashed each other. tx_sdr_client.py is the
  # arbiter: rtl_tcp owns the device and every decoder attaches to the IQ
  # stream over rtl_tcp. The decoder set was chosen by scour
  # (tx_scour github topic:rtlsdr) and checked against nixpkgs.
  systemd.services.tx-sdr-client = {
    description = "Tianxia SDR client (one owner of the dongle, many decoders)";
    after = [ "network.target" "rtl-tcp.service" ];
    wants = [ "rtl-tcp.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_sdr_client.py --serve";
      Restart = "on-failure";
      RestartSec = "10s";
      # The arbiter binds /run/tianxia/sdr-control.sock for the device
      # handover (the band sweep asks for the device instead of racing it).
      RuntimeDirectory = "tianxia";
      WorkingDirectory = "/var/lib/tianxia";
      StandardOutput = "journal";
      StandardError = "journal";
    };
  };
}
