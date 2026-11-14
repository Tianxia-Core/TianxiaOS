// ffp: FFP-MURUA-LIB murua-suite-lib rust
//! Murua Sovereign Telemetry & Actuation Suite (v8.4-OMEGA)
//! Counteracting Asymmetric Priority Buffering, UPU Terminal-Dues Gaming & Oxbow Hub Stagnation
//! Complies strictly with DSS-14.2, Polyglot FFP-First, and SLECO-SO++ Execution Standard.

pub mod acoustic;
pub mod barabasi;
pub mod dss14;
pub mod escrow;
pub mod softem;
pub mod toon;

pub use acoustic::{
    AcousticSweepMeasurement, ProofOfSweepToken, SrmAcousticGate, SteelPlateProperties,
};
pub use barabasi::{
    BarabasiOxbowEstimator, CCBDScore, CorridorParameters, DeliveryPrediction, DwellDecomposition,
};
pub use dss14::{MahavidyaDomain, MerkleProvenanceLedger, TelemetryRecord};
pub use escrow::{
    EscrowCase, StatutoryDepotInquiry, VeritasEscrowActuator, VeritasRexDisputeDossier,
};
pub use softem::{CarrierClaim, SoftemProbe, SoftemVerificationResult};
pub use toon::{ToonTelemetryRow, ToonTronCodec, TronShipmentNode};

pub const VERSION: &str = "8.4.0-OMEGA";
pub const SPEC_CLASSIFICATION: &str = "TianxiaOS / Ndimmôrwyn / Murua Enterprise Architecture";
