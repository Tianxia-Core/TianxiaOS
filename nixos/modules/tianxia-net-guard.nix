# ffp: TX-NET-GUARD declarative nix
# Persist the mesh self-protection guard + home-network attestation.
#
# WHY THE `path` AND THE ABSOLUTE INTERPRETER MATTER
#   Both units run shell scripts from /var/lib/tianxia/bin. Two things broke:
#     1. NixOS has no /bin/bash, and the scripts' `#!/usr/bin/env bash` cannot
#        find bash either, because a generated unit's default PATH carries only
#        coreutils/findutils/grep/sed. ExecStart of the script itself therefore
#        failed with 203/EXEC.
#     2. tx_net_attest.sh needs ip/awk/curl/wg. Without them every baseline
#        check reported "skip(unavailable)" and the attestation completed
#        successfully while verifying nothing -- a silent no-op.
#   Declaring `path` and naming bash explicitly fixes both, and keeps the
#   scripts portable for the Termux side (which has a different prefix).
{ pkgs, ... }:
{
  systemd.services.tx-net-safety = {
    description = "Tianxia network self-protection guard";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    path = with pkgs; [ bash iproute2 gawk gnugrep curl ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${pkgs.bash}/bin/bash /var/lib/tianxia/bin/tx_net_safety.sh";
    };
  };
  systemd.timers.tx-net-safety = {
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "90s"; OnUnitActiveSec = "180s"; AccuracySec = "15s"; };
  };
  systemd.services.tx-net-attest = {
    description = "Tianxia home-network attestation";
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    path = with pkgs; [ bash iproute2 gawk curl wireguard-tools tailscale ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${pkgs.bash}/bin/bash /var/lib/tianxia/bin/tx_net_attest.sh";
    };
  };
  systemd.timers.tx-net-attest = {
    wantedBy = [ "timers.target" ];
    timerConfig = { OnBootSec = "60s"; OnUnitActiveSec = "120s"; AccuracySec = "20s"; };
  };
}
