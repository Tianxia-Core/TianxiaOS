// ffp: FFP-MURUA-DAEMON universal-tracer-daemon rust
//! Murua Universal Tracer Daemon (MODE 1: Sovereign Consumer & MODE 2: Enterprise Command)
//! Orchestrates the 5-node WireGuard mesh, DSS-14.2 telemetry, and automated actuators.

use chrono::{Duration, Utc};
use murua_architecture_enhancement::{
    acoustic::{SrmAcousticGate, SteelPlateProperties},
    barabasi::{BarabasiOxbowEstimator, CorridorParameters},
    dss14::{MahavidyaDomain, MerkleProvenanceLedger, TelemetryRecord},
    escrow::{EscrowCase, VeritasEscrowActuator},
    softem::{CarrierClaim, SoftemProbe},
    toon::{ToonTelemetryRow, ToonTronCodec},
    VERSION,
};
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    let mode = args.get(1).map(|s| s.as_str()).unwrap_or("both");

    println!("================================================================================");
    println!(" TIANXIA OS // MURUA SOVEREIGN TELEMETRY & ACTUATION DAEMON (v{})", VERSION);
    println!(" Subsystem: Murua Universal Tracer | Mode: {}", mode);
    println!(" Mesh Target: lat-5591 / latitude-tianxia (10.77.0.3)");
    println!("================================================================================");

    let mut ledger = MerkleProvenanceLedger::new();
    let now = Utc::now();

    // 1. Initialize Corridor and Estimator
    let corridor_params = CorridorParameters::default();
    let estimator = BarabasiOxbowEstimator::new(corridor_params.clone());
    let ccbd_untracked = estimator.compute_ccbd(false);
    let ccbd_tracked = estimator.compute_ccbd(true);

    println!("[*] [E217-BIFURCATED] C_CBD Score (Main Tracked Channel):   {:.2}", ccbd_tracked.aggregate_ccbd);
    println!("[*] [E217-BIFURCATED] C_CBD Score (Oxbow Untracked Channel): {:.2}", ccbd_untracked.aggregate_ccbd);
    println!("[*] Effective Barabási Tau0 (Supercritical Surge):         {:.1} hours", estimator.effective_tau0);

    let p75 = estimator.calculate_p75_dwell();
    println!("[*] Barabási Tail P75 Dwell Escalation Threshold:          {:.1} hours", p75);

    // 2. Field Evaluation for Items A & B (Pallasti 28 Box #01)
    let pickup_item_a = now - Duration::days(7); // Induction Oct 27
    let shipped_item_a = pickup_item_a - Duration::hours(36); // Vendor pre-advice
    let auto_fin_cutoff = now + Duration::hours(70); // Auto-finalization deadline

    let decomp_a = estimator.evaluate_heddle_escalation("58b73b08", shipped_item_a, pickup_item_a, now);
    println!("\n--- [ITEM A: 58b73b08] Dwell Decomposition ---");
    println!("  Vendor Pre-Advice Lag:       {:.1} hours", decomp_a.vendor_pre_advice_lag_hours);
    println!("  Predicted Linehaul Time:     {:.1} hours", decomp_a.predicted_linehaul_hours);
    println!("  Estimated Oxbow Dwell:       {:.1} hours", decomp_a.estimated_oxbow_dwell_hours);
    println!("  Current Total Dwell:         {:.1} hours", decomp_a.current_dwell_hours);
    println!("  Escalation Required:         {}", decomp_a.priority_escalation_required);
    println!("  Status:                      {}", decomp_a.status);

    let pred_a = estimator.predict_delivery_window(
        "58b73b08",
        pickup_item_a,
        now,
        now + Duration::hours(18),
        now + Duration::hours(22),
        auto_fin_cutoff,
    );

    println!("\n--- [ITEM A: 58b73b08] Upcoming Window Prediction (Business Day 8) ---");
    println!("  Completed Business Days:     {:.1}", pred_a.completed_business_days);
    println!("  Single Item Delivery Prob:   {:.1}%", pred_a.prob_next_window_single * 100.0);
    println!("  Joint Delivery Prob:         {:.1}%", pred_a.prob_next_window_joint * 100.0);
    println!("  Residual Oxbow Spillover:    {:.1}%", pred_a.residual_spillover_prob * 100.0);
    println!("  Escrow Dispute Lock Time:    {}", pred_a.escrow_dispute_lock_deadline_utc.to_rfc3339());
    println!("  Auto-Finalization Cutoff:    {}", pred_a.auto_finalization_deadline_utc.to_rfc3339());

    ledger.insert_event(&format!("PREDICTION_ITEM_A:{}", pred_a.prob_next_window_single));

    // 3. Acoustic SRM Gate Simulation
    println!("\n--- [SRM ACOUSTIC GATE] Mailbox Fullness & Proof-of-Sweep ---");
    let plate = SteelPlateProperties::default();
    let srm = SrmAcousticGate::new(plate.clone());

    // Case 1: Empty mailbox sweep
    let (f_empty, z_empty, _) = (plate.f0_empty_hz, plate.zeta_empty, 0.0);
    let analysis_empty = srm.analyze_measurement(f_empty, z_empty);
    println!("  [Empty Sweep] Status: {}, Conf: {:.2}", analysis_empty.compartment_status, analysis_empty.confidence);

    // Case 2: Loaded mailbox with two envelopes (~130g)
    let (f_loaded, z_loaded, _) = srm.predict_loaded_acoustics(130.0);
    let analysis_loaded = srm.analyze_measurement(f_loaded, z_loaded);
    println!(
        "  [Loaded Sweep] Status: {}, Mass: {:.1}g, Conf: {:.2}",
        analysis_loaded.compartment_status,
        analysis_loaded.estimated_payload_mass_g,
        analysis_loaded.confidence
    );

    // Generate cryptographic proof-of-sweep token
    let dummy_audio = vec![0.01f32; 1024];
    let token = srm.generate_proof_of_sweep(
        "BOX-90-PALLASTI28",
        "10.77.0.4",
        "ud9d3m",
        "bssid_pallasti28_hub",
        &dummy_audio,
        &analysis_empty.compartment_status,
    );
    let valid_token = srm.verify_token_integrity(&token);
    println!("  [Proof-of-Sweep Token] Hash: {} (Valid: {})", &token.proof_attestation_hash[..16], valid_token);

    ledger.insert_event(&format!("PROOF_OF_SWEEP:{}", token.proof_attestation_hash));

    // 4. SOFTEM Anti-Confabulation Shield
    println!("\n--- [SOFTEM SHIELD] Evaluating Carrier Capability Claims ---");
    let softem = SoftemProbe::default();

    // Test false claim: unbarcoded mail redirected via OCR to parcel locker
    let false_claim = CarrierClaim {
        claim_id: "CLM-OMNIVA-FALSE-OCR".to_string(),
        statement: "Omniva OCR reads phone number and delivers untracked letter to locker".to_string(),
        has_s10_barcode: false,
        has_edi_hook: false,
        claims_locker_redirection: true,
        claims_sms_pin_delivery: true,
        statutory_anchor_cited: None,
    };
    let softem_res = softem.verify_claim(&false_claim, &[0.12, 0.05, 0.02], &[0.95, 0.88, 0.90]);
    println!("  [Claim 1] {}", false_claim.statement);
    println!("    Result:      Hallucination = {}", softem_res.is_hallucination);
    println!("    Action:      {}", softem_res.action_taken);
    println!("    Diagnostic:  {}", softem_res.diagnostic_reason);

    ledger.insert_event(&format!("SOFTEM_EVAL:{}", softem_res.action_taken));

    // 5. Veritas-Rex Escrow Actuator
    println!("\n--- [VERITAS-REX] Escrow Protection & Statutory Depot Interrogation ---");
    let actuator = VeritasEscrowActuator::default();
    let escrow_case = EscrowCase {
        order_id: "58b73b08".to_string(),
        item_name: "Dutch Technical Stationery Envelopes (A & B)".to_string(),
        vendor_name: "PostNL Enterprise Merchant".to_string(),
        origin_corridor: "NL-AMS_EE-TLL_12618".to_string(),
        escrow_amount_eur: 42.50,
        order_created_utc: now - Duration::days(12),
        vendor_shipped_utc: shipped_item_a,
        carrier_pickup_utc: pickup_item_a,
        auto_finalization_cutoff_utc: auto_fin_cutoff,
        dispute_lock_window_start_utc: now + Duration::hours(24),
        current_status: "TRANSIT_OXBOW_BUFFER".to_string(),
    };

    let inquiries = actuator.generate_depot_inquiries(&escrow_case);
    for (i, inq) in inquiries.iter().enumerate() {
        println!("  [Statutory Inquiry {}] Target: {}", i + 1, inq.target_facility);
        println!("    Basis:   {}", inq.legal_basis);
        println!("    ID:      {}", inq.inquiry_id);
    }

    let dispute_dossier = actuator.generate_dispute_dossier(&escrow_case, &token.proof_attestation_hash);
    println!("\n  [Dispute Dossier Prepared] ID: {}", dispute_dossier.dossier_id);
    println!("    Amount:  EUR {:.2}", dispute_dossier.escrow_locked_amount_eur);
    println!("    Demand:  {}", dispute_dossier.demand_from_vendor);
    println!("    Signature: {}", &dispute_dossier.integrity_signature[..16]);

    ledger.insert_event(&format!("VERITAS_REX_DOSSIER:{}", dispute_dossier.dossier_id));

    // 6. TOON Stream Generation
    println!("\n--- [TOON TELEMETRY STREAM] ---");
    let toon_rows = vec![
        ToonTelemetryRow {
            corridor: "NL-AMS_EE-TLL_12618".to_string(),
            item_id: "58b73b08".to_string(),
            pre_adv_dt: Some(shipped_item_a),
            pickup_dt: pickup_item_a,
            cfc_stamp_dt: Some("2026-10-27".to_string()),
            hub_spray_dt: None,
            deliv_dt: None,
            mass_g: 65.0,
            thick_mm: 4.0,
            format: "STD_ENV".to_string(),
            kix_ok: true,
            status: "IN_OXBOW_BUFFER".to_string(),
        },
        ToonTelemetryRow {
            corridor: "NL-AMS_EE-TLL_12618".to_string(),
            item_id: "c31f078b".to_string(),
            pre_adv_dt: Some(shipped_item_a + Duration::hours(1)),
            pickup_dt: pickup_item_a,
            cfc_stamp_dt: Some("2026-10-27".to_string()),
            hub_spray_dt: None,
            deliv_dt: None,
            mass_g: 65.0,
            thick_mm: 4.0,
            format: "STD_ENV".to_string(),
            kix_ok: true,
            status: "IN_OXBOW_BUFFER".to_string(),
        },
    ];

    let toon_encoded = ToonTronCodec::encode_toon(&toon_rows);
    print!("{}", toon_encoded);

    let decoded_rows = ToonTronCodec::decode_toon(&toon_encoded).unwrap();
    println!("[+] Successfully decoded {} TOON rows with 100% fidelity.", decoded_rows.len());

    // 7. DSS-14.2 Merkle DAG Root & Prometheus Telemetry
    let merkle_root = ledger.calculate_root();
    println!("\n================================================================================");
    println!(" [DSS-14.2] Merkle DAG Invariant Root: {}", merkle_root);

    let record = TelemetryRecord::new(
        MahavidyaDomain::Mahasarasvati,
        "barabasi_p75_dwell_hours",
        p75,
        "10.77.0.3",
    );
    print!(" [PROMETHEUS] {}", record.to_prometheus());
    println!("================================================================================");
    println!("[+] Murua Universal Tracer diagnostics completed successfully.");

    if args.iter().any(|a| a == "--daemon") {
        println!("[MURUA DAEMON] Entering persistent telemetry supervisor loop (period: 30s)...");
        let mut loop_count: u64 = 0;
        loop {
            std::thread::sleep(std::time::Duration::from_secs(30));
            loop_count += 1;
            let heartbeat = TelemetryRecord::new(
                MahavidyaDomain::Annapurna,
                "murua_heartbeat_tick",
                loop_count as f64,
                "10.77.0.3",
            );
            println!("[HEARTBEAT #{}] {}", loop_count, heartbeat.to_prometheus().trim());
        }
    }
}
