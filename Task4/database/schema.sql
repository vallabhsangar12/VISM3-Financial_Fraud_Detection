-- ============================================================
-- FraudShield Database Schema — PostgreSQL
-- Task 4 | Vinayak IT Internship | Month 3
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ────────────────────────────────────────────────────────────
-- USERS (Analysts & Admins)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id      UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    username     VARCHAR(50)   NOT NULL UNIQUE,
    email        VARCHAR(120)  NOT NULL UNIQUE,
    full_name    VARCHAR(100),
    role         VARCHAR(20)   NOT NULL DEFAULT 'analyst'  -- 'admin' | 'analyst' | 'viewer'
                              CHECK (role IN ('admin', 'analyst', 'viewer')),
    hashed_pw    TEXT          NOT NULL,
    is_active    BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    last_login   TIMESTAMPTZ
);

-- ────────────────────────────────────────────────────────────
-- TRANSACTIONS (Raw ingested records)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    txn_id              VARCHAR(20)   PRIMARY KEY,
    card_id             VARCHAR(20)   NOT NULL,
    account_id          VARCHAR(20),
    amount              NUMERIC(14,2) NOT NULL,
    time_seconds        FLOAT,               -- Seconds since epoch (dataset feature)
    merchant_category   VARCHAR(50),
    location            VARCHAR(100),
    is_night            SMALLINT      DEFAULT 0 CHECK (is_night IN (0,1)),
    rapid_txn           SMALLINT      DEFAULT 0 CHECK (rapid_txn IN (0,1)),
    -- V1–V28 PCA features stored as JSONB for flexibility
    v_features          JSONB,
    fraud_score         FLOAT,
    risk_level          VARCHAR(10)   CHECK (risk_level IN ('CRITICAL','HIGH','MEDIUM','LOW')),
    ground_truth        SMALLINT      CHECK (ground_truth IN (0, 1)),   -- 0=legit, 1=fraud
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_txn_card_id    ON transactions (card_id);
CREATE INDEX IF NOT EXISTS idx_txn_risk_level ON transactions (risk_level);
CREATE INDEX IF NOT EXISTS idx_txn_created_at ON transactions (created_at DESC);

-- ────────────────────────────────────────────────────────────
-- ALERTS (Fraud flags raised by the detection model)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    alert_id        UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    txn_id          VARCHAR(20)   NOT NULL REFERENCES transactions (txn_id),
    fraud_score     FLOAT         NOT NULL,
    risk_level      VARCHAR(10)   NOT NULL,
    status          VARCHAR(20)   NOT NULL DEFAULT 'Pending'
                                  CHECK (status IN ('Pending','Investigating','Resolved')),
    resolution      VARCHAR(30)   CHECK (resolution IN ('True Fraud','False Positive','Inconclusive')),
    investigator_id UUID          REFERENCES users (user_id),
    notes           TEXT,
    severity        VARCHAR(10)   CHECK (severity IN ('Low','Medium','High','Critical')),
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_status     ON alerts (status);
CREATE INDEX IF NOT EXISTS idx_alert_risk       ON alerts (risk_level);
CREATE INDEX IF NOT EXISTS idx_alert_created_at ON alerts (created_at DESC);

-- Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_alerts_updated_at
    BEFORE UPDATE ON alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ────────────────────────────────────────────────────────────
-- CASES (Investigation cases linked to alerts)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cases (
    case_id         VARCHAR(20)   PRIMARY KEY,      -- e.g. "CASE-A1B2C3"
    alert_id        UUID          REFERENCES alerts (alert_id),
    txn_id          VARCHAR(20)   REFERENCES transactions (txn_id),
    title           VARCHAR(200)  NOT NULL,
    description     TEXT          NOT NULL,
    priority        VARCHAR(10)   NOT NULL DEFAULT 'Medium'
                                  CHECK (priority IN ('Low','Medium','High','Critical')),
    status          VARCHAR(15)   NOT NULL DEFAULT 'Open'
                                  CHECK (status IN ('Open','In Progress','Closed')),
    assigned_to     UUID          REFERENCES users (user_id),
    outcome         VARCHAR(30)   CHECK (outcome IN ('Confirmed Fraud','False Alarm','Inconclusive')),
    closed_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_case_status ON cases (status);
CREATE INDEX IF NOT EXISTS idx_case_assigned ON cases (assigned_to);

CREATE TRIGGER trg_cases_updated_at
    BEFORE UPDATE ON cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ────────────────────────────────────────────────────────────
-- CASE NOTES (Append-only comments on a case)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS case_notes (
    note_id     UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id     VARCHAR(20)   NOT NULL REFERENCES cases (case_id),
    author_id   UUID          REFERENCES users (user_id),
    body        TEXT          NOT NULL,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_note_case ON case_notes (case_id, created_at);

-- ────────────────────────────────────────────────────────────
-- AUDIT LOGS (Immutable append-only audit trail)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id      UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID          REFERENCES users (user_id),
    username    VARCHAR(50),                -- Denormalised for query speed
    action      VARCHAR(200)  NOT NULL,
    entity_type VARCHAR(30),               -- 'alert' | 'case' | 'model' | 'system'
    entity_id   VARCHAR(50),
    ip_address  INET,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_entity  ON audit_logs (entity_type, entity_id);

-- Prevent deletion (audit logs are immutable)
CREATE RULE no_delete_audit_log AS ON DELETE TO audit_logs DO INSTEAD NOTHING;

-- ────────────────────────────────────────────────────────────
-- DAILY FRAUD REPORTS (Pre-aggregated for dashboards)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS daily_reports (
    report_date         DATE          PRIMARY KEY,
    total_transactions  INTEGER       NOT NULL DEFAULT 0,
    fraud_count         INTEGER       NOT NULL DEFAULT 0,
    fraud_amount        NUMERIC(16,2) NOT NULL DEFAULT 0,
    false_positives     INTEGER       NOT NULL DEFAULT 0,
    true_positives      INTEGER       NOT NULL DEFAULT 0,
    avg_fraud_score     FLOAT,
    generated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ────────────────────────────────────────────────────────────
-- SEED DATA: Demo admin user (password: secret)
-- ────────────────────────────────────────────────────────────
INSERT INTO users (username, email, full_name, role, hashed_pw)
VALUES
    ('admin',   'admin@fraudshield.io',   'System Admin',    'admin',   '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'),
    ('analyst', 'analyst@fraudshield.io', 'Lead Analyst',    'analyst', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW')
ON CONFLICT (username) DO NOTHING;
