// ffp: FFP-MURUA-ESCROW-BIN escrow-actuator-cli rust
//! Murua Veritas-Rex Escrow Actuator CLI
//! Formulates statutory depot notices and prepares platform dispute dossiers.

use chrono::{Duration, Utc};
use murua_architecture_enhancement::escrow::{EscrowCase, VeritasEscrowActuator};
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    let order_id = args.get(1).map(|s| s.as_str()).unwrap_or("58b73b08");

    let actuator = VeritasEscrowActuator::default();
    let now = Utc::now();

    println!("================================================================================");
    println!(" MURUA VERITAS-REX ESCROW ACTUATOR & STATUTORY DISPATCHER");
    println!(" Target Order: {}", order_id);
    println!(" Recipient:    {}", actuator.recipient_name);
    println!(" Address:      {}", actuator.delivery_address);
    println!("================================================================================");

    let case = EscrowCase {
        order_id: order_id.to_string(),
        item_name: "PostNL Priority Letter Post Stationery".to_string(),
        vendor_name: "PostNL Merchant Partner".to_string(),
        origin_corridor: "NL-AMS_EE-TLL_12618".to_string(),
        escrow_amount_eur: 42.50,
        order_created_utc: now - Duration::days(12),
        vendor_shipped_utc: now - Duration::days(10),
        carrier_pickup_utc: now - Duration::days(8),
        auto_finalization_cutoff_utc: now + Duration::hours(48),
        dispute_lock_window_start_utc: now - Duration::hours(1),
        current_status: "IN_OXBOW_BUFFER".to_string(),
    };

    let should_lock = actuator.should_lock_escrow(&case, now, true);
    println!("Escrow Lock Assessment: [BOX EMPTY = TRUE]");
    println!("  Should Lock Escrow Immediately: {}", should_lock);

    println!("\nGenerating Statutory Depot Inquiries:");
    let inquiries = actuator.generate_depot_inquiries(&case);
    for inq in inquiries {
        println!("\n--------------------------------------------------------------------------------");
        println!("FACILITY: {}", inq.target_facility);
        println!("LEGAL BASIS: {}", inq.legal_basis);
        println!("INQUIRY ID:  {}", inq.inquiry_id);
        println!("PAYLOAD:\n{}", inq.inquiry_payload_text);
    }

    println!("\nGenerating Veritas-Rex Escrow Dispute Dossier:");
    let dossier = actuator.generate_dispute_dossier(&case, "BLAKE3_SWEEP_PROOF_PALLASTI28_BOX01_NOV6_EMPTY");
    println!("DOSSIER ID: {}", dossier.dossier_id);
    println!("LOCKED AMOUNT: EUR {:.2}", dossier.escrow_locked_amount_eur);
    println!("REASON:\n{}", dossier.formal_dispute_reason);
    println!("DEMAND:\n{}", dossier.demand_from_vendor);
    println!("INTEGRITY SIGNATURE: {}", dossier.integrity_signature);
    println!("================================================================================");
}
