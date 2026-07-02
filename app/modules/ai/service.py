import json
from datetime import date

from app.modules.fund.public import FundQueryFacade
from app.modules.fund.schemas import FundProfileRequest, FundValueRequest
from app.infrastructure.clients.langchain_client import chat, stream_chat


def summarize_fund(fund_code: str) -> str:
    prompt = build_fund_summary_prompt(fund_code)
    return chat(prompt)


def stream_fund_summary(fund_code: str):
    prompt = build_fund_summary_prompt(fund_code)
    yield from stream_chat(prompt)


def build_fund_summary_prompt(fund_code: str) -> str:
    normalized_code = fund_code.strip()
    fund_query = FundQueryFacade()
    fund_value = fund_query.get_fund_value(
        FundValueRequest(fund_code=normalized_code, source="auto"),
    )
    profile = fund_query.get_fund_profile(
        FundProfileRequest(symbol=normalized_code, year=str(date.today().year)),
    )
    nav_trend_summary = fund_query.get_fund_nav_trend_summary(normalized_code)

    return _build_summary_prompt(
        normalized_code, fund_value, profile, nav_trend_summary
    )


def _build_summary_prompt(
    fund_code: str, fund_value, profile, nav_trend_summary: dict[str, object]
) -> str:
    return f"""
你是一名审慎、专业的基金研究员。请基于给定数据，对基金做中文分析。
必须只使用输入数据，不要编造基金经理观点、实时新闻、宏观结论或未提供的持仓变化。
如果某项数据缺失，请明确写“数据暂缺”，不要猜测。

基金代码：{fund_code}

【净值与估算数据】
{_to_json(fund_value)}

【基金画像】
基础信息：
{_to_json(profile.basic_info)}

前十大持仓或主要持仓：
{_to_json(_limit_rows(profile.holdings, 10))}

【行业/板块配置】
{_to_json(_limit_rows(profile.industry_allocations, 10))}

【近一年净值走势摘要】
{_to_json(nav_trend_summary)}

要求：
1. 输出结构必须包含：基金画像、当前净值表现、行业/板块分析、近一年走势分析、当日操作建议、风险提示、免责声明。
2. 当前净值表现要区分“估算数据”和“已公布净值”。如果估算日期与公布日期不一致，必须说明两者不可直接比较，不要计算估算偏差。
3. 行业/板块分析要结合持仓和行业配置，说明主要暴露方向、集中度和可能受影响的市场风格。
4. 近一年走势分析要结合区间收益、最大回撤和最近净值点，判断波动特征，不要只看单日涨跌。
5. 当日操作建议的场景是“收盘前操作”，主要用于交易日下午收盘前做是否申购、暂停、减仓或继续持有的判断；必须主要使用历史信息和当日估值信息，包括近一年走势、最大回撤、最近净值点、当日估算净值、当日估算增长率、行业/板块暴露。盘后净值和公布日增长率只用于复核，不作为收盘前操作的直接依据。
6. 当日操作建议必须基于输入数据生成，不要泛泛而谈；必须包含以下小项：
   - 动作结论：从“观望”“小额定投/小仓位试探”“持有不追高”“分批止盈/降低仓位”“暂不新增”中选择一种，不能输出“必须买入/必须卖出”。
   - 仓位建议：给出保守、清晰的仓位处理方式，例如“不新增”“小仓位”“分批”“控制总仓位”，不要承诺收益。
   - 触发条件：说明收盘前可以改变操作的条件，例如当日估算涨跌幅继续扩大、估值从正转负或从负转正、历史高波动下接近回撤压力区、行业暴露方向与当日估值表现不匹配。
   - 盘后复核：提醒盘后用已公布净值、公布日期、公布日增长率复核当日判断；盘后净值只用于复核，不要把盘后结果倒推成收盘前确定性结论。
7. 如果估算日期与公布日期不一致，必须写明“估算日期与公布日期不一致”，并说明当日估值信息只适合做收盘前参考，不能直接和上一公布净值计算偏差。
8. 风险提示要覆盖净值波动、行业集中、估算数据滞后或缺失、历史业绩不代表未来。
9. 免责声明必须说明：以上内容仅用于学习和信息分析，不构成投资建议。
""".strip()


def _to_json(value) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    return json.dumps(value, ensure_ascii=False, default=str, indent=2)


def _limit_rows(rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    return rows[:limit]
