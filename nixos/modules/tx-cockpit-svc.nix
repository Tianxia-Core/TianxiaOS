# ffp: TX-COCKPIT-SVC declarative nix
# Tianxia cockpit: static PWA + same-origin status API on :8081.
#
# Replaces the plain `python -m http.server` with tx_cockpit_api.py, which serves
# the same ui/ directory and additionally exposes /api/{status,spectrum,adsb,
# models,mesh}. Doing the aggregation server-side means the PWA never makes a
# cross-origin request to the model gateway (:8790), which sends no CORS headers.
{ config, lib, pkgs, ... }:
{
  systemd.services.tx-cockpit = {
    description = "Tianxia cockpit PWA + status API (:8081)";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    wantedBy = [ "multi-user.target" ];
    # systemd puts startLimit* in [Unit], not [Service]; setting it under
    # serviceConfig logs "Unknown key name ... ignoring" at every rebuild.
    startLimitIntervalSec = 900;
    serviceConfig = {
      Type = "simple";
      Restart = "on-failure";
      RestartSec = "10";
      StartLimitBurst = 5;
      WorkingDirectory = "/var/lib/tianxia";
      Environment = [
        # TX_COCKPIT_HOST / TX_GATEWAY_URL are deliberately UNSET: the mesh
        # IP changes on a tailnet re-key, and a pinned stale address makes
        # the API bind a phantom address that every client times out on
        # (net.ipv4.ip_nonlocal_bind=1 lets the bind succeed). The API
        # resolves the current tailnet address at start-up instead.
        "TX_COCKPIT_PORT=8081"
        "TX_COCKPIT_UI=/var/lib/tianxia/ui"
      ];
      ExecStart = "${pkgs.python3}/bin/python3 /var/lib/tianxia/bin/tx_cockpit_api.py";
    };
  };
}