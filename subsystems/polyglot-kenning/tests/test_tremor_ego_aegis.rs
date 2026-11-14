// ffp: FFP-TST-005 test-tremor-ego-aegis rust

use tianxiaos_polyglot_kenning::resilience::{
    Aegis9SecurityController, EgoGraphOptimizer, TremorDampingEngine,
};

#[test]
fn test_tremor_shock_damping() {
    let tremor = TremorDampingEngine::default();
    let res = tremor.compute_damping_response(50.0, 0.01);

    // Damping backpressure must oppose host shock acceleration
    assert!(res.synthetic_backpressure_wave > 0.0);
    assert_eq!(res.host_shock_accel, 50.0);
    assert!(res.dissipated_energy_ratio > 0.0);
}

#[test]
fn test_ego_pruning_decision() {
    let ego = EgoGraphOptimizer::default();

    let high_eff = ego.evaluate_node("GoodNode", 5.0, 0.01, 2.0);
    assert!(!high_eff.should_prune);
    assert!(high_eff.memoized_kenning_key.is_none());

    let bloat = ego.evaluate_node("BloatNode", 0.01, 1.0, 500.0);
    assert!(bloat.should_prune);
    assert!(bloat.memoized_kenning_key.is_some());
}

#[test]
fn test_aegis9_concentric_audit() {
    let aegis = Aegis9SecurityController::default();
    let audit = aegis.audit_all_rings();

    assert_eq!(audit.rings.len(), 9);
    assert!(audit.overall_enclave_secure);
    assert!(audit.compromised_ring.is_none());
}
