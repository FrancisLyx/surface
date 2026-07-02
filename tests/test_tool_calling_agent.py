from langchain_core.messages import AIMessage

from app.modules.agent.events import AgentStreamEvent
from app.modules.agent.graphs import fund_analysis as fund_analysis_graph
from app.modules.fund.schemas import (
    FundDetailItem,
    FundEstimationItem,
    FundProfileResponse,
    FundValueResponse,
)
from app.modules.fund.public import FundQueryFacade


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


def test_tool_calling_fund_agent_lets_model_choose_tools(monkeypatch):
    fake_model = FakeToolCallingModel()
    monkeypatch.setattr(fund_analysis_graph, "build_chat_model", lambda: fake_model)

    monkeypatch.setattr(
        FundQueryFacade,
        "get_fund_value",
        lambda self, request: FundValueResponse(
            fund_code=request.fund_code,
            source="estimation",
            estimation=FundEstimationItem(
                code=request.fund_code,
                name="易方达价值成长混合",
                estimate_date="2026-07-01",
                estimated_nav="2.9000",
                estimated_growth_rate="1.20%",
                published_date="2026-06-30",
                published_nav="2.8000",
                published_growth_rate="-2.24%",
                estimate_deviation="",
                previous_nav_date="2026-06-29",
                previous_nav="2.8600",
            ),
            latest_nav=None,
        ),
    )
    monkeypatch.setattr(
        FundQueryFacade,
        "get_fund_profile",
        lambda self, request: FundProfileResponse(
            symbol=request.symbol,
            year=request.year,
            basic_info=[FundDetailItem(item="基金简称", value="易方达价值成长混合")],
            fee_sections=[],
            holdings=[{"股票名称": "示例股票", "占净值比例": "5.00%"}],
            industry_allocations=[{"行业类别": "制造业", "占净值比例": "20.00%"}],
        ),
    )
    monkeypatch.setattr(
        FundQueryFacade,
        "get_fund_nav_trend_summary",
        lambda self, fund_code: {
            "period": "近一年",
            "period_return": "8.00%",
            "max_drawdown": "-12.00%",
        },
    )

    events = list(
        fund_analysis_graph.stream_fund_deep_analysis(
            {"fund_code": "110010"}, user=None, db=None
        )
    )
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
