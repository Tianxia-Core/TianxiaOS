// ffp: FFP-ML-215 chinese-sovereign-dual-engine rust
// File: src/forge/dual_engine.rs
// Compliance: DSS-14 (MATANGI + MAHASARASVATI + ANNAPURNA) + ENHAN3

use serde::{Deserialize, Serialize};

/// E215: Chinese Sovereign Dual Engine (Qwen 3 + DeepSeek V3/R1 Orchestration)
#[derive(Debug, PartialEq, Eq, Clone, Copy, Serialize, Deserialize)]
pub enum SovereignModelTarget {
    Qwen3MoeTabular,     // TOON/TRON formatting, high-velocity instructions
    DeepSeekV3R1Mla,     // Deep mathematical reasoning, AST refactoring, MLA
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelRoutingDecision {
    pub task_id: String,
    pub target_model: SovereignModelTarget,
    pub format_hint: String, // "TOON", "TRON", "AST"
    pub local_vuda_capable: bool,
    pub reason: String,
}

pub struct ChineseDualEngineRouter;

impl ChineseDualEngineRouter {
    pub fn route_task(task_id: &str, prompt: &str) -> ModelRoutingDecision {
        let is_deep_reasoning = prompt.contains("proof")
            || prompt.contains("theorem")
            || prompt.contains("AST")
            || prompt.contains("verify")
            || prompt.contains("invariant");

        let is_tabular_format = prompt.contains("TOON")
            || prompt.contains("TRON")
            || prompt.contains("JSON")
            || prompt.contains("table")
            || prompt.contains("schema");

        if is_deep_reasoning {
            ModelRoutingDecision {
                task_id: task_id.to_string(),
                target_model: SovereignModelTarget::DeepSeekV3R1Mla,
                format_hint: "AST".to_string(),
                local_vuda_capable: true,
                reason: "Deep multi-step reasoning, mathematical invariants, or AST verification".to_string(),
            }
        } else if is_tabular_format {
            ModelRoutingDecision {
                task_id: task_id.to_string(),
                target_model: SovereignModelTarget::Qwen3MoeTabular,
                format_hint: "TOON".to_string(),
                local_vuda_capable: true,
                reason: "Structural/tabular formatting, schema serialization, or rapid instruction dispatch".to_string(),
            }
        } else {
            ModelRoutingDecision {
                task_id: task_id.to_string(),
                target_model: SovereignModelTarget::Qwen3MoeTabular,
                format_hint: "STANDARD".to_string(),
                local_vuda_capable: true,
                reason: "Standard procedural execution path".to_string(),
            }
        }
    }
}
