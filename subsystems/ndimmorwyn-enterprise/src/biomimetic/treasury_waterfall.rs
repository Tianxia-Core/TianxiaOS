// ffp: FFP-FIN-225 treasury-veritas-waterfall rust
// File: src/biomimetic/treasury_waterfall.rs
// Compliance: DSS-14 (CHHINNAMASTA + KAMALA + ANNAPURNA) + ENHAN3

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// E225: 4-Tranche Veritas-Rex Cash-Lock Waterfall
/// Enforces exact Primary Escrow Settlement Lock (€628.00 Tranche 0A)
/// -> Tranche 0B Operating Liquidity Reserve (€1,572.00) -> Tranche 1 Sovereign Runway (€3,384.15) -> Tranche 2 R&D Surplus
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WaterfallAllocation {
    pub vault_key: String,
    pub cap_cents: i64,
    pub allocated_cents: i64,
    pub is_fully_funded: bool,
}

pub struct VeritasRexWaterfall {
    pub tranche_caps_cents: Vec<(String, i64)>,
}

impl VeritasRexWaterfall {
    pub fn new() -> Self {
        Self {
            tranche_caps_cents: vec![
                ("vault_0a_escrow_settlement_lock".to_string(), 628_00),
                ("vault_0b_operating_liquidity_reserve".to_string(), 1_572_00),
                ("vault_1_sovereign_runway_tranche".to_string(), 3_384_15),
                ("vault_2_rd_expansion_surplus".to_string(), i64::MAX),
            ],
        }
    }

    pub fn allocate(
        &self,
        inbound_cents: i64,
        current_vaults_cents: &HashMap<String, i64>,
    ) -> (HashMap<String, i64>, Vec<WaterfallAllocation>) {
        let mut rem = inbound_cents.max(0);
        let mut updated = current_vaults_cents.clone();
        let mut allocations = Vec::new();

        for (key, cap) in &self.tranche_caps_cents {
            let cur = *updated.get(key).unwrap_or(&0);
            let needed = if *cap == i64::MAX { i64::MAX } else { cap.saturating_sub(cur) };

            let alloc = if needed > 0 && rem > 0 {
                let a = rem.min(needed);
                rem -= a;
                a
            } else {
                0
            };

            let final_val = cur + alloc;
            updated.insert(key.clone(), final_val);
            allocations.push(WaterfallAllocation {
                vault_key: key.clone(),
                cap_cents: *cap,
                allocated_cents: final_val,
                is_fully_funded: *cap != i64::MAX && final_val >= *cap,
            });
        }

        (updated, allocations)
    }
}
