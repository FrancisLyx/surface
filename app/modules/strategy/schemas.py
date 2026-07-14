from typing import Any, Literal

from pydantic import BaseModel, Field


StrategyLineKey = Literal["domestic", "overseas", "candidate"]
ObservationDirection = Literal["strengthening", "weakening", "mixed", "no_data"]
DisciplineRiskLevel = Literal["low", "medium", "high", "unknown"]
MarketScriptKey = Literal[
    "domestic_story",
    "overseas_earnings",
    "hard_tech_siphon",
    "rotation_other",
    "unknown",
]
StrategyAnalyzeType = Literal[
    "market_structure_intraday_watch",
    "market_structure_discipline_advice",
]


class StrategyEtfQuote(BaseModel):
    line_key: StrategyLineKey = Field(description="策略主线标识")
    line_name: str = Field(description="策略主线名称")
    etf_code: str = Field(description="ETF 代码")
    etf_name: str = Field(description="ETF 名称")
    latest_price: float | None = Field(default=None, description="最新价")
    iopv: float | None = Field(default=None, description="IOPV 实时估值")
    discount_rate: float | None = Field(default=None, description="基金折价率")
    change_amount: float | None = Field(default=None, description="涨跌额")
    change_percent: float | None = Field(default=None, description="涨跌幅")
    volume: float | None = Field(default=None, description="成交量")
    turnover: float | None = Field(default=None, description="成交额")
    open_price: float | None = Field(default=None, description="开盘价")
    high_price: float | None = Field(default=None, description="最高价")
    low_price: float | None = Field(default=None, description="最低价")
    previous_close: float | None = Field(default=None, description="昨收")
    trade_date: str = Field(description="数据日期")
    update_time: str = Field(description="更新时间")
    source: str = Field(description="数据来源")


class MarketScript(BaseModel):
    key: MarketScriptKey
    label: str
    description: str


class MarketStructureRealtimeResponse(BaseModel):
    items: list[StrategyEtfQuote]
    market_script: MarketScript


class SectorWatchPoint(BaseModel):
    label: str = Field(description="关注板块")
    direction: ObservationDirection = Field(description="实时观察方向")
    observation: str = Field(description="实时观察结论")
    average_change_percent: float | None = Field(
        default=None, description="候选 ETF 平均涨跌幅"
    )
    total_turnover: float | None = Field(
        default=None, description="候选 ETF 合计成交额"
    )
    observed_etfs: list[StrategyEtfQuote] = Field(description="实时观察到的 ETF")


class WatchPointSource(BaseModel):
    etf_codes: list[str] = Field(description="用于判断或观察的 ETF 代码")
    update_time: str = Field(description="判断数据更新时间")
    provider: str = Field(description="规则或行情来源")


class MarketStructureWatchPointsResponse(BaseModel):
    market_script: MarketScript
    sectors: list[SectorWatchPoint]
    source: WatchPointSource


class DisciplineAdvice(BaseModel):
    action: str = Field(description="操作动作建议")
    risk_level: DisciplineRiskLevel = Field(
        default="medium", description="当前纪律风险级别"
    )
    position_hint: str = Field(description="仓位提示")
    reason: str = Field(description="建议原因")
    evidence_quotes: list[str] = Field(
        default_factory=list, description="实时 ETF 证据"
    )
    trigger_conditions: list[str] = Field(
        default_factory=list, description="触发当前建议的条件"
    )
    invalidation_conditions: list[str] = Field(
        default_factory=list, description="建议失效或需要复核的条件"
    )
    risk_controls: list[str] = Field(description="风控条件")


class MarketStructureDisciplineAdviceResponse(BaseModel):
    market_script: MarketScript
    advice: DisciplineAdvice
    source: WatchPointSource


class StrategyEtfSearchResponse(BaseModel):
    keyword: str
    total: int
    items: list[StrategyEtfQuote]


class MarketStructureToolContextResponse(BaseModel):
    realtime: MarketStructureRealtimeResponse
    watch_points: MarketStructureWatchPointsResponse
    discipline_advice: MarketStructureDisciplineAdviceResponse
    candidate_etfs: dict[str, StrategyEtfSearchResponse]


class StrategyAnalyzeRequest(BaseModel):
    analyze_type: str = Field(description="分析类型")
    params: dict[str, Any] = Field(default_factory=dict, description="分析参数")


class StrategyAnalyzeResponse(BaseModel):
    analyze_type: str
    strategy_code: str
    strategy_name: str
    agent_code: str
    agent_name: str
    data: dict[str, Any]
