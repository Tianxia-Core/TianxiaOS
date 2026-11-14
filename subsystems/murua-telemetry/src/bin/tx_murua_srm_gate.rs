// ffp: FFP-MURUA-SRM-BIN srm-gate-cli rust
//! Murua SRM Lamb-Wave Acoustic Gate CLI
//! Analyzes modal resonance frequency shifts, computes viscoelastic damping,
//! and issues cryptographic Proof-of-Sweep tokens.

use murua_architecture_enhancement::acoustic::{SrmAcousticGate, SteelPlateProperties};
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    let mass_input: f64 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(130.0);

    let plate = SteelPlateProperties::default();
    let srm = SrmAcousticGate::new(plate.clone());

    println!("================================================================================");
    println!(" MURUA SRM ACOUSTIC-SPATIAL MAILBOX GATE");
    println!(" EN 13724 Steel Compartment d = {:.1} mm, Area = {:.4} m^2", plate.thickness_m * 1000.0, plate.tray_width_m * plate.tray_depth_m);
    println!(" Base Frequency f0 = {:.1} Hz, Base Damping zeta = {:.4}", plate.f0_empty_hz, plate.zeta_empty);
    println!(" Flexural Rigidity D = {:.2} N*m", srm.flexural_rigidity());
    println!("================================================================================");

    let (f_loaded, z_loaded, delta_inv_q) = srm.predict_loaded_acoustics(mass_input);
    println!("Loaded Simulation with Mass = {:.1} g:", mass_input);
    println!("  Predicted Resonance f_loaded: {:.2} Hz (Shift: {:.2} Hz)", f_loaded, f_loaded - plate.f0_empty_hz);
    println!("  Predicted Damping zeta_loaded:{:.5}", z_loaded);
    println!("  Predicted Delta Q^-1:         {:.5}", delta_inv_q);

    let analysis = srm.analyze_measurement(f_loaded, z_loaded);
    println!("\nInverted Measurement Classification:");
    println!("  Detected Status:              {}", analysis.compartment_status);
    println!("  Estimated Payload Mass:       {:.1} g", analysis.estimated_payload_mass_g);
    println!("  Classification Confidence:    {:.2}%", analysis.confidence * 100.0);

    let dummy_audio = vec![0.005f32; 2048];
    let token = srm.generate_proof_of_sweep(
        "TERA-3-BOX-90",
        "10.77.0.4",
        "ud9d3m",
        "wifi_hash_ground_floor",
        &dummy_audio,
        &analysis.compartment_status,
    );

    println!("\nCryptographic Proof-of-Sweep Attestation:");
    println!("  Mailbox ID:       {}", token.mailbox_id);
    println!("  Inspector Node:   {}", token.inspector_node_ip);
    println!("  Timestamp:        {}", token.timestamp_utc.to_rfc3339());
    println!("  Acoustic Hash:    {}", &token.acoustic_signature_blake3[..24]);
    println!("  Attestation Hash: {}", token.proof_attestation_hash);
    println!("  Verification:     {}", if srm.verify_token_integrity(&token) { "VALID" } else { "TAMPERED" });
    println!("================================================================================");
}
