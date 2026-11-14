// ffp: FFP-BIO-220 phyllotactic-mesh-scheduler rust
// File: src/biomimetic/phyllotaxis.rs
// Compliance: DSS-14 (BHUVANESVARI + TARA + ANNAPURNA) + ENHAN3

use serde::{Deserialize, Serialize};
use std::f64::consts::PI;

pub const GOLDEN_ANGLE_RAD: f64 = 2.39996322972865332; // 137.507764 degrees

/// E220: Golden-Angle Phyllotactic 5-Node WireGuard (wg0) Scheduler
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Wg0MeshNode {
    pub id: String,
    pub ip: String,
    pub port: u16,
    pub mif_profile: String,
    pub angular_phase_offset_rad: f64,
}

pub struct PhyllotacticScheduler {
    pub nodes: Vec<Wg0MeshNode>,
}

impl PhyllotacticScheduler {
    pub fn new() -> Self {
        let node_specs = [
            ("hetzner-core", "10.77.0.1", 9777, "MIF50_CLOUD"),
            ("xps-9310", "10.77.0.2", 9777, "MIF30_CLIENT"),
            ("lat-5591", "10.77.0.3", 9777, "MIF50_TX-NODE-01"),
            ("pixel-8-pro", "10.77.0.4", 9777, "MIF20_SRM_IMU"),
            ("poco-x5", "10.77.0.5", 9777, "MIF20_EDGE"),
        ];

        let mut nodes = Vec::new();
        for (i, (id, ip, port, profile)) in node_specs.iter().enumerate() {
            let phase = ((i as f64) * GOLDEN_ANGLE_RAD) % (2.0 * PI);
            nodes.push(Wg0MeshNode {
                id: id.to_string(),
                ip: ip.to_string(),
                port: *port,
                mif_profile: profile.to_string(),
                angular_phase_offset_rad: phase,
            });
        }

        Self { nodes }
    }

    /// Calculates collision-free RPC dispatch time offset in microseconds
    pub fn calculate_node_time_offset_us(&self, node_index: usize, slot_step: u64) -> u64 {
        let phase = ((node_index as f64 + slot_step as f64) * GOLDEN_ANGLE_RAD) % (2.0 * PI);
        let normalized = phase / (2.0 * PI);
        (normalized * 50_000.0).round() as u64 // 0..50ms phase-staggered window
    }
}
