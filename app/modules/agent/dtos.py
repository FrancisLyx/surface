from dataclasses import dataclass
from datetime import datetime
from typing import Any


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
class AgentRunDTO:
    id: int
    agent_id: int
    user_id: int
    status: str
    input_json: dict[str, Any]
    output_text: str | None
    created_at: datetime
