# ffp: FFP-NIX-PQ-ROSENPASS declarative nix
{ config, lib, pkgs, ... }:
let
  cfg = config.services.tianxia-rosenpass;
in {
  # Unconditional. See the header note: an enable flag that defaults to off is
  # a silent no-op waiting to happen.
  options.services.tianxia-rosenpass = {
    rpDir = lib.mkOption { type = lib.types.str; default = "/etc/rosenpass"; };
    livePsk = lib.mkOption { type = lib.types.str; default = "/etc/rosenpass/psk-hub-relay.live"; };
    applyEnv = lib.mkOption { type = lib.types.str; default = "/etc/rosenpass/apply.env"; };
    applyScript = lib.mkOption { type = lib.types.str; default = "/usr/local/bin/tx-rosenpass-apply.sh"; };
    # Deliberately a literal path, NOT ${pkgs.rosenpass}. Referencing a package
    # attribute that may not exist in the pinned nixpkgs would fail evaluation of
    # the WHOLE system, not just this service. Set this to the nixpkgs path once
    # you have confirmed the attribute exists.
    rosenpassBin = lib.mkOption { type = lib.types.str; default = "/usr/local/bin/rosenpass"; };
    listen = lib.mkOption { type = lib.types.str; default = "0.0.0.0:10001"; };
    # The hub is NAT-bound and can only dial out, so the peer endpoint must be
    # the relay's PUBLIC address, not its mesh address.
    peerEndpoint = lib.mkOption { type = lib.types.str; default = "<TX_RELAY_IPV4>:10001"; };
  };

  config = {
    # NixOS gives unit files a minimal PATH (coreutils, findutils, grep, sed,
    # systemd) that does NOT include wireguard-tools. Without this the apply hook
    # exits 127 with "wg: command not found" and the PSK is never applied.
    environment.systemPackages = [ pkgs.wireguard-tools ];

    # rosenpass derives the SAME key on both ends, so both persist it and both
    # reload it on boot. hub-relay.psk stays the static bootstrap that
    # networking.wireguard reads; rotations land in livePsk and the path unit
    # applies them without an interface restart.
    #
    # --outfile deliberately does NOT point at hub-relay.psk: a
    # truncate-then-write could let a rebuild or the kernel read a half-written
    # key, which would take the tunnel down for a reason that looks unrelated.
    systemd.services.tianxia-rosenpass = {
      description = "Rosenpass key exchange for the Tianxia mesh (hub)";
      after = [ "network-online.target" ];
      wants = [ "network-online.target" ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        # rosenpass 0.2.3 takes TOKEN-VALUE pairs, not --flags. Verified with
        # rosenpass exchange --help. The flag form (--key/--listen/--outfile)
        # parses as an unknown option and the daemon exits immediately, which
        # systemd reports as a failed unit with no useful message.
        ExecStart = lib.concatStringsSep " " [
          "${cfg.rosenpassBin}" "exchange"
          "public-key" "${cfg.rpDir}/hub.rp.pub"
          "secret-key" "${cfg.rpDir}/hub.rp.sec"
          "listen" "${cfg.listen}"
          "peer"
          "public-key" "${cfg.rpDir}/relay.rp.pub"
          "endpoint" "${cfg.peerEndpoint}"
          "outfile" "${cfg.livePsk}"
        ];
        Restart = "on-failure";
        RestartSec = 5;
        ProtectSystem = "strict";
        ReadWritePaths = [ cfg.rpDir "/var/lib/rosenpass" ];
      };
    };

    systemd.paths.tianxia-psk-apply = {
      wantedBy = [ "multi-user.target" ];
      pathConfig = {
        PathChanged = cfg.livePsk;
        Unit = "tianxia-psk-apply.service";
      };
    };

    systemd.services.tianxia-psk-apply = {
      description = "Apply Rosenpass-rotated PSK to wg0";
      wantedBy = [ ];
      path = [ pkgs.wireguard-tools pkgs.coreutils pkgs.gnugrep pkgs.util-linux ];
      serviceConfig = {
        Type = "oneshot";
        EnvironmentFile = cfg.applyEnv;
        ExecStart = cfg.applyScript;
        CapabilityBoundingSet = "CAP_NET_ADMIN";
        NoNewPrivileges = true;
      };
    };
  };
}
