// ffp: FFP-MURUA-SOFTEM softem-probe rust
//! SOFTEM Factual Attribution Probe & ENHAN3 Anti-Confabulation Shield
//! Rejects AI logistics hallucinations (such as OCR locker redirection for unbarcoded mail)
//! via symbolic ontology constraints and spike-weighted Huber loss verification.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CarrierClaim {
    pub claim_id: String,
    pub statement: String,
    pub has_s10_barcode: bool,
    pub has_edi_hook: bool,
    pub claims_locker_redirection: bool,
    pub claims_sms_pin_delivery: bool,
    pub statutory_anchor_cited: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SoftemVerificationResult {
    pub claim_id: String,
    pub passed_ontology_filter: bool,
    pub softem_loss: f64,
    pub attribution_score: f64,
    pub is_hallucination: bool,
    pub action_taken: String,
    pub diagnostic_reason: String,
}

pub struct SoftemProbe {
    pub epsilon_huber: f64,
    pub beta_softmax: f64,
    pub fact_threshold: f64,
}

impl Default for SoftemProbe {
    fn default() -> Self {
        Self {
            epsilon_huber: 0.15,
            beta_softmax: 2.0,
            fact_threshold: 0.70,
        }
    }
}

impl SoftemProbe {
    pub fn new(epsilon_huber: f64, beta_softmax: f64, fact_threshold: f64) -> Self {
        Self {
            epsilon_huber,
            beta_softmax,
            fact_threshold,
        }
    }

    /// Symbolic System-1 constraint evaluation against Postiseadus & UPU QLUG ontology
    pub fn verify_symbolic_ontology(&self, claim: &CarrierClaim) -> (bool, String) {
        // Core invariant: unbarcoded items without EDI CANNOT trigger pakiautomaat locker SMS codes
        if !claim.has_s10_barcode && !claim.has_edi_hook {
            if claim.claims_locker_redirection || claim.claims_sms_pin_delivery {
                return (
                    false,
                    "VIOLATION: Untracked lihtkiri cannot trigger automated parcel locker SMS injection without S10/EDI barcode. Confabulation detected."
                        .to_string(),
                );
            }
        }

        (true, "VALID: Claim satisfies UPU/Postiseadus domain invariants.".to_string())
    }

    /// Compute single-point Huber loss: H(y, y_hat, eps)
    pub fn huber_loss(&self, y: f64, y_hat: f64) -> f64 {
        let diff = (y - y_hat).abs();
        if diff <= self.epsilon_huber {
            0.5 * diff * diff
        } else {
            self.epsilon_huber * (diff - 0.5 * self.epsilon_huber)
        }
    }

    /// Evaluates activation vector against factual anchors using spike-weighted Huber loss
    /// L_SOFTEM = (1/N) * sum( w_i * Huber(delta_hat_i, delta_real_i, eps) )
    /// w_i = softmax( beta * max(0, delta_real_i) ) * N
    pub fn compute_spike_weighted_loss(
        &self,
        predicted_deltas: &[f64],
        ground_truth_deltas: &[f64],
    ) -> f64 {
        let n = predicted_deltas.len();
        if n == 0 || n != ground_truth_deltas.len() {
            return 1.0;
        }

        // 1. Calculate unnormalized softmax exponents: exp(beta * max(0, delta_real_i))
        let mut exp_vals = Vec::with_capacity(n);
        let mut sum_exp = 0.0;
        for &gt in ground_truth_deltas {
            let val = (self.beta_softmax * gt.max(0.0)).exp();
            exp_vals.push(val);
            sum_exp += val;
        }

        if sum_exp <= 1e-12 {
            sum_exp = 1.0;
        }

        // 2. Weights: omega_i = (exp_vals[i] / sum_exp) * N
        // 3. Weighted Huber sum
        let mut total_loss = 0.0;
        for i in 0..n {
            let omega_i = (exp_vals[i] / sum_exp) * (n as f64);
            let loss_i = self.huber_loss(predicted_deltas[i], ground_truth_deltas[i]);
            total_loss += omega_i * loss_i;
        }

        total_loss / (n as f64)
    }

    /// Comprehensive verification pipeline integrating System-1 ontology and SOFTEM loss
    pub fn verify_claim(
        &self,
        claim: &CarrierClaim,
        predicted_activations: &[f64],
        ground_truth_anchors: &[f64],
    ) -> SoftemVerificationResult {
        let (ontology_ok, ontology_msg) = self.verify_symbolic_ontology(claim);

        let loss = self.compute_spike_weighted_loss(predicted_activations, ground_truth_anchors);
        // Attribution score in [0.0, 1.0]: higher means more factual
        let attribution_score = (1.0 / (1.0 + loss * 5.0)).clamp(0.0, 1.0);

        let is_hallucination = !ontology_ok || attribution_score < self.fact_threshold;

        let (action, diagnostic) = if is_hallucination {
            (
                "BOTANICAL_LEAF_ABSCISSION_PRUNED".to_string(),
                format!("PRUNED [STATE_LOCK_ZERO_LOSS]: {}", ontology_msg),
            )
        } else {
            (
                "FACTUAL_ANCHOR_VERIFIED".to_string(),
                format!(
                    "VERIFIED: Attribution score {:.3} >= threshold {:.3}",
                    attribution_score, self.fact_threshold
                ),
            )
        };

        SoftemVerificationResult {
            claim_id: claim.claim_id.clone(),
            passed_ontology_filter: ontology_ok,
            softem_loss: loss,
            attribution_score,
            is_hallucination,
            action_taken: action,
            diagnostic_reason: diagnostic,
        }
    }
}
