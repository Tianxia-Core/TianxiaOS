# ffp: TX-SECENHAN-HARDENING declarative nix
# Generated from etc/secenhan_report.json (tx_pari_secenhan.py) 2026-09-26.
# Tier A: full armor. Tier B: full + /root read-only. Tier C (net/etc writers): skipped.
{ config, lib, ... }:
{
  systemd.services = {
  "tx-apex" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = true;
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tx-catalog" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = true;
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tx-model-mimo" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = true;
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tx-model-qwen38" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = true;
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tx-ui" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = true;
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-alert-bridge" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-alert-nats-bridge" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-alert-sentinel" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-amdi-hub" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-auto-remediator" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-autodoc-agent" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-autonomy" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-bge" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-clip-sync" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-cockpit" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-compute-worker" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-drop-forwarder" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-dss-ratchet" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-echo-responder" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-etamanga" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-flash-scan" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-gui-bridge" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-hussar-patrol" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-ireb-sync" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-lady-naga-4b" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-lan-mouse" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-leader-elector" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-lfm" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-mesh-failover" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-minicpm" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-net-bridge" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-pluginus-4b" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-prometheus-exporter" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-qwen-dl" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-rgo-allocator" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-rgu-dispatcher" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-rpc-broker" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-rpc-tunnel" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-study-trap" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-telegram-herald" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-telemetry-receiver" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-telemetry-sink" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-telemetry" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-thermal-broadcaster" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-thermal-mitigation" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-uncensored" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-unikernel-worker" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-vector-cache" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-vibe" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-watchdog" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-worker-autoscaler" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-workqueue-exporter" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-x402-bridge" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tianxia-x402-gateway" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tx-model-gateway" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  "tx-rosenpass" = { serviceConfig = {
    NoNewPrivileges = true;
    ProtectSystem = "full";
    ProtectHome = "read-only";
    PrivateTmp = true;
    ProtectKernelTunables = true;
    ProtectControlGroups = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
  }; };
  };
}
