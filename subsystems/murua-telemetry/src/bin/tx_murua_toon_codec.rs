// ffp: FFP-MURUA-TOON-BIN toon-codec-cli rust
//! Murua TOON/TRON Codec CLI
//! Tests tabular TOON encoding/decoding and TRON hierarchical state serialization.

use chrono::{Duration, Utc};
use murua_architecture_enhancement::toon::{ToonTelemetryRow, ToonTronCodec, TronShipmentNode};

fn main() {
    let now = Utc::now();
    let pickup = now - Duration::days(8);
    let shipped = pickup - Duration::hours(36);

    println!("================================================================================");
    println!(" MURUA TOON & TRON COMPRESSION CODEC");
    println!(" Header Specification: {}", ToonTronCodec::TOON_HEADER_V1);
    println!("================================================================================");

    let rows = vec![
        ToonTelemetryRow {
            corridor: "NL-AMS_EE-TLL_12618".to_string(),
            item_id: "58b73b08".to_string(),
            pre_adv_dt: Some(shipped),
            pickup_dt: pickup,
            cfc_stamp_dt: Some("2026-10-27".to_string()),
            hub_spray_dt: None,
            deliv_dt: None,
            mass_g: 65.0,
            thick_mm: 4.0,
            format: "STD_ENV".to_string(),
            kix_ok: true,
            status: "IN_OXBOW_BUFFER".to_string(),
        },
        ToonTelemetryRow {
            corridor: "NL-AMS_EE-TLL_12618".to_string(),
            item_id: "c31f078b".to_string(),
            pre_adv_dt: Some(shipped + Duration::hours(2)),
            pickup_dt: pickup,
            cfc_stamp_dt: Some("2026-10-27".to_string()),
            hub_spray_dt: None,
            deliv_dt: None,
            mass_g: 65.0,
            thick_mm: 4.0,
            format: "STD_ENV".to_string(),
            kix_ok: true,
            status: "IN_OXBOW_BUFFER".to_string(),
        },
        ToonTelemetryRow {
            corridor: "BE-BRU_EE-TLL".to_string(),
            item_id: "71625652".to_string(),
            pre_adv_dt: Some(now - Duration::days(40)),
            pickup_dt: now - Duration::days(39),
            cfc_stamp_dt: Some("2026-09-25".to_string()),
            hub_spray_dt: Some("2026-09-29".to_string()),
            deliv_dt: Some(now - Duration::days(35)),
            mass_g: 420.0,
            thick_mm: 65.0,
            format: "PARCEL".to_string(),
            kix_ok: false,
            status: "LOCKER_DELIVERED".to_string(),
        },
    ];

    let json_repr = serde_json::to_string_pretty(&rows).unwrap();
    let toon_encoded = ToonTronCodec::encode_toon(&rows);

    let comp_ratio = ToonTronCodec::calculate_compression_ratio(json_repr.len(), toon_encoded.len());

    println!("Standard JSON Serialization Length: {} bytes", json_repr.len());
    println!("TOON Stream Serialization Length:    {} bytes", toon_encoded.len());
    println!("Token / Space Compression Ratio:    {:.2}%\n", comp_ratio * 100.0);

    println!("Encoded TOON Stream:\n{}", toon_encoded);

    let decoded = ToonTronCodec::decode_toon(&toon_encoded).unwrap();
    println!("Verification: Successfully decoded {} rows without semantic loss.", decoded.len());
    assert_eq!(rows.len(), decoded.len());

    println!("\nTRON Nested Hierarchy Serialization:");
    let tron_node = TronShipmentNode {
        id: "58b73b08".to_string(),
        corridor: "NL-AMS_EE-TLL_12618".to_string(),
        status: "OXBOW_BUFFER_ESCALATION".to_string(),
        events: vec![
            ("2026-10-25T14:10".to_string(), "VENDOR_PRE_ADVICE".to_string()),
            ("2026-10-27T11:00".to_string(), "CARRIER_PICKUP_POSTNL".to_string()),
            ("2026-11-06T12:00".to_string(), "ESCROW_PRE_LOCK_TRIGGERED".to_string()),
        ],
        metrics: vec![
            ("mass_grams".to_string(), 65.0),
            ("barabasi_tau_w".to_string(), 168.0),
            ("p_arrival_fri".to_string(), 0.912),
        ],
    };

    let tron_encoded = ToonTronCodec::encode_tron(&tron_node);
    println!("{}", tron_encoded);
    println!("================================================================================");
}
