CREATE TABLE IF NOT EXISTS agent_definitions (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    system_prompt TEXT NOT NULL DEFAULT '',
    graph_code VARCHAR(100) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    is_builtin BOOLEAN NOT NULL DEFAULT TRUE,
    owner_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_agent_definitions_code UNIQUE (code)
);

CREATE INDEX IF NOT EXISTS ix_agent_definitions_code
    ON agent_definitions (code);

CREATE INDEX IF NOT EXISTS ix_agent_definitions_enabled
    ON agent_definitions (enabled);

CREATE TABLE IF NOT EXISTS agent_conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id BIGINT NOT NULL REFERENCES agent_definitions(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL DEFAULT '新会话',
    target_type VARCHAR(50),
    target_code VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_agent_conversations_user_id
    ON agent_conversations (user_id);

CREATE INDEX IF NOT EXISTS ix_agent_conversations_agent_id
    ON agent_conversations (agent_id);

CREATE INDEX IF NOT EXISTS ix_agent_conversations_target_type
    ON agent_conversations (target_type);

CREATE INDEX IF NOT EXISTS ix_agent_conversations_target_code
    ON agent_conversations (target_code);

CREATE TABLE IF NOT EXISTS agent_messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id BIGINT NOT NULL REFERENCES agent_definitions(id) ON DELETE CASCADE,
    role VARCHAR(30) NOT NULL,
    message_type VARCHAR(50) NOT NULL DEFAULT 'text',
    content TEXT NOT NULL DEFAULT '',
    tool_call_id VARCHAR(100),
    tool_name VARCHAR(100),
    payload_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_agent_messages_conversation_id
    ON agent_messages (conversation_id);

CREATE INDEX IF NOT EXISTS ix_agent_messages_user_id
    ON agent_messages (user_id);

CREATE INDEX IF NOT EXISTS ix_agent_messages_agent_id
    ON agent_messages (agent_id);

CREATE INDEX IF NOT EXISTS ix_agent_messages_role
    ON agent_messages (role);

CREATE INDEX IF NOT EXISTS ix_agent_messages_message_type
    ON agent_messages (message_type);

CREATE INDEX IF NOT EXISTS ix_agent_messages_tool_call_id
    ON agent_messages (tool_call_id);

CREATE INDEX IF NOT EXISTS ix_agent_messages_tool_name
    ON agent_messages (tool_name);

CREATE TABLE IF NOT EXISTS agent_runs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id BIGINT NOT NULL REFERENCES agent_definitions(id) ON DELETE CASCADE,
    conversation_id BIGINT REFERENCES agent_conversations(id) ON DELETE SET NULL,
    input_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_text TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'running',
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_agent_runs_user_id
    ON agent_runs (user_id);

CREATE INDEX IF NOT EXISTS ix_agent_runs_agent_id
    ON agent_runs (agent_id);

CREATE INDEX IF NOT EXISTS ix_agent_runs_conversation_id
    ON agent_runs (conversation_id);

CREATE INDEX IF NOT EXISTS ix_agent_runs_status
    ON agent_runs (status);

CREATE TABLE IF NOT EXISTS agent_reports (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id BIGINT NOT NULL REFERENCES agent_definitions(id) ON DELETE CASCADE,
    run_id BIGINT NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    target_type VARCHAR(50) NOT NULL DEFAULT 'fund',
    target_code VARCHAR(100),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_agent_reports_user_id
    ON agent_reports (user_id);

CREATE INDEX IF NOT EXISTS ix_agent_reports_agent_id
    ON agent_reports (agent_id);

CREATE INDEX IF NOT EXISTS ix_agent_reports_run_id
    ON agent_reports (run_id);

CREATE INDEX IF NOT EXISTS ix_agent_reports_target_type
    ON agent_reports (target_type);

CREATE INDEX IF NOT EXISTS ix_agent_reports_target_code
    ON agent_reports (target_code);
