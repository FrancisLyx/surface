import json
from dataclasses import dataclass
from typing import Any, Literal

AgentEventType = Literal["conversation", "step", "tool_call", "tool_result", "message", "error"]


@dataclass(frozen=True)
class AgentStreamEvent:
    event: AgentEventType
    data: dict[str, Any] | str


def step_event(step_id: str, title: str, status: str, error_message: str | None = None) -> AgentStreamEvent:
    payload: dict[str, Any] = {
        "step_id": step_id,
        "title": title,
        "status": status,
    }
    if error_message:
        payload["error_message"] = error_message
    return AgentStreamEvent(event="step", data=payload)


def tool_call_event(tool_call_id: str, step_id: str, tool_name: str, input_data: dict[str, Any]) -> AgentStreamEvent:
    return AgentStreamEvent(
        event="tool_call",
        data={
            "type": "tool_call",
            "tool_call_id": tool_call_id,
            "step_id": step_id,
            "tool_name": tool_name,
            "input": input_data,
        },
    )


def tool_result_event(tool_call_id: str, status: str, summary: str, data: Any | None = None) -> AgentStreamEvent:
    payload: dict[str, Any] = {
        "type": "tool_result",
        "tool_call_id": tool_call_id,
        "status": status,
        "summary": summary,
    }
    if data is not None:
        payload["data"] = data
    return AgentStreamEvent(event="tool_result", data=payload)


def message_event(content: str) -> AgentStreamEvent:
    return AgentStreamEvent(event="message", data={"type": "assistant_delta", "content": content})


def conversation_event(conversation_id: int) -> AgentStreamEvent:
    return AgentStreamEvent(
        event="conversation",
        data={"type": "conversation", "conversation_id": conversation_id},
    )


def error_event(message: str) -> AgentStreamEvent:
    return AgentStreamEvent(event="error", data={"message": message})


def encode_event_data(data: dict[str, Any] | str) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
