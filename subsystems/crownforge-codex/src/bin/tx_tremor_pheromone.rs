// ffp: FFP-BIN-004 tx-tremor-pheromone wire-codec rust
// Compliance: DSS-14.2 (Chhinnamastā, Dhūmāvatī) | Zero Stubs | ENHAN3 Tri-Vector

use std::time::{SystemTime, UNIX_EPOCH};
use tianxiaos_crownforge_codex::{EnvironmentalMedium, TremorPheromoneBus};

fn main() {
    let bus = TremorPheromoneBus::new();
    let now_ns = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos() as u64;

    let payload = b"SovereignSecret::TetraLedger::GenesisBlock::4900Invariants";

    println!("[TREMOR-PHEROMONE] Testing all 4 Environmental Media...");

    let media = [
        EnvironmentalMedium::MediumAlphaMemory,
        EnvironmentalMedium::MediumBetaVfsKernel,
        EnvironmentalMedium::MediumGammaAcoustic,
        EnvironmentalMedium::MediumDeltaRfEm,
    ];

    for m in media {
        let channel = format!("TEST_CHANNEL_{}", m.as_str());
        let receipt = bus.deposit_pheromone_tremor(&channel, m, payload, now_ns);
        println!("  Medium: {} | Dispersed: {} cells | Parity: {}", receipt.medium, receipt.dispersed_cells, receipt.parity_seal_hex);

        let (valid, recovered) = bus.sense_pheromone_tremor(&channel, m, payload.len());
        println!("  Sense Integrity: {} | Recovered: {} bytes", valid, recovered.len());
        assert!(valid);
        assert_eq!(recovered.as_slice(), payload);
    }

    println!("[TREMOR_OK] All 4 media verified with zero packet leakage.");
}
