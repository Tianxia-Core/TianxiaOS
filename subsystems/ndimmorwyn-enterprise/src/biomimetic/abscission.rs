// ffp: FFP-BIO-222 botanical-abscission-pruner rust
// File: src/biomimetic/abscission.rs
// Compliance: DSS-14 (KALI + CHHINNAMASTA + MAHASARASVATI) + ENHAN3

use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

/// E222: Botanical Abscission Tree Pruner (Resorbing Chlorophyll & Sealing Cork Pointers)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JsonlNode {
    pub id: String,
    pub parent_id: Option<String>,
    pub role: String,
    pub content: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AbscissionPruneResult {
    pub original_node_count: usize,
    pub surviving_node_count: usize,
    pub resorbed_invariants_count: usize,
    pub suberin_cork_sealed_pointers: usize,
    pub resorbed_chlorophyll: Vec<String>,
    pub humus_lessons_mulched: Vec<String>,
}

pub struct BotanicalAbscissionPruner {
    pub state_lock_regexes: Vec<(String, Regex)>,
}

impl BotanicalAbscissionPruner {
    pub fn new() -> Self {
        let grammar = vec![
            ("NIX_FLAKE", Regex::new(r"(?:/nix/store/[a-z0-9]{32}-[^\s]+|flake\.nix)").unwrap()),
            ("WG0_MESH", Regex::new(r"(?:10\.77\.0\.[1-5]|10\.0\.99\.\d+|wg0)").unwrap()),
            ("HW_IDENT", Regex::new(r"(?:TX-NODE-01|10770001001|AF_XDP|LimeSDR)").unwrap()),
            ("TREASURY_LCK", Regex::new(r"(?:TX-LOCK-0A|ESCROW-TRANCHE|MERKLE-SEAL)").unwrap()),
            ("CRYPTO_H", Regex::new(r"(?:sha256:[a-f0-9]{64}|b3sum)").unwrap()),
        ];
        Self {
            state_lock_regexes: grammar.into_iter().map(|(k, v)| (k.to_string(), v)).collect(),
        }
    }

    pub fn prune_tree(&self, nodes: &[JsonlNode]) -> (Vec<JsonlNode>, AbscissionPruneResult) {
        let mut resorbed = HashSet::new();
        let mut dead_ids = HashSet::new();
        let mut parent_map = HashMap::new();
        let mut humus_lessons = Vec::new();

        for node in nodes {
            parent_map.insert(node.id.clone(), node.parent_id.clone());

            // 1. Resorb chlorophyll invariants across all nodes
            for (tag, rx) in &self.state_lock_regexes {
                for mat in rx.find_iter(&node.content) {
                    resorbed.insert(format!("[{}] {}", tag, mat.as_str()));
                }
            }

            // Identify dead/failed necrotic branches
            if node.content.contains("HTTP 429")
                || node.content.contains("HTTP 500")
                || node.content.contains("Traceback (most recent")
                || node.content.contains("404: Not Found")
            {
                dead_ids.insert(node.id.clone());
                humus_lessons.push(format!("DSS14_HUMUS({}): Excised necrotic branch", node.id));
            }
        }

        // Suberin cork seal pointer resolution
        let resolve_ancestor = |mut pid: Option<String>| -> Option<String> {
            let mut seen = HashSet::new();
            while let Some(current_pid) = pid.clone() {
                if dead_ids.contains(&current_pid) && !seen.contains(&current_pid) {
                    seen.insert(current_pid.clone());
                    pid = parent_map.get(&current_pid).cloned().flatten();
                } else {
                    break;
                }
            }
            pid
        };

        let mut surviving = Vec::new();
        let mut cork_sealed = 0;

        for node in nodes {
            if dead_ids.contains(&node.id) {
                continue;
            }
            let mut updated_node = node.clone();
            if let Some(ref pid) = updated_node.parent_id {
                if dead_ids.contains(pid) {
                    updated_node.parent_id = resolve_ancestor(Some(pid.clone()));
                    cork_sealed += 1;
                }
            }
            surviving.push(updated_node);
        }

        let result = AbscissionPruneResult {
            original_node_count: nodes.len(),
            surviving_node_count: surviving.len(),
            resorbed_invariants_count: resorbed.len(),
            suberin_cork_sealed_pointers: cork_sealed,
            resorbed_chlorophyll: resorbed.into_iter().collect(),
            humus_lessons_mulched: humus_lessons,
        };

        (surviving, result)
    }
}
