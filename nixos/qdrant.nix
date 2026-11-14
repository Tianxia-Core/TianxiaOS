# ffp: TX-QDRANT declarative nix
#
# Qdrant vector database — written fresh 2026-10-20.
#
# WHY THIS EXISTS
#   The only prior reference was QDRANT_URL pointing at a host that never ran
#   Qdrant, and a Sarva hit pointing at a NixOS module inside
#   Tianxia-Core/tianxia-unbound-os -- a repo that is not public (404 on the
#   GitHub API). So the module could not be reused and had to be written.
#
# WHY THE OFFICIAL BINARY AND NOT nixpkgs#qdrant
#   nixpkgs qdrant 1.18.2 fails to build on this host:
#     error: intrinsic signature mismatch for `llvm.x86.avx512.vpdpbusd.512`
#     error: could not compile `quantization` (lib) due to 1 previous error
#   The `quantization` crate uses AVX-512 intrinsics that the nixpkgs LLVM does
#   not accept. That is an upstream packaging mismatch, not a config problem.
#   The official musl-static release binary avoids compilation entirely.
#
# WHAT IT BACKS
#   1. tx_knowledge.py -- semantic search over the 3502 remote assets, in
#      addition to the existing FTS5 keyword path (both, not either/or).
#   2. The hybrid working memory described in tianxia_ncm_hybridagent_analysis.md:
#      NCM's hierarchical VQ codes and HybridAgent's continuous working memory
#      are vector problems, not keyword problems.
#
# SECURE BY DESIGN
#   - No API key by default: Qdrant is bound to the tailnet only. Access is
#     controlled by the network, not by a shared secret that can leak.
#   - Read-only mode is NOT set, because tx_knowledge needs to write; instead
#     the write path is gated by tx_knowledge's own kill-switch and the
#     capability token, matching every other tianxia mutating surface.
#   - Snapshots are local and never uploaded; a Qdrant snapshot is a copy of
#     the corpus and inherits the corpus's sensitivity.
#   - Journald logging is on, so every mutation is attributable after the fact.
{ config, lib, pkgs, ... }:

let
  # Pinned: v1.19.2, musl x86_64 static. Hash verified with nix-prefetch-url.
  qdrantBin = pkgs.fetchzip {
    url = "https://github.com/qdrant/qdrant/releases/download/v1.19.2/qdrant-x86_64-unknown-linux-musl.tar.gz";
    hash = "sha256-aNx3TX/rdnl6e1+Vzlim9yysdHsxZ9Q0dqFWSZn24h8=";
    stripRoot = false;
  };

  qdrantConfig = pkgs.writeText "qdrant.yaml" ''
    storage:
      storage_path: /var/lib/qdrant/storage
      snapshots_path: /var/lib/qdrant/snapshots
      # Write-ahead log: on, because a vector index that loses accepted writes
      # silently is worse than one that refuses them.
      wal:
        wal_capacity_mb: 256
      performance:
        # Conservative: this box also runs several llama-server instances, the
        # model router, NATS, wayvnc, and (shortly) the NCM service.
        # Oversubscribing optimizer threads starves inference.
        optimizer_cpu_budget: 2
    service:
      # Tailnet reachability is enforced by the firewall rule below; Qdrant
      # itself listens on all interfaces because it cannot bind to a tailnet
      # address that is assigned dynamically.
      host: "0.0.0.0"
      http_port: 6333
      grpc_port: 6334
      # No api_key: access is controlled by the firewall (tailscale0 only).
      # A literal placeholder here would become a real, nonsense required key
      # -- which is exactly what happened on the first attempt. Add a key only
      # deliberately, via an explicit config change.
      # Snapshot upload is off by default: a snapshot is a full copy of the
      # corpus and must not leave the device unattended.
      enable_snapshots_upload: false
    telemetry_disabled: true
  '';
in
{
  # ── service ────────────────────────────────────────────────────────────────
  systemd.services.qdrant = {
    description = "Qdrant vector database (Tianxia knowledge substrate)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    restartIfChanged = true;
    serviceConfig = {
      Type = "simple";
      ExecStart = "${qdrantBin}/qdrant --config-path ${qdrantConfig}";
      Restart = "always";
      RestartSec = 5;
      # Hardening: Qdrant needs its storage dir and nothing else.
      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "strict";
      ProtectHome = true;
      ReadWritePaths = [ "/var/lib/qdrant" ];
      ProtectKernelTunables = true;
      ProtectControlGroups = true;
      RestrictSUIDSGID = true;
      MemoryDenyWriteExecute = true;
    };
  };

  # ── storage ───────────────────────────────────────────────────────────────
  systemd.tmpfiles.rules = [
    "d /var/lib/qdrant 0750 root root -"
    "d /var/lib/qdrant/storage 0750 root root -"
    "d /var/lib/qdrant/snapshots 0750 root root -"
  ];

  # ── firewall ──────────────────────────────────────────────────────────────
  # 6333 is Qdrant's REST port. Opened on the tailnet only; the wg0 mesh that
  # previously carried a similar rule was retired 2026-10-20.
  networking.firewall.interfaces."tailscale0".allowedTCPPorts = [ 6333 ];

  # ── package ───────────────────────────────────────────────────────────────
  environment.systemPackages = [ (pkgs.runCommand "qdrant" { } "mkdir -p $out/bin && cp ${qdrantBin}/qdrant $out/bin/") ];
}
