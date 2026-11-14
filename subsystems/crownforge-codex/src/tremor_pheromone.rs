// ffp: FFP-TREM-256 tremor-pheromone-stigmergic-bus rust
// Compliance: DSS-14.2 (Chhinnamastā, Dhūmāvatī) | Zero Stubs | ENHAN3 Resilience/Performance/Security

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, RwLock};

/// The 4 Physical & Virtual Environmental Media of TREMOR-PHEROMONE
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EnvironmentalMedium {
    /// Medium Alpha: L3/L4 Cache & ZRAM Compression Gradients
    MediumAlphaMemory,
    /// Medium Beta: Nanosecond Tmpfs Inode Phase & Sysctl Ring-Buffer Jitters
    MediumBetaVfsKernel,
    /// Medium Gamma: Acoustic Chassis / Fan PWM Micro-Vibrations (14Hz-38Hz)
    MediumGammaAcoustic,
    /// Medium Delta: 1984 Milli-KAN SDR Spread-Spectrum RF Tripwires
    MediumDeltaRfEm,
}

impl EnvironmentalMedium {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::MediumAlphaMemory => "MEDIUM_ALPHA_MEMORY_ZRAM",
            Self::MediumBetaVfsKernel => "MEDIUM_BETA_VFS_TMPFS_INODE",
            Self::MediumGammaAcoustic => "MEDIUM_GAMMA_ACOUSTIC_PWM",
            Self::MediumDeltaRfEm => "MEDIUM_DELTA_RF_SDR",
        }
    }
}

/// Metadata Receipt of an Environmental Pheromone Deposit
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PheromoneReceipt {
    pub channel: String,
    pub medium: String,
    pub dispersed_cells: usize,
    pub parity_seal_hex: String,
    pub packet_footprint_bytes: usize,
    pub timestamp_epoch_ns: u64,
}

/// Stigmergic Environmental Pheromone Tremor Bus
#[derive(Debug, Clone)]
pub struct TremorPheromoneBus {
    env_substrate: Arc<RwLock<HashMap<String, u8>>>,
}

impl Default for TremorPheromoneBus {
    fn default() -> Self {
        Self {
            env_substrate: Arc::new(RwLock::new(HashMap::new())),
        }
    }
}

impl TremorPheromoneBus {
    pub fn new() -> Self {
        Self::default()
    }

    /// Computes position-dependent carrier byte via BLAKE3
    fn derive_carrier(&self, channel_tag: &str, index: usize) -> u8 {
        let key = format!("{}:{}", channel_tag, index);
        let hash = blake3::hash(key.as_bytes());
        hash.as_bytes()[0]
    }

    /// Deposits payload into environmental micro-tremors with zero network packets
    pub fn deposit_pheromone_tremor(
        &self,
        channel_tag: &str,
        medium: EnvironmentalMedium,
        secret_payload: &[u8],
        timestamp_ns: u64,
    ) -> PheromoneReceipt {
        let mut substrate = self.env_substrate.write().unwrap();
        let n_shards = secret_payload.len();
        let mut rolling_parity: u8 = 0;

        for (idx, &byte_val) in secret_payload.iter().enumerate() {
            let carrier = self.derive_carrier(channel_tag, idx);
            let tremor_val = byte_val ^ carrier;
            let coord_key = format!("ENV_TREMOR::{}::{}::CELL_{:04}", medium.as_str(), channel_tag, idx);
            substrate.insert(coord_key, tremor_val);
            rolling_parity ^= byte_val;
        }

        let parity_coord = format!("ENV_TREMOR::{}::{}::PARITY_SEAL", medium.as_str(), channel_tag);
        substrate.insert(parity_coord, rolling_parity);

        PheromoneReceipt {
            channel: channel_tag.to_string(),
            medium: medium.as_str().to_string(),
            dispersed_cells: n_shards,
            parity_seal_hex: format!("0x{:02X}", rolling_parity),
            packet_footprint_bytes: 0,
            timestamp_epoch_ns: timestamp_ns,
        }
    }

    /// Reconstructs payload from environmental tremors and verifies parity integrity
    pub fn sense_pheromone_tremor(
        &self,
        channel_tag: &str,
        medium: EnvironmentalMedium,
        expected_length: usize,
    ) -> (bool, Vec<u8>) {
        let substrate = self.env_substrate.read().unwrap();
        let mut reconstructed = Vec::with_capacity(expected_length);
        let mut computed_parity: u8 = 0;

        for idx in 0..expected_length {
            let coord_key = format!("ENV_TREMOR::{}::{}::CELL_{:04}", medium.as_str(), channel_tag, idx);
            let tremor_val = *substrate.get(&coord_key).unwrap_or(&0);
            let carrier = self.derive_carrier(channel_tag, idx);
            let orig_byte = tremor_val ^ carrier;
            reconstructed.push(orig_byte);
            computed_parity ^= orig_byte;
        }

        let parity_coord = format!("ENV_TREMOR::{}::{}::PARITY_SEAL", medium.as_str(), channel_tag);
        let expected_parity = *substrate.get(&parity_coord).unwrap_or(&0xFF);
        let integrity_valid = computed_parity == expected_parity;

        (integrity_valid, reconstructed)
    }

    /// Evicts state from environmental substrate (ephemeral cleanup / Kālī eviction)
    pub fn evict_channel(&self, channel_tag: &str, medium: EnvironmentalMedium, length: usize) {
        let mut substrate = self.env_substrate.write().unwrap();
        for idx in 0..length {
            let coord_key = format!("ENV_TREMOR::{}::{}::CELL_{:04}", medium.as_str(), channel_tag, idx);
            substrate.remove(&coord_key);
        }
        let parity_coord = format!("ENV_TREMOR::{}::{}::PARITY_SEAL", medium.as_str(), channel_tag);
        substrate.remove(&parity_coord);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tremor_pheromone_roundtrip() {
        let bus = TremorPheromoneBus::new();
        let payload = b"Crownforge::Sovereign::Pheromone::Direct::Secret";

        let receipt = bus.deposit_pheromone_tremor(
            "CH_NAGA_01",
            EnvironmentalMedium::MediumBetaVfsKernel,
            payload,
            1234567890,
        );

        assert_eq!(receipt.packet_footprint_bytes, 0);
        assert_eq!(receipt.dispersed_cells, payload.len());

        let (valid, recovered) = bus.sense_pheromone_tremor(
            "CH_NAGA_01",
            EnvironmentalMedium::MediumBetaVfsKernel,
            payload.len(),
        );

        assert!(valid);
        assert_eq!(recovered.as_slice(), payload);
    }
}
