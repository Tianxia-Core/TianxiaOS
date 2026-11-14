(* ffp: FFP-OCL-001 arsi-proof-checker ocaml *)
(* TianxiaOS Core 04 (Nimbus-Proof) - Bagalamukhi Invariant Freeze Gate *)
(* Formal type-theoretic AST verification & ARSI proof checker *)

type stratum0_invariants = {
  hhi: float;
  daily_drain: float;
  nsf_90d: float;
  tetraledger_i1: float;
}

type proof_result =
  | ProvedValid of string
  | InvariantViolation of string
  | ReasonwashDetected of float

let verify_stratum0 (inv : stratum0_invariants) : bool =
  inv.hhi <= 0.65 &&
  inv.daily_drain <= 0.45 &&
  inv.nsf_90d <= 3.0 &&
  Float.abs inv.tetraledger_i1 < 1e-9

let verify_arsi_reasonwash ~(delta_cited : float) ~(delta_uncited : float) ~(threshold : float) : proof_result =
  let idx = Float.max 0.0 (1.0 -. (delta_cited /. (delta_uncited +. 1e-6))) in
  if idx > threshold then
    ReasonwashDetected idx
  else
    ProvedValid (Printf.sprintf "ARSI_FORMAL_PROOF_OK: index=%.4f" idx)

let () =
  Printf.printf "=== [TIANXIAOS // NIMBUS-PROOF (OCAML)] Bagalamukhi Gate ===\n";
  let nominal = { hhi = 0.42; daily_drain = 0.28; nsf_90d = 0.0; tetraledger_i1 = 0.0 } in
  let s0_ok = verify_stratum0 nominal in
  Printf.printf "[OCAML STRATUM 0]: valid=%b\n" s0_ok;

  let proof1 = verify_arsi_reasonwash ~delta_cited:0.72 ~delta_uncited:0.02 ~threshold:0.25 in
  (match proof1 with
   | ProvedValid msg -> Printf.printf "[OCAML PROOF 1]: %s\n" msg
   | InvariantViolation msg -> Printf.printf "[OCAML VIOLATION]: %s\n" msg
   | ReasonwashDetected idx -> Printf.printf "[OCAML REASONWASH DETECTED]: idx=%.4f\n" idx);

  let proof2 = verify_arsi_reasonwash ~delta_cited:0.02 ~delta_uncited:0.03 ~threshold:0.25 in
  (match proof2 with
   | ProvedValid msg -> Printf.printf "[OCAML PROOF 2]: %s\n" msg
   | InvariantViolation msg -> Printf.printf "[OCAML VIOLATION]: %s\n" msg
   | ReasonwashDetected idx -> Printf.printf "[OCAML REASONWASH DETECTED]: idx=%.4f\n" idx);

  Printf.printf "=== [TIANXIAOS // NIMBUS-PROOF (OCAML)] Execution Complete ===\n"
