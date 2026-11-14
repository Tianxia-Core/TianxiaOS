// ffp: FFP-SEC-224 srm-lamb-wave-gate rust
// File: src/srm/lamb_wave.rs
// Compliance: DSS-14 (BHAIRAVI + BAGALAMUKHI) + ENHAN3

use serde::{Deserialize, Serialize};

/// Canonical Avian [3, 2] ("t-t-t — t-t") Inter-Onset Interval Ratios: [dt1, dt2, dt_pause, dt4]
pub const PENTAD_3_2_RATIOS: [f64; 4] = [1.0, 1.0, 2.618, 1.0];
/// Inverted Duress [2, 3] ("t-t — t-t-t") Inter-Onset Interval Ratios: [dt1, dt_pause, dt3, dt4]
pub const PENTAD_2_3_DURESS: [f64; 4] = [1.0, 2.618, 1.0, 1.0];
pub const RATIO_TOLERANCE: f64 = 0.25;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TapImpulse {
    pub timestamp_us: u64,
    pub lamb_wave_dispersion_us: f64, // Δτ between S0/A0 solid wave and air acoustic wave (US8854339B2)
    pub corner_impedance_score: f64,  // CNN-GCCA-SVR top-left (0,0) vertex reflection score [0.0..1.0]
    pub imu_peak_g: f64,              // Pixel 8 Pro (10.77.0.4) 400Hz MEMS accelerometer coincidence
    pub magprint_em_corr: f64,        // MagPrint++ (IEEE TMC 2026) VRM-to-Magnetometer correlation
}

impl TapImpulse {
    pub fn new(
        timestamp_us: u64,
        dispersion_us: f64,
        impedance_score: f64,
        imu_g: f64,
        magprint_corr: f64,
    ) -> Self {
        Self {
            timestamp_us,
            lamb_wave_dispersion_us: dispersion_us,
            corner_impedance_score: impedance_score,
            imu_peak_g: imu_g,
            magprint_em_corr: magprint_corr,
        }
    }

    pub fn is_physical_tap_valid(&self) -> bool {
        (12.0..=480.0).contains(&self.lamb_wave_dispersion_us)
            && self.corner_impedance_score >= 0.78
            && self.imu_peak_g >= 0.18
            && self.magprint_em_corr >= 0.90
    }
}

#[derive(Debug, PartialEq, Eq, Clone, Copy, Serialize, Deserialize)]
pub enum CadenceClassification {
    Valid32Sovereign,
    Duress23Inversion,
    LambWaveDispersionSpoof,
    MagprintOrImpedanceMismatch,
    NonMonotonicTimestamps,
    CadenceRatioDrift,
}

pub fn classify_pentad_cadence(taps: &[TapImpulse; 5]) -> (CadenceClassification, bool, bool) {
    for tap in taps.iter() {
        if !(12.0..=480.0).contains(&tap.lamb_wave_dispersion_us) {
            return (CadenceClassification::LambWaveDispersionSpoof, false, false);
        }
        if tap.corner_impedance_score < 0.78 || tap.imu_peak_g < 0.18 || tap.magprint_em_corr < 0.90 {
            return (CadenceClassification::MagprintOrImpedanceMismatch, false, false);
        }
    }

    let mut dt = [0.0f64; 4];
    for i in 0..4 {
        if taps[i + 1].timestamp_us <= taps[i].timestamp_us {
            return (CadenceClassification::NonMonotonicTimestamps, false, false);
        }
        dt[i] = (taps[i + 1].timestamp_us - taps[i].timestamp_us) as f64;
    }

    // Check [3, 2] ("t-t-t — t-t"): dt[0], dt[1], dt[3] are fast taps; dt[2] is pause
    let base_3_2 = (dt[0] + dt[1] + dt[3]) / 3.0;
    if (40_000.0..=450_000.0).contains(&base_3_2) {
        let match_3_2 = (0..4).all(|i| {
            ((dt[i] / base_3_2) - PENTAD_3_2_RATIOS[i]).abs() <= RATIO_TOLERANCE * PENTAD_3_2_RATIOS[i]
        });
        if match_3_2 {
            return (CadenceClassification::Valid32Sovereign, true, false);
        }
    }

    // Check [2, 3] ("t-t — t-t-t") Duress: dt[0], dt[2], dt[3] are fast taps; dt[1] is pause
    let base_2_3 = (dt[0] + dt[2] + dt[3]) / 3.0;
    if (40_000.0..=450_000.0).contains(&base_2_3) {
        let match_2_3 = (0..4).all(|i| {
            ((dt[i] / base_2_3) - PENTAD_2_3_DURESS[i]).abs() <= RATIO_TOLERANCE * PENTAD_2_3_DURESS[i]
        });
        if match_2_3 {
            return (CadenceClassification::Duress23Inversion, false, true);
        }
    }

    (CadenceClassification::CadenceRatioDrift, false, false)
}
