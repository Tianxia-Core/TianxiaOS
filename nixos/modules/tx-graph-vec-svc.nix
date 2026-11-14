# ffp: TX-GRAPH-VEC-SVC declarative nix
# Vector-index backend for the memory graph (TX-GRAPH-VEC-SVC).
#
# tx_graph_core targets the sqliteai-vector loadable extension (vector_init /
# vector_quantize / vector_quantize_scan) for quantized kNN over the 1024-dim
# Qwen3-Embedding vectors. The wheel is not in nixpkgs, so it is provisioned
# into a dedicated venv (venv/graph) with uv. tx_graph_core appends that venv's
# site-packages to sys.path, so every bin/ caller gets the extension without
# being forced through the venv interpreter.
#
# Measured effect: vec_search over 13,582 embeddings went from ~1859 ms (exact
# cosine scan) to 53-81 ms (quantized kNN), i.e. a 25-35x speedup.
#
# vector_init + vector_quantize run per-connection inside
# tx_graph_core.connect(); the quantize call keeps the index fresh after every
# embedding write, so this unit only has to guarantee the wheel is importable.
{ config, lib, pkgs, ... }:
{
  systemd.services.tx-graph-vec = {
    description = "sqliteai-vector wheel for tx_graph_core (venv/graph)";
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      WorkingDirectory = "/var/lib/tianxia";
      # Idempotent: create the venv only when missing, then ensure the wheel.
      ExecStart = "${pkgs.runtimeShell} -c 'V=/var/lib/tianxia/venv/graph; [ -x $V/bin/python ] || ${pkgs.uv}/bin/uv venv $V --python 3.14; ${pkgs.uv}/bin/uv pip install --python $V/bin/python sqliteai-vector'";
      # Fail loudly if the extension is not importable: a silent miss degrades
      # every vector search to the O(n) exact scan.
      ExecStartPost = "/var/lib/tianxia/bin/tx_graph_vec_check.sh";
    };
  };
}
