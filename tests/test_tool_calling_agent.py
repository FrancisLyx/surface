from langchain_core.messages import AIMessage
import pytest

from app.modules.agent.events import AgentStreamEvent
from app.modules.agent.graphs import fund_analysis as fund_analysis_graph
from app.modules.agent.tool_gateway import DefaultAgentToolGateway


class FakeToolCallingModel:
    def __init__(self):
        self.messages = []

    def bind_tools(self, tools):
        self.tools = tools
        return self

    def invoke(self, messages):
        self.messages.append(messages)
        if len(self.messages) == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_fund_value",
                        "args": {"fund_code": "110010"},
                        "id": "call_value",
                    },
                    {
                        "name": "get_fund_profile",
                        "args": {"fund_code": "110010"},
                        "id": "call_profile",
                    },
                    {
                        "name": "get_fund_nav_trend_summary",
                        "args": {"fund_code": "110010"},
                        "id": "call_nav",
                    },
                ],
            )
        raise AssertionError(
            "final answer should be streamed directly after tool results"
        )

    def stream(self, messages):
        self.messages.append(messages)
        yield AIMessage(content="# 基金分析\n")
        yield AIMessage(content="动作结论：观望")


class FakeFavoriteListToolModel:
    def __init__(self):
        self.messages = []

    def bind_tools(self, tools):
        self.tools = tools
        return self

    def invoke(self, messages):
        self.messages.append(messages)
        if len(self.messages) == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_favorite_fund_list",
                        "args": {},
                        "id": "call_favorites",
                    },
                ],
            )
        raise AssertionError("final answer should be streamed after favorite list")

    def stream(self, messages):
        self.messages.append(messages)
        yield AIMessage(content="你有 1 只自选基金")


class FakeToolGateway:
    def __init__(self):
        self.calls = []

    async def execute(self, tool_name, args, user):
        self.calls.append((tool_name, args, user))
        if tool_name == "get_fund_value":
            return {"fund_code": args["fund_code"]}
        if tool_name == "get_fund_profile":
            return {"basic_info": [{"item": "基金简称", "value": "易方达价值成长混合"}]}
        if tool_name == "get_fund_nav_trend_summary":
            return {
                "period": "近一年",
                "period_return": "8.00%",
                "max_drawdown": "-12.00%",
            }
        if tool_name == "get_favorite_fund_list":
            return {
                "total": 1,
                "items": [
                    {
                        "fund_code": "110010",
                        "fund_name": "易方达价值成长混合",
                        "fund_type": "混合型",
                    }
                ],
            }
        raise AssertionError(f"unexpected tool: {tool_name}")


@pytest.mark.asyncio
async def test_default_tool_gateway_supports_market_strategy_tools(monkeypatch):
    from app.modules.strategy import service as strategy_service

    monkeypatch.setattr(
        strategy_service,
        "get_market_structure_watch_points",
        lambda market_script_key=None: {
            "market_script_key": market_script_key,
            "sectors": ["机器人", "生物医药"],
        },
    )
    monkeypatch.setattr(
        strategy_service,
        "get_market_structure_discipline_advice",
        lambda market_script_key=None: {
            "market_script_key": market_script_key,
            "action": "观望",
        },
    )
    monkeypatch.setattr(
        strategy_service,
        "get_market_structure_tool_context",
        lambda: {"market_script": "rotation_other", "quotes": []},
    )
    monkeypatch.setattr(
        strategy_service,
        "search_strategy_etfs",
        lambda keyword, limit=10: {
            "keyword": keyword,
            "limit": limit,
            "items": [{"etf_code": "516950"}],
        },
    )

    gateway = DefaultAgentToolGateway()

    watch_points = await gateway.execute(
        "get_market_structure_watch_points",
        {"market_script_key": "rotation_other"},
        user=None,
    )
    discipline = await gateway.execute(
        "get_market_structure_discipline_advice",
        {"market_script_key": "rotation_other"},
        user=None,
    )
    context = await gateway.execute(
        "get_market_structure_tool_context",
        {},
        user=None,
    )
    etfs = await gateway.execute(
        "search_strategy_etfs",
        {"keyword": "机器人", "limit": 5},
        user=None,
    )

    assert watch_points == {
        "market_script_key": "rotation_other",
        "sectors": ["机器人", "生物医药"],
    }
    assert discipline == {
        "market_script_key": "rotation_other",
        "action": "观望",
    }
    assert context == {"market_script": "rotation_other", "quotes": []}
    assert etfs == {
        "keyword": "机器人",
        "limit": 5,
        "items": [{"etf_code": "516950"}],
    }


