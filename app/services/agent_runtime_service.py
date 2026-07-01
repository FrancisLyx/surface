from typing import Any

from sqlalchemy.orm import Session

from app.agents.fund_analysis_graph import (
    stream_aggressive_ajia_analysis,
    stream_agent_chat_response,
    stream_favorite_fund_scan,
    stream_fund_deep_analysis,
)
from app.db.models.agent import AgentDefinition
from app.db.models.user import User


def stream_agent(agent: AgentDefinition, payload: dict[str, Any], user: User, db: Session):
    if agent.graph_code == "fund_deep_analysis_graph":
        yield from stream_fund_deep_analysis(payload, user, db)
        return

    if agent.graph_code == "favorite_fund_scan_graph":
        yield from stream_favorite_fund_scan(payload, user, db)
        return

    if agent.graph_code == "aggressive_ajia_graph":
        yield from stream_aggressive_ajia_analysis(payload, user, db)
        return

    raise ValueError(f"unsupported graph: {agent.graph_code}")


def stream_agent_chat(agent: AgentDefinition, payload: dict[str, Any], history: list[dict[str, str]], user: User, db: Session):
    if agent.graph_code in {"fund_deep_analysis_graph", "aggressive_ajia_graph"}:
        persona = "aggressive_ajia" if agent.graph_code == "aggressive_ajia_graph" else "professional"
        yield from stream_agent_chat_response(payload, history, persona=persona)
        return

    if agent.graph_code == "favorite_fund_scan_graph":
        yield from stream_agent_chat_response(payload, history, persona="favorite_scan")
        return

    raise ValueError(f"unsupported graph: {agent.graph_code}")
