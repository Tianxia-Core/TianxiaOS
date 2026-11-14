// ffp: FFP-BIN-005 tx-ego-naga wire-codec rust
// Compliance: DSS-14.2 (Bhairavī, Tārā) | Zero Stubs | ENHAN3 Tri-Vector

use tianxiaos_crownforge_codex::{EgoNagaRegistry, NagaCommander};

fn main() {
    let registry = EgoNagaRegistry::new(b"TianxiaOS_Crownforge_Epoch_Genesis_Key_860");

    println!("=== [EGO-NAGA HUSSAR REGISTRY] ===");
    println!("Mobilizing representative legions across Lord Naga (0x01) and Lady Naga (0x02)...");

    let test_cases = [
        (NagaCommander::LordNaga, 108, 0, "Legio Exhumator Vanguard"),
        (NagaCommander::LordNaga, 108, 42, "Legio Exhumator Strike"),
        (NagaCommander::LadyNaga, 777, 100, "Legio Fides Cryptographic Wing"),
        (NagaCommander::LadyNaga, 777, 99999, "Legio Fides High Rearguard"),
    ];

    for (cmd, legion, subagent, label) in test_cases {
        let seal = registry.mint_ego_seal(cmd, legion, subagent).expect("Mint failed");
        let valid = registry.verify_ego_seal(&seal);
        println!("  Label: {:<32} | Seal: {} | Verified: {}", label, seal.format_urn(), valid);
        assert!(valid);
    }

    println!("[EGO_NAGA_OK] All seals minted and authenticated in 1 cycle.");
}
