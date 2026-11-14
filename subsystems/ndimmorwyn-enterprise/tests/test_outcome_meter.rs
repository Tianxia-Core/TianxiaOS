// ffp: FFP-TST-002 test-outcome-meter rust
// Compliance: DSS-14 (ANNAPURNA + KAMALA) + ENHAN3

use tianxiaos_ndimmorwyn_enterprise::aurum::*;

#[test]
fn test_outcome_metering_gross_margin_and_toon() {
    let execution = RguOutcomeExecution {
        rgu_id: "RGU-AURUM-01".to_string(),
        ffp_count: 5,
        client_id: "client-test-corp".to_string(),
        outcome_verified: true,
        outcome_fee_cents: 10_000_00, // €10,000
        bitnet_cpu_tokens: 50_000,
        cloud_escalation_cost_cents: 500_00, // €500 (95% margin)
        microvm_ram_mb_seconds: 12_000,
    };

    let receipt = meter_rgu_outcome(&execution);
    assert_eq!(receipt.billable_cents, 10_000_00);
    assert!((receipt.gross_margin_ratio - 0.95).abs() < 0.001);
    assert!(!receipt.force_local_vuda_fallback);
    assert!(receipt.toon_serialized_log.contains("SCHEMA[rgu|ffp|client|bill_c|cost_c|margin|vuda_lock]"));
}

#[test]
fn test_outcome_metering_margin_floor_trips_vuda_fallback() {
    let execution = RguOutcomeExecution {
        rgu_id: "RGU-AURUM-02".to_string(),
        ffp_count: 7,
        client_id: "client-heavy-burn".to_string(),
        outcome_verified: true,
        outcome_fee_cents: 1_000_00,
        bitnet_cpu_tokens: 10_000,
        cloud_escalation_cost_cents: 300_00, // Margin = (1000 - 300) / 1000 = 70% (< 85% floor)
        microvm_ram_mb_seconds: 4_000,
    };

    let receipt = meter_rgu_outcome(&execution);
    assert!(receipt.force_local_vuda_fallback);
}
