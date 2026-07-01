from collections.abc import Iterator
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.api.routes.agent.agent_schema import (
    AgentConversationDetailResponse,
    AgentConversationListItem,
    AgentConversationMessageItem,
    AgentListItem,
    AgentReportDetailResponse,
    AgentReportListItem,
)
from app.core.pagination import PageResponse
from app.db.models.agent import AgentConversation, AgentDefinition, AgentMessage, AgentReport, AgentRun
from app.db.models.user import User
from app.services.agent_event import (
    AgentStreamEvent,
    conversation_event,
    error_event,
)
from app.services import agent_runtime_service

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


def ensure_builtin_agents(db: Session) -> None:
    for item in BUILTIN_AGENTS:
        agent = db.scalar(select(AgentDefinition).where(AgentDefinition.code == item["code"]))
        if agent is None:
            db.add(
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
    db.commit()


def list_agents(db: Session, user: User, page: int = 1, page_size: int = 20) -> PageResponse[AgentListItem]:
    ensure_builtin_agents(db)
    where_clause = and_(
        AgentDefinition.enabled.is_(True),
        or_(AgentDefinition.is_builtin.is_(True), AgentDefinition.owner_user_id == user.id),
    )
    total = db.scalar(select(func.count()).select_from(AgentDefinition).where(where_clause)) or 0
    pages = (total + page_size - 1) // page_size if total else 0
    offset = (page - 1) * page_size
    agents = db.scalars(
        select(AgentDefinition)
        .where(where_clause)
        .order_by(AgentDefinition.id.asc())
        .offset(offset)
        .limit(page_size)
    ).all()
    return PageResponse(
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        items=[_to_agent_item(agent) for agent in agents],
    )


def stream_chat(
    db: Session,
    user: User,
    agent_id: int,
    message: str,
    conversation_id: int | None = None,
    fund_code: str | None = None,
) -> Iterator[AgentStreamEvent]:
    ensure_builtin_agents(db)
    agent = _get_enabled_agent_by_id(db, user, agent_id)
    normalized_message = message.strip()
    if not normalized_message:
        raise HTTPException(status_code=400, detail="message is required")

    normalized_fund_code = fund_code.strip() if fund_code else None
    conversation = _get_or_create_conversation(db, user, agent, conversation_id, normalized_message, normalized_fund_code)
    yield conversation_event(conversation.id)

    started_at = perf_counter()
    run: AgentRun | None = None
    assistant_chunks: list[str] = []
    try:
        history = _conversation_history(db, conversation.id)
        db.add(
            AgentMessage(
                conversation_id=conversation.id,
                user_id=user.id,
                agent_id=agent.id,
                role="user",
                message_type="text",
                content=normalized_message,
                payload_json={"fund_code": normalized_fund_code} if normalized_fund_code else None,
            )
        )
        db.commit()

        run = AgentRun(
            user_id=user.id,
            agent_id=agent.id,
            conversation_id=conversation.id,
            input_json={"message": normalized_message, "fund_code": normalized_fund_code},
            status="running",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        for event in agent_runtime_service.stream_agent_chat(
            agent,
            {"message": normalized_message, "fund_code": normalized_fund_code},
            history,
            user,
            db,
        ):
            if event.event == "message" and isinstance(event.data, dict):
                content = str(event.data.get("content") or "")
                assistant_chunks.append(content)
            elif event.event == "tool_call" and isinstance(event.data, dict):
                _save_tool_message(db, conversation, agent, user, event.data, role="tool", message_type="tool_call")
            elif event.event == "tool_result" and isinstance(event.data, dict):
                _save_tool_message(db, conversation, agent, user, event.data, role="tool", message_type="tool_result")
            yield event
    except Exception as exc:
        if run is not None:
            run.status = "failed"
            run.error_message = str(exc)
            run.duration_ms = _duration_ms(started_at)
            run.finished_at = datetime.now(timezone.utc)
        db.commit()
        yield error_event(str(exc))
        return

    assistant_content = "".join(assistant_chunks)
    if assistant_content:
        db.add(
            AgentMessage(
                conversation_id=conversation.id,
                user_id=user.id,
                agent_id=agent.id,
                role="assistant",
                message_type="text",
                content=assistant_content,
            )
        )
    run.output_text = assistant_content
    run.status = "success"
    run.duration_ms = _duration_ms(started_at)
    run.finished_at = datetime.now(timezone.utc)
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()


def list_reports(
    db: Session,
    user: User,
    agent_id: int | None = None,
    target_code: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> PageResponse[AgentReportListItem]:
    ensure_builtin_agents(db)
    filters = [AgentReport.user_id == user.id]
    if target_code and target_code.strip():
        filters.append(AgentReport.target_code == target_code.strip())
    if agent_id:
        filters.append(AgentDefinition.id == agent_id)

    where_clause = and_(*filters)
    total = (
        db.scalar(
            select(func.count())
            .select_from(AgentReport)
            .join(AgentDefinition, AgentDefinition.id == AgentReport.agent_id)
            .where(where_clause)
        )
        or 0
    )
    pages = (total + page_size - 1) // page_size if total else 0
    offset = (page - 1) * page_size
    rows = db.execute(
        select(AgentReport, AgentDefinition)
        .join(AgentDefinition, AgentDefinition.id == AgentReport.agent_id)
        .where(where_clause)
        .order_by(AgentReport.created_at.desc(), AgentReport.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()

    return PageResponse(
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        items=[_to_report_item(report, agent) for report, agent in rows],
    )


def list_conversations(
    db: Session,
    user: User,
    agent_id: int,
    page: int = 1,
    page_size: int = 20,
) -> PageResponse[AgentConversationListItem]:
    ensure_builtin_agents(db)
    _get_enabled_agent_by_id(db, user, agent_id)
    where_clause = and_(AgentConversation.user_id == user.id, AgentConversation.agent_id == agent_id)
    total = db.scalar(select(func.count()).select_from(AgentConversation).where(where_clause)) or 0
    pages = (total + page_size - 1) // page_size if total else 0
    offset = (page - 1) * page_size
    conversations = db.scalars(
        select(AgentConversation)
        .where(where_clause)
        .order_by(AgentConversation.updated_at.desc(), AgentConversation.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()
    return PageResponse(
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        items=[_to_conversation_item(item) for item in conversations],
    )


def get_conversation_detail(db: Session, user: User, conversation_id: int) -> AgentConversationDetailResponse:
    ensure_builtin_agents(db)
    conversation = db.scalar(
        select(AgentConversation).where(
            AgentConversation.id == conversation_id,
            AgentConversation.user_id == user.id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="conversation not found")
    _get_enabled_agent_by_id(db, user, conversation.agent_id)
    messages = db.scalars(
        select(AgentMessage)
        .where(
            AgentMessage.conversation_id == conversation.id,
            AgentMessage.role.in_(["user", "assistant"]),
        )
        .order_by(AgentMessage.created_at.asc(), AgentMessage.id.asc())
    ).all()
    return AgentConversationDetailResponse(
        id=conversation.id,
        agent_id=conversation.agent_id,
        title=conversation.title,
        target_type=conversation.target_type,
        target_code=conversation.target_code,
        messages=[_to_conversation_message_item(item) for item in messages],
    )


def get_report_detail(db: Session, user: User, report_id: int) -> AgentReportDetailResponse:
    ensure_builtin_agents(db)
    row = db.execute(
        select(AgentReport, AgentDefinition)
        .join(AgentDefinition, AgentDefinition.id == AgentReport.agent_id)
        .where(AgentReport.id == report_id, AgentReport.user_id == user.id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="report not found")

    report, agent = row
    return AgentReportDetailResponse(**_to_report_item(report, agent).model_dump(), content=report.content)


def _get_enabled_agent_by_id(db: Session, user: User, agent_id: int) -> AgentDefinition:
    agent = db.scalar(
        select(AgentDefinition).where(
            AgentDefinition.id == agent_id,
            AgentDefinition.enabled.is_(True),
            or_(AgentDefinition.is_builtin.is_(True), AgentDefinition.owner_user_id == user.id),
        )
    )
    if agent is None:
        raise HTTPException(status_code=404, detail="agent not found")
    return agent


def _to_agent_item(agent: AgentDefinition) -> AgentListItem:
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


def _build_report_title(agent: AgentDefinition, payload: dict[str, Any]) -> str:
    target = _target_code(agent, payload)
    if target:
        return f"{target} {agent.name}"
    return agent.name


def _target_type(agent: AgentDefinition) -> str:
    return "portfolio" if agent.code == "favorite_fund_scan" else "fund"


def _target_code(agent: AgentDefinition, payload: dict[str, Any]) -> str | None:
    if agent.code in {"fund_deep_analysis", "aggressive_ajia"}:
        value = payload.get("fund_code")
        return str(value).strip() if value else None
    return None


def _get_or_create_conversation(
    db: Session,
    user: User,
    agent: AgentDefinition,
    conversation_id: int | None,
    message: str,
    fund_code: str | None,
) -> AgentConversation:
    if conversation_id:
        conversation = db.scalar(
            select(AgentConversation).where(
                AgentConversation.id == conversation_id,
                AgentConversation.user_id == user.id,
                AgentConversation.agent_id == agent.id,
            )
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="conversation not found")
        if fund_code and not conversation.target_code:
            conversation.target_code = fund_code
            conversation.target_type = "fund"
        return conversation

    title = message[:30] or agent.name
    conversation = AgentConversation(
        user_id=user.id,
        agent_id=agent.id,
        title=title,
        target_type="fund" if fund_code else None,
        target_code=fund_code,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def _conversation_history(db: Session, conversation_id: int) -> list[dict[str, str]]:
    messages = db.scalars(
        select(AgentMessage)
        .where(
            AgentMessage.conversation_id == conversation_id,
            AgentMessage.role.in_(["user", "assistant"]),
        )
        .order_by(AgentMessage.created_at.desc(), AgentMessage.id.desc())
        .limit(20)
    ).all()
    return [{"role": item.role, "content": item.content} for item in reversed(messages)]


def _save_tool_message(
    db: Session,
    conversation: AgentConversation,
    agent: AgentDefinition,
    user: User,
    data: dict[str, Any],
    role: str,
    message_type: str,
) -> None:
    db.add(
        AgentMessage(
            conversation_id=conversation.id,
            user_id=user.id,
            agent_id=agent.id,
            role=role,
            message_type=message_type,
            content=str(data.get("summary") or data.get("tool_name") or message_type),
            tool_call_id=data.get("tool_call_id"),
            tool_name=data.get("tool_name"),
            payload_json=data,
        )
    )
    db.commit()


def _duration_ms(started_at: float) -> int:
    return max(int((perf_counter() - started_at) * 1000), 0)
