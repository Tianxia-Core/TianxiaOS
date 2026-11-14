// ffp: FFP-TST-003 test-tetraledger rust
// Compliance: DSS-14 (KAMALA + ANNAPURNA + CHHINNAMASTA) + ENHAN3

use tianxiaos_ndimmorwyn_enterprise::aurum::*;
use tianxiaos_ndimmorwyn_enterprise::biomimetic::*;
use std::collections::HashMap;

#[test]
fn test_openreserve_adequacy_and_claim_settlement() {
    let mut ledger = OpenReserveLedger::new("VAULT-001", 1_000_000_00, 1_000_000_00);
    assert!(ledger.verify_reserve_adequacy());

    let claim = ledger
        .mint_and_settle_claim("txEUR", 500_000_00, "RGU-01", "RGU-02", 1000)
        .expect("Minting should succeed");
    assert!(claim.settled);
    assert!(ledger.verify_reserve_adequacy());
}

#[test]
fn test_ubyx_par_value_clearing() {
    let ubyx = UbyxParityBus::new();
    let res = ubyx.clear_at_par("USDC", "EURC", 50_000_00).expect("Clearing should succeed");
    assert_eq!(res.gross_amount_cents, 50_000_00);
    assert_eq!(res.net_settled_cents, 50_000_00);
    assert!(res.parity_preserved);
}

#[test]
fn test_treasury_veritas_waterfall() {
    let waterfall = VeritasRexWaterfall::new();
    let (vaults, allocations) = waterfall.allocate(628_00, &HashMap::new());

    assert_eq!(*vaults.get("vault_0a_escrow_settlement_lock").unwrap(), 628_00);
    assert!(allocations[0].is_fully_funded);
}
