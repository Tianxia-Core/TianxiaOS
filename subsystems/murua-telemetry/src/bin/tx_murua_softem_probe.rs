// ffp: FFP-MURUA-SOFTEM-BIN softem-probe-cli rust
//! Murua SOFTEM Factual Attribution Probe CLI
//! Tests carrier claims against Postiseadus symbolic constraints and Huber loss.

use murua_architecture_enhancement::softem::{CarrierClaim, SoftemProbe};
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    let test_mode = args.get(1).map(|s| s.as_str()).unwrap_or("hallucination");

    let softem = SoftemProbe::default();

    println!("================================================================================");
    println!(" MURUA SOFTEM FACTUAL ATTRIBUTION PROBE");
    println!(" Mode: {} | Epsilon Huber = {:.2} | Beta Softmax = {:.1}", test_mode, softem.epsilon_huber, softem.beta_softmax);
    println!("================================================================================");

    let (claim, preds, reals) = if test_mode == "valid" {
        (
            CarrierClaim {
                claim_id: "CLM-OMNIVA-VALID-SCAN".to_string(),
                statement: "S10 barcoded parcel scanned at Rukki tee 7 dock triggers automated locker dispatch".to_string(),
                has_s10_barcode: true,
                has_edi_hook: true,
                claims_locker_redirection: true,
                claims_sms_pin_delivery: true,
                statutory_anchor_cited: Some("UPU S10 Standard / Omniva Pakiteenus".to_string()),
            },
            vec![0.92, 0.88, 0.95],
            vec![0.95, 0.90, 0.96],
        )
    } else {
        (
            CarrierClaim {
                claim_id: "CLM-OMNIVA-CONFABULATED-OCR".to_string(),
                statement: "Omniva OCR reads telephone number from unbarcoded letter and creates parcel locker SMS".to_string(),
                has_s10_barcode: false,
                has_edi_hook: false,
                claims_locker_redirection: true,
                claims_sms_pin_delivery: true,
                statutory_anchor_cited: None,
            },
            vec![0.15, 0.10, 0.05],
            vec![0.95, 0.90, 0.96],
        )
    };

    let result = softem.verify_claim(&claim, &preds, &reals);

    println!("Claim ID:             {}", result.claim_id);
    println!("Statement:            {}", claim.statement);
    println!("Ontology Filter Pass: {}", result.passed_ontology_filter);
    println!("Spike Huber Loss:     {:.5}", result.softem_loss);
    println!("Attribution Score:    {:.4}", result.attribution_score);
    println!("Is Hallucination:     {}", result.is_hallucination);
    println!("Action Taken:         {}", result.action_taken);
    println!("Diagnostic:           {}", result.diagnostic_reason);
    println!("================================================================================");
}
