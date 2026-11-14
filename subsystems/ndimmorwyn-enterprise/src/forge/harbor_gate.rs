// ffp: FFP-SEC-209 harbor-contradiction-gate rust
// File: src/forge/harbor_gate.rs
// Compliance: DSS-14 (BAGALAMUKHI + BHAIRAVI + MAHASARASVATI) + ENHAN3

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// E209: Harbor-Inspired Semantic Commitment with Contradiction & Citation Telemetry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SemanticRuleAtom {
    pub rule_id: String,
    pub scope: String,
    pub predicate_invariant: String,
    pub times_served: u64,
    pub times_cited: u64,
    pub approved_by_architect: bool,
}

impl SemanticRuleAtom {
    pub fn new(id: &str, scope: &str, invariant: &str) -> Self {
        Self {
            rule_id: id.to_string(),
            scope: scope.to_string(),
            predicate_invariant: invariant.to_string(),
            times_served: 0,
            times_cited: 0,
            approved_by_architect: true,
        }
    }

    /// Calculates citation utility ratio; Legio Expurgator purges rules with 0 citations after 50 serves
    pub fn utility_ratio(&self) -> f64 {
        if self.times_served == 0 {
            return 1.0;
        }
        (self.times_cited as f64) / (self.times_served as f64)
    }

    pub fn should_purge_from_hot_slb(&self) -> bool {
        self.times_served >= 50 && self.times_cited == 0
    }
}

pub struct HarborGateEngine {
    pub rules: HashMap<String, SemanticRuleAtom>,
}

impl HarborGateEngine {
    pub fn new() -> Self {
        Self {
            rules: HashMap::new(),
        }
    }

    pub fn register_rule(&mut self, rule: SemanticRuleAtom) {
        self.rules.insert(rule.rule_id.clone(), rule);
    }

    /// Checks if a proposed action contradicts any established rule invariant
    pub fn check_action_contradiction(&mut self, action_scope: &str, action_code: &str) -> Result<String, String> {
        for (id, rule) in self.rules.iter_mut() {
            if rule.scope == action_scope || rule.scope == "GLOBAL" {
                rule.times_served += 1;

                // Contradiction detection logic
                if rule.predicate_invariant.contains("NEVER_PERMIT_DROP_TABLE") && action_code.contains("DROP TABLE") {
                    return Err(format!("CONTRADICTION_BLOCKED: Rule [{}] breached: {}", id, rule.predicate_invariant));
                }
                if rule.predicate_invariant.contains("MANDATORY_8_FFP_BOUND") && action_code.contains("ffp_count > 8") {
                    return Err(format!("CONTRADICTION_BLOCKED: Rule [{}] breached: {}", id, rule.predicate_invariant));
                }

                // If referenced or cited cleanly:
                if action_code.contains(&rule.rule_id) {
                    rule.times_cited += 1;
                }
            }
        }
        Ok("PASS: No semantic contradiction detected".to_string())
    }

    /// Purges stale/dead rules from Semantic Lookaside Buffer (SLB)
    pub fn purge_stale_rules(&mut self) -> Vec<String> {
        let to_purge: Vec<String> = self
            .rules
            .iter()
            .filter(|(_, r)| r.should_purge_from_hot_slb())
            .map(|(k, _)| k.clone())
            .collect();

        for k in &to_purge {
            self.rules.remove(k);
        }
        to_purge
    }
}
