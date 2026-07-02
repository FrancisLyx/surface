import asyncio
import logging
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.outbox.repository import OutboxPublisher, OutboxRepository

logger = logging.getLogger(__name__)
SessionFactory = Callable[[], AsyncSession]


class OutboxWorker:
    def __init__(
        self,
        session_factory: SessionFactory,
        publisher: OutboxPublisher,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._publisher = publisher
        self._batch_size = batch_size

    async def run_once(self) -> int:
        async with self._session_factory() as session:
            repository = OutboxRepository(session)
            messages = await repository.list_pending(self._batch_size)
            for message in messages:
                try:
                    await self._publisher.publish(message)
                    await repository.mark_published(message)
                except Exception as exc:
                    logger.exception(
                        "outbox publish failed",
                        extra={"message_id": message.message_id},
                    )
                    await repository.mark_failed(message, str(exc))
            await session.commit()
            return len(messages)

    async def run_forever(self, interval_seconds: float = 5.0) -> None:
        while True:
            await self.run_once()
            await asyncio.sleep(interval_seconds)
