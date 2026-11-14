// ffp: FFP-MURUA-SRM acoustic-srm-gate rust
//! SRM Lamb-Wave Acoustic-Spatial Mailbox Assay & Cryptographic Proof-of-Sweep Oracle
//! Implements non-invasive acoustic fullness detection on EN 13724 steel mailboxes
//! and zero-trust proof-of-inspection attestation.

use blake3::Hasher;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SteelPlateProperties {
    pub thickness_m: f64,          // d = 0.0012 m (1.2 mm)
    pub density_kg_m3: f64,        // rho_s = 7850 kg/m^3
    pub youngs_modulus_pa: f64,    // E = 2.0e11 Pa
    pub poissons_ratio: f64,       // nu = 0.30
    pub tray_width_m: f64,         // 0.35 m
    pub tray_depth_m: f64,         // 0.25 m
    pub f0_empty_hz: f64,          // Base resonance f0 ~ 420.0 Hz
    pub zeta_empty: f64,           // Unloaded damping zeta ~ 0.004
}

impl Default for SteelPlateProperties {
    fn default() -> Self {
        Self {
            thickness_m: 0.0012,
            density_kg_m3: 7850.0,
            youngs_modulus_pa: 2.0e11,
            poissons_ratio: 0.30,
            tray_width_m: 0.35,
            tray_depth_m: 0.25,
            f0_empty_hz: 420.0,
            zeta_empty: 0.004,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AcousticSweepMeasurement {
    pub measured_f0_hz: f64,
    pub measured_zeta: f64,
    pub delta_f0_hz: f64,
    pub delta_inv_q: f64,
    pub estimated_payload_mass_g: f64,
    pub compartment_status: String,
    pub confidence: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProofOfSweepToken {
    pub mailbox_id: String,
    pub inspector_node_ip: String,
    pub timestamp_utc: DateTime<Utc>,
    pub geohash: String,
    pub wifi_bssid_hash: String,
    pub acoustic_signature_blake3: String,
    pub proof_attestation_hash: String,
    pub outcome_status: String,
}

pub struct SrmAcousticGate {
    pub plate: SteelPlateProperties,
}

impl SrmAcousticGate {
    pub fn new(plate: SteelPlateProperties) -> Self {
        Self { plate }
    }

    /// Computes flexural rigidity D = E*d^3 / (12*(1-nu^2))
    pub fn flexural_rigidity(&self) -> f64 {
        let d = self.plate.thickness_m;
        let num = self.plate.youngs_modulus_pa * d * d * d;
        let den = 12.0 * (1.0 - self.plate.poissons_ratio * self.plate.poissons_ratio);
        num / den
    }

    /// Predicts modal frequency shift and damping change given added mass in grams
    pub fn predict_loaded_acoustics(&self, added_mass_grams: f64) -> (f64, f64, f64) {
        let tray_area = self.plate.tray_width_m * self.plate.tray_depth_m;
        let mass_kg = (added_mass_grams / 1000.0).max(0.0);
        let delta_m_double_prime = mass_kg / tray_area; // kg/m^2

        let plate_areal_mass = self.plate.density_kg_m3 * self.plate.thickness_m; // kg/m^2
        let mass_ratio = delta_m_double_prime / plate_areal_mass;

        // f_loaded = f_empty * (1 + delta_m'' / (rho_s * d))^(-0.5)
        let f_loaded = self.plate.f0_empty_hz * (1.0 + mass_ratio).powf(-0.5);

        // Added viscoelastic boundary damping: paper fiber damping scales with mass
        let zeta_loaded = self.plate.zeta_empty + 0.0003 * added_mass_grams.clamp(0.0, 500.0);
        let delta_inv_q = 2.0 * (zeta_loaded - self.plate.zeta_empty);

        (f_loaded, zeta_loaded, delta_inv_q)
    }

    /// Analyzes raw frequency and damping measurement to classify compartment status
    pub fn analyze_measurement(&self, measured_f0_hz: f64, measured_zeta: f64) -> AcousticSweepMeasurement {
        let delta_f0 = measured_f0_hz - self.plate.f0_empty_hz;
        let delta_inv_q = 2.0 * (measured_zeta - self.plate.zeta_empty);

        let plate_areal_mass = self.plate.density_kg_m3 * self.plate.thickness_m;
        let tray_area = self.plate.tray_width_m * self.plate.tray_depth_m;

        // Invert f_loaded = f_empty * (1 + ratio)^(-0.5) => ratio = (f_empty / f_loaded)^2 - 1
        let ratio = if measured_f0_hz > 10.0 {
            let term = self.plate.f0_empty_hz / measured_f0_hz;
            (term * term - 1.0).max(0.0)
        } else {
            0.0
        };

        let est_mass_kg = ratio * plate_areal_mass * tray_area;
        let est_mass_g = est_mass_kg * 1000.0;

        // Classification threshold: delta_f0 <= -5.0 Hz and delta_inv_q >= 0.010
        let (status, confidence) = if delta_f0 <= -6.0 && delta_inv_q >= 0.012 {
            let conf = (delta_inv_q / 0.035).clamp(0.70, 0.99);
            ("MAIL_PRESENT_LOADED".to_string(), conf)
        } else if delta_f0.abs() < 4.0 && delta_inv_q < 0.008 {
            ("EMPTY_COMPARTMENT".to_string(), 0.96)
        } else {
            ("AMBIGUOUS_BORDERLINE".to_string(), 0.50)
        };

        AcousticSweepMeasurement {
            measured_f0_hz,
            measured_zeta,
            delta_f0_hz: delta_f0,
            delta_inv_q,
            estimated_payload_mass_g: (est_mass_g * 10.0).round() / 10.0,
            compartment_status: status,
            confidence,
        }
    }

    /// Generates cryptographic Proof-of-Sweep token verifying physical inspection
    pub fn generate_proof_of_sweep(
        &self,
        mailbox_id: &str,
        inspector_node_ip: &str,
        geohash: &str,
        wifi_bssid_hash: &str,
        raw_audio_samples: &[f32],
        outcome_status: &str,
    ) -> ProofOfSweepToken {
        let ts = Utc::now();

        // Hash the 1.5s acoustic waveform
        let mut audio_hasher = Hasher::new();
        for sample in raw_audio_samples {
            audio_hasher.update(&sample.to_le_bytes());
        }
        let acoustic_sig = audio_hasher.finalize().to_hex().to_string();

        // Hash all proof components into sovereign attestation
        let mut proof_hasher = Hasher::new();
        proof_hasher.update(mailbox_id.as_bytes());
        proof_hasher.update(inspector_node_ip.as_bytes());
        proof_hasher.update(ts.to_rfc3339().as_bytes());
        proof_hasher.update(geohash.as_bytes());
        proof_hasher.update(wifi_bssid_hash.as_bytes());
        proof_hasher.update(acoustic_sig.as_bytes());
        proof_hasher.update(outcome_status.as_bytes());
        let proof_hash = proof_hasher.finalize().to_hex().to_string();

        ProofOfSweepToken {
            mailbox_id: mailbox_id.to_string(),
            inspector_node_ip: inspector_node_ip.to_string(),
            timestamp_utc: ts,
            geohash: geohash.to_string(),
            wifi_bssid_hash: wifi_bssid_hash.to_string(),
            acoustic_signature_blake3: acoustic_sig,
            proof_attestation_hash: proof_hash,
            outcome_status: outcome_status.to_string(),
        }
    }

    /// Verifies the cryptographic integrity of a ProofOfSweepToken
    pub fn verify_token_integrity(&self, token: &ProofOfSweepToken) -> bool {
        let mut proof_hasher = Hasher::new();
        proof_hasher.update(token.mailbox_id.as_bytes());
        proof_hasher.update(token.inspector_node_ip.as_bytes());
        proof_hasher.update(token.timestamp_utc.to_rfc3339().as_bytes());
        proof_hasher.update(token.geohash.as_bytes());
        proof_hasher.update(token.wifi_bssid_hash.as_bytes());
        proof_hasher.update(token.acoustic_signature_blake3.as_bytes());
        proof_hasher.update(token.outcome_status.as_bytes());
        let expected_hash = proof_hasher.finalize().to_hex().to_string();
        token.proof_attestation_hash == expected_hash
    }
}
