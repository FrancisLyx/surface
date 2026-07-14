from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.current_user import CurrentUser
from app.modules.agent.dtos import AgentDefinitionDTO
from app.modules.agent.graphs.fund_analysis import (
    stream_aggressive_ajia_analysis,
    stream_agent_chat_response,
    stream_favorite_fund_scan,
    stream_fund_deep_analysis,
)
from app.modules.agent.tool_gateway import AgentToolGateway


async def stream_agent(
    agent: AgentDefinitionDTO,
    payload: dict[str, Any],
    user: CurrentUser,
    db: AsyncSession | None,
):
    if agent.graph_code == "fund_deep_analysis_graph":
        async for event in stream_fund_deep_analysis(payload, user, db):
            yield event
        return

    if agent.graph_code == "favorite_fund_scan_graph":
        for event in stream_favorite_fund_scan(payload, user, db):
            yield event
        return

    if agent.graph_code == "aggressive_ajia_graph":
        async for event in stream_aggressive_ajia_analysis(payload, user, db):
            yield event
        return

    raise ValueError(f"unsupported graph: {agent.graph_code}")


async def stream_agent_chat(
    agent: AgentDefinitionDTO,
    payload: dict[str, Any],
    history: list[dict[str, str]],
    user: CurrentUser,
    db: AsyncSession | None,
    tool_gateway: AgentToolGateway | None = None,
):
    if agent.graph_code in {"fund_deep_analysis_graph", "aggressive_ajia_graph"}:
        persona = (
            "aggressive_ajia"
            if agent.graph_code == "aggressive_ajia_graph"
            else "professional"
        )
        async for event in stream_agent_chat_response(
            payload, history, persona=persona, user=user, tool_gateway=tool_gateway
        ):
            yield event
        return

    if agent.graph_code == "favorite_fund_scan_graph":
        async for event in stream_agent_chat_response(
            payload,
            history,
            persona="favorite_scan",
            user=user,
            tool_gateway=tool_gateway,
        ):
            yield event
        return

    if agent.graph_code == "market_intraday_watch_graph":
        async for event in stream_agent_chat_response(
            payload,
            history,
            persona="market_intraday_watch",
            user=user,
            tool_gateway=tool_gateway,
        ):
            yield event
        return

    if agent.graph_code == "market_discipline_advisor_graph":
        async for event in stream_agent_chat_response(
            payload,
            history,
            persona="market_discipline_advisor",
            user=user,
            tool_gateway=tool_gateway,
        ):
            yield event
        return

    raise ValueError(f"unsupported graph: {agent.graph_code}")
