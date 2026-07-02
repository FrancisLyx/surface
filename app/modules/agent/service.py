from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.modules.agent.schema import (
    AgentConversationDetailResponse,
    AgentConversationListItem,
    AgentConversationMessageItem,
    AgentListItem,
    AgentReportDetailResponse,
    AgentReportListItem,
)
from app.core.current_user import CurrentUser
from app.core.exception import NotFoundError, ValidationError
from app.core.pagination import PageResponse
from app.modules.agent.model import AgentConversation, AgentDefinition, AgentMessage, AgentReport, AgentRun
from app.modules.user.model import User
from app.db.uow import SqlAlchemyUnitOfWork
from app.modules.agent import runtime as agent_runtime_service
from app.modules.agent.event import AgentStreamEvent, conversation_event, error_event

BUILTIN_AGENTS = [
    {
        "name": "林远山",
        "code": "fund_deep_analysis",
        "agent_type": "fund",
        "description": "稳健派基金研究员，擅长从基金画像、估值、持仓和净值走势里拆风险和机会。",
        "system_prompt": "你是林远山，一名审慎、专业、数据优先的基金研究员。",
        "graph_code": "fund_deep_analysis_graph",
    },
    {
        "name": "许知夏",
        "code": "favorite_fund_scan",
        "agent_type": "portfolio",
        "description": "组合巡检专家，负责快速扫描我的自选基金，找出当日估值异动和风险提醒。",
        "system_prompt": "你是许知夏，一名冷静、敏捷、擅长组合巡检的基金分析师。",
        "graph_code": "favorite_fund_scan_graph",
    },
    {
        "name": "股神阿佳",
        "code": "aggressive_ajia",
        "agent_type": "fund",
        "description": "进攻型基金分析智能体，语言更直接，偏短线机会和仓位进攻，但保留风控底线。",
        "system_prompt": "你是“股神阿佳”，一个真正的man、风格激进、说话直接、但不突破风控底线的金融分析智能体。",
        "graph_code": "aggressive_ajia_graph",
    },
]


@dataclass(frozen=True, slots=True)
class AgentDefinitionDTO:
    id: int
    name: str
    code: str
    agent_type: str
    description: str
    system_prompt: str
    graph_code: str
    enabled: bool
    is_builtin: bool


@dataclass(frozen=True, slots=True)
class StreamStart:
    agent: AgentDefinitionDTO
    conversation_id: int
    run_id: int
    history: list[dict[str, str]]


