# ffp: TX-EMBED-SERVICE declarative nix
#
# Embedding server for the Tianxia knowledge substrate.
#
# WHY THIS EXISTS
#   Qdrant needs vectors. The previous embedding endpoint was
#   emb06-server.service bound to the wg0 address 10.0.99.2:11495, which the
#   mesh retirement deleted -- so the knowledge index had no embedder.
#   all-minilm-l6-v2.gguf is already on disk (45 MB, 384-dim); this exposes it.
#
# WHY 127.0.0.1 AND NOT THE TAILNET
#   Only Qdrant and tx_knowledge consume it, both on this host. Binding to
#   loopback means the embedding surface is not reachable even from the tailnet,
#   which is strictly tighter than the firewall rule would be.
#
# NOTE ON MODELS
#   bge-reranker-v2-m3 (also on disk) is NOT an embedder -- it returns all-zero
#   vectors through /v1/embeddings. Qwen3-Embedding-0.6B (1024-dim) is available
#   at models/eval/ if higher-quality vectors are wanted later; all-minilm is
#   chosen now because it is 20x smaller and the index is keyword-plus-vector,
#   not vector-only.
{ config, lib, pkgs, ... }:

{
  systemd.services.tianxia-embed = {
    description = "Tianxia embedding server (all-minilm-l6-v2)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    restartIfChanged = true;
    serviceConfig = {
      Type = "simple";
      ExecStart = "${pkgs.llama-cpp}/bin/llama-server -m /var/lib/tianxia/models/all-minilm-l6-v2.gguf --embeddings --pooling mean -c 512 -t 2 --port 8092 --host 127.0.0.1";
      Restart = "always";
      RestartSec = 5;
      NoNewPrivileges = true;
      PrivateTmp = true;
      ProtectSystem = "strict";
      ReadWritePaths = [ "/var/lib/tianxia" ];
    };
  };
}