@pytest.mark.asyncio
async def test_tool_calling_fund_agent_lets_model_choose_tools(monkeypatch):
    fake_model = FakeToolCallingModel()
    tool_gateway = FakeToolGateway()
    monkeypatch.setattr(fund_analysis_graph, "build_chat_model", lambda: fake_model)

    events = [
        event
        async for event in fund_analysis_graph.stream_agent_chat_response(
            {"fund_code": "110010", "message": "请分析基金 110010"},
            history=[],
            tool_gateway=tool_gateway,
        )
    ]
    chunks = [
        event.data
        for event in events
        if isinstance(event, AgentStreamEvent) and event.event == "message"
    ]

    assert chunks == [
        {"type": "assistant_delta", "content": "# 基金分析\n"},
        {"type": "assistant_delta", "content": "动作结论：观望"},
    ]
    assert len(fake_model.messages) == 2
    tool_messages = [
        message
        for message in fake_model.messages[1]
        if message.__class__.__name__ == "ToolMessage"
    ]
    assert [message.name for message in tool_messages] == [
        "get_fund_value",
        "get_fund_profile",
        "get_fund_nav_trend_summary",
    ]
    tool_call_events = [
        event
        for event in events
        if isinstance(event, AgentStreamEvent) and event.event == "tool_call"
    ]
    assert [event.data["tool_name"] for event in tool_call_events] == [
        "get_fund_value",
        "get_fund_profile",
        "get_fund_nav_trend_summary",
    ]
    tool_result_events = [
        event
        for event in events
        if isinstance(event, AgentStreamEvent) and event.event == "tool_result"
    ]
    assert tool_result_events[0].data["data"]["fund_code"] == "110010"
    assert (
        tool_result_events[1].data["data"]["basic_info"][0]["value"]
        == "易方达价值成长混合"
    )
    assert tool_result_events[2].data["data"]["period_return"] == "8.00%"


@pytest.mark.asyncio
async def test_tool_calling_agent_uses_gateway_for_favorite_fund_list(monkeypatch):
    fake_model = FakeFavoriteListToolModel()
    tool_gateway = FakeToolGateway()
    user = object()
    monkeypatch.setattr(fund_analysis_graph, "build_chat_model", lambda: fake_model)

    events = [
        event
        async for event in fund_analysis_graph.stream_agent_chat_response(
            {"message": "我的自选列表有哪些"},
            history=[],
            persona="favorite_scan",
            user=user,
            tool_gateway=tool_gateway,
        )
    ]

    tool_names = [
        event.data["tool_name"]
        for event in events
        if isinstance(event, AgentStreamEvent) and event.event == "tool_call"
    ]
    tool_results = [
        event.data["data"]
        for event in events
        if isinstance(event, AgentStreamEvent) and event.event == "tool_result"
    ]

    assert tool_names == ["get_favorite_fund_list"]
    assert tool_results == [
        {
            "total": 1,
            "items": [
                {
                    "fund_code": "110010",
                    "fund_name": "易方达价值成长混合",
                    "fund_type": "混合型",
                }
            ],
        }
    ]
    assert tool_gateway.calls == [("get_favorite_fund_list", {}, user)]
