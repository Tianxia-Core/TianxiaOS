// ffp: FFP-TST-004 test-filippov-router rust
// Compliance: DSS-14 (TARA + MATANGI) + ENHAN3

use tianxiaos_ndimmorwyn_enterprise::biomimetic::*;

#[test]
fn test_filippov_sliding_manifold_routing() {
    let mut router = FilippovConstructalRouter::new();

    // Low entropy routes to bitnet edge
    let res_low = router.route_along_sliding_manifold(0.15, 5.0);
    assert_eq!(res_low.selected_channel, "mif20_bitnet_edge");
    assert_eq!(res_low.wire_format, "TOON_PIPE_TABULAR_51PCT");

    // High QPS switches wire format to Telegraph English
    let res_high_qps = router.route_along_sliding_manifold(0.85, 30.0);
    assert_eq!(res_high_qps.wire_format, "TELEGRAPH_ENGLISH_50PCT");
}

#[test]
fn test_phyllotactic_scheduler_angles() {
    let sched = PhyllotacticScheduler::new();
    assert_eq!(sched.nodes.len(), 5);

    // Verify each node has a unique non-overlapping phase
    for i in 0..sched.nodes.len() {
        for j in (i + 1)..sched.nodes.len() {
            let diff = (sched.nodes[i].angular_phase_offset_rad - sched.nodes[j].angular_phase_offset_rad).abs();
            assert!(diff > 0.01, "Phyllotactic phase collision between nodes {} and {}", i, j);
        }
    }
}
