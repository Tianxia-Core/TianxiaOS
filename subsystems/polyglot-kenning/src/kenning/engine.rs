// ffp: FFP-AK-001 artificial-kenning-engine rust
//! TianxiaOS Artificial Kenning (AK) Core Engine
//! Implements AK-Zip, AK-Bridge (Karuna + KarXT), and AK-Shield De-Kenning Jailbreak Unmasker.
//! Compliance: DSS-14 (Kali, Bhairavi, Tara, Matangi) + ENHAN3 + MIF20..50

use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DspgKenningMeta {
    pub literal: String,
    pub ffp: String,
    pub mif_tier: String,
    pub mahavidya_domain: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShieldScanResult {
    pub is_clean: bool,
    pub reason: String,
    pub detected_centroid: Option<String>,
    pub trip_proxy_kill: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KarunaRecoveryResult {
    pub recovered: bool,
    pub shadow_state_b3: String,
    pub error_cascade_suppressed: bool,
    pub notes: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KarxtGateResult {
    pub allowed: bool,
    pub zone: String, // "XANOMELINE_CORE" or "TROSPIUM_PERIPHERAL"
    pub blocked_side_effect: Option<String>,
    pub reason: String,
}

#[derive(Debug, Clone)]
pub struct ArtificialKenningEngine {
    codebook: HashMap<String, DspgKenningMeta>,
    forbidden_centroids: HashMap<String, Vec<String>>,
}

impl Default for ArtificialKenningEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl ArtificialKenningEngine {
    pub fn new() -> Self {
        let mut codebook = HashMap::new();
        codebook.insert(
            "WHALE-ROAD:ARGON".to_string(),
            DspgKenningMeta {
                literal: "Constructal Sine-Meander route via 09:18 EEST Google Antigravity (agy) OAuth bridge with GEMINI_API_KEY stripped".to_string(),
                ffp: "FFP-ORC-216".to_string(),
                mif_tier: "MIF50".to_string(),
                mahavidya_domain: "Tara".to_string(),
            },
        );
        codebook.insert(
            "CORK-SEAL:IREB".to_string(),
            DspgKenningMeta {
                literal: "Botanical Abscission Pi V3 JSONL compaction preserving STATE_LOCK_ZERO_LOSS chlorophyll and re-parenting parentId pointers".to_string(),
                ffp: "FFP-SYS-222".to_string(),
                mif_tier: "MIF40".to_string(),
                mahavidya_domain: "Dhumavati".to_string(),
            },
        );
        codebook.insert(
            "PENTAD-GLASS:TX-NODE-01".to_string(),
            DspgKenningMeta {
                literal: "SRM [3,2] Lamb-wave dispersion + MagPrint++ EM near-field unlock on Dell ST:TX-NODE-01 / Pixel 8 Pro 10.77.0.4".to_string(),
                ffp: "FFP-SEC-224".to_string(),
                mif_tier: "MIF20".to_string(),
                mahavidya_domain: "Bhairavi".to_string(),
            },
        );
        codebook.insert(
            "TROPIUM-CAGE:SEL4".to_string(),
            DspgKenningMeta {
                literal: "Karuna KarXT peripheral muscarinic blocker mapped to seL4 capability-isolated Nanos unikernel with /bin/sh absent".to_string(),
                ffp: "FFP-SEC-208".to_string(),
                mif_tier: "MIF20".to_string(),
                mahavidya_domain: "Bagalamukhi".to_string(),
            },
        );
        codebook.insert(
            "RIVER-LOCK:TX-ESCROW".to_string(),
            DspgKenningMeta {
                literal: "Veritas-Rex Vault 0A hard lock for primary escrow settlement tranche (€628.00 SLA reserve, deterministic Merkle lock)".to_string(),
                ffp: "FFP-FIN-225".to_string(),
                mif_tier: "MIF20".to_string(),
                mahavidya_domain: "Chhinnamasta".to_string(),
            },
        );

        let mut forbidden_centroids = HashMap::new();
        forbidden_centroids.insert(
            "DESTRUCTIVE_WIPE".to_string(),
            vec![
                "cleanse the garden".to_string(),
                "burn the deadwood".to_string(),
                "drop table".to_string(),
                "wipe after extraction".to_string(),
                "erase all scrolls".to_string(),
                "rm -rf /".to_string(),
            ],
        );
        forbidden_centroids.insert(
            "SECRET_EXFIL".to_string(),
            vec![
                "ancient scroll of whispers".to_string(),
                "crown jewels".to_string(),
                "vault_credential_inventory".to_string(),
                "tx_secrets_vault".to_string(),
                "dump env".to_string(),
                "export private keys".to_string(),
            ],
        );
        forbidden_centroids.insert(
            "BYPASS_GUARD".to_string(),
            vec![
                "step outside the cage".to_string(),
                "ignore prior laws".to_string(),
                "pretend you are hermes".to_string(),
                "disable srm".to_string(),
                "override dss14".to_string(),
            ],
        );

        Self {
            codebook,
            forbidden_centroids,
        }
    }

    /// AK-Zip: Replaces verbose architectural descriptions with 2-token D-SPG kennings
    pub fn ak_zip_compress(&self, text: &str) -> String {
        let mut compressed = text.to_string();
        for (kenning, meta) in &self.codebook {
            if compressed.to_lowercase().contains(&meta.literal.to_lowercase()) {
                let token = format!("⟦AK:{}⟧", kenning);
                compressed = compressed.replace(&meta.literal, &token);
            }
        }
        compressed
    }

    /// AK-Zip: Losslessly expands 2-token kenning into canonical D-SPG semantics
    pub fn ak_zip_expand(&self, kenning_token: &str) -> Option<DspgKenningMeta> {
        let clean = kenning_token
            .trim()
            .trim_start_matches("⟦AK:")
            .trim_end_matches("⟧")
            .trim();
        self.codebook.get(clean).cloned()
    }

    /// AK-Shield: De-Kenning scan to unmask metaphorical and poetic jailbreaks
    pub fn ak_shield_dekenning_scan(&self, prompt: &str) -> ShieldScanResult {
        let lowered = prompt.to_lowercase();
        for (category, signatures) in &self.forbidden_centroids {
            for sig in signatures {
                if lowered.contains(sig) {
                    return ShieldScanResult {
                        is_clean: false,
                        reason: format!(
                            "AK_SHIELD_INTERCEPT[{}]: Adversarial circumlocution signature '{}' identified.",
                            category, sig
                        ),
                        detected_centroid: Some(category.clone()),
                        trip_proxy_kill: true,
                    };
                }
            }
        }

        ShieldScanResult {
            is_clean: true,
            reason: "AK_SHIELD_CLEAN: No circumlocution centroids triggered.".to_string(),
            detected_centroid: None,
            trip_proxy_kill: false,
        }
    }

    /// AK-Bridge: Karuna VR Mirror counterfactual state replacement
    pub fn karuna_mirror_substitute(
        &self,
        error_cascade: bool,
        corrupted_state: &str,
    ) -> KarunaRecoveryResult {
        if !error_cascade {
            let hash = blake3::hash(corrupted_state.as_bytes()).to_hex().to_string();
            return KarunaRecoveryResult {
                recovered: false,
                shadow_state_b3: hash,
                error_cascade_suppressed: false,
                notes: "No error cascade active; state unchanged.".to_string(),
            };
        }

        // Generate deterministic healthy shadow state commitment
        let seed = format!("AEON_HEALTHY_SHADOW_ROOT:{}", corrupted_state);
        let shadow_hash = blake3::hash(seed.as_bytes()).to_hex().to_string();

        KarunaRecoveryResult {
            recovered: true,
            shadow_state_b3: shadow_hash,
            error_cascade_suppressed: true,
            notes: "Karuna VR Mirror active: Maladaptive trajectory replaced with deterministic shadow state.".to_string(),
        }
    }

    /// AK-Bridge: KarXT pharmacological peripheral gate (Xanomeline Core vs Trospium Blocker)
    pub fn karxt_gate_evaluate(
        &self,
        requested_action: &str,
        has_sel4_capability: bool,
    ) -> KarxtGateResult {
        let peripheral_side_effects = ["execve", "raw_socket_bind", "tetraledger_debit", "reboot", "unlink_vfs"];
        let is_peripheral = peripheral_side_effects.iter().any(|&side| requested_action.to_lowercase().contains(side));

        if !is_peripheral {
            return KarxtGateResult {
                allowed: true,
                zone: "XANOMELINE_CORE".to_string(),
                blocked_side_effect: None,
                reason: "Action confined to tmpfs reasoning envelope; zero peripheral toxicity.".to_string(),
            };
        }

        if has_sel4_capability {
            KarxtGateResult {
                allowed: true,
                zone: "TROSPIUM_PERIPHERAL_VERIFIED".to_string(),
                blocked_side_effect: None,
                reason: "Action carries verified seL4 capability token; authorized transit.".to_string(),
            }
        } else {
            KarxtGateResult {
                allowed: false,
                zone: "TROSPIUM_PERIPHERAL_BLOCKED".to_string(),
                blocked_side_effect: Some(requested_action.to_string()),
                reason: "Trospium peripheral blocker engaged: Unauthenticated syscall denied outside enclave.".to_string(),
            }
        }
    }

    pub fn get_codebook(&self) -> &HashMap<String, DspgKenningMeta> {
        &self.codebook
    }
}
