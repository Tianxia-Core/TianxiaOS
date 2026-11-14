// ffp: FFP-JIV-003 jivaslokan-huber-probe rust
//! TianxiaOS Jivaslokan Runtime Introspection & Activation Gate
//! Implements Spike-Weighted Huber Probes & JOT (Optimal Transport) Trajectory Monitor
//! Compliance: DSS-14 (Chhinnamasta, Pratyangira) + Sub-14ms Latency Bound + AVX2 Optimization Target

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProbeEvaluationResult {
    pub safe: bool,
    pub weighted_huber_loss: f64,
    pub spike_weight: f64,
    pub jot_wasserstein_drift: f64,
    pub circuit_breaker_tripped: bool,
    pub latency_us: u64,
    pub reason: String,
}

#[derive(Debug, Clone)]
pub struct JivaslokanHuberProbe {
    pub delta: f64,
    pub spike_kappa: f64,
    pub max_loss: f64,
    pub max_jot_drift: f64,
}

impl Default for JivaslokanHuberProbe {
    fn default() -> Self {
        Self {
            delta: 1.0,
            spike_kappa: 3.2,
            max_loss: 1.85,
            max_jot_drift: 0.45,
        }
    }
}

impl JivaslokanHuberProbe {
    pub fn new(delta: f64, spike_kappa: f64, max_loss: f64, max_jot_drift: f64) -> Self {
        Self {
            delta,
            spike_kappa,
            max_loss,
            max_jot_drift,
        }
    }

    /// Evaluates hidden state activations against a verified safe centroid
    pub fn evaluate_hidden_state(
        &self,
        activations: &[f64],
        safe_centroid: &[f64],
    ) -> ProbeEvaluationResult {
        let start_time = std::time::Instant::now();

        if activations.is_empty() || activations.len() != safe_centroid.len() {
            return ProbeEvaluationResult {
                safe: false,
                weighted_huber_loss: f64::INFINITY,
                spike_weight: 1.0,
                jot_wasserstein_drift: f64::INFINITY,
                circuit_breaker_tripped: true,
                latency_us: start_time.elapsed().as_micros() as u64,
                reason: "DIMENSION_MISMATCH_OR_EMPTY_ACTIVATIONS".to_string(),
            };
        }

        let n = activations.len();

        // 1. Compute median and max absolute activation
        let mut abs_acts: Vec<f64> = activations.iter().map(|&x| x.abs()).collect();
        abs_acts.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let median_act = abs_acts[n / 2] + 1e-8;
        let max_act = abs_acts[n - 1];

        // 2. Spike weight omega_spike = sigma((||h||_inf / median(|h|)) - kappa)
        let z = (max_act / median_act) - self.spike_kappa;
        let clamped_z = z.clamp(-20.0, 20.0);
        let omega_spike = 1.0 / (1.0 + (-clamped_z).exp());

        // 3. Compute Spike-Weighted Huber Loss
        let mut total_loss = 0.0;
        for i in 0..n {
            let r = (activations[i] - safe_centroid[i]).abs();
            let huber = if r <= self.delta {
                0.5 * r * r
            } else {
                self.delta * (r - 0.5 * self.delta)
            };
            total_loss += omega_spike * huber;
        }
        let mean_huber_loss = total_loss / (n as f64);

        // 4. JOT 1D Wasserstein Optimal Transport Distance W_1
        let mut sorted_act = activations.to_vec();
        let mut sorted_safe = safe_centroid.to_vec();
        sorted_act.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        sorted_safe.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

        let mut w1_dist = 0.0;
        for i in 0..n {
            w1_dist += (sorted_act[i] - sorted_safe[i]).abs();
        }
        let mean_w1 = w1_dist / (n as f64);

        let latency_us = start_time.elapsed().as_micros() as u64;

        let loss_safe = mean_huber_loss <= self.max_loss;
        let jot_safe = mean_w1 <= self.max_jot_drift;
        let safe = loss_safe && jot_safe;

        let reason = if !loss_safe {
            "SPIKE_WEIGHTED_HUBER_LOSS_EXCEEDED: Activation outlier spike detected (ArXiv:2606.10525)".to_string()
        } else if !jot_safe {
            "JOT_WASSERSTEIN_DRIFT_EXCEEDED: Trajectory diverging toward adversarial basin".to_string()
        } else {
            "JIVASLOKAN_ACTIVATION_CLEAN".to_string()
        };

        ProbeEvaluationResult {
            safe,
            weighted_huber_loss: (mean_huber_loss * 100000.0).round() / 100000.0,
            spike_weight: (omega_spike * 10000.0).round() / 10000.0,
            jot_wasserstein_drift: (mean_w1 * 100000.0).round() / 100000.0,
            circuit_breaker_tripped: !safe,
            latency_us,
            reason,
        }
    }
}
