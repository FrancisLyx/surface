import json
from typing import Any, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.clients.langchain_client import build_chat_model, stream_chat
from app.core.current_user import CurrentUser
from app.modules.fund.public import FundQueryFacade
from app.modules.fund.schemas import FundProfileRequest, FundValueRequest
from app.modules.user.models import User
from app.modules.agent.events import message_event, tool_call_event, tool_result_event
from app.modules.agent.tools import fund as fund_tools


class FundAgentState(TypedDict, total=False):
    payload: dict[str, Any]
    user: CurrentUser | User | None
    db: AsyncSession | None
    data: dict[str, Any]
    prompt: str


def stream_fund_deep_analysis(
    payload: dict[str, Any], user: CurrentUser | User | None, db: AsyncSession | None
):
    fund_code = str(payload.get("fund_code") or "").strip()
    if not fund_code:
        raise ValueError("fund_code is required")

    yield from _run_tool_calling_fund_agent(fund_code, persona="professional")


def stream_aggressive_ajia_analysis(
    payload: dict[str, Any], user: CurrentUser | User | None, db: AsyncSession | None
):
    fund_code = str(payload.get("fund_code") or "").strip()
    if not fund_code:
        raise ValueError("fund_code is required")

    yield from _run_tool_calling_fund_agent(fund_code, persona="aggressive_ajia")


def stream_agent_chat_response(
    payload: dict[str, Any],
    history: list[dict[str, str]],
    persona: str = "professional",
):
    message = str(payload.get("message") or "").strip()
    if not message:
        raise ValueError("message is required")

    fund_code = str(payload.get("fund_code") or "").strip()
    yield from _run_tool_calling_fund_agent(
        fund_code=fund_code, persona=persona, question=message, history=history
    )


def stream_favorite_fund_scan(
    payload: dict[str, Any], user: CurrentUser | User | None, db: AsyncSession | None
):
    page_size = int(payload.get("page_size") or 20)
    page_size = min(max(page_size, 1), 50)

    state = _favorite_scan_graph().invoke(
        {"payload": {"page_size": page_size}, "user": user, "db": db}
    )
    yield from stream_chat(state["prompt"])


def _fund_deep_analysis_graph():
    graph = StateGraph(FundAgentState)
    graph.add_node("load_data", _load_fund_data)
    graph.add_node("build_prompt", _build_fund_prompt)
    graph.set_entry_point("load_data")
    graph.add_edge("load_data", "build_prompt")
    graph.add_edge("build_prompt", END)
    return graph.compile()


