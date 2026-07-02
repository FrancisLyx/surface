"""initial schema

Revision ID: 2026_07_02_0001
Revises:
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2026_07_02_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("role_id", sa.BigInteger(), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"])
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)
    op.create_index(op.f("ix_users_role_id"), "users", ["role_id"])

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "user_favorite_funds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("fund_code", sa.String(length=20), nullable=False),
        sa.Column("fund_name", sa.String(length=255), nullable=False),
        sa.Column("fund_type", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "fund_code", name="uq_user_favorite_funds_user_id_fund_code"
        ),
    )
    op.create_index(op.f("ix_user_favorite_funds_id"), "user_favorite_funds", ["id"])
    op.create_index(
        op.f("ix_user_favorite_funds_user_id"), "user_favorite_funds", ["user_id"]
    )
    op.create_index(
        op.f("ix_user_favorite_funds_fund_code"), "user_favorite_funds", ["fund_code"]
    )

    op.create_table(
        "ai_fund_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("fund_code", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_fund_reports_id"), "ai_fund_reports", ["id"])
    op.create_index(op.f("ix_ai_fund_reports_user_id"), "ai_fund_reports", ["user_id"])
    op.create_index(
        op.f("ix_ai_fund_reports_fund_code"), "ai_fund_reports", ["fund_code"]
    )

    op.create_table(
        "agent_definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("graph_code", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("is_builtin", sa.Boolean(), nullable=False),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_agent_definitions_code"),
    )
    op.create_index(op.f("ix_agent_definitions_id"), "agent_definitions", ["id"])
    op.create_index(op.f("ix_agent_definitions_code"), "agent_definitions", ["code"])
    op.create_index(
        op.f("ix_agent_definitions_enabled"), "agent_definitions", ["enabled"]
    )

    op.create_table(
        "agent_conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=True),
        sa.Column("target_code", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agent_definitions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_conversations_id"), "agent_conversations", ["id"])
    op.create_index(
        op.f("ix_agent_conversations_user_id"), "agent_conversations", ["user_id"]
    )
    op.create_index(
        op.f("ix_agent_conversations_agent_id"), "agent_conversations", ["agent_id"]
    )
    op.create_index(
        op.f("ix_agent_conversations_target_type"),
        "agent_conversations",
        ["target_type"],
    )
    op.create_index(
        op.f("ix_agent_conversations_target_code"),
        "agent_conversations",
        ["target_code"],
    )

    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_id", sa.BigInteger(), nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=True),
        sa.Column("input_json", sa.JSON(), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agent_definitions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["agent_conversations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_runs_id"), "agent_runs", ["id"])
    op.create_index(op.f("ix_agent_runs_user_id"), "agent_runs", ["user_id"])
    op.create_index(op.f("ix_agent_runs_agent_id"), "agent_runs", ["agent_id"])
    op.create_index(
        op.f("ix_agent_runs_conversation_id"), "agent_runs", ["conversation_id"]
    )
    op.create_index(op.f("ix_agent_runs_status"), "agent_runs", ["status"])

    op.create_table(
        "agent_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("message_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_call_id", sa.String(length=100), nullable=True),
        sa.Column("tool_name", sa.String(length=100), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agent_definitions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["agent_conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_messages_id"), "agent_messages", ["id"])
    op.create_index(
        op.f("ix_agent_messages_conversation_id"), "agent_messages", ["conversation_id"]
    )
    op.create_index(op.f("ix_agent_messages_user_id"), "agent_messages", ["user_id"])
    op.create_index(op.f("ix_agent_messages_agent_id"), "agent_messages", ["agent_id"])
    op.create_index(op.f("ix_agent_messages_role"), "agent_messages", ["role"])
    op.create_index(
        op.f("ix_agent_messages_message_type"), "agent_messages", ["message_type"]
    )
    op.create_index(
        op.f("ix_agent_messages_tool_call_id"), "agent_messages", ["tool_call_id"]
    )
    op.create_index(
        op.f("ix_agent_messages_tool_name"), "agent_messages", ["tool_name"]
    )

    op.create_table(
        "agent_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("agent_id", sa.BigInteger(), nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_code", sa.String(length=100), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agent_definitions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_reports_id"), "agent_reports", ["id"])
    op.create_index(op.f("ix_agent_reports_user_id"), "agent_reports", ["user_id"])
    op.create_index(op.f("ix_agent_reports_agent_id"), "agent_reports", ["agent_id"])
    op.create_index(op.f("ix_agent_reports_run_id"), "agent_reports", ["run_id"])
    op.create_index(
        op.f("ix_agent_reports_target_type"), "agent_reports", ["target_type"]
    )
    op.create_index(
        op.f("ix_agent_reports_target_code"), "agent_reports", ["target_code"]
    )

    op.create_table(
        "outbox_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=200), nullable=False),
        sa.Column("aggregate_type", sa.String(length=100), nullable=True),
        sa.Column("aggregate_id", sa.String(length=100), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("headers_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=100), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_outbox_messages_message_id"),
        "outbox_messages",
        ["message_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_outbox_messages_event_type"), "outbox_messages", ["event_type"]
    )
    op.create_index(
        op.f("ix_outbox_messages_aggregate_type"), "outbox_messages", ["aggregate_type"]
    )
    op.create_index(
        op.f("ix_outbox_messages_aggregate_id"), "outbox_messages", ["aggregate_id"]
    )
    op.create_index(op.f("ix_outbox_messages_status"), "outbox_messages", ["status"])
    op.create_index(
        op.f("ix_outbox_messages_next_attempt_at"),
        "outbox_messages",
        ["next_attempt_at"],
    )

    op.create_table(
        "inbox_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("consumer_name", sa.String(length=100), nullable=False),
        sa.Column("message_id", sa.String(length=64), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consumer_name", "message_id", name="uq_inbox_messages_consumer_message"
        ),
    )


def downgrade() -> None:
    op.drop_table("inbox_messages")
    op.drop_index(
        op.f("ix_outbox_messages_next_attempt_at"), table_name="outbox_messages"
    )
    op.drop_index(op.f("ix_outbox_messages_status"), table_name="outbox_messages")
    op.drop_index(op.f("ix_outbox_messages_aggregate_id"), table_name="outbox_messages")
    op.drop_index(
        op.f("ix_outbox_messages_aggregate_type"), table_name="outbox_messages"
    )
    op.drop_index(op.f("ix_outbox_messages_event_type"), table_name="outbox_messages")
    op.drop_index(op.f("ix_outbox_messages_message_id"), table_name="outbox_messages")
    op.drop_table("outbox_messages")
    op.drop_table("agent_reports")
    op.drop_table("agent_messages")
    op.drop_table("agent_runs")
    op.drop_table("agent_conversations")
    op.drop_table("agent_definitions")
    op.drop_table("ai_fund_reports")
    op.drop_table("user_favorite_funds")
    op.drop_table("system_settings")
    op.drop_table("users")
