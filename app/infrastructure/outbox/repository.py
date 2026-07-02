from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.outbox.models import OutboxMessage


class OutboxPublisher(Protocol):
    async def publish(self, message: OutboxMessage) -> None: ...


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, message: OutboxMessage) -> None:
        self._session.add(message)

    async def list_pending(self, limit: int = 100) -> list[OutboxMessage]:
        now = datetime.now(timezone.utc)
        statement = (
            select(OutboxMessage)
            .where(OutboxMessage.status == "pending")
            .where(
                (OutboxMessage.next_attempt_at.is_(None))
                | (OutboxMessage.next_attempt_at <= now)
            )
            .order_by(OutboxMessage.created_at)
            .limit(limit)
        )
        result = await self._session.scalars(statement)
        return list(result.all())

    async def mark_published(self, message: OutboxMessage) -> None:
        message.status = "published"
        message.published_at = datetime.now(timezone.utc)
        message.error_message = None

    async def mark_failed(self, message: OutboxMessage, error: str) -> None:
        message.retry_count += 1
        message.error_message = error[:2000]
        if message.retry_count >= message.max_retries:
            message.status = "dead"
