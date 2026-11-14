-- ffp: FFP-SQL-001 crownforge-tetraledger-schema declarative
-- Compliance: DSS-14.2 (Mahāsarasvatī, Paramaśiva) | Zero Stubs | ENHAN3 Tri-Vector

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. Omphalos Serendipity Seeds Ledger
CREATE TABLE IF NOT EXISTS omphalos_serendipity_seeds (
    seed_id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_intent TEXT NOT NULL,
    target_domain TEXT NOT NULL,
    seed_384_hex TEXT NOT NULL UNIQUE,
    stochastic_resonance_snr REAL NOT NULL,
    arsi_prime_score REAL NOT NULL,
    created_at_epoch_ns INTEGER NOT NULL
);

-- 2. Noetic Kenning Telemetry & Sentience Ledger
CREATE TABLE IF NOT EXISTS noetic_kenning_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed_id INTEGER NOT NULL REFERENCES omphalos_serendipity_seeds(seed_id),
    valence REAL NOT NULL,
    arousal REAL NOT NULL,
    dominance REAL NOT NULL,
    urgency REAL NOT NULL,
    resonance REAL NOT NULL,
    caution REAL NOT NULL,
    sixth_sense_score REAL NOT NULL,
    ego_separation REAL NOT NULL,
    decision_gate TEXT NOT NULL,
    created_at_epoch_ns INTEGER NOT NULL
);

-- 3. Tremor Pheromone Dispersions Ledger
CREATE TABLE IF NOT EXISTS tremor_pheromone_dispersions (
    dispersion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_tag TEXT NOT NULL,
    environmental_medium TEXT NOT NULL,
    dispersed_cells INTEGER NOT NULL,
    parity_seal_hex TEXT NOT NULL,
    packet_footprint_bytes INTEGER NOT NULL DEFAULT 0,
    created_at_epoch_ns INTEGER NOT NULL
);

-- 4. Ego Naga Hussar Army Registry
CREATE TABLE IF NOT EXISTS ego_naga_hussar_registry (
    seal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    commander_id INTEGER NOT NULL, -- 1=Lord Naga, 2=Lady Naga
    commander_name TEXT NOT NULL,
    legion_id INTEGER NOT NULL CHECK (legion_id >= 0 AND legion_id < 64000),
    subagent_index INTEGER NOT NULL CHECK (subagent_index >= 0 AND subagent_index < 100000),
    seal_u128_hex TEXT NOT NULL UNIQUE,
    urn_tag TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at_epoch_ns INTEGER NOT NULL
);

-- 5. Maha Madpie Breakout Events Ledger
CREATE TABLE IF NOT EXISTS maha_madpie_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    boundary_hash TEXT NOT NULL,
    stalled_problem TEXT NOT NULL,
    stall_count INTEGER NOT NULL,
    scoured_domain TEXT NOT NULL,
    transplanted_principle TEXT NOT NULL,
    rosette_cells INTEGER NOT NULL DEFAULT 7,
    status TEXT NOT NULL,
    resolved_at_epoch_ns INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_seeds_domain ON omphalos_serendipity_seeds(target_domain);
CREATE INDEX IF NOT EXISTS idx_hussar_legion ON ego_naga_hussar_registry(legion_id, subagent_index);
CREATE INDEX IF NOT EXISTS idx_madpie_boundary ON maha_madpie_events(boundary_hash);
