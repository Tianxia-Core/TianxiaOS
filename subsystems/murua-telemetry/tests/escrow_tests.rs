// ffp: FFP-MURUA-TEST-ESCROW test rust
use chrono::{Duration, Utc};
use murua_architecture_enhancement::escrow::{EscrowCase, VeritasEscrowActuator};

#[test]
fn test_escrow_lock_timing_trigger() {
    let actuator = VeritasEscrowActuator::default();
    let now = Utc::now();

    let case = EscrowCase {
        order_id: "58b73b08".to_string(),
        item_name: "Technical Stationery".to_string(),
        vendor_name: "PostNL Partner".to_string(),
        origin_corridor: "NL-AMS_EE-TLL_12618".to_string(),
        escrow_amount_eur: 42.50,
        order_created_utc: now - Duration::days(12),
        vendor_shipped_utc: now - Duration::days(10),
        carrier_pickup_utc: now - Duration::days(8),
        auto_finalization_cutoff_utc: now + Duration::hours(36), // 36h away (< 48h!)
        dispute_lock_window_start_utc: now - Duration::hours(2), // Already passed
        current_status: "IN_OXBOW_BUFFER".to_string(),
    };

    // If box is NOT empty (mail delivered), lock is false
    assert!(!actuator.should_lock_escrow(&case, now, false));

    // If box IS empty, lock is true
    assert!(actuator.should_lock_escrow(&case, now, true));
}

#[test]
fn test_statutory_depot_inquiries_generation() {
    let actuator = VeritasEscrowActuator::new(
        "Authorized Recipient".to_string(),
        "Pallasti 28, 12618 Tallinn".to_string(),
    );
    let now = Utc::now();

    let case = EscrowCase {
        order_id: "58b73b08".to_string(),
        item_name: "Technical Stationery".to_string(),
        vendor_name: "PostNL Partner".to_string(),
        origin_corridor: "NL-AMS_EE-TLL_12618".to_string(),
        escrow_amount_eur: 42.50,
        order_created_utc: now - Duration::days(12),
        vendor_shipped_utc: now - Duration::days(10),
        carrier_pickup_utc: now - Duration::days(8),
        auto_finalization_cutoff_utc: now + Duration::hours(48),
        dispute_lock_window_start_utc: now - Duration::hours(1),
        current_status: "IN_OXBOW_BUFFER".to_string(),
    };

    let inquiries = actuator.generate_depot_inquiries(&case);
    assert_eq!(inquiries.len(), 2);

    // Target 1: Mustika Postkontor hold-shelf
    assert!(inquiries[0].target_facility.contains("Mustika"));
    assert!(inquiries[0].legal_basis.contains("Postiseadus §35"));
    assert!(inquiries[0].inquiry_payload_text.contains("Pallasti 28"));

    // Target 2: Rukki tee 7 undeliverable commission
    assert!(inquiries[1].target_facility.contains("Rukki tee 7"));
    assert!(inquiries[1].legal_basis.contains("Postiseadus §36"));
}

#[test]
fn test_dispute_dossier_integrity() {
    let actuator = VeritasEscrowActuator::default();
    let now = Utc::now();

    let case = EscrowCase {
        order_id: "58b73b08".to_string(),
        item_name: "Technical Stationery".to_string(),
        vendor_name: "PostNL Partner".to_string(),
        origin_corridor: "NL-AMS_EE-TLL_12618".to_string(),
        escrow_amount_eur: 42.50,
        order_created_utc: now - Duration::days(12),
        vendor_shipped_utc: now - Duration::days(10),
        carrier_pickup_utc: now - Duration::days(8),
        auto_finalization_cutoff_utc: now + Duration::hours(48),
        dispute_lock_window_start_utc: now - Duration::hours(1),
        current_status: "IN_OXBOW_BUFFER".to_string(),
    };

    let dossier = actuator.generate_dispute_dossier(&case, "SWEEP_PROOF_HASH_12345");
    assert!(dossier.dossier_id.starts_with("VR-DOSSIER-"));
    assert_eq!(dossier.escrow_locked_amount_eur, 42.50);
    assert_eq!(dossier.proof_of_sweep_hash, "SWEEP_PROOF_HASH_12345");
    assert!(dossier.demand_from_vendor.contains("PostNL Kassabon"));
    assert!(!dossier.integrity_signature.is_empty());
}
