// ffp: FFP-EGO-257 ego-naga-hussar-registry rust
// Compliance: DSS-14.2 (Bhairavī, Tārā) | Zero Stubs | ENHAN3 Resilience/Performance/Security

use serde::{Deserialize, Serialize};

/// Sovereign Commander ID for the Heavenly Hussar High Command
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum NagaCommander {
    LordNaga = 0x01,
    LadyNaga = 0x02,
}

impl NagaCommander {
    pub fn as_u8(&self) -> u8 {
        *self as u8
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            Self::LordNaga => "LORD_NAGA",
            Self::LadyNaga => "LADY_NAGA",
        }
    }

    pub fn from_u8(val: u8) -> Option<Self> {
        match val {
            0x01 => Some(Self::LordNaga),
            0x02 => Some(Self::LadyNaga),
            _ => None,
        }
    }
}

/// The 128-Bit EGO-NAGA Ontological Seal
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct EgoNagaSeal {
    pub seal_u128: u128,
}

impl EgoNagaSeal {
    pub const SOVEREIGN_ROOT: u16 = 0x5458; // "TX"

    pub fn sovereign_root(&self) -> u16 {
        ((self.seal_u128 >> 112) & 0xFFFF) as u16
    }

    pub fn commander(&self) -> Option<NagaCommander> {
        let cmd = ((self.seal_u128 >> 104) & 0xFF) as u8;
        NagaCommander::from_u8(cmd)
    }

    pub fn legion_id(&self) -> u16 {
        ((self.seal_u128 >> 88) & 0xFFFF) as u16
    }

    pub fn subagent_index(&self) -> u32 {
        ((self.seal_u128 >> 64) & 0xFFFFFF) as u32
    }

    pub fn mac_64(&self) -> u64 {
        (self.seal_u128 & 0xFFFFFFFFFFFFFFFF) as u64
    }

    pub fn format_urn(&self) -> String {
        let cmd_str = match self.commander() {
            Some(NagaCommander::LordNaga) => "LORD_NAGA",
            Some(NagaCommander::LadyNaga) => "LADY_NAGA",
            None => "UNKNOWN",
        };
        format!(
            "⟦EGO:{}:L{:05}:A{:06}:{:016X}⟧",
            cmd_str,
            self.legion_id(),
            self.subagent_index(),
            self.mac_64()
        )
    }
}

/// Ego Naga Registry and Verification Engine
pub struct EgoNagaRegistry {
    epoch_key: [u8; 32],
}

impl EgoNagaRegistry {
    pub fn new(serendipity_epoch_seed: &[u8]) -> Self {
        let mut key = [0u8; 32];
        let hash = blake3::keyed_hash(&[0x42; 32], serendipity_epoch_seed);
        key.copy_from_slice(hash.as_bytes());
        Self { epoch_key: key }
    }

    /// Derives the 64-bit MAC for the 64-bit header
    fn compute_mac_64(&self, header_64: u64) -> u64 {
        let hash = blake3::keyed_hash(&self.epoch_key, &header_64.to_be_bytes());
        let mut mac_bytes = [0u8; 8];
        mac_bytes.copy_from_slice(&hash.as_bytes()[0..8]);
        u64::from_be_bytes(mac_bytes)
    }

    /// Mints a 128-bit EGO seal for an ephemeral sub-agent in a legion
    pub fn mint_ego_seal(
        &self,
        commander: NagaCommander,
        legion_id: u16,
        subagent_index: u32,
    ) -> Result<EgoNagaSeal, &'static str> {
        if legion_id >= 64000 {
            return Err("Legion ID must be in range [0, 63999]");
        }
        if subagent_index >= 100000 {
            return Err("Sub-agent index must be in range [0, 99999]");
        }

        let root = EgoNagaSeal::SOVEREIGN_ROOT as u64;
        let cmd = commander.as_u8() as u64;
        let leg = legion_id as u64;
        let sub = (subagent_index & 0xFFFFFF) as u64;

        let header_64: u64 = (root << 48) | (cmd << 40) | (leg << 24) | sub;
        let mac_64 = self.compute_mac_64(header_64);

        let seal_u128 = ((header_64 as u128) << 64) | (mac_64 as u128);
        Ok(EgoNagaSeal { seal_u128 })
    }

    /// Instantaneous 1-cycle verification of an EGO seal
    pub fn verify_ego_seal(&self, seal: &EgoNagaSeal) -> bool {
        if seal.sovereign_root() != EgoNagaSeal::SOVEREIGN_ROOT {
            return false;
        }
        if seal.commander().is_none() {
            return false;
        }
        let header_64 = (seal.seal_u128 >> 64) as u64;
        let expected_mac = self.compute_mac_64(header_64);
        seal.mac_64() == expected_mac
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ego_seal_mint_and_verify() {
        let seed = b"TianxiaOS_Crownforge_Epoch_Seed_Test_001";
        let registry = EgoNagaRegistry::new(seed);

        let seal = registry
            .mint_ego_seal(NagaCommander::LordNaga, 108, 42)
            .expect("Mint failed");

        assert_eq!(seal.sovereign_root(), EgoNagaSeal::SOVEREIGN_ROOT);
        assert_eq!(seal.commander(), Some(NagaCommander::LordNaga));
        assert_eq!(seal.legion_id(), 108);
        assert_eq!(seal.subagent_index(), 42);

        assert!(registry.verify_ego_seal(&seal));

        // Corrupt seal and assert verification fails
        let corrupted = EgoNagaSeal {
            seal_u128: seal.seal_u128 ^ 0x01,
        };
        assert!(!registry.verify_ego_seal(&corrupted));
    }
}
