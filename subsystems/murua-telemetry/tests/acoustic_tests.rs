// ffp: FFP-MURUA-TEST-ACOUSTIC test rust
use murua_architecture_enhancement::acoustic::{SrmAcousticGate, SteelPlateProperties};

#[test]
fn test_flexural_rigidity_calculation() {
    let plate = SteelPlateProperties::default();
    let srm = SrmAcousticGate::new(plate.clone());

    let d = plate.thickness_m; // 0.0012m
    let e = plate.youngs_modulus_pa; // 2.0e11
    let nu = plate.poissons_ratio; // 0.30

    let expected_d = (e * d * d * d) / (12.0 * (1.0 - nu * nu));
    let calculated_d = srm.flexural_rigidity();

    assert!((calculated_d - expected_d).abs() < 1e-6);
    assert!(calculated_d > 25.0 && calculated_d < 40.0);
}

#[test]
fn test_mass_loaded_frequency_shift() {
    let plate = SteelPlateProperties::default();
    let srm = SrmAcousticGate::new(plate.clone());

    // 0 grams: unloaded
    let (f0, z0, inv_q0) = srm.predict_loaded_acoustics(0.0);
    assert_eq!(f0, plate.f0_empty_hz);
    assert_eq!(z0, plate.zeta_empty);
    assert_eq!(inv_q0, 0.0);

    // 65 grams (Item A single standard envelope)
    let (f65, z65, inv_q65) = srm.predict_loaded_acoustics(65.0);
    assert!(f65 < f0);
    assert!(z65 > z0);
    assert!(inv_q65 > 0.0);

    // 130 grams (Item A + Item B two envelopes)
    let (f130, z130, inv_q130) = srm.predict_loaded_acoustics(130.0);
    assert!(f130 < f65);
    assert!(z130 > z65);
    assert!(inv_q130 > inv_q65);

    // Verify frequency drop corresponds to physical mass loading
    let drop_65 = f0 - f65;
    assert!(drop_65 >= 10.0 && drop_65 <= 20.0);
    let drop_130 = f0 - f130;
    assert!(drop_130 >= 20.0 && drop_130 <= 35.0);
}

#[test]
fn test_measurement_classification() {
    let plate = SteelPlateProperties::default();
    let srm = SrmAcousticGate::new(plate.clone());

    // Empty state
    let empty_res = srm.analyze_measurement(plate.f0_empty_hz, plate.zeta_empty);
    assert_eq!(empty_res.compartment_status, "EMPTY_COMPARTMENT");
    assert!(empty_res.confidence >= 0.90);

    // Loaded state (404.5 Hz, zeta 0.024)
    let loaded_res = srm.analyze_measurement(404.5, 0.024);
    assert_eq!(loaded_res.compartment_status, "MAIL_PRESENT_LOADED");
    assert!(loaded_res.estimated_payload_mass_g > 50.0);
    assert!(loaded_res.confidence >= 0.70);
}

#[test]
fn test_proof_of_sweep_integrity() {
    let plate = SteelPlateProperties::default();
    let srm = SrmAcousticGate::new(plate);

    let raw_audio = vec![0.02f32; 100];
    let token = srm.generate_proof_of_sweep(
        "TERA-3-BOX-90",
        "10.77.0.4",
        "ud9d3m",
        "wifi_ground_floor",
        &raw_audio,
        "EMPTY_COMPARTMENT",
    );

    // Token must verify
    assert!(srm.verify_token_integrity(&token));

    // Tampered token must fail verification
    let mut tampered = token.clone();
    tampered.outcome_status = "MAIL_PRESENT_LOADED".to_string();
    assert!(!srm.verify_token_integrity(&tampered));
}
