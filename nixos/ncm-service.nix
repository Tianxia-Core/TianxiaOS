# ffp: TX-NCM-SERVICE declarative nix
#
# NCM (Next-Concept Modeling) inference service.
#
# Source model: HazyResearch/ncm (arXiv:2610.14162). A multiscale residual
# VQ-VAE encodes text into a hierarchy of discrete codes; a transformer
# generates one LEVEL at a time, all codes within a level in parallel.
# One forward pass per level, not per token.
#
# WHY A NIXOS MODULE AND NOT A BARE SCRIPT
#   The service needs LD_LIBRARY_PATH pointing at a stdenv libstdc++ because it
#   runs a pip-installed torch wheel. Hardcoding a /nix/store path is fragile
#   (GC can collect it); pkgs.stdenv.cc.cc.lib is stable and declarative.
#
# WHY NOT programs.nix-ld
#   nix-ld 2.x populates /nix/var/nix/profiles/default/lib via tmpfiles, but on
#   this host that path is a symlink to per-user/root/profile, so the libs never
#   landed. Rather than fight the symlink, the service sets its own
#   LD_LIBRARY_PATH. nix-ld remains enabled for other unpatched binaries.
#
# SECURE BY DESIGN
#   - Binds to the tailnet IP only, resolved at start (never 0.0.0.0).
#   - Kill-switch: AUTONOMY_PAUSED / PROBE_STOP return 503 and are logged.
#   - No capability gate: this is read-only inference. The hybrid model router
#     depends on it being ungated; adding a gate would break routing.
#   - Append-only JSONL ledger records prompt SHA-256, never prompt text.
#   - Single worker: this host runs several llama-server instances, NATS, the
#     model router, wayvnc and Qdrant. Serialising generation prevents
#     inference starvation.
{ config, lib, pkgs, ... }:

let
  ncmVenv = "/var/lib/tianxia/venv/ncm";
  ncmModelDir = "/var/lib/tianxia/models/ncm/xsum";
  ncmCodeDir = "/var/lib/tianxia/src/ncm";
  port = 8091;
in
{
  systemd.services.tianxia-ncm = {
    description = "Tianxia NCM inference service (OpenAI-compatible, CPU)";
    after = [ "network.target" "tailscaled.service" ];
    wantedBy = [ "multi-user.target" ];
    restartIfChanged = true;
    path = [ pkgs.coreutils pkgs.iproute2 config.services.tailscale.package ];
    serviceConfig = {
      Type = "simple";
      # Resolve the tailnet IP at start so the service never binds 0.0.0.0.
      ExecStart = pkgs.writeShellScript "tx-ncm-start" ''
        set -eu
        IP="$(tailscale ip -4 2>/dev/null || echo 127.0.0.1)"
        export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        export TX_BASE_DIR=/var/lib/tianxia
        export TX_NCM_MODEL_DIR=${ncmModelDir}
        export TX_NCM_CODE=${ncmCodeDir}
        export TX_NCM_PORT=${toString port}
        # ProtectHome makes /root read-only; HF/transformers must not try to
        # write its cache there. Point it at the writable tianxia tree.
        export HF_HOME=/var/lib/tianxia/cache/huggingface
        export TRANSFORMERS_CACHE=/var/lib/tianxia/cache/huggingface
        mkdir -p /var/lib/tianxia/cache/huggingface
        exec ${ncmVenv}/bin/python /var/lib/tianxia/bin/tx_ncm_serve.py --host "$IP" --port ${toString port}
      '';
      Restart = "always";
      RestartSec = 10;
      WorkingDirectory = "/var/lib/tianxia";
      # Hardening: the service needs its model dir, venv, and the ledger.
      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "strict";
      ProtectHome = true;
      ReadWritePaths = [ "/var/lib/tianxia" ];
      ProtectKernelTunables = true;
      ProtectControlGroups = true;
      RestrictSUIDSGID = true;
      MemoryDenyWriteExecute = false; # torch JIT needs W+X
      # torch CPU inference is memory-hungry; give it room but cap it.
      MemoryMax = "8G";
    };
  };

  # Firewall: 8091 on the tailnet only. The retired wg0 mesh carried similar
  # rules; tailscale0 is the substrate now.
  networking.firewall.interfaces."tailscale0".allowedTCPPorts = [ port ];
}
