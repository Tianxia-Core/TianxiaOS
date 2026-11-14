// ffp: FFP-TST-001 test-srm-gate rust
// Compliance: DSS-14 (BHAIRAVI + BAGALAMUKHI) + ENHAN3

use tianxiaos_ndimmorwyn_enterprise::srm::*;

#[test]
fn test_sovereign_3_2_pentad_unlocks_aeon_true_vault() {
    let engine = SrmApexEngine::new();
    let reality = DasavidyayanaReality::default();
    let entropy = SerendipityEntropy::default();

    let t0 = 1_000_000u64;
    let sovereign_taps: [TapImpulse; 5] = [
        TapImpulse::new(t0, 30.0, 0.95, 0.40, 0.965),
        TapImpulse::new(t0 + 100_000, 32.0, 0.94, 0.42, 0.966),
        TapImpulse::new(t0 + 200_000, 31.0, 0.93, 0.41, 0.964),
        TapImpulse::new(t0 + 461_800, 33.0, 0.96, 0.45, 0.968),
        TapImpulse::new(t0 + 561_800, 32.0, 0.95, 0.43, 0.965),
    ];

    let res = engine.evaluate_gate("/run/tx/aeon_core", &sovereign_taps, &reality, &entropy);
    match res {
        SrmApexResolution::AeonTrueVaultUnlocked { vfs_mount, valid_until_ms, .. } => {
            assert_eq!(vfs_mount, "/run/tx/aeon_true_subvol");
            assert!(valid_until_ms > 0);
        }
        _ => panic!("Expected AeonTrueVaultUnlocked for sovereign [3,2] pentad!"),
    }
}

#[test]
fn test_duress_2_3_pentad_silently_mounts_loki_smile() {
    let engine = SrmApexEngine::new();
    let reality = DasavidyayanaReality::default();
    let entropy = SerendipityEntropy::default();

    let t0 = 1_000_000u64;
    let duress_taps: [TapImpulse; 5] = [
        TapImpulse::new(t0, 30.0, 0.95, 0.40, 0.965),
        TapImpulse::new(t0 + 100_000, 32.0, 0.94, 0.42, 0.966),
        TapImpulse::new(t0 + 361_800, 31.0, 0.93, 0.41, 0.964),
        TapImpulse::new(t0 + 461_800, 33.0, 0.96, 0.45, 0.968),
        TapImpulse::new(t0 + 561_800, 32.0, 0.95, 0.43, 0.965),
    ];

    let res = engine.evaluate_gate("/run/tx/aeon_core", &duress_taps, &reality, &entropy);
    match res {
        SrmApexResolution::LokiSmileShadowMounted { vfs_mount, reason_code, .. } => {
            assert_eq!(vfs_mount, "/run/tx/loki_shadow_honey_subvol");
            assert_eq!(reason_code, "DURESS_2_3_ACTIVE");
        }
        _ => panic!("Expected LokiSmileShadowMounted for duress [2,3] pentad!"),
    }
}