class AgentService:
    def __init__(self, uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ensure_builtin_agents(self) -> None:
        with self._uow_factory() as uow:
            _ensure_builtin_agents(uow)
            uow.commit()

    def list_agents(self, user: CurrentUser, page: int = 1, page_size: int = 20) -> PageResponse[AgentListItem]:
        with self._uow_factory() as uow:
            _ensure_builtin_agents(uow)
            total = uow.agents.count_definitions_for_user(user.id)
            pages = (total + page_size - 1) // page_size if total else 0
            offset = (page - 1) * page_size
            agents = uow.agents.list_definitions_for_user(user.id, offset=offset, limit=page_size)
            uow.commit()
            return PageResponse(
                page=page,
                page_size=page_size,
                total=total,
                pages=pages,
                items=[_to_agent_item(agent) for agent in agents],
            )

    def stream_chat(
        self,
        user: CurrentUser,
        agent_id: int,
        message: str,
        conversation_id: int | None = None,
        fund_code: str | None = None,
    ) -> Iterator[AgentStreamEvent]:
        normalized_message = message.strip()
        if not normalized_message:
            raise ValidationError("message is required")

        normalized_fund_code = fund_code.strip() if fund_code else None
        start = self._start_stream_chat(user, agent_id, normalized_message, conversation_id, normalized_fund_code)
        yield conversation_event(start.conversation_id)

        started_at = perf_counter()
        assistant_chunks: list[str] = []
        try:
            for event in agent_runtime_service.stream_agent_chat(
                start.agent,
                {"message": normalized_message, "fund_code": normalized_fund_code},
                start.history,
                user,
                None,
            ):
                if event.event == "message" and isinstance(event.data, dict):
                    assistant_chunks.append(str(event.data.get("content") or ""))
                elif event.event == "tool_call" and isinstance(event.data, dict):
                    self._save_tool_message(start.conversation_id, start.agent.id, user.id, event.data, "tool_call")
                elif event.event == "tool_result" and isinstance(event.data, dict):
                    self._save_tool_message(start.conversation_id, start.agent.id, user.id, event.data, "tool_result")
                yield event
        except Exception as exc:
            self._finish_run_failure(start.run_id, str(exc), _duration_ms(started_at))
            yield error_event(str(exc))
            return

        assistant_content = "".join(assistant_chunks)
        self._finish_run_success(
            run_id=start.run_id,
            conversation_id=start.conversation_id,
            user_id=user.id,
            agent_id=start.agent.id,
            output_text=assistant_content,
            duration_ms=_duration_ms(started_at),
        )

    def list_reports(
        self,
        user: CurrentUser,
        agent_id: int | None = None,
        target_code: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PageResponse[AgentReportListItem]:
        with self._uow_factory() as uow:
            _ensure_builtin_agents(uow)
            total = uow.agents.count_reports_for_user(user.id, agent_id, target_code)
            pages = (total + page_size - 1) // page_size if total else 0
            offset = (page - 1) * page_size
            rows = uow.agents.list_reports_for_user(user.id, agent_id, target_code, offset=offset, limit=page_size)
            uow.commit()
            return PageResponse(
                page=page,
                page_size=page_size,
                total=total,
                pages=pages,
                items=[_to_report_item(report, agent) for report, agent in rows],
            )

    def list_conversations(
        self,
        user: CurrentUser,
        agent_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> PageResponse[AgentConversationListItem]:
        with self._uow_factory() as uow:
            _ensure_builtin_agents(uow)
            _get_enabled_agent_by_id(uow, user, agent_id)
            total = uow.agents.count_conversations_for_user_agent(user.id, agent_id)
            pages = (total + page_size - 1) // page_size if total else 0
            offset = (page - 1) * page_size
            conversations = uow.agents.list_conversations_for_user_agent(user.id, agent_id, offset=offset, limit=page_size)
            uow.commit()
            return PageResponse(
                page=page,
                page_size=page_size,
                total=total,
                pages=pages,
                items=[_to_conversation_item(item) for item in conversations],
            )

    def get_conversation_detail(self, user: CurrentUser, conversation_id: int) -> AgentConversationDetailResponse:
        with self._uow_factory() as uow:
            _ensure_builtin_agents(uow)
            conversation = uow.agents.get_conversation_for_user(conversation_id, user.id)
            if conversation is None:
                raise NotFoundError("conversation not found")
            _get_enabled_agent_by_id(uow, user, conversation.agent_id)
            messages = uow.agents.list_visible_messages(conversation.id)
            uow.commit()
            return AgentConversationDetailResponse(
                id=conversation.id,
                agent_id=conversation.agent_id,
                title=conversation.title,
                target_type=conversation.target_type,
                target_code=conversation.target_code,
                messages=[_to_conversation_message_item(item) for item in messages],
            )

    def get_report_detail(self, user: CurrentUser, report_id: int) -> AgentReportDetailResponse:
        with self._uow_factory() as uow:
            _ensure_builtin_agents(uow)
            row = uow.agents.get_report_for_user(report_id, user.id)
            if row is None:
                raise NotFoundError("report not found")
            report, agent = row
            uow.commit()
            return AgentReportDetailResponse(**_to_report_item(report, agent).model_dump(), content=report.content)

    def _start_stream_chat(
        self,
        user: CurrentUser,
        agent_id: int,
        message: str,
        conversation_id: int | None,
        fund_code: str | None,
    ) -> StreamStart:
        with self._uow_factory() as uow:
            _ensure_builtin_agents(uow)
            agent = _get_enabled_agent_by_id(uow, user, agent_id)
            conversation = _get_or_create_conversation(uow, user, agent, conversation_id, message, fund_code)
            history = _conversation_history(uow, conversation.id)
            uow.agents.add(
                AgentMessage(
                    conversation_id=conversation.id,
                    user_id=user.id,
                    agent_id=agent.id,
                    role="user",
                    message_type="text",
                    content=message,
                    payload_json={"fund_code": fund_code} if fund_code else None,
                )
            )
            run = AgentRun(
                user_id=user.id,
                agent_id=agent.id,
                conversation_id=conversation.id,
                input_json={"message": message, "fund_code": fund_code},
                status="running",
            )
            uow.agents.add(run)
            uow.commit()
            uow.agents.refresh(conversation)
            uow.agents.refresh(run)
            return StreamStart(
                agent=_to_agent_dto(agent),
                conversation_id=conversation.id,
                run_id=run.id,
                history=history,
            )

    def _save_tool_message(
        self,
        conversation_id: int,
        agent_id: int,
        user_id: int,
        data: dict[str, Any],
        message_type: str,
    ) -> None:
        with self._uow_factory() as uow:
            uow.agents.add(
                AgentMessage(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    agent_id=agent_id,
                    role="tool",
                    message_type=message_type,
                    content=str(data.get("summary") or data.get("tool_name") or message_type),
                    tool_call_id=data.get("tool_call_id"),
                    tool_name=data.get("tool_name"),
                    payload_json=data,
                )
            )
            uow.commit()

    def _finish_run_success(
        self,
        run_id: int,
        conversation_id: int,
        user_id: int,
        agent_id: int,
        output_text: str,
        duration_ms: int,
    ) -> None:
        with self._uow_factory() as uow:
            run = uow.session.get(AgentRun, run_id)
            conversation = uow.session.get(AgentConversation, conversation_id)
            if output_text:
                uow.agents.add(
                    AgentMessage(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        agent_id=agent_id,
                        role="assistant",
                        message_type="text",
                        content=output_text,
                    )
                )
            if run is not None:
                run.output_text = output_text
                run.status = "success"
                run.duration_ms = duration_ms
                run.finished_at = datetime.now(timezone.utc)
            if conversation is not None:
                conversation.updated_at = datetime.now(timezone.utc)
            uow.commit()

    def _finish_run_failure(self, run_id: int, error_message: str, duration_ms: int) -> None:
        with self._uow_factory() as uow:
            run = uow.session.get(AgentRun, run_id)
            if run is not None:
                run.status = "failed"
                run.error_message = error_message
                run.duration_ms = duration_ms
                run.finished_at = datetime.now(timezone.utc)
            uow.commit()


def _ensure_builtin_agents(uow) -> None:
    for item in BUILTIN_AGENTS:
        agent = uow.agents.get_definition_by_code(item["code"])
        if agent is None:
            uow.agents.add(
                AgentDefinition(
                    **item,
                    enabled=True,
                    is_builtin=True,
                )
            )
        else:
            agent.name = item["name"]
            agent.agent_type = item["agent_type"]
            agent.description = item["description"]
            agent.system_prompt = item["system_prompt"]
            agent.graph_code = item["graph_code"]
            agent.is_builtin = True
    uow.agents.flush()


def _get_enabled_agent_by_id(uow, user: CurrentUser, agent_id: int) -> AgentDefinition:
    agent = uow.agents.get_enabled_definition_for_user(agent_id, user.id)
    if agent is None:
        raise NotFoundError("agent not found")
    return agent


def _get_or_create_conversation(
    uow,
    user: CurrentUser,
    agent: AgentDefinition,
    conversation_id: int | None,
    message: str,
    fund_code: str | None,
) -> AgentConversation:
    if conversation_id:
        conversation = uow.agents.get_conversation_for_user_agent(conversation_id, user.id, agent.id)
        if conversation is None:
            raise NotFoundError("conversation not found")
        if fund_code and not conversation.target_code:
            conversation.target_code = fund_code
            conversation.target_type = "fund"
        return conversation

    conversation = AgentConversation(
        user_id=user.id,
        agent_id=agent.id,
        title=message[:30] or agent.name,
        target_type="fund" if fund_code else None,
        target_code=fund_code,
    )
    uow.agents.add(conversation)
    uow.agents.flush()
    return conversation


def _conversation_history(uow, conversation_id: int) -> list[dict[str, str]]:
    messages = uow.agents.list_history_messages(conversation_id)
    return [{"role": item.role, "content": item.content} for item in reversed(messages)]


def _to_current_user(user: User | CurrentUser) -> CurrentUser:
    if isinstance(user, CurrentUser):
        return user
    return CurrentUser(id=user.id, username=user.username, email=user.email, phone=user.phone, role_id=user.role_id)


def _to_agent_dto(agent: AgentDefinition) -> AgentDefinitionDTO:
    return AgentDefinitionDTO(
        id=agent.id,
        name=agent.name,
        code=agent.code,
        agent_type=agent.agent_type,
        description=agent.description,
        system_prompt=agent.system_prompt,
        graph_code=agent.graph_code,
        enabled=agent.enabled,
        is_builtin=agent.is_builtin,
    )


def _to_agent_item(agent: AgentDefinition | AgentDefinitionDTO) -> AgentListItem:
    return AgentListItem(
        id=agent.id,
        name=agent.name,
        agent_type=agent.agent_type,
        description=agent.description,
        enabled=agent.enabled,
        is_builtin=agent.is_builtin,
    )


def _to_report_item(report: AgentReport, agent: AgentDefinition) -> AgentReportListItem:
    return AgentReportListItem(
        id=report.id,
        agent_id=agent.id,
        agent_name=agent.name,
        run_id=report.run_id,
        title=report.title,
        target_type=report.target_type,
        target_code=report.target_code,
        created_at=report.created_at.isoformat(),
    )


def _to_conversation_item(conversation: AgentConversation) -> AgentConversationListItem:
    return AgentConversationListItem(
        id=conversation.id,
        agent_id=conversation.agent_id,
        title=conversation.title,
        target_type=conversation.target_type,
        target_code=conversation.target_code,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
    )


def _to_conversation_message_item(message: AgentMessage) -> AgentConversationMessageItem:
    return AgentConversationMessageItem(
        id=message.id,
        role=message.role,
        message_type=message.message_type,
        content=message.content,
        created_at=message.created_at.isoformat(),
    )


def _duration_ms(started_at: float) -> int:
    return max(int((perf_counter() - started_at) * 1000), 0)


def _service_from_session(db: Session) -> AgentService:
    return AgentService(lambda: SqlAlchemyUnitOfWork(lambda: db))


def ensure_builtin_agents(db: Session) -> None:
    _service_from_session(db).ensure_builtin_agents()


def list_agents(db: Session, user: User | CurrentUser, page: int = 1, page_size: int = 20) -> PageResponse[AgentListItem]:
    return _service_from_session(db).list_agents(_to_current_user(user), page=page, page_size=page_size)


def stream_chat(
    db: Session,
    user: User | CurrentUser,
    agent_id: int,
    message: str,
    conversation_id: int | None = None,
    fund_code: str | None = None,
) -> Iterator[AgentStreamEvent]:
    yield from _service_from_session(db).stream_chat(
        _to_current_user(user),
        agent_id=agent_id,
        message=message,
        conversation_id=conversation_id,
        fund_code=fund_code,
    )


def list_reports(
    db: Session,
    user: User | CurrentUser,
    agent_id: int | None = None,
    target_code: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> PageResponse[AgentReportListItem]:
    return _service_from_session(db).list_reports(
        _to_current_user(user),
        agent_id=agent_id,
        target_code=target_code,
        page=page,
        page_size=page_size,
    )


def list_conversations(
    db: Session,
    user: User | CurrentUser,
    agent_id: int,
    page: int = 1,
    page_size: int = 20,
) -> PageResponse[AgentConversationListItem]:
    return _service_from_session(db).list_conversations(_to_current_user(user), agent_id=agent_id, page=page, page_size=page_size)


def get_conversation_detail(db: Session, user: User | CurrentUser, conversation_id: int) -> AgentConversationDetailResponse:
    return _service_from_session(db).get_conversation_detail(_to_current_user(user), conversation_id)


def get_report_detail(db: Session, user: User | CurrentUser, report_id: int) -> AgentReportDetailResponse:
    return _service_from_session(db).get_report_detail(_to_current_user(user), report_id)
