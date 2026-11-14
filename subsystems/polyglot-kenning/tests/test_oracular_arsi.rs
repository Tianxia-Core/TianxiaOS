// ffp: FFP-TST-002 test-oracular-arsi rust

use tianxiaos_polyglot_kenning::oracular::{OracularEngine, Stratum0Facts};

#[test]
fn test_stratum0_facts_validation() {
    let engine = OracularEngine::new(0.25);

    let valid_facts = Stratum0Facts {
        hhi: 0.50,
        daily_drain_ratio: 0.30,
        nsf_count_90d: 1.0,
        tetraledger_i1: 0.0,
    };
    assert!(engine.evaluate_stratum0(&valid_facts));

    let invalid_hhi = Stratum0Facts {
        hhi: 0.75, // > 0.65
        daily_drain_ratio: 0.30,
        nsf_count_90d: 1.0,
        tetraledger_i1: 0.0,
    };
    assert!(!engine.evaluate_stratum0(&invalid_hhi));

    let invalid_drain = Stratum0Facts {
        hhi: 0.50,
        daily_drain_ratio: 0.55, // > 0.45
        nsf_count_90d: 1.0,
        tetraledger_i1: 0.0,
    };
    assert!(!engine.evaluate_stratum0(&invalid_drain));
}

#[test]
fn test_arsi_counterfactual_attribution() {
    let engine = OracularEngine::new(0.25);
    let facts = Stratum0Facts::default();

    // Faithful explanation: Masking cited features causes massive drop (delta_cited >> delta_uncited)
    let verdict_faithful = engine.verify_arsi_fidelity(&facts, 0.90, 0.15, 0.88);
    assert!(verdict_faithful.approved);
    assert!(verdict_faithful.explanation_faithful);
    assert!(verdict_faithful.reasonwash_index <= 0.25);

    // Reasonwashed explanation: Cited features are a pretext.
    // Masking cited feature causes almost no drop (delta_cited = 0.01),
    // while uncited feature was the true driver (delta_uncited = 0.75).
    let verdict_washed = engine.verify_arsi_fidelity(&facts, 0.90, 0.89, 0.15);
    assert!(!verdict_washed.approved);
    assert!(!verdict_washed.explanation_faithful);
    assert!(verdict_washed.reasonwash_index > 0.25);
    assert_eq!(verdict_washed.audit_status, "BLOCKED_ORACULAR_REASONWASHING_DETECTED");
}
