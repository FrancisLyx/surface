CREATE TABLE IF NOT EXISTS ai_fund_reports (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fund_code VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_fund_reports_user_id
    ON ai_fund_reports (user_id);

CREATE INDEX IF NOT EXISTS ix_ai_fund_reports_fund_code
    ON ai_fund_reports (fund_code);

CREATE INDEX IF NOT EXISTS ix_ai_fund_reports_created_at
    ON ai_fund_reports (created_at);
