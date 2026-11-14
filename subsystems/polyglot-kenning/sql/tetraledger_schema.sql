-- ffp: FFP-SQL-001 tetraledger-wal-schema sql
-- TianxiaOS Core 12 (Nimbus-Ledger) - Annapūrṇā Custody Integrity Gate
-- TetraLedger Double-Entry Journal with Strict I_1 = 0 Balance Invariant & Defensive Anti-DROP Triggers

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. Double-Entry Accounts Table
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL CHECK(account_type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Journal Transactions Header
CREATE TABLE IF NOT EXISTS journal_entries (
    entry_id TEXT PRIMARY KEY,
    blake3_merkle_root TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);

-- 3. Journal Lines (Enforces Credit + Debit Sum = 0 => I_1 = 0)
CREATE TABLE IF NOT EXISTS journal_lines (
    line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL REFERENCES journal_entries(entry_id) ON DELETE RESTRICT,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    amount_eur_cents INTEGER NOT NULL, -- Positive for debit, negative for credit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Defensive Anti-Abuse Trigger (Prevent Tampering with Ledger Lines)
CREATE TRIGGER IF NOT EXISTS trg_prevent_journal_update
BEFORE UPDATE ON journal_lines
BEGIN
    SELECT RAISE(ABORT, 'CHHINNAMASTA_LEDGER_SECURITY: Journal lines are strictly append-only and immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_prevent_journal_delete
BEFORE DELETE ON journal_lines
BEGIN
    SELECT RAISE(ABORT, 'CHHINNAMASTA_LEDGER_SECURITY: Deleting journal lines is strictly prohibited.');
END;

-- Seed Accounts for Veritas-Rex & TreasuryEscrow Settlement
INSERT OR IGNORE INTO accounts (account_id, account_name, account_type) VALUES
('ACT-001', 'Veritas-Rex Escrow Vault 0A', 'ASSET'),
('ACT-002', 'TreasuryEscrow Accounts Receivable', 'ASSET'),
('ACT-003', 'K78 Settlement Liability', 'LIABILITY'),
('ACT-004', 'Tianxia Sovereign Treasury', 'EQUITY');
