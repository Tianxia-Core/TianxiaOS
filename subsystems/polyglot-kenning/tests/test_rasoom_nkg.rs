// ffp: FFP-TST-004 test-rasoom-nkg rust

use tianxiaos_polyglot_kenning::rasoom::RasoomNkgEngine;

#[test]
fn test_nsibidi_edge_encoding() {
    let rasoom = RasoomNkgEngine::new();

    let edge = rasoom.encode_nsibidi_edge("NodeA", "NodeB", 0x0101, b"TEST_PAYLOAD");
    assert!(edge.contains("⟦NSB:COVENANT_SEAL⟧"));
    assert!(edge.contains("0x0101"));
    assert!(edge.contains("NodeA"));
    assert!(edge.contains("NodeB"));

    let edge_dispute = rasoom.encode_nsibidi_edge("Nimue", "Escrow", 0x0102, b"DISPUTE");
    assert!(edge_dispute.contains("⟦NSB:IKPE_DISPUTE⟧"));
    assert!(edge_dispute.contains("GATEWAY_HOLDBACK"));
}

#[test]
fn test_konnakol_tdma_generation() {
    let rasoom = RasoomNkgEngine::new();
    let schedule = rasoom.generate_konnakol_tdma_schedule(1000);

    assert_eq!(schedule.total_nodes, 5);
    assert_eq!(schedule.slots.len(), 5);
    assert!(!schedule.korvai_convergence_hash.is_empty());

    // Verify all 5 mesh nodes present
    let names: Vec<String> = schedule.slots.iter().map(|s| s.node_name.clone()).collect();
    assert!(names.contains(&"hetzner-core".to_string()));
    assert!(names.contains(&"lat-5591".to_string()));
    assert!(names.contains(&"pixel-8-pro".to_string()));
}
