from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent.models import (
    AgentConversation,
    AgentDefinition,
    AgentMessage,
    AgentReport,
    AgentRun,
)


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_definition_by_code(self, code: str) -> AgentDefinition | None:
        return await self._session.scalar(
            select(AgentDefinition).where(AgentDefinition.code == code)
        )

    async def get_run(self, run_id: int) -> AgentRun | None:
        return await self._session.get(AgentRun, run_id)

    async def get_conversation(self, conversation_id: int) -> AgentConversation | None:
        return await self._session.get(AgentConversation, conversation_id)

    async def get_enabled_definition_for_user(
        self, agent_id: int, user_id: int
    ) -> AgentDefinition | None:
        return await self._session.scalar(
            select(AgentDefinition).where(
                AgentDefinition.id == agent_id,
                AgentDefinition.enabled.is_(True),
                or_(
                    AgentDefinition.is_builtin.is_(True),
                    AgentDefinition.owner_user_id == user_id,
                ),
            )
        )

    async def count_definitions_for_user(self, user_id: int) -> int:
        return (
            await self._session.scalar(
                select(func.count())
                .select_from(AgentDefinition)
                .where(self._definition_where(user_id))
            )
            or 0
        )

    async def list_definitions_for_user(
        self, user_id: int, offset: int, limit: int
    ) -> list[AgentDefinition]:
        result = await self._session.scalars(
            select(AgentDefinition)
            .where(self._definition_where(user_id))
            .order_by(AgentDefinition.id.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.all())

    async def count_reports_for_user(
        self, user_id: int, agent_id: int | None, target_code: str | None
    ) -> int:
        return (
            await self._session.scalar(
                select(func.count())
                .select_from(AgentReport)
                .join(AgentDefinition, AgentDefinition.id == AgentReport.agent_id)
                .where(self._report_where(user_id, agent_id, target_code))
            )
            or 0
        )

    async def list_reports_for_user(
        self,
        user_id: int,
        agent_id: int | None,
        target_code: str | None,
        offset: int,
        limit: int,
    ) -> list[tuple[AgentReport, AgentDefinition]]:
        result = await self._session.execute(
            select(AgentReport, AgentDefinition)
            .join(AgentDefinition, AgentDefinition.id == AgentReport.agent_id)
            .where(self._report_where(user_id, agent_id, target_code))
            .order_by(AgentReport.created_at.desc(), AgentReport.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def get_report_for_user(
        self, report_id: int, user_id: int
    ) -> tuple[AgentReport, AgentDefinition] | None:
        result = await self._session.execute(
            select(AgentReport, AgentDefinition)
            .join(AgentDefinition, AgentDefinition.id == AgentReport.agent_id)
            .where(AgentReport.id == report_id, AgentReport.user_id == user_id)
        )
        row = result.first()
        return row if row is None else (row[0], row[1])

    async def count_conversations_for_user_agent(
        self, user_id: int, agent_id: int
    ) -> int:
        return (
            await self._session.scalar(
                select(func.count())
                .select_from(AgentConversation)
                .where(
                    AgentConversation.user_id == user_id,
                    AgentConversation.agent_id == agent_id,
                )
            )
            or 0
        )

    async def list_conversations_for_user_agent(
        self,
        user_id: int,
        agent_id: int,
        offset: int,
        limit: int,
    ) -> list[AgentConversation]:
        result = await self._session.scalars(
            select(AgentConversation)
            .where(
                AgentConversation.user_id == user_id,
                AgentConversation.agent_id == agent_id,
            )
            .order_by(AgentConversation.updated_at.desc(), AgentConversation.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.all())

    async def get_conversation_for_user(
        self, conversation_id: int, user_id: int
    ) -> AgentConversation | None:
        return await self._session.scalar(
            select(AgentConversation).where(
                AgentConversation.id == conversation_id,
                AgentConversation.user_id == user_id,
            )
        )

    async def get_conversation_for_user_agent(
        self,
        conversation_id: int,
        user_id: int,
        agent_id: int,
    ) -> AgentConversation | None:
        return await self._session.scalar(
            select(AgentConversation).where(
                AgentConversation.id == conversation_id,
                AgentConversation.user_id == user_id,
                AgentConversation.agent_id == agent_id,
            )
        )

    async def list_visible_messages(self, conversation_id: int) -> list[AgentMessage]:
        result = await self._session.scalars(
            select(AgentMessage)
            .where(
                AgentMessage.conversation_id == conversation_id,
                AgentMessage.role.in_(["user", "assistant"]),
            )
            .order_by(AgentMessage.created_at.asc(), AgentMessage.id.asc())
        )
        return list(result.all())

    async def list_history_messages(self, conversation_id: int) -> list[AgentMessage]:
        result = await self._session.scalars(
            select(AgentMessage)
            .where(
                AgentMessage.conversation_id == conversation_id,
                AgentMessage.role.in_(["user", "assistant"]),
            )
            .order_by(AgentMessage.created_at.desc(), AgentMessage.id.desc())
            .limit(20)
        )
        return list(result.all())

    def add(self, value) -> None:
        self._session.add(value)

    async def flush(self) -> None:
        await self._session.flush()

    async def refresh(self, value) -> None:
        await self._session.refresh(value)

    def _definition_where(self, user_id: int):
        return and_(
            AgentDefinition.enabled.is_(True),
            or_(
                AgentDefinition.is_builtin.is_(True),
                AgentDefinition.owner_user_id == user_id,
            ),
        )

    def _report_where(
        self, user_id: int, agent_id: int | None, target_code: str | None
    ):
        filters = [AgentReport.user_id == user_id]
        if target_code and target_code.strip():
            filters.append(AgentReport.target_code == target_code.strip())
        if agent_id:
            filters.append(AgentDefinition.id == agent_id)
        return and_(*filters)
