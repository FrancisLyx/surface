from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class OutboxMessage(Base):
    __tablename__ = "outbox_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    aggregate_type: Mapped[str | None] = mapped_column(
        String(100), index=True, nullable=True
    )
    aggregate_id: Mapped[str | None] = mapped_column(
        String(100), index=True, nullable=True
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    headers_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    status: Mapped[str] = mapped_column(
        String(30), index=True, nullable=False, default="pending"
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True, nullable=True
    )
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    locked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @classmethod
    def from_event(
        cls,
        event: object,
        *,
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
        headers: dict[str, Any] | None = None,
    ) -> "OutboxMessage":
        payload = (
            event
            if isinstance(event, dict)
            else getattr(event, "__dict__", {"value": str(event)})
        )
        return cls(
            message_id=uuid4().hex,
            event_type=type(event).__name__
            if not isinstance(event, dict)
            else str(event.get("event_type", "dict")),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload_json=dict(payload),
            headers_json=headers or {},
        )
