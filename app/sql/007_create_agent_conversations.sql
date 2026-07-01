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

ALTER TABLE agent_runs
    ADD COLUMN IF NOT EXISTS conversation_id BIGINT REFERENCES agent_conversations(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_agent_runs_conversation_id
    ON agent_runs (conversation_id);
