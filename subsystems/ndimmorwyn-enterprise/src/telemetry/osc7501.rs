// ffp: FFP-TEL-233 osc7501-libghostty-bridge rust
// File: src/telemetry/osc7501.rs
// Compliance: DSS-14 (TRIPURA + MATANGI + MAHASARASVATI) + ENHAN3

use serde::{Deserialize, Serialize};

/// E233: Termius libghostty OSC 7501 Program Status Protocol Bridge
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Osc7501TelemetryFrame {
    pub state: String,     // "active", "unlocked", "deflected", "settled", "pruned"
    pub task_id: String,
    pub detail: String,
    pub timestamp_ms: u64,
}

impl Osc7501TelemetryFrame {
    pub fn new(state: &str, task_id: &str, detail: &str) -> Self {
        Self {
            state: state.to_string(),
            task_id: task_id.to_string(),
            detail: detail.to_string(),
            timestamp_ms: chrono::Utc::now().timestamp_millis() as u64,
        }
    }

    /// Emits exact terminal escape code: \x1b]7501;state=...;task=...;detail=...\x07
    pub fn to_ansi_sequence(&self) -> String {
        format!(
            "\x1b]7501;state={};task={};detail={}\x07",
            self.state, self.task_id, self.detail
        )
    }
}
