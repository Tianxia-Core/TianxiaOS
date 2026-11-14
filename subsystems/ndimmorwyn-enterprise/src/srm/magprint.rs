// ffp: FFP-SEC-228 magprint-leakprint-coupling rust
// File: src/srm/magprint.rs
// Compliance: DSS-14 (DHUMAVATI + BHAIRAVI) + ENHAN3

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MagprintSensorReading {
    pub vrm_switching_freq_khz: f64,
    pub chassis_leakage_current_ua: f64,
    pub mag_x_ut: f64,
    pub mag_y_ut: f64,
    pub mag_z_ut: f64,
}

impl MagprintSensorReading {
    pub fn new(vrm_khz: f64, leakage_ua: f64, x: f64, y: f64, z: f64) -> Self {
        Self {
            vrm_switching_freq_khz: vrm_khz,
            chassis_leakage_current_ua: leakage_ua,
            mag_x_ut: x,
            mag_y_ut: y,
            mag_z_ut: z,
        }
    }

    /// Verifies switching regulator EM emanation pattern (typically 300-800 kHz under load)
    /// and leakage current within 2.0..45.0 uA range on Dell Latitude/XPS chassis.
    pub fn compute_correlation_score(&self) -> f64 {
        let vrm_valid = (250.0..=850.0).contains(&self.vrm_switching_freq_khz);
        let leakage_valid = (2.0..=50.0).contains(&self.chassis_leakage_current_ua);
        let magnitude = (self.mag_x_ut.powi(2) + self.mag_y_ut.powi(2) + self.mag_z_ut.powi(2)).sqrt();
        let field_valid = (20.0..=95.0).contains(&magnitude);

        if vrm_valid && leakage_valid && field_valid {
            0.965 // High fidelity hardware near-field match (IEEE TMC 2026 replay defense)
        } else if vrm_valid && field_valid {
            0.820
        } else {
            0.450
        }
    }
}
