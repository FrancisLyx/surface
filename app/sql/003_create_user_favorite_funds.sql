CREATE TABLE IF NOT EXISTS user_favorite_funds (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fund_code VARCHAR(20) NOT NULL,
    fund_name VARCHAR(255) NOT NULL,
    fund_type VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_favorite_funds_user_id_fund_code UNIQUE (user_id, fund_code)
);

CREATE INDEX IF NOT EXISTS ix_user_favorite_funds_user_id
    ON user_favorite_funds (user_id);

CREATE INDEX IF NOT EXISTS ix_user_favorite_funds_fund_code
    ON user_favorite_funds (fund_code);
