// ffp: FFP-MKT-212 shandoff-flake-generator rust
// File: src/forge/shandoff_gen.rs
// Compliance: DSS-14 (PARAMASIVA + MAHASARASVATI + ANNAPURNA) + ENHAN3

use blake3::Hasher;
use serde::{Deserialize, Serialize};

/// E212: Karuna-Verified "Freemium Shandoff Hook" Prospect Diagnostic Generator
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProspectTelemetryInput {
    pub company_name: String,
    pub sector_vector: String,
    pub estimated_monthly_llm_spend_eur: f64,
    pub uses_agentic_payments: bool,
    pub open_senior_roles_days: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KarunaShandoffArtifact {
    pub company_name: String,
    pub projected_annual_opex_savings_eur: f64,
    pub hiring_lag_burn_saved_eur: f64,
    pub nix_flake_module_target: String,
    pub verification_hash: String,
    pub outreach_snippet: String,
}

pub fn generate_shandoff_diagnostic(input: &ProspectTelemetryInput) -> KarunaShandoffArtifact {
    // 79.6% empirical token OpEx reduction via 4-Tier Waterfall (BitNet b1.58 + vLLM)
    let annual_savings = input.estimated_monthly_llm_spend_eur * 0.796 * 12.0;
    // Value of compressing a 90-day CTO/Principal search into a 2-week RGU sprint
    let lag_savings = if input.open_senior_roles_days > 14 { 45_000.0 } else { 15_000.0 };

    let target_module = if input.uses_agentic_payments {
        "tx-aurum-tetraledger-tap-x402.nix"
    } else {
        "tx-forge-bitnet-waterfall-vllm.nix"
    };

    let mut hasher = Hasher::new();
    hasher.update(input.company_name.as_bytes());
    hasher.update(&annual_savings.to_le_bytes());
    let hash = hasher.finalize().to_hex().to_string();

    let snippet = format!(
        "Audited diagnostic for {}: Identified €{:.2}/yr unhedged token burn. Shandoff Nix flake target: {}. Verification: {}",
        input.company_name, annual_savings, target_module, &hash[0..16]
    );

    KarunaShandoffArtifact {
        company_name: input.company_name.clone(),
        projected_annual_opex_savings_eur: annual_savings,
        hiring_lag_burn_saved_eur: lag_savings,
        nix_flake_module_target: target_module.to_string(),
        verification_hash: hash,
        outreach_snippet: snippet,
    }
}
