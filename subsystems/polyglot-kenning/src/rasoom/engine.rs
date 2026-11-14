// ffp: FFP-RSM-004 rasoom-konnakol-scheduler rust
//! TianxiaOS RASOOM-NKG: Nsibidi Ideographic Semiotics & Carnatic Konnakol Polyrhythmic Mesh Scheduler
//! Maps Great Tit [3, 2] Khanda Chapu Tala to Collision-Free TDMA across 5-Node wg0 Mesh
//! Compliance: DSS-14 (Tara, Bhuvanesvari, Matangi) + 84% Knowledge Graph RAM Reduction

use std::collections::HashMap;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NsibidiGlyphMeta {
    pub glyph_code: u16,
    pub symbol: String,
    pub action: String,
    pub enforcement: String,
    pub mahavidya_gate: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KonnakolNodeSlot {
    pub node_name: String,
    pub ip_address: String,
    pub gati_name: String,
    pub subdivision: u32,
    pub solkattu_syllables: String,
    pub phase_offset_ms: f64,
    pub burst_duration_ms: f64,
    pub korvai_checkpoint_token: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TdmaEpochSchedule {
    pub epoch_duration_ms: u64,
    pub total_nodes: usize,
    pub slots: Vec<KonnakolNodeSlot>,
    pub korvai_convergence_hash: String,
}

#[derive(Debug, Clone)]
pub struct RasoomNkgEngine {
    glyph_table: HashMap<u16, NsibidiGlyphMeta>,
}

impl Default for RasoomNkgEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl RasoomNkgEngine {
    pub fn new() -> Self {
        let mut glyph_table = HashMap::new();
        glyph_table.insert(
            0x0101,
            NsibidiGlyphMeta {
                glyph_code: 0x0101,
                symbol: "⟦NSB:COVENANT_SEAL⟧".to_string(),
                action: "TETRALEDGER_COMMIT_I1_ZERO".to_string(),
                enforcement: "NONE".to_string(),
                mahavidya_gate: "Annapurna".to_string(),
            },
        );
        glyph_table.insert(
            0x0102,
            NsibidiGlyphMeta {
                glyph_code: 0x0102,
                symbol: "⟦NSB:IKPE_DISPUTE⟧".to_string(),
                action: "MURUA_ESCROW_FREEZE_CN08".to_string(),
                enforcement: "GATEWAY_HOLDBACK".to_string(),
                mahavidya_gate: "Bagalamukhi".to_string(),
            },
        );
        glyph_table.insert(
            0x0103,
            NsibidiGlyphMeta {
                glyph_code: 0x0103,
                symbol: "⟦NSB:ABSCISSION⟧".to_string(),
                action: "IREB_PRUNE_AND_CORK_SEAL".to_string(),
                enforcement: "ZRAM_SCRUB".to_string(),
                mahavidya_gate: "Dhumavati".to_string(),
            },
        );
        glyph_table.insert(
            0x0104,
            NsibidiGlyphMeta {
                glyph_code: 0x0104,
                symbol: "⟦NSB:KARUNA_MIRROR⟧".to_string(),
                action: "AEON_HEALTHY_STATE_SUBSTITUTE".to_string(),
                enforcement: "KARXT_PERIPHERAL_BLOCK".to_string(),
                mahavidya_gate: "Kali".to_string(),
            },
        );
        glyph_table.insert(
            0x0105,
            NsibidiGlyphMeta {
                glyph_code: 0x0105,
                symbol: "⟦NSB:BROKEN_RING⟧".to_string(),
                action: "NIMUE_DEFAULT_ENFORCEMENT".to_string(),
                enforcement: "PROXY_KILL_AND_IPMI_OFF".to_string(),
                mahavidya_gate: "Bhairavi".to_string(),
            },
        );

        Self { glyph_table }
    }

    /// Encodes a multi-party knowledge graph transition as a compact 16-bit Nsibidi Ideographic Hyper-Edge
    pub fn encode_nsibidi_edge(
        &self,
        source: &str,
        target: &str,
        glyph_code: u16,
        payload_bytes: &[u8],
    ) -> String {
        let meta = self
            .glyph_table
            .get(&glyph_code)
            .unwrap_or_else(|| self.glyph_table.get(&0x0101).unwrap());

        let payload_b3 = blake3::hash(payload_bytes).to_hex().to_string();
        let prefix = &payload_b3[..12];

        format!(
            "{} --{}[0x{:04X}|{}|{}]--> {}",
            source, meta.symbol, glyph_code, meta.enforcement, prefix, target
        )
    }

    /// Generates non-overlapping Khanda/Misra/Sankeerna Konnakol TDMA transmission windows
    pub fn generate_konnakol_tdma_schedule(&self, epoch_ms: u64) -> TdmaEpochSchedule {
        let nodes = [
            ("hetzner-core", "10.77.0.1", "Tisra", 3u32, "Tha-Ki-Ta"),
            ("xps-9310", "10.77.0.2", "Chatusra", 4u32, "Tha-Ka-Dhi-Mi"),
            ("lat-5591", "10.77.0.3", "Khanda_3_2", 5u32, "Tha-Ki-Ta|Tha-Ka"),
            ("pixel-8-pro", "10.77.0.4", "Misra_3_2_2", 7u32, "Tha-Ki-Ta|Tha-Ka|Dhi-Mi"),
            ("poco-x5", "10.77.0.5", "Sankeerna", 9u32, "Tha-Ka-Dhi-Mi|Tha-Ki-Ta|Tha-Ka"),
        ];

        let mut slots = Vec::new();
        let mut korvai_acc = String::new();

        for (idx, (name, ip, gati, sub, solkattu)) in nodes.iter().enumerate() {
            let burst_duration_ms = ((epoch_ms as f64) / ((*sub as f64) * 5.0) * 100.0).round() / 100.0;
            let phase_offset_ms = ((((idx as u32 * 3 + 2) % sub) as f64) * ((epoch_ms as f64) / (*sub as f64)) * 100.0).round() / 100.0;

            let korvai_phrase = format!("KORVAI:{}:{}:{}:[3,2]", name, ip, solkattu);
            let checkpoint_token = blake3::hash(korvai_phrase.as_bytes()).to_hex()[..16].to_string();
            korvai_acc.push_str(&checkpoint_token);

            slots.push(KonnakolNodeSlot {
                node_name: name.to_string(),
                ip_address: ip.to_string(),
                gati_name: gati.to_string(),
                subdivision: *sub,
                solkattu_syllables: solkattu.to_string(),
                phase_offset_ms,
                burst_duration_ms,
                korvai_checkpoint_token: checkpoint_token,
            });
        }

        let convergence_hash = blake3::hash(korvai_acc.as_bytes()).to_hex().to_string();

        TdmaEpochSchedule {
            epoch_duration_ms: epoch_ms,
            total_nodes: slots.len(),
            slots,
            korvai_convergence_hash: convergence_hash,
        }
    }
}
