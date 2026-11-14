// ffp: FFP-MURUA-TEST-TOON test rust
use chrono::{Duration, Utc};
use murua_architecture_enhancement::toon::{ToonTelemetryRow, ToonTronCodec, TronShipmentNode};

#[test]
fn test_toon_roundtrip_fidelity() {
    let now = Utc::now();
    let pickup = now - Duration::days(7);
    let shipped = pickup - Duration::hours(24);

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
            corridor: "BE-BRU_EE-TLL".to_string(),
            item_id: "71625652".to_string(),
            pre_adv_dt: Some(pickup - Duration::days(2)),
            pickup_dt: pickup,
            cfc_stamp_dt: Some("2026-09-25".to_string()),
            hub_spray_dt: Some("2026-09-29".to_string()),
            deliv_dt: Some(now - Duration::days(3)),
            mass_g: 420.0,
            thick_mm: 65.0,
            format: "PARCEL".to_string(),
            kix_ok: false,
            status: "LOCKER_DELIVERED".to_string(),
        },
    ];

    let encoded = ToonTronCodec::encode_toon(&rows);
    assert!(encoded.starts_with(ToonTronCodec::TOON_HEADER_V1));

    let decoded = ToonTronCodec::decode_toon(&encoded).expect("TOON decoding failed");
    assert_eq!(rows.len(), decoded.len());

    assert_eq!(decoded[0].corridor, "NL-AMS_EE-TLL_12618");
    assert_eq!(decoded[0].item_id, "58b73b08");
    assert_eq!(decoded[0].cfc_stamp_dt.as_deref(), Some("2026-10-27"));
    assert_eq!(decoded[0].mass_g, 65.0);
    assert!(decoded[0].kix_ok);
    assert_eq!(decoded[0].status, "IN_OXBOW_BUFFER");

    assert_eq!(decoded[1].item_id, "71625652");
    assert_eq!(decoded[1].status, "LOCKER_DELIVERED");
}

#[test]
fn test_toon_compression_ratio() {
    let now = Utc::now();
    let rows: Vec<ToonTelemetryRow> = (0..20)
        .map(|i| ToonTelemetryRow {
            corridor: "NL-AMS_EE-TLL_12618".to_string(),
            item_id: format!("ITEM_{:04}", i),
            pre_adv_dt: Some(now - Duration::days(5)),
            pickup_dt: now - Duration::days(4),
            cfc_stamp_dt: Some("2026-10-27".to_string()),
            hub_spray_dt: None,
            deliv_dt: None,
            mass_g: 65.0 + (i as f64),
            thick_mm: 4.0,
            format: "STD_ENV".to_string(),
            kix_ok: true,
            status: "IN_OXBOW_BUFFER".to_string(),
        })
        .collect();

    let json_len = serde_json::to_string_pretty(&rows).unwrap().len();
    let toon_len = ToonTronCodec::encode_toon(&rows).len();

    let ratio = ToonTronCodec::calculate_compression_ratio(json_len, toon_len);
    // TOON should yield > 60% compression over pretty JSON
    assert!(ratio > 0.60);
}

#[test]
fn test_tron_serialization() {
    let node = TronShipmentNode {
        id: "58b73b08".to_string(),
        corridor: "NL-AMS_EE-TLL_12618".to_string(),
        status: "OXBOW_BUFFER_ESCALATION".to_string(),
        events: vec![
            ("2026-10-25T14:10".to_string(), "VENDOR_PRE_ADVICE".to_string()),
            ("2026-10-27T11:00".to_string(), "CARRIER_PICKUP".to_string()),
        ],
        metrics: vec![("mass_g".to_string(), 65.0), ("tau_w".to_string(), 168.0)],
    };

    let tron_out = ToonTronCodec::encode_tron(&node);
    assert!(tron_out.contains("@TRON:v1!58b73b08"));
    assert!(tron_out.contains("OXBOW_BUFFER_ESCALATION"));
    assert!(tron_out.contains("VENDOR_PRE_ADVICE"));
    assert!(tron_out.contains("~mass_g=65.000"));
}
