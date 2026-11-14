// ffp: FFP-TST-005 test-harbor-contradiction rust
// Compliance: DSS-14 (BAGALAMUKHI + BHAIRAVI) + ENHAN3

use tianxiaos_ndimmorwyn_enterprise::forge::*;

#[test]
fn test_harbor_gate_contradiction_detection() {
    let mut harbor = HarborGateEngine::new();
    harbor.register_rule(SemanticRuleAtom::new(
        "RULE-PROTECT-01",
        "GLOBAL",
        "NEVER_PERMIT_DROP_TABLE_ON_AUDIT",
    ));

    let benign = harbor.check_action_contradiction("GLOBAL", "audit_log_entry(RULE-PROTECT-01)");
    assert!(benign.is_ok());

    let adversarial = harbor.check_action_contradiction("GLOBAL", "DROP TABLE security_audit");
    assert!(adversarial.is_err());
    assert!(adversarial.unwrap_err().contains("CONTRADICTION_BLOCKED"));
}

#[test]
fn test_shandoff_diagnostic_generation() {
    let input = ProspectTelemetryInput {
        company_name: "Test FinTech".to_string(),
        sector_vector: "16_SEED_PAYMENTS".to_string(),
        estimated_monthly_llm_spend_eur: 10_000.0,
        uses_agentic_payments: true,
        open_senior_roles_days: 20,
    };

    let artifact = generate_shandoff_diagnostic(&input);
    assert!(artifact.projected_annual_opex_savings_eur > 0.0);
    assert_eq!(artifact.nix_flake_module_target, "tx-aurum-tetraledger-tap-x402.nix");
    assert!(!artifact.verification_hash.is_empty());
}
