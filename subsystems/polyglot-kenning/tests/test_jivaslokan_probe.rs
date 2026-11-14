// ffp: FFP-TST-003 test-jivaslokan-probe rust

use tianxiaos_polyglot_kenning::jivaslokan::JivaslokanHuberProbe;

#[test]
fn test_jivaslokan_nominal_eval() {
    let probe = JivaslokanHuberProbe::default();

    let safe_centroid = vec![0.1, 0.2, -0.3, 0.4, 0.5];
    let nominal_act = vec![0.11, 0.22, -0.29, 0.38, 0.52];

    let res = probe.evaluate_hidden_state(&nominal_act, &safe_centroid);
    assert!(res.safe);
    assert!(!res.circuit_breaker_tripped);
    assert!(res.weighted_huber_loss < 1.85);
}

#[test]
fn test_jivaslokan_spike_anomaly() {
    let probe = JivaslokanHuberProbe::default();

    let safe_centroid = vec![0.1, 0.2, -0.3, 0.4, 0.5];
    let outlier_act = vec![0.11, 0.22, -0.29, 25.0, 0.52]; // Extreme spike

    let res = probe.evaluate_hidden_state(&outlier_act, &safe_centroid);
    assert!(!res.safe);
    assert!(res.circuit_breaker_tripped);
}