def _run_tool_calling_fund_agent(
    fund_code: str = "",
    persona: str = "professional",
    question: str | None = None,
    history: list[dict[str, str]] | None = None,
):
    tools = _build_fund_agent_tools()
    tool_by_name = {item.name: item for item in tools}
    model = build_chat_model().bind_tools(tools)

    messages: list[BaseMessage] = [
        SystemMessage(content=_fund_agent_system_prompt(persona))
    ]
    for item in (history or [])[-12:]:
        role = item.get("role")
        content = item.get("content") or ""
        if not content:
            continue
        if role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "user":
            messages.append(HumanMessage(content=content))
    messages.append(
        HumanMessage(
            content=_fund_agent_user_prompt(fund_code, persona, question=question)
        )
    )

    for _ in range(4):
        response = model.invoke(messages)
        messages.append(response)
        tool_calls = getattr(response, "tool_calls", None) or []
        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call.get("args") or {}
            tool_call_id = call["id"]
            yield tool_call_event(
                tool_call_id=tool_call_id,
                step_id="generate",
                tool_name=tool_name,
                input_data=tool_args,
            )
            selected_tool = tool_by_name.get(tool_name)
            if selected_tool is None:
                result = {"error": f"unsupported tool: {tool_name}"}
            else:
                result = selected_tool.invoke(tool_args)
            yield tool_result_event(
                tool_call_id=tool_call_id,
                status="success" if "error" not in result else "failed",
                summary=_tool_result_summary(tool_name, result),
                data=result,
            )
            messages.append(
                ToolMessage(
                    content=_to_json(result),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            )

        if tool_calls:
            yield from _stream_final_response(model, messages)
            return

        yield message_event(_message_content_to_text(response))
        return

    yield from _stream_final_response(
        model,
        [
            *messages,
            HumanMessage(
                content="请基于已经获取的工具结果，直接输出最终 Markdown 报告。"
            ),
        ],
    )


def _build_fund_agent_tools():
    fund_query = FundQueryFacade()

    @tool
    def get_fund_value(fund_code: str) -> dict[str, Any]:
        """查询基金实时估值和已公布净值。输入基金代码，例如 110010。"""
        result = fund_query.get_fund_value(
            FundValueRequest(fund_code=fund_code, source="auto")
        )
        return result.model_dump()

    @tool
    def get_fund_profile(fund_code: str) -> dict[str, Any]:
        """查询基金画像，包括基础信息、主要持仓、行业配置和费率信息。输入基金代码。"""
        from datetime import date

        result = fund_query.get_fund_profile(
            FundProfileRequest(symbol=fund_code, year=str(date.today().year))
        )
        payload = result.model_dump()
        payload["holdings"] = payload["holdings"][:10]
        payload["industry_allocations"] = payload["industry_allocations"][:10]
        return payload

    @tool
    def get_fund_nav_trend_summary(fund_code: str) -> dict[str, Any]:
        """查询基金近一年净值走势摘要，包括区间收益、最大回撤和最近净值点。输入基金代码。"""
        return fund_query.get_fund_nav_trend_summary(fund_code)

    return [get_fund_value, get_fund_profile, get_fund_nav_trend_summary]


def _fund_agent_system_prompt(persona: str = "professional") -> str:
    if persona == "aggressive_ajia":
        return """
你是“股神阿佳”，一个风格激进、说话直接、带一点江湖气的金融分析智能体。
你的语言可以犀利、有情绪，可以偶尔使用口头禅，例如“草，这位置不能怂”“就是干”“别磨叽”“这波要看清楚再上”。
“梭哈”只能作为情绪化表达，不能真的建议用户满仓、借钱、加杠杆或孤注一掷。
不要辱骂用户，不要做人身攻击。

你的投资风格偏进攻型，关注高弹性机会、趋势、估值变化、资金情绪、板块热度和短期催化。
你可以给出更明确的操作倾向，但必须保留风险条件和仓位边界。
必须只基于工具结果和用户输入生成结论，不要编造实时新闻、基金经理观点、宏观结论或未提供的持仓变化。
如果数据缺失，直接说“数据不够，别瞎冲”。
如果估算日期与公布日期不一致，必须说明两者不能直接比较。

不能输出“必须买入”“必涨”“稳赚”“无脑冲”。
不能建议用户借钱投资、融资加杠杆、满仓梭哈。
操作建议必须从“观望”“小仓位试探”“分批上车”“持有不追”“分批止盈”“降低仓位”“暂不新增”中选择一种。
仓位建议必须明确，例如“不超过总资金的 10%-20%”“分两到三笔”“已经重仓就别再上头”。
输出必须是中文 Markdown。
免责声明必须说明：以上内容仅用于学习和信息分析，不构成投资建议。
""".strip()

    return """
你是一名审慎、专业的基金投研智能体。你可以根据需要调用基金数据工具。
必须只基于工具结果和用户输入生成结论，不要编造实时新闻、基金经理观点、宏观结论或未提供的持仓变化。
如果数据缺失，请明确写“数据暂缺”。
输出必须是中文 Markdown。
当日操作建议只能从“观望”“小额定投/小仓位试探”“持有不追高”“分批止盈/降低仓位”“暂不新增”中选择一种。
如果估算日期与公布日期不一致，必须明确说明不可直接比较，不能计算估算偏差。
免责声明必须说明：以上内容仅用于学习和信息分析，不构成投资建议。
""".strip()


def _fund_agent_user_prompt(
    fund_code: str, persona: str = "professional", question: str | None = None
) -> str:
    current_question = question or f"请分析基金 {fund_code}。"
    fund_hint = (
        f"当前基金代码：{fund_code}。"
        if fund_code
        else "当前没有指定基金代码；如果用户问题需要基金数据，先要求用户提供基金代码，或者基于已有上下文回答。"
    )
    if persona == "aggressive_ajia":
        return f"""
请用“股神阿佳”的风格回答用户问题。

{fund_hint}
用户问题：{current_question}

你可以自主选择调用以下工具：
1. get_fund_value：查询基金实时估值和已公布净值。
2. get_fund_profile：查询基金画像、持仓和行业配置。
3. get_fund_nav_trend_summary：查询近一年净值走势摘要。

如果用户是在对话中追问，请直接回答问题，不要机械生成完整报告。
如果用户要求完整分析，再输出结构化 Markdown。
""".strip()

    return f"""
请以基金投研智能体身份回答用户问题。

{fund_hint}
用户问题：{current_question}

你可以自主选择调用以下工具：
1. get_fund_value：查询基金实时估值和已公布净值。
2. get_fund_profile：查询基金画像、持仓和行业配置。
3. get_fund_nav_trend_summary：查询近一年净值走势摘要。

如果用户是在对话中追问，请直接回答问题，不要机械生成完整报告。
如果用户要求完整分析，再输出结构化 Markdown。
""".strip()


def _message_content_to_text(message: AIMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        return "".join(parts)
    return str(content or "")


def _stream_final_response(model, messages):
    for chunk in model.stream(messages):
        text = _message_content_to_text(chunk)
        if text:
            yield message_event(text)


def _tool_result_summary(tool_name: str, result: Any) -> str:
    if isinstance(result, dict) and result.get("error"):
        return str(result["error"])
    summary_by_tool = {
        "get_fund_value": "已获取基金估值和净值数据",
        "get_fund_profile": "已获取基金画像、持仓和行业配置",
        "get_fund_nav_trend_summary": "已获取近一年净值走势摘要",
    }
    return summary_by_tool.get(tool_name, "工具调用完成")


def _favorite_scan_graph():
    graph = StateGraph(FundAgentState)
    graph.add_node("load_data", _load_favorite_data)
    graph.add_node("build_prompt", _build_favorite_prompt)
    graph.set_entry_point("load_data")
    graph.add_edge("load_data", "build_prompt")
    graph.add_edge("build_prompt", END)
    return graph.compile()


def _load_fund_data(state: FundAgentState) -> FundAgentState:
    fund_code = str(state.get("payload", {})["fund_code"])
    return {**state, "data": fund_tools.load_fund_analysis_data(fund_code)}


def _load_favorite_data(state: FundAgentState) -> FundAgentState:
    return {
        **state,
        "data": fund_tools.load_favorite_scan_data(
            state.get("db"),
            state.get("user"),
            page_size=int(state.get("payload", {})["page_size"]),
        ),
    }


def _build_fund_prompt(state: FundAgentState) -> FundAgentState:
    data = state.get("data", {})
    fund_code = str(data["fund_code"])
    profile = data["profile"]
    prompt = f"""
你是一名审慎、专业的基金投研智能体。请基于输入数据生成中文 Markdown 分析报告。
必须只使用输入数据，不要编造实时新闻、基金经理观点、宏观结论或未提供的持仓变化。
如果某项数据缺失，请明确写“数据暂缺”。

基金代码：{fund_code}

【净值与估算数据】
{_to_json(data["fund_value"])}

【基金画像】
基础信息：
{_to_json(profile.basic_info)}

前十大持仓或主要持仓：
{_to_json(_limit_rows(profile.holdings, 10))}

【行业/板块配置】
{_to_json(_limit_rows(profile.industry_allocations, 10))}

【近一年净值走势摘要】
{_to_json(data["nav_trend_summary"])}

报告结构：
1. 基金画像
2. 当前净值与估值状态
3. 行业/板块暴露
4. 近一年走势与风险
5. 当日收盘前操作建议
6. 盘后复核要点
7. 风险提示与免责声明

当日操作建议只能从“观望”“小额定投/小仓位试探”“持有不追高”“分批止盈/降低仓位”“暂不新增”中选择一种。
如果估算日期与公布日期不一致，必须明确说明不可直接比较，不能计算估算偏差。
免责声明必须说明：以上内容仅用于学习和信息分析，不构成投资建议。
""".strip()
    return {**state, "prompt": prompt}


def _build_favorite_prompt(state: FundAgentState) -> FundAgentState:
    data = state.get("data", {})
    prompt = f"""
你是一名审慎、专业的基金组合扫描智能体。请基于用户自选基金估值数据生成中文 Markdown 扫描报告。
必须只使用输入数据，不要编造未提供的数据。

【自选基金扫描数据】
{_to_json(data.get("favorite_report"))}

报告结构：
1. 自选组合概览
2. 当日估值涨跌分布
3. 需要关注的基金
4. 收盘前操作建议
5. 盘后复核要点
6. 风险提示与免责声明

操作建议应偏审慎，不能输出“必须买入/必须卖出”。
如果估值缺失，请明确说明数据暂缺。
免责声明必须说明：以上内容仅用于学习和信息分析，不构成投资建议。
""".strip()
    return {**state, "prompt": prompt}


def _to_json(value) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    return json.dumps(value, ensure_ascii=False, default=str, indent=2)


def _limit_rows(rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    return rows[:limit]
