// ffp: FFP-MURUA-ESCROW escrow-veritas-actuator rust
//! Veritas-Rex Escrow Waterfall & Autonomous Remedial Actuation Engine
//! Manages pre-emptive dispute locks, cryptographic proof dossiers,
//! and statutory depot inquiries under Estonian Postal Act (Postiseadus §35/§36).

use blake3::Hasher;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EscrowCase {
    pub order_id: String,
    pub item_name: String,
    pub vendor_name: String,
    pub origin_corridor: String,
    pub escrow_amount_eur: f64,
    pub order_created_utc: DateTime<Utc>,
    pub vendor_shipped_utc: DateTime<Utc>,
    pub carrier_pickup_utc: DateTime<Utc>,
    pub auto_finalization_cutoff_utc: DateTime<Utc>,
    pub dispute_lock_window_start_utc: DateTime<Utc>,
    pub current_status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatutoryDepotInquiry {
    pub inquiry_id: String,
    pub target_facility: String, // e.g. "MUSTIKA_POSTKONTOR" or "RUKKI_TEE_7_COMMISSION"
    pub legal_basis: String,     // "Postiseadus §35 / §36"
    pub recipient_name: String,
    pub delivery_address: String, // "Pallasti 28, 12618 Tallinn"
    pub consignment_description: String,
    pub physical_dimensions: String, // "Standard envelope, ~65g, 4mm thickness"
    pub inquiry_payload_text: String,
    pub dispatched_utc: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VeritasRexDisputeDossier {
    pub dossier_id: String,
    pub order_id: String,
    pub escrow_locked_amount_eur: f64,
    pub proof_of_sweep_hash: String,
    pub formal_dispute_reason: String,
    pub demand_from_vendor: String,
    pub statutory_citations: Vec<String>,
    pub created_at_utc: DateTime<Utc>,
    pub submission_deadline_utc: DateTime<Utc>,
    pub integrity_signature: String,
}

pub struct VeritasEscrowActuator {
    pub recipient_name: String,
    pub delivery_address: String,
}

impl Default for VeritasEscrowActuator {
    fn default() -> Self {
        Self {
            recipient_name: "Authorized Recipient (Box #01)".to_string(),
            delivery_address: "Pallasti 28, Mustamäe, 12618 Tallinn, Estonia".to_string(),
        }
    }
}

impl VeritasEscrowActuator {
    pub fn new(recipient_name: String, delivery_address: String) -> Self {
        Self {
            recipient_name,
            delivery_address,
        }
    }

    /// Evaluates whether an escrow case requires immediate dispute locking
    pub fn should_lock_escrow(&self, case: &EscrowCase, now_utc: DateTime<Utc>, box_empty: bool) -> bool {
        if !box_empty {
            return false;
        }

        // Lock if current time has crossed dispute lock window start or within 48h of cutoff
        let hours_to_cutoff = (case.auto_finalization_cutoff_utc - now_utc)
            .num_seconds() as f64
            / 3600.0;

        now_utc >= case.dispute_lock_window_start_utc || hours_to_cutoff <= 48.0
    }

    /// Generates Tier 1 statutory depot inquiry under Estonian Postiseadus §35/§36
    pub fn generate_depot_inquiries(&self, case: &EscrowCase) -> Vec<StatutoryDepotInquiry> {
        let ts = Utc::now();

        // 1. Mustika Postkontor (Karjavälja 4) hold-shelf check
        let mustika_text = format!(
            "PÄRING LIHTSAADETISTE HOIORIIULIST (Postiseadus §35 alusel):\n\
             Palun kontrollida Mustika Postkontori (Karjavälja 4) registreerimata lihtkirjade riiulit.\n\
             Saaja: {}\n\
             Aadress: {}\n\
             Saadetise kirjeldus: 2 tk rahvusvahelised lihtümbrikud Hollandist (PostNL), postitatud 27.10.2026.\n\
             Sisu: märkmikud / kirjatarbed. Kaal ca 65g tk.\n\
             Palume teavitada saajat leiust enne tagastustoimingute algust.",
            self.recipient_name, self.delivery_address
        );

        let mut h1 = Hasher::new();
        h1.update(mustika_text.as_bytes());
        let id1 = format!("DEPOT-MUSTIKA-{}", &h1.finalize().to_hex()[..12]);

        let inq1 = StatutoryDepotInquiry {
            inquiry_id: id1,
            target_facility: "Mustika Postkontor (Karjavälja 4)".to_string(),
            legal_basis: "Eesti Vabariigi Postiseadus §35 (Saadetise väljastamise kord)".to_string(),
            recipient_name: self.recipient_name.clone(),
            delivery_address: self.delivery_address.clone(),
            consignment_description: format!("PostNL Priority Envelopes (Order {})", case.order_id),
            physical_dimensions: "2x Standard Paper Envelopes, ~65g, ~4mm".to_string(),
            inquiry_payload_text: mustika_text,
            dispatched_utc: ts,
        };

        // 2. Rukki tee 7 Undeliverable Commission notice
        let rukki_text = format!(
            "AVALDUS POSTISEADUS §36 ALUSEL (Rukki tee 7 jaotuskeskuse komisjonile):\n\
             Juhul kui saadetise aadresskleebis on vigastatud või eraldunud sorteerimisel EERUKB jaotuskeskuses,\n\
             registreerida käesolev taotlus saadetise tuvastamiseks:\n\
             Sihtkoht: {}\n\
             Eeldatav saabumiskuupäev jaotusse: 30.10.2026 - 04.11.2026.\n\
             Päritolu: PostNL (NLAMSA), tellimusviide: {}.\n\
             Õigustatud isik nõuab saadetise väljastamist või hoiustamist.",
            self.delivery_address, case.order_id
        );

        let mut h2 = Hasher::new();
        h2.update(rukki_text.as_bytes());
        let id2 = format!("DEPOT-RUKKI-{}", &h2.finalize().to_hex()[..12]);

        let inq2 = StatutoryDepotInquiry {
            inquiry_id: id2,
            target_facility: "Omniva Jaotuskeskus Rukki tee 7 (EERUKB)".to_string(),
            legal_basis: "Eesti Vabariigi Postiseadus §36 (Väljamaksuta või kättetoimetamata postisaadetised)".to_string(),
            recipient_name: self.recipient_name.clone(),
            delivery_address: self.delivery_address.clone(),
            consignment_description: format!("PostNL Envelopes (Order {})", case.order_id),
            physical_dimensions: "Standard Paper Envelopes, ~65g, ~4mm".to_string(),
            inquiry_payload_text: rukki_text,
            dispatched_utc: ts,
        };

        vec![inq1, inq2]
    }

    /// Generates Tier 2 Veritas-Rex Dispute Dossier for platform escrow locking
    pub fn generate_dispute_dossier(
        &self,
        case: &EscrowCase,
        proof_of_sweep_hash: &str,
    ) -> VeritasRexDisputeDossier {
        let ts = Utc::now();
        let reason = format!(
            "NON-DELIVERY ESCROW FREEZE: Consignment {} has exceeded the 8-business-day EU Priority SLA window.\n\
             Physical mailbox {} verified empty on Friday Nov 6 with acoustic cryptographic proof {}.\n\
             Auto-finalization boundary on Monday Nov 9 at 14:10 EET must be halted immediately.",
            case.order_id, self.delivery_address, proof_of_sweep_hash
        );

        let demand = "Vendor must provide official PostNL Kassabon / Postkantoor proof of drop-off, \
                      including time-of-day receipt and 29-character UPU receptacle pre-advice \
                      confirming dispatch occurred prior to 17:00 CET on Oct 27, 2026."
            .to_string();

        let citations = vec![
            "UPU Letter Post Regulations Article 30-109 / 30-110".to_string(),
            "Eesti Vabariigi Postiseadus §35 & §36".to_string(),
            "EU Consumer Rights Directive 2011/83/EU Article 18".to_string(),
        ];

        let mut hasher = Hasher::new();
        hasher.update(case.order_id.as_bytes());
        hasher.update(&case.escrow_amount_eur.to_le_bytes());
        hasher.update(proof_of_sweep_hash.as_bytes());
        hasher.update(ts.to_rfc3339().as_bytes());
        let sig = hasher.finalize().to_hex().to_string();

        let dossier_id = format!("VR-DOSSIER-{}", &sig[..14]);

        VeritasRexDisputeDossier {
            dossier_id,
            order_id: case.order_id.clone(),
            escrow_locked_amount_eur: case.escrow_amount_eur,
            proof_of_sweep_hash: proof_of_sweep_hash.to_string(),
            formal_dispute_reason: reason,
            demand_from_vendor: demand,
            statutory_citations: citations,
            created_at_utc: ts,
            submission_deadline_utc: case.auto_finalization_cutoff_utc,
            integrity_signature: sig,
        }
    }
}
