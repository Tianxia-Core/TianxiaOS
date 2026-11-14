// ffp: FFP-FIN-203 paid-rgu-outcome-meter rust
// File: src/aurum/outcome_meter.rs
// Compliance: DSS-14 (ANNAPURNA + KAMALA + MAHASARASVATI) + ENHAN3

use serde::{Deserialize, Serialize};

/// E203: Paid.ai-Inspired Sub-FFP Outcome Metering & Gross Margin Guard
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RguOutcomeExecution {
    pub rgu_id: String,               // Strictly bounded <= 8 FFPs
    pub ffp_count: u8,
    pub client_id: String,
    pub outcome_verified: bool,       // Verified by DSS-14 or TetraLedger state lock
    pub outcome_fee_cents: i64,       // Fixed outcome price billed to enterprise client
    pub bitnet_cpu_tokens: u64,       // Tier-1/2 local tokens (€0.00 GPU cost)
    pub cloud_escalation_cost_cents: i64,
    pub microvm_ram_mb_seconds: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutcomeBillingReceipt {
    pub rgu_id: String,
    pub billable_cents: i64,
    pub gross_margin_ratio: f64,
    pub force_local_vuda_fallback: bool,
    pub toon_serialized_log: String,
}

pub fn meter_rgu_outcome(exec: &RguOutcomeExecution) -> OutcomeBillingReceipt {
    assert!(exec.ffp_count <= 8, "RGU Violation: Exceeds 8-FFP Sovereign Limit");

    let billable = if exec.outcome_verified { exec.outcome_fee_cents } else { 0 };
    let direct_cost = exec.cloud_escalation_cost_cents;
    let margin = if billable > 0 {
        ((billable - direct_cost) as f64) / (billable as f64)
    } else {
        0.0
    };

    // Enforce >= 85% Gross Margin Floor; trip fallback to local VUDA / BitNet if breached
    let force_local = margin < 0.85;

    // Emit compact TOON (Token-Oriented Object Notation) pipe-delimited telemetry row
    let toon_log = format!(
        "SCHEMA[rgu|ffp|client|bill_c|cost_c|margin|vuda_lock]\n{}|{}|{}|{}|{}|{:.4}|{}",
        exec.rgu_id, exec.ffp_count, exec.client_id, billable, direct_cost, margin, force_local
    );

    OutcomeBillingReceipt {
        rgu_id: exec.rgu_id.clone(),
        billable_cents: billable,
        gross_margin_ratio: margin,
        force_local_vuda_fallback: force_local,
        toon_serialized_log: toon_log,
    }
}
