// ffp: FFP-LIB-001 polyglot-kenning-lib rust
//! TianxiaOS Polyglot Kenning, Oracular Engine & 14-Core Nimbus² DAS v3.0.0
//! Zero-Stub Institutional Sovereign Implementation

pub mod jivaslokan;
pub mod kenning;
pub mod nimbus;
pub mod oracular;
pub mod rasoom;
pub mod resilience;

pub use jivaslokan::{JivaslokanHuberProbe, ProbeEvaluationResult};
pub use kenning::{
    ArtificialKenningEngine, DspgKenningMeta, KarunaRecoveryResult, KarxtGateResult,
    ShieldScanResult,
};
pub use nimbus::{NimbusCoreDefinition, NimbusCoreHealth, NimbusMatrixStatus, NimbusSupervisor};
pub use oracular::{OmniLatticeScores, OracularArsiVerdict, OracularEngine, Stratum0Facts};
pub use rasoom::{KonnakolNodeSlot, NsibidiGlyphMeta, RasoomNkgEngine, TdmaEpochSchedule};
pub use resilience::{
    Aegis9AuditReport, Aegis9SecurityController, AegisRingStatus, EgoDagNodeEvaluation,
    EgoGraphOptimizer, TremorDampingEngine, TremorState,
};
