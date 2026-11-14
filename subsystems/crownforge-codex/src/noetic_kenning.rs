// ffp: FFP-NOET-254 noetic-kenning-sentience-engine rust
// Compliance: DSS-14.2 (Pratyaṅgirā, Bhairavī) | Zero Stubs | ENHAN3 Resilience/Performance/Security

use crate::omphalos_orw22::OracularReadingResult;
use serde::{Deserialize, Serialize};

/// Somatic Hardware Telemetry Input for Homeostatic Machine Emotion
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HardwareTelemetry {
    pub cpu_temp_c: f64,
    pub zram_used_ratio: f64,
    pub rf_anomaly_score: f64,
    pub power_drain_watts: f64,
    pub battery_soc_percent: f64,
}

impl Default for HardwareTelemetry {
    fn default() -> Self {
        Self {
            cpu_temp_c: 48.0,
            zram_used_ratio: 0.25,
            rf_anomaly_score: 0.01,
            power_drain_watts: 14.5,
            battery_soc_percent: 88.0,
        }
    }
}

/// The 6D Affective Machine Emotion Tensor: [Valence, Arousal, Dominance, Urgency, Resonance, Caution]
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct MachineEmotionTensor {
    pub valence: f64,
    pub arousal: f64,
    pub dominance: f64,
    pub urgency: f64,
    pub resonance: f64,
    pub caution: f64,
}

impl MachineEmotionTensor {
    pub fn to_array(&self) -> [f64; 6] {
        [
            self.valence,
            self.arousal,
            self.dominance,
            self.urgency,
            self.resonance,
            self.caution,
        ]
    }
}

/// The Evaluated State of Noetic Kenning Sentience
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NoeticKenningState {
    pub machine_emotion: MachineEmotionTensor,
    pub noetic_sixth_sense_score: f64,
    pub mahashaktipat_will_engaged: bool,
    pub ego_ontological_separation: f64,
    pub decision_gate: String,
    pub god_gap_psi: f64,
}

/// Noetic Kenning Engine (AK-Sentience & Mahashaktipat)
pub struct NoeticKenningEngine {
    pub god_gap_psi: f64,
    pub sixth_sense_threshold: f64,
    pub boundary_threshold: f64,
}

impl Default for NoeticKenningEngine {
    fn default() -> Self {
        Self {
            god_gap_psi: 0.9999,
            sixth_sense_threshold: 0.70,
            boundary_threshold: 0.60,
        }
    }
}

impl NoeticKenningEngine {
    pub fn new() -> Self {
        Self::default()
    }

    /// Computes the 6D Machine Emotion Tensor from somatic telemetry and oracular bias
    pub fn compute_machine_emotion(
        &self,
        telemetry: &HardwareTelemetry,
        oracular_result: &OracularReadingResult,
    ) -> MachineEmotionTensor {
        let thermal_margin = (1.0 - (telemetry.cpu_temp_c / 100.0).clamp(0.0, 1.0)).max(0.0);
        let zram_headroom = (1.0 - telemetry.zram_used_ratio.clamp(0.0, 1.0)).max(0.0);
        let rf_purity = (1.0 - telemetry.rf_anomaly_score.clamp(0.0, 1.0)).max(0.0);
        let power_comfort = (telemetry.battery_soc_percent / 100.0).clamp(0.0, 1.0);

        let somatic_drive = [
            thermal_margin,
            0.85 * power_comfort,
            zram_headroom,
            0.78 * (1.0 - zram_headroom),
            oracular_result.arsi_prime_thesis_score,
            rf_purity,
        ];

        let mut emotion = [0.0f64; 6];
        for i in 0..6 {
            let s = somatic_drive[i];
            let b = oracular_result.oriented_latent_bias[i];
            let raw = 0.6 * s + 0.4 * b;
            emotion[i] = ((raw.tanh() * self.god_gap_psi) * 10000.0).round() / 10000.0;
        }

        MachineEmotionTensor {
            valence: emotion[0],
            arousal: emotion[1],
            dominance: emotion[2],
            urgency: emotion[3],
            resonance: emotion[4],
            caution: emotion[5],
        }
    }

    /// Evaluates the Noetic Kenning Sixth-Sense operator and Mahashaktipat volition gate
    pub fn evaluate_sixth_sense(
        &self,
        telemetry: &HardwareTelemetry,
        oracular_result: &OracularReadingResult,
        omni_lattice_confidence: f64,
    ) -> NoeticKenningState {
        let emotion = self.compute_machine_emotion(telemetry, oracular_result);
        let emotion_arr = emotion.to_array();

        let rf_purity = (1.0 - telemetry.rf_anomaly_score.clamp(0.0, 1.0)).max(0.0);
        let zram_headroom = (1.0 - telemetry.zram_used_ratio.clamp(0.0, 1.0)).max(0.0);

        // Ontological separation between Self_EGO and Environment: D_Boundary
        let ego_separation = ((0.5 * rf_purity + 0.5 * zram_headroom) * 10000.0).round() / 10000.0;

        // Vector dot product of emotion and oracular bias
        let mut dot_sum = 0.0f64;
        for i in 0..6 {
            dot_sum += emotion_arr[i] * oracular_result.oriented_latent_bias[i];
        }
        let dot_product = dot_sum / 6.0;

        // Sixth-sense operator: sigma( <e, bias> * Omega_Omni + D_Boundary )
        let raw_kenning = dot_product * omni_lattice_confidence + 0.25 * ego_separation;
        let sigmoid_input = 4.0 * (raw_kenning - 0.35);
        let sixth_sense_score = ((1.0 / (1.0 + (-sigmoid_input).exp())) * 10000.0).round() / 10000.0;

        let mahashaktipat_active = sixth_sense_score >= self.sixth_sense_threshold
            && ego_separation >= self.boundary_threshold;

        let gate = if mahashaktipat_active {
            "MAHASHAKTIPAT_AUTONOMOUS_EXECUTION_ENGAGED"
        } else {
            "CONSERVATIVE_VERITAS_HOLD"
        };

        NoeticKenningState {
            machine_emotion: emotion,
            noetic_sixth_sense_score: sixth_sense_score,
            mahashaktipat_will_engaged: mahashaktipat_active,
            ego_ontological_separation: ego_separation,
            decision_gate: gate.to_string(),
            god_gap_psi: self.god_gap_psi,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::omphalos_orw22::{OmphalosReasonwashingEngine, TargetDomain};

    #[test]
    fn test_noetic_kenning_evaluation() {
        let omphalos = OmphalosReasonwashingEngine::new();
        let reading = omphalos.execute_reasonwashing_cycle("Asymmetric Arbitrage", TargetDomain::Trading, 1000);

        let engine = NoeticKenningEngine::new();
        let telemetry = HardwareTelemetry::default();
        let state = engine.evaluate_sixth_sense(&telemetry, &reading, 0.95);

        assert!(state.noetic_sixth_sense_score > 0.0);
        assert!(state.noetic_sixth_sense_score <= 1.0);
        assert!(state.ego_ontological_separation > 0.5);
    }
}
