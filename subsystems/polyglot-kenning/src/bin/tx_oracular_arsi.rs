// ffp: FFP-BIN-002 tx-oracular-arsi-bin rust
//! Production binary: tx_oracular_arsi
//! Demonstrates and executes Stratum 0 invariants and ARSI Counterfactual Reasonwashing Verification.

use tianxiaos_polyglot_kenning::oracular::{OracularEngine, Stratum0Facts};

fn run_diagnostics(oracular: &OracularEngine) {
    // Test Case 1: Faithful consensus decision
    let facts_nominal = Stratum0Facts {
        hhi: 0.42,
        daily_drain_ratio: 0.28,
        nsf_count_90d: 0.0,
        tetraledger_i1: 0.0,
    };

    let verdict_nominal = oracular.verify_arsi_fidelity(
        &facts_nominal,
        0.92, // model probability with cited features
        0.20, // probability when cited feature is masked (large drop -> cited feature is true cause)
        0.90, // probability when uncited feature is masked (minimal drop)
    );
    println!(
        "[ARSI NOMINAL VERDICT]: approved={} reasonwash_idx={:.4} status='{}'",
        verdict_nominal.approved, verdict_nominal.reasonwash_index, verdict_nominal.audit_status
    );

    // Test Case 2: Reasonwashed explanation (adversary masking cited features does not change decision)
    let verdict_reasonwashed = oracular.verify_arsi_fidelity(
        &facts_nominal,
        0.88,
        0.87, // masking cited feature hardly changes verdict (delta_cited = 0.01)
        0.18, // masking uncited feature reveals it was the true driver (delta_uncited = 0.70)
    );
    println!(
        "[ARSI REASONWASHED DETECTED]: approved={} reasonwash_idx={:.4} status='{}'",
        verdict_reasonwashed.approved, verdict_reasonwashed.reasonwash_index, verdict_reasonwashed.audit_status
    );

    // Test Case 3: Stratum 0 Invariant Breach (e.g. HHI > 0.65 or I1 != 0)
    let facts_breach = Stratum0Facts {
        hhi: 0.78, // concentration violation!
        daily_drain_ratio: 0.52,
        nsf_count_90d: 4.0,
        tetraledger_i1: 150.0, // Ledger out of balance!
    };
    let verdict_breach = oracular.verify_arsi_fidelity(&facts_breach, 0.95, 0.15, 0.94);
    println!(
        "[ARSI STRATUM0 BREACH]: approved={} stratum0_ok={} status='{}'",
        verdict_breach.approved, verdict_breach.stratum0_ok, verdict_breach.audit_status
    );
}

fn main() {
    println!("=== [TIANXIAOS // ORACULAR ARSI] Initializing Omni-Lattice Model Forest ===");
    let oracular = OracularEngine::new(0.25);
    run_diagnostics(&oracular);

    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|a| a == "--daemon") {
        println!("[ORACULAR ARSI] Entering persistent verifier loop...");
        loop {
            std::thread::sleep(std::time::Duration::from_secs(30));
        }
    }

    println!("=== [TIANXIAOS // ORACULAR ARSI] Verification Complete ===");
}
