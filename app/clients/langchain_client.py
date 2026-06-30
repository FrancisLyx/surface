from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import get_settings


def chat(prompt: str) -> str:
    model = _build_model()

    response = model.invoke(_build_messages(prompt))

    return str(response.content or "")


def stream_chat(prompt: str):
    model = _build_model()

    for chunk in model.stream(_build_messages(prompt)):
        content = chunk.content
        if isinstance(content, str) and content:
            yield content
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        yield str(text)


def _build_model() -> ChatOpenAI:
    settings = get_settings()
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY is not configured")

    return ChatOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
        temperature=0.2,
    )


def _build_messages(prompt: str) -> list[SystemMessage | HumanMessage]:
    return [
        SystemMessage(content="你是一个严谨的金融数据分析助手。"),
        HumanMessage(content=prompt),
    ]
