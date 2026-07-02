from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.modules.agent.model import AgentConversation, AgentDefinition, AgentMessage, AgentReport


class AgentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_definition_by_code(self, code: str) -> AgentDefinition | None:
        return self._session.scalar(select(AgentDefinition).where(AgentDefinition.code == code))

    def get_enabled_definition_for_user(self, agent_id: int, user_id: int) -> AgentDefinition | None:
        return self._session.scalar(
            select(AgentDefinition).where(
                AgentDefinition.id == agent_id,
                AgentDefinition.enabled.is_(True),
                or_(AgentDefinition.is_builtin.is_(True), AgentDefinition.owner_user_id == user_id),
            )
        )

    def count_definitions_for_user(self, user_id: int) -> int:
        return self._session.scalar(
            select(func.count()).select_from(AgentDefinition).where(self._definition_where(user_id))
        ) or 0

    def list_definitions_for_user(self, user_id: int, offset: int, limit: int) -> list[AgentDefinition]:
        return list(
            self._session.scalars(
                select(AgentDefinition)
                .where(self._definition_where(user_id))
                .order_by(AgentDefinition.id.asc())
                .offset(offset)
                .limit(limit)
            ).all()
        )

    def count_reports_for_user(self, user_id: int, agent_id: int | None, target_code: str | None) -> int:
        return self._session.scalar(
            select(func.count())
            .select_from(AgentReport)
            .join(AgentDefinition, AgentDefinition.id == AgentReport.agent_id)
            .where(self._report_where(user_id, agent_id, target_code))
        ) or 0

    def list_reports_for_user(
        self,
        user_id: int,
        agent_id: int | None,
        target_code: str | None,
        offset: int,
        limit: int,
    ) -> list[tuple[AgentReport, AgentDefinition]]:
        return list(
            self._session.execute(
                select(AgentReport, AgentDefinition)
                .join(AgentDefinition, AgentDefinition.id == AgentReport.agent_id)
                .where(self._report_where(user_id, agent_id, target_code))
                .order_by(AgentReport.created_at.desc(), AgentReport.id.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )

    def get_report_for_user(self, report_id: int, user_id: int) -> tuple[AgentReport, AgentDefinition] | None:
        row = self._session.execute(
            select(AgentReport, AgentDefinition)
            .join(AgentDefinition, AgentDefinition.id == AgentReport.agent_id)
            .where(AgentReport.id == report_id, AgentReport.user_id == user_id)
        ).first()
        return row if row is None else (row[0], row[1])

    def count_conversations_for_user_agent(self, user_id: int, agent_id: int) -> int:
        return self._session.scalar(
            select(func.count()).select_from(AgentConversation).where(
                AgentConversation.user_id == user_id,
                AgentConversation.agent_id == agent_id,
            )
        ) or 0

    def list_conversations_for_user_agent(
        self,
        user_id: int,
        agent_id: int,
        offset: int,
        limit: int,
    ) -> list[AgentConversation]:
        return list(
            self._session.scalars(
                select(AgentConversation)
                .where(AgentConversation.user_id == user_id, AgentConversation.agent_id == agent_id)
                .order_by(AgentConversation.updated_at.desc(), AgentConversation.id.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )

    def get_conversation_for_user(self, conversation_id: int, user_id: int) -> AgentConversation | None:
        return self._session.scalar(
            select(AgentConversation).where(
                AgentConversation.id == conversation_id,
                AgentConversation.user_id == user_id,
            )
        )

    def get_conversation_for_user_agent(
        self,
        conversation_id: int,
        user_id: int,
        agent_id: int,
    ) -> AgentConversation | None:
        return self._session.scalar(
            select(AgentConversation).where(
                AgentConversation.id == conversation_id,
                AgentConversation.user_id == user_id,
                AgentConversation.agent_id == agent_id,
            )
        )

    def list_visible_messages(self, conversation_id: int) -> list[AgentMessage]:
        return list(
            self._session.scalars(
                select(AgentMessage)
                .where(
                    AgentMessage.conversation_id == conversation_id,
                    AgentMessage.role.in_(["user", "assistant"]),
                )
                .order_by(AgentMessage.created_at.asc(), AgentMessage.id.asc())
            ).all()
        )

    def list_history_messages(self, conversation_id: int) -> list[AgentMessage]:
        return list(
            self._session.scalars(
                select(AgentMessage)
                .where(
                    AgentMessage.conversation_id == conversation_id,
                    AgentMessage.role.in_(["user", "assistant"]),
                )
                .order_by(AgentMessage.created_at.desc(), AgentMessage.id.desc())
                .limit(20)
            ).all()
        )

    def add(self, value) -> None:
        self._session.add(value)

    def flush(self) -> None:
        self._session.flush()

    def refresh(self, value) -> None:
        self._session.refresh(value)

    def _definition_where(self, user_id: int):
        return and_(
            AgentDefinition.enabled.is_(True),
            or_(AgentDefinition.is_builtin.is_(True), AgentDefinition.owner_user_id == user_id),
        )

    def _report_where(self, user_id: int, agent_id: int | None, target_code: str | None):
        filters = [AgentReport.user_id == user_id]
        if target_code and target_code.strip():
            filters.append(AgentReport.target_code == target_code.strip())
        if agent_id:
            filters.append(AgentDefinition.id == agent_id)
        return and_(*filters)
