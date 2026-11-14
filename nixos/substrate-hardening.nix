# ffp: TX-SUBSTRATE-HARDENING declarative nix
{ config, pkgs, ... }:
{
  systemd.services.tianxia-inference.serviceConfig = {
    ProtectSystem = "strict";
    ProtectHome = true;
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectKernelModules = true;
    ProtectControlGroups = true;
    NoNewPrivileges = true;
    RestrictRealtime = true;
    RestrictSUIDSGID = true;
    ReadWritePaths = [ "/var/lib/tianxia" "/run/tianxia" ];
  };

  systemd.services.tianxia-timesfm.serviceConfig = {
    ProtectSystem = "strict";
    ProtectHome = true;
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectKernelModules = true;
    NoNewPrivileges = true;
    ReadWritePaths = [ "/var/lib/tianxia" "/run/tianxia" ];
  };

  systemd.services.tianxia-kokoro.serviceConfig = {
    ProtectSystem = "strict";
    ProtectHome = true;
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectKernelModules = true;
    NoNewPrivileges = true;
    ReadWritePaths = [ "/var/lib/tianxia" "/run/tianxia" ];
  };

  systemd.services.tianxia-uds-gateway.serviceConfig = {
    ProtectSystem = "strict";
    ProtectHome = true;
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectKernelModules = true;
    NoNewPrivileges = true;
    ReadWritePaths = [ "/var/lib/tianxia" "/run/tianxia" ];
  };
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
