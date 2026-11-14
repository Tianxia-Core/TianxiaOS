// ffp: FFP-MURUA-TEST-SOFTEM test rust
use murua_architecture_enhancement::softem::{CarrierClaim, SoftemProbe};

#[test]
fn test_symbolic_ontology_rejection() {
    let probe = SoftemProbe::default();

    // False claim: untracked post redirected to locker
    let bogus = CarrierClaim {
        claim_id: "CLM-001".to_string(),
        statement: "Omniva redirects untracked letters to locker via phone OCR".to_string(),
        has_s10_barcode: false,
        has_edi_hook: false,
        claims_locker_redirection: true,
        claims_sms_pin_delivery: true,
        statutory_anchor_cited: None,
    };

    let (valid, msg) = probe.verify_symbolic_ontology(&bogus);
    assert!(!valid);
    assert!(msg.contains("VIOLATION"));

    // Valid claim: S10 parcel with EDI
    let valid_claim = CarrierClaim {
        claim_id: "CLM-002".to_string(),
        statement: "S10 parcel routed to Smartpost locker".to_string(),
        has_s10_barcode: true,
        has_edi_hook: true,
        claims_locker_redirection: true,
        claims_sms_pin_delivery: true,
        statutory_anchor_cited: Some("UPU S10".to_string()),
    };

    let (valid2, msg2) = probe.verify_symbolic_ontology(&valid_claim);
    assert!(valid2);
    assert!(msg2.contains("VALID"));
}

#[test]
fn test_huber_loss_boundary_conditions() {
    let probe = SoftemProbe::default(); // eps = 0.15

    // Inside linear boundary diff <= 0.15: 0.5 * diff^2
    let loss_small = probe.huber_loss(1.0, 1.10); // diff = 0.10
    let expected_small = 0.5 * 0.10 * 0.10;
    assert!((loss_small - expected_small).abs() < 1e-9);

    // Outside linear boundary diff > 0.15: eps * (diff - 0.5 * eps)
    let loss_large = probe.huber_loss(1.0, 1.50); // diff = 0.50
    let expected_large = 0.15 * (0.50 - 0.5 * 0.15);
    assert!((loss_large - expected_large).abs() < 1e-9);
}

#[test]
fn test_spike_weighted_loss_and_abscission() {
    let probe = SoftemProbe::default();

    let bogus_claim = CarrierClaim {
        claim_id: "CLM-BOGUS".to_string(),
        statement: "Bogus OCR claim".to_string(),
        has_s10_barcode: false,
        has_edi_hook: false,
        claims_locker_redirection: true,
        claims_sms_pin_delivery: false,
        statutory_anchor_cited: None,
    };

    // Divergent predictions vs real anchors
    let preds = vec![0.10, 0.05, 0.02];
    let anchors = vec![0.95, 0.90, 0.92];

    let res = probe.verify_claim(&bogus_claim, &preds, &anchors);
    assert!(res.is_hallucination);
    assert_eq!(res.action_taken, "BOTANICAL_LEAF_ABSCISSION_PRUNED");
    assert!(res.diagnostic_reason.contains("PRUNED [STATE_LOCK_ZERO_LOSS]"));
}
