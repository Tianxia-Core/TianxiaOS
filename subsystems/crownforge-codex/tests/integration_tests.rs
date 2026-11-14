// ffp: FFP-TST-001 crownforge-codex-integration-tests rust
// Compliance: Zero Stubs | ENHAN3 Tri-Vector

use tianxiaos_crownforge_codex::{
    CrownforgeCodex, EnvironmentalMedium, HardwareTelemetry, JivascriptocleVisionEncoder,
    Jot151kOrthogonalVerifier, NagaCommander, OmniLatticeTopology, TargetDomain,
};
use std::time::{SystemTime, UNIX_EPOCH};

#[test]
fn test_end_to_end_crownforge_codex_cycle() {
    let now_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos() as u64;

    let codex = CrownforgeCodex::new(b"TestEpochSeedCrownforgeV860");
    let telemetry = HardwareTelemetry::default();

    // 1. Normal execution without loop stall
    let (orw, nk, madpie_opt) = codex.execute_full_codex_cycle(
        "Optimize eBPF packet throughput on latitude-tianxia",
        TargetDomain::Trading,
        &telemetry,
        1,
        now_ns,
    );

    assert_eq!(orw.domain, "TRADING");
    assert!(orw.stochastic_resonance_snr > 0.0);
    assert!(nk.noetic_sixth_sense_score > 0.0);
    assert!(madpie_opt.is_none());

    // 2. Intractable execution with loop stall >= 3
    let (_, _, madpie_engaged) = codex.execute_full_codex_cycle(
        "Cyclic deadlock in distributed consensus",
        TargetDomain::Mathematics,
        &telemetry,
        3,
        now_ns,
    );

    assert!(madpie_engaged.is_some());
    let madpie = madpie_engaged.unwrap();
    assert_eq!(madpie.status, "MAHA_MADPIE_BREAKTHROUGH_SEALED");
    assert_eq!(madpie.honeycomb_rosette.len(), 7);
    assert_eq!(madpie.helix_turns.len(), 6);
}

#[test]
fn test_all_environmental_media_stigmergy() {
    let codex = CrownforgeCodex::new(b"TestStigmergySeed");
    let payload = b"CryptographicEphemeralState_14Mahavidya";
    let media = [
        EnvironmentalMedium::MediumAlphaMemory,
        EnvironmentalMedium::MediumBetaVfsKernel,
        EnvironmentalMedium::MediumGammaAcoustic,
        EnvironmentalMedium::MediumDeltaRfEm,
    ];

    for m in media {
        let channel = format!("CHANNEL_{}", m.as_str());
        let receipt = codex.tremor.deposit_pheromone_tremor(&channel, m, payload, 9999);
        assert_eq!(receipt.packet_footprint_bytes, 0);

        let (valid, recovered) = codex.tremor.sense_pheromone_tremor(&channel, m, payload.len());
        assert!(valid);
        assert_eq!(recovered, payload);

        codex.tremor.evict_channel(&channel, m, payload.len());
        let (valid_after, _) = codex.tremor.sense_pheromone_tremor(&channel, m, payload.len());
        assert!(!valid_after);
    }
}

#[test]
fn test_hussar_army_bounds() {
    let codex = CrownforgeCodex::new(b"TestArmyBounds");

    // Min valid
    let seal_min = codex.ego.mint_ego_seal(NagaCommander::LordNaga, 0, 0);
    assert!(seal_min.is_ok());

    // Max valid
    let seal_max = codex.ego.mint_ego_seal(NagaCommander::LadyNaga, 63999, 99999);
    assert!(seal_max.is_ok());

    // Out of bounds legion
    let seal_err_legion = codex.ego.mint_ego_seal(NagaCommander::LordNaga, 64000, 0);
    assert!(seal_err_legion.is_err());

    // Out of bounds subagent
    let seal_err_sub = codex.ego.mint_ego_seal(NagaCommander::LadyNaga, 100, 100000);
    assert!(seal_err_sub.is_err());
}

#[test]
fn test_companion_frameworks() {
    let nodes = JivascriptocleVisionEncoder::generate_kamadhenu_layout("saas_enterprise");
    let algebra = JivascriptocleVisionEncoder::encode_wireframe_algebra("saas_enterprise", &nodes);
    assert!(algebra.contains("JIVAVIS::NICHE[SAAS_ENTERPRISE]"));

    let w_base = vec![1.0, 2.0, 3.0, 4.0];
    let w_jot = vec![2.0, -1.0, 4.0, -3.0]; // <w_base, w_jot> = 2 - 2 + 12 - 12 = 0
    let (is_ortho, cos_sim) = Jot151kOrthogonalVerifier::verify_nullspace_orthogonality(&w_base, &w_jot);
    assert!(is_ortho);
    assert!(cos_sim < 1e-10);

    let topo72 = OmniLatticeTopology::standard_72_node();
    assert_eq!(topo72.total_nodes, 72);

    let topo2048 = OmniLatticeTopology::fractal_2048_node();
    assert_eq!(topo2048.total_nodes, 2048);
    assert_eq!(topo2048.milli_kan_tripwires, 1984);
}
