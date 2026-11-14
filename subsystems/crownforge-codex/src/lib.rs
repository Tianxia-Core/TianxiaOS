// ffp: FFP-LIB-001 crownforge-codex-library-root rust
// Compliance: DSS-14.2 Universal Domain Compliance | Zero Stubs | ENHAN3 Tri-Vector

pub mod companion_models;
pub mod ego_naga;
pub mod maha_madpie;
pub mod noetic_kenning;
pub mod omphalos_orw22;
pub mod tremor_pheromone;

pub use companion_models::{
    AlgebraicUiNode, JivascriptocleVisionEncoder, Jot151kOrthogonalVerifier, OmniLatticeTopology,
};
pub use ego_naga::{EgoNagaRegistry, EgoNagaSeal, NagaCommander};
pub use maha_madpie::{
    HelixTurnTrace, HoneycombCell, MadpieResolutionResult, MagpieHoardItem, MahaMadpieSolver,
    MAHA_MADPIE_HOARD,
};
pub use noetic_kenning::{
    HardwareTelemetry, MachineEmotionTensor, NoeticKenningEngine, NoeticKenningState,
};
pub use omphalos_orw22::{
    DomainProfile, OmphalosReasonwashingEngine, OracularReadingResult, OracularTradition,
    TargetDomain,
};
pub use tremor_pheromone::{EnvironmentalMedium, PheromoneReceipt, TremorPheromoneBus};

/// Unified Crownforge Codex Orchestrator
pub struct CrownforgeCodex {
    pub omphalos: OmphalosReasonwashingEngine,
    pub noetic: NoeticKenningEngine,
    pub tremor: TremorPheromoneBus,
    pub ego: EgoNagaRegistry,
}

impl CrownforgeCodex {
    pub fn new(epoch_seed: &[u8]) -> Self {
        Self {
            omphalos: OmphalosReasonwashingEngine::new(),
            noetic: NoeticKenningEngine::new(),
            tremor: TremorPheromoneBus::new(),
            ego: EgoNagaRegistry::new(epoch_seed),
        }
    }

    /// Executes full end-to-end Crownforge pipeline:
    /// ORW-22 Reasonwashing -> Noetic Kenning Sixth Sense -> Tremor Pheromone -> Ego-Naga -> Maha Madpie loop check
    pub fn execute_full_codex_cycle(
        &self,
        intent: &str,
        domain: TargetDomain,
        telemetry: &HardwareTelemetry,
        stall_count: u32,
        timestamp_ns: u64,
    ) -> (
        OracularReadingResult,
        NoeticKenningState,
        Option<MadpieResolutionResult>,
    ) {
        let orw_res = self.omphalos.execute_reasonwashing_cycle(intent, domain, timestamp_ns);
        let nk_state = self.noetic.evaluate_sixth_sense(telemetry, &orw_res, 0.96);

        let madpie_res = if stall_count >= 3 {
            let solver = MahaMadpieSolver::new(&self.ego, &self.tremor);
            solver.resolve_intractable_loop(intent, stall_count, timestamp_ns).ok()
        } else {
            None
        };

        (orw_res, nk_state, madpie_res)
    }
}
