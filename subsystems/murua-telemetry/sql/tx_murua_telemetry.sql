-- ffp: FFP-MURUA-SQL database declarative
-- Master Bilateral Corridor & Constructal-Barabasi Priors
CREATE TABLE IF NOT EXISTS murua_corridor_priors (
    corridor_id TEXT PRIMARY KEY,           -- e.g., 'NL-AMS_EE-TLL_12618'
    origin_impc TEXT NOT NULL,              -- 'NLAMSA' (Amsterdam IMEC)
    dest_impc TEXT NOT NULL,                -- 'EERUKB' (Omniva Rukki tee 7)
    dest_depot TEXT NOT NULL,               -- 'MUSTAMAE_KANDEKESKUS'
    c_cbd_score REAL NOT NULL,              -- Bifurcated Constructal-Barabasi Score
    barabasi_tau0_hours REAL DEFAULT 36.0,  -- Priority queue characteristic time scale
    rho_parcel_load REAL DEFAULT 0.82,      -- Active Class 1 parcel traffic intensity
    linehaul_mu_log REAL DEFAULT 4.05,      -- Log-normal linehaul mean
    linehaul_sigma_log REAL DEFAULT 0.28,   -- Log-normal linehaul std dev
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Forensic Envelope & Crowdsourced Observation Ledger
CREATE TABLE IF NOT EXISTS murua_envelope_forensics (
    observation_id TEXT PRIMARY KEY,
    corridor_id TEXT REFERENCES murua_corridor_priors(corridor_id),
    order_ref_hash TEXT NOT NULL,           -- e.g., '58b73b08', 'c31f078b'
    reporter_node_ip TEXT DEFAULT '10.77.0.4',
    
    -- 4-Point Temporal Decomposition
    vendor_shipped_ts TIMESTAMP,            -- Electronic "Shipped" button timestamp
    carrier_pickup_ts TIMESTAMP NOT NULL,   -- Verified physical carrier collection
    origin_cfc_postmark_dt DATE,            -- Extracted from front cancellation stamp
    dest_hub_inkjet_dt DATE,                -- Extracted from reverse Omniva dot-matrix spray
    box_last_empty_ts TIMESTAMP,            -- Last verified empty sweep at Box #01
    box_discovered_ts TIMESTAMP,            -- Exact keyed discovery timestamp
    
    -- Physical & Acoustic Measurements
    envelope_class TEXT CHECK(envelope_class IN ('STD_ENVELOPE', 'A5_PADDED', 'C4_FLAT', 'PACKET')),
    gross_mass_grams REAL,                  -- Digital scale weight (±0.1g)
    thickness_mm REAL,                      -- Caliper thickness
    srm_acoustic_delta_zeta REAL,           -- Lamb-wave damping shift on EN 13724 steel tray
    
    -- Decoded Symbology Payloads
    franking_indicia_type TEXT CHECK(franking_indicia_type IN ('POSTZEGELCODE_9CHAR', 'ADHESIVE_STAMP', 'PORT_BETAALD', 'DATAMATRIX_2D')),
    postnl_kix_string TEXT,                 -- Decoded RM4SCC/KIX string
    orange_id_tag_raw TEXT,                 -- Decoded 4-state fluorescent bar sequence
    omniva_spray_raw TEXT,                  -- Decoded Rukki tee inward sorting string
    
    -- Verification & Trust
    softem_attribution_score REAL DEFAULT 1.0,
    photo_front_blake3 TEXT,
    photo_back_blake3 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Master Merkle Provenance Audit Trail
CREATE TABLE IF NOT EXISTS murua_audit_ledger (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    leaf_hash TEXT NOT NULL,
    merkle_root TEXT NOT NULL,
    node_ip TEXT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed Initial Corridors
INSERT OR REPLACE INTO murua_corridor_priors (
    corridor_id, origin_impc, dest_impc, dest_depot,
    c_cbd_score, barabasi_tau0_hours, rho_parcel_load, linehaul_mu_log, linehaul_sigma_log
) VALUES
('NL-AMS_EE-TLL_12618', 'NLAMSA', 'EERUKB', 'MUSTAMAE_KANDEKESKUS', 11500.0, 36.0, 0.82, 4.05, 0.28),
('BE-BRU_EE-TLL', 'BEBRUA', 'EESMAA', 'BALTI_JAAM_SMARTPOST', 19800.0, 12.0, 0.45, 3.80, 0.22),
('DE-FRA_EE-TLL', 'DEFRAB', 'EERUKB', 'MUSTAMAE_KANDEKESKUS', 8400.0, 48.0, 0.89, 4.20, 0.35);
