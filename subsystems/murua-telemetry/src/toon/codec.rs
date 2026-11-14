// ffp: FFP-MURUA-TOON toon-tron-codec rust
//! TOON (Token-Oriented Object Notation) & TRON (Token-Reduced Object Notation)
//! High-compression serialization engine for postal telemetry and nested shipment states.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ToonTelemetryRow {
    pub corridor: String,
    pub item_id: String,
    pub pre_adv_dt: Option<DateTime<Utc>>,
    pub pickup_dt: DateTime<Utc>,
    pub cfc_stamp_dt: Option<String>,
    pub hub_spray_dt: Option<String>,
    pub deliv_dt: Option<DateTime<Utc>>,
    pub mass_g: f64,
    pub thick_mm: f64,
    pub format: String,
    pub kix_ok: bool,
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TronShipmentNode {
    pub id: String,
    pub corridor: String,
    pub status: String,
    pub events: Vec<(String, String)>, // (timestamp_str, event_type)
    pub metrics: Vec<(String, f64)>,   // (metric_key, metric_value)
}

pub struct ToonTronCodec;

impl ToonTronCodec {
    pub const TOON_HEADER_V1: &'static str =
        "@TOON:v1|corridor|item_id|pre_adv_dt|pickup_dt|cfc_stamp_dt|hub_spray_dt|deliv_dt|mass_g|thick_mm|fmt|kix_ok|status";

    /// Encodes a slice of telemetry records into a compact TOON stream
    pub fn encode_toon(rows: &[ToonTelemetryRow]) -> String {
        let mut out = String::new();
        out.push_str(Self::TOON_HEADER_V1);
        out.push('\n');

        for row in rows {
            let pre_adv = match row.pre_adv_dt {
                Some(dt) => dt.format("%Y-%m-%dT%H:%M").to_string(),
                None => "null".to_string(),
            };
            let pickup = row.pickup_dt.format("%Y-%m-%dT%H:%M").to_string();
            let cfc = row.cfc_stamp_dt.as_deref().unwrap_or("null");
            let spray = row.hub_spray_dt.as_deref().unwrap_or("null");
            let deliv = match row.deliv_dt {
                Some(dt) => dt.format("%Y-%m-%dT%H:%M").to_string(),
                None => "null".to_string(),
            };

            let line = format!(
                "{}|{}|{}|{}|{}|{}|{}|{:.1}|{:.1}|{}|{}|{}\n",
                row.corridor,
                row.item_id,
                pre_adv,
                pickup,
                cfc,
                spray,
                deliv,
                row.mass_g,
                row.thick_mm,
                row.format,
                row.kix_ok,
                row.status
            );
            out.push_str(&line);
        }

        out
    }

    /// Decodes a TOON formatted string back into structured rows
    pub fn decode_toon(payload: &str) -> Result<Vec<ToonTelemetryRow>, String> {
        let mut rows = Vec::new();
        let lines: Vec<&str> = payload.lines().collect();
        if lines.is_empty() {
            return Ok(rows);
        }

        let header = lines[0].trim();
        if !header.starts_with("@TOON:v1") {
            return Err(format!("Invalid TOON header: {}", header));
        }

        for (idx, line) in lines[1..].iter().enumerate() {
            let trimmed = line.trim();
            if trimmed.is_empty() || trimmed.starts_with('#') {
                continue;
            }

            let parts: Vec<&str> = trimmed.split('|').collect();
            if parts.len() < 12 {
                return Err(format!(
                    "Line {} has invalid field count (expected >= 12, got {})",
                    idx + 2,
                    parts.len()
                ));
            }

            let parse_opt_dt = |s: &str| -> Option<DateTime<Utc>> {
                if s == "null" || s.is_empty() {
                    None
                } else {
                    chrono::NaiveDateTime::parse_from_str(s, "%Y-%m-%dT%H:%M")
                        .ok()
                        .map(|ndt| DateTime::<Utc>::from_naive_utc_and_offset(ndt, Utc))
                }
            };

            let pre_adv_dt = parse_opt_dt(parts[2]);
            let pickup_dt = parse_opt_dt(parts[3]).unwrap_or_else(Utc::now);
            let cfc_stamp_dt = if parts[4] == "null" {
                None
            } else {
                Some(parts[4].to_string())
            };
            let hub_spray_dt = if parts[5] == "null" {
                None
            } else {
                Some(parts[5].to_string())
            };
            let deliv_dt = parse_opt_dt(parts[6]);
            let mass_g: f64 = parts[7].parse().unwrap_or(0.0);
            let thick_mm: f64 = parts[8].parse().unwrap_or(0.0);
            let format_str = parts[9].to_string();
            let kix_ok = parts[10].eq_ignore_ascii_case("true");
            let status = parts[11].to_string();

            rows.push(ToonTelemetryRow {
                corridor: parts[0].to_string(),
                item_id: parts[1].to_string(),
                pre_adv_dt,
                pickup_dt,
                cfc_stamp_dt,
                hub_spray_dt,
                deliv_dt,
                mass_g,
                thick_mm,
                format: format_str,
                kix_ok,
                status,
            });
        }

        Ok(rows)
    }

    /// Serializes a nested shipment state into TRON format
    pub fn encode_tron(node: &TronShipmentNode) -> String {
        let mut out = String::new();
        out.push_str(&format!("@TRON:v1!{}:{}:{}\n", node.id, node.corridor, node.status));

        out.push_str("  #EV\n");
        for (ts, ev) in &node.events {
            out.push_str(&format!("    >{}={}\n", ts, ev));
        }

        out.push_str("  #MT\n");
        for (key, val) in &node.metrics {
            out.push_str(&format!("    ~{}={:.3}\n", key, val));
        }

        out
    }

    /// Calculates token compression ratio between standard JSON and TOON/TRON representation
    pub fn calculate_compression_ratio(json_len: usize, compressed_len: usize) -> f64 {
        if json_len == 0 {
            return 0.0;
        }
        1.0 - (compressed_len as f64 / json_len as f64)
    }
}
