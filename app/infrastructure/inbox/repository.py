from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.inbox.models import InboxMessage


class InboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def try_mark_processed(self, consumer_name: str, message_id: str) -> bool:
        self._session.add(
            InboxMessage(consumer_name=consumer_name, message_id=message_id)
        )
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            return False
        return True

    async def has_processed(self, consumer_name: str, message_id: str) -> bool:
        statement = select(InboxMessage.id).where(
            InboxMessage.consumer_name == consumer_name,
            InboxMessage.message_id == message_id,
        )
        return await self._session.scalar(statement) is not None
