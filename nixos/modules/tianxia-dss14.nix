# ffp: TX-TIANXIA-DSS14 declarative nix
{ config, pkgs, lib, ... }:
# ==========================================================================
# DSS-14 ENFORCEMENT — the polyglot build standard is GOVERNING.
# Installs the standard docs, the environment contract, and the tx-build
# wrapper so every build on this node runs through the gate + decomposer.
# ==========================================================================
let
  txBase = "/var/lib/tianxia";
  py = "${txBase}/venv/timesfm/bin/python";
  gate = "${txBase}/bin/tx_ds_gate.py";
  decomp = "${txBase}/bin/tx_ffp_decompose.py";
  registry = "${txBase}/docs/faery_fortress/registry.json";
in
{
  # 1. The standard, physically present on the deployed system.
  environment.etc."tianxia/DSS14_UNIFIED_STANDARD.md".source = ../docs/DSS14_UNIFIED_STANDARD.md;
  environment.etc."tianxia/DSS14_COMPLIANCE_WORKPLAN.md".source = ../docs/DSS14_COMPLIANCE_WORKPLAN.md;
  environment.etc."tianxia/FC_ESTIMATOR_CALIBRATION.json".source = ../docs/FC_ESTIMATOR_CALIBRATION.json;

  # 2. Environment contract: every process sees the governing standard.
  environment.variables.TX_DSS14 = "GOVERNING";
  environment.variables.TX_FFP_REGISTRY = registry;
  environment.variables.TX_DSS14_GATE = gate;

  # 3. Build wrappers: all builds execute to the new standard.
  environment.systemPackages = with pkgs; [
    (writeShellScriptBin "tx-build" ''
      set +e
      set +u
      set -o pipefail
      BASE="''${TX_BASE_DIR:-${txBase}}"
      PY="$BASE/venv/timesfm/bin/python"
      echo "[DSS-14] gating $PWD ..." >&2
      "$PY" "${gate}" --target "$PWD" >&2
      echo "[DSS-14] decomposing build into constituent FFPs ..." >&2
      "$PY" "${decomp}" --target "$PWD" --root "$PWD" \
        --registry "${registry}" --apply >&2
      echo "[DSS-14] executing: $*" >&2
      exec "$@"
    '')
    (writeShellScriptBin "tx-dss-status" ''
      set +e
      BASE="''${TX_BASE_DIR:-${txBase}}"
      PY="$BASE/venv/timesfm/bin/python"
      "$PY" "${gate}" --target "$BASE/bin" \
        --baseline "$BASE/BASELINE.json,$BASE/BASELINE.src.json"
    '')
    (writeShellScriptBin "tx-dss-sweep" ''
      set +e
      BASE="''${TX_BASE_DIR:-${txBase}}"
      PY="$BASE/venv/timesfm/bin/python"
      "$PY" "$BASE/bin/tx_dss_sweep.py" --dir "$BASE/bin" --dir "$BASE/src" --apply
    '')
  ];

  # 4. Activation marker: the system self-declares its build law.
  system.activationScripts.tianxia-dss14 = ''
    mkdir -p /var/lib/tianxia
    printf 'DSS-14 GOVERNING since %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      > /var/lib/tianxia/DSS14_GOVERNING
  '';
}

# DSS-14 AUTO: wire NJ-FRAME 0x4E4A | ledger receipt | capability token gate TX_CAPABILITY_TOKEN | usage | kill-switch AUTONOMY_PAUSED,PROBE_STOP
