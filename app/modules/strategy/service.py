from dataclasses import dataclass

from app.core.exception import BadGatewayError, NotFoundError
from app.core.exception import ValidationError
from app.infrastructure.clients import akshare_client
from app.modules.strategy.schemas import (
    DisciplineAdvice,
    DisciplineRiskLevel,
    MarketScript,
    MarketScriptKey,
    MarketStructureDisciplineAdviceResponse,
    MarketStructureRealtimeResponse,
    MarketStructureToolContextResponse,
    MarketStructureWatchPointsResponse,
    ObservationDirection,
    SectorWatchPoint,
    StrategyAnalyzeRequest,
    StrategyAnalyzeResponse,
    StrategyEtfSearchResponse,
    StrategyEtfQuote,
    StrategyLineKey,
    WatchPointSource,
)

ETF_SPOT_SOURCE = "akshare.fund_etf_spot_em"
MARKET_STRUCTURE_STRATEGY_CODE = "market_structure"
MARKET_STRUCTURE_STRATEGY_NAME = "市场格局风向标"

SECTOR_ETF_KEYWORDS: dict[str, list[str]] = {
    "国产半导体": ["半导体", "芯片", "科创芯片", "半导体设备"],
    "华为链": ["通信", "云计算", "服务器", "信息技术"],
    "海外算力链": ["通信", "算力", "人工智能", "云计算"],
    "存储链": ["芯片", "半导体", "电子"],
    "机器人": ["机器人", "智能制造", "高端装备"],
    "生物医药": ["生物医药", "医药", "医疗", "创新药"],
    "硬科技前排": ["半导体", "芯片", "通信", "人工智能"],
    "成交额核心 ETF": ["588710", "515880"],
    "核心 ETF": ["588710", "515880"],
}


@dataclass(frozen=True)
class StrategyEtfConfig:
    line_key: StrategyLineKey
    line_name: str
    etf_code: str


@dataclass(frozen=True)
class WatchSectorConfig:
    label: str
    keywords: tuple[str, ...]


MARKET_STRUCTURE_ETFS = (
    StrategyEtfConfig(
        line_key="domestic",
        line_name="国产硬科技线",
        etf_code="588710",
    ),
    StrategyEtfConfig(
        line_key="overseas",
        line_name="海外算力链",
        etf_code="515880",
    ),
)

MARKET_SCRIPTS: dict[MarketScriptKey, MarketScript] = {
    "domestic_story": MarketScript(
        key="domestic_story",
        label="国产替代主线",
        description="国产硬科技线强、海外算力链弱，资金继续讲国产替代故事。",
    ),
    "overseas_earnings": MarketScript(
        key="overseas_earnings",
        label="业绩线回归",
        description="海外算力链强、国产硬科技线弱，资金更重视业绩兑现。",
    ),
    "hard_tech_siphon": MarketScript(
        key="hard_tech_siphon",
        label="硬科技虹吸",
        description="两条硬科技主线同步走强，注意其他方向被抽血。",
    ),
    "rotation_other": MarketScript(
        key="rotation_other",
        label="轮动他处",
        description="两条硬科技主线同步走弱，观察机器人、生物医药等轮动方向。",
    ),
    "unknown": MarketScript(
        key="unknown",
        label="等待确认",
        description="ETF 涨跌幅数据不完整，暂不判断市场剧本。",
    ),
}

WATCH_POINT_SECTORS: dict[MarketScriptKey, list[WatchSectorConfig]] = {
    "domestic_story": [
        WatchSectorConfig(
            label="国产半导体",
            keywords=("半导体", "芯片", "科创芯片", "半导体设备", "588710"),
        ),
        WatchSectorConfig(
            label="华为链",
            keywords=("通信", "信息技术", "云计算", "服务器", "连接器"),
        ),
    ],
    "overseas_earnings": [
        WatchSectorConfig(
            label="海外算力链",
            keywords=("通信", "算力", "人工智能", "云计算", "液冷", "电源"),
        ),
        WatchSectorConfig(
            label="存储链",
            keywords=("存储", "芯片", "半导体", "电子"),
        ),
    ],
    "hard_tech_siphon": [
        WatchSectorConfig(
            label="硬科技前排",
            keywords=("半导体", "芯片", "通信", "人工智能", "信息技术"),
        ),
        WatchSectorConfig(
            label="成交额核心 ETF",
            keywords=("588710", "515880"),
        ),
    ],
    "rotation_other": [
        WatchSectorConfig(
            label="机器人",
            keywords=("机器人", "智能制造", "高端装备"),
        ),
        WatchSectorConfig(
            label="生物医药",
            keywords=("生物医药", "医药", "医疗", "创新药"),
        ),
    ],
    "unknown": [
        WatchSectorConfig(
            label="核心 ETF",
            keywords=("588710", "515880"),
        )
    ],
}

DISCIPLINE_ADVICE: dict[MarketScriptKey, DisciplineAdvice] = {
    "domestic_story": DisciplineAdvice(
        action="持有不追高",
        position_hint="已有国产硬科技仓位可观察前排承接，新增仓位保持小额试探。",
        reason="国产线占优但后排容易受前排兑现影响，优先防追高。",
        risk_controls=[
            "前排冲高回落时停止追后排。",
            "21 日线不抵抗时降低仓位。",
            "放量滞涨时优先确认成交额是否有效承接。",
        ],
    ),
    "overseas_earnings": DisciplineAdvice(
        action="小仓位试探",
        position_hint="围绕业绩兑现方向分批观察，不做单笔重仓。",
        reason="海外算力和存储占优时更看业绩弹性，但兑现波动也更直接。",
        risk_controls=[
            "业绩兑现后开盘下杀时先退出观察。",
            "不在高开急拉后追入。",
            "跌破 60 日线后等待平台抵抗。",
        ],
    ),
    "hard_tech_siphon": DisciplineAdvice(
        action="持有不追高",
        position_hint="已有核心仓位以持有为主，新增只看前排回踩承接。",
        reason="双线走强说明硬科技虹吸，但全场抽血时后排波动会放大。",
        risk_controls=[
            "只看成交额核心标的，不追低辨识度后排。",
            "双线任一方转弱时降低进攻强度。",
            "放量滞涨时优先锁定利润。",
        ],
    ),
    "rotation_other": DisciplineAdvice(
        action="降低仓位",
        position_hint="硬科技后排不硬扛，等待机器人或医药轮动强度确认。",
        reason="两条硬科技主线同步走弱，主线内继续加仓的胜率下降。",
        risk_controls=[
            "21 日线不抵抗就走",
            "跌破 60 日线后，只看是否形成小平台抵抗",
            "不抵抗且放量杀，等待破位后重新形成箱体或 34 日线修复",
            "不在硬科技后排补跌时摊平。",
            "机器人和医药也只看前排，不追一字后排。",
            "等待 34 日线或箱体抵抗后再考虑回补。",
        ],
    ),
    "unknown": DisciplineAdvice(
        action="观望",
        position_hint="数据不完整时先不做新增决策。",
        reason="四象限剧本未确认，操作纪律优先于主观判断。",
        risk_controls=[
            "等待 ETF 涨跌幅和成交额更新。",
            "避免基于单一标的波动推断主线。",
        ],
    ),
}


def get_market_structure_realtime() -> MarketStructureRealtimeResponse:
    spot_df = _get_etf_spot_quotes()
    return _build_realtime_response(spot_df)


def _get_etf_spot_quotes():
    try:
        return akshare_client.get_etf_spot_quotes()
    except Exception as exc:
        raise BadGatewayError(f"AkShare ETF spot query failed: {exc}") from exc


def _build_realtime_response(spot_df) -> MarketStructureRealtimeResponse:
    quotes = [
        _build_strategy_etf_quote(spot_df, config) for config in MARKET_STRUCTURE_ETFS
    ]
    return MarketStructureRealtimeResponse(
        items=quotes,
        market_script=_build_market_script(quotes),
    )


def analyze_strategy(payload: StrategyAnalyzeRequest) -> StrategyAnalyzeResponse:
    if payload.analyze_type == "market_structure_intraday_watch":
        spot_df = _get_etf_spot_quotes()
        realtime = _build_realtime_response(spot_df)
        watch_points = _build_watch_points_from_spot(
            spot_df, realtime.market_script.key
        )
        return StrategyAnalyzeResponse(
            analyze_type=payload.analyze_type,
            strategy_code=MARKET_STRUCTURE_STRATEGY_CODE,
            strategy_name=MARKET_STRUCTURE_STRATEGY_NAME,
            agent_code="market_intraday_watch",
            agent_name="盘中观察员",
            data={
                "realtime": realtime.model_dump(),
                "watch_points": watch_points.model_dump(),
            },
        )

    if payload.analyze_type == "market_structure_discipline_advice":
        spot_df = _get_etf_spot_quotes()
        realtime = _build_realtime_response(spot_df)
        discipline_advice = _build_discipline_advice_response(
            realtime,
            _param_market_script_key(payload.params),
        )
        return StrategyAnalyzeResponse(
            analyze_type=payload.analyze_type,
            strategy_code=MARKET_STRUCTURE_STRATEGY_CODE,
            strategy_name=MARKET_STRUCTURE_STRATEGY_NAME,
            agent_code="market_discipline_advisor",
            agent_name="纪律风控官",
            data={
                "discipline_advice": discipline_advice.model_dump(),
            },
        )

    raise ValidationError(f"unsupported analyze_type: {payload.analyze_type}")


def get_market_structure_watch_points(
    market_script_key: MarketScriptKey | None = None,
) -> MarketStructureWatchPointsResponse:
    spot_df = _get_etf_spot_quotes()

    if market_script_key is not None:
        return _build_watch_points_from_spot(spot_df, market_script_key)

    realtime = _build_realtime_response(spot_df)
    return _build_watch_points_from_spot(spot_df, realtime.market_script.key)


def get_market_structure_discipline_advice(
    market_script_key: MarketScriptKey | None = None,
) -> MarketStructureDisciplineAdviceResponse:
    realtime = _build_realtime_response(_get_etf_spot_quotes())
    return _build_discipline_advice_response(realtime, market_script_key)


def _build_discipline_advice_response(
    realtime: MarketStructureRealtimeResponse,
    market_script_key: MarketScriptKey | None = None,
) -> MarketStructureDisciplineAdviceResponse:
    market_script = (
        MARKET_SCRIPTS[market_script_key]
        if market_script_key is not None
        else realtime.market_script
    )
    advice = _build_dynamic_discipline_advice(market_script, realtime.items)
    return MarketStructureDisciplineAdviceResponse(
        market_script=market_script,
        advice=advice,
        source=WatchPointSource(
            etf_codes=[item.etf_code for item in realtime.items],
            update_time=_latest_update_time(realtime.items),
            provider=ETF_SPOT_SOURCE,
        ),
    )


def search_strategy_etfs(keyword: str, limit: int = 10) -> StrategyEtfSearchResponse:
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return StrategyEtfSearchResponse(keyword=keyword, total=0, items=[])

    spot_df = _get_etf_spot_quotes()

    items = _search_quotes_in_df(
        spot_df,
        keywords=[normalized_keyword],
        limit=limit,
    )
    return StrategyEtfSearchResponse(
        keyword=normalized_keyword,
        total=len(items),
        items=items,
    )


def get_market_structure_tool_context() -> MarketStructureToolContextResponse:
    spot_df = _get_etf_spot_quotes()
    realtime = _build_realtime_response(spot_df)
    source = WatchPointSource(
        etf_codes=[item.etf_code for item in realtime.items],
        update_time=_latest_update_time(realtime.items),
        provider=ETF_SPOT_SOURCE,
    )
    watch_points = _build_watch_points_from_spot(spot_df, realtime.market_script.key)
    discipline_advice = MarketStructureDisciplineAdviceResponse(
        market_script=realtime.market_script,
        advice=_build_dynamic_discipline_advice(realtime.market_script, realtime.items),
        source=source,
    )

    candidate_etfs = {
        sector.label: StrategyEtfSearchResponse(
            keyword=sector.label,
            total=len(sector.observed_etfs),
            items=sector.observed_etfs,
        )
        for sector in watch_points.sectors
    }
    return MarketStructureToolContextResponse(
        realtime=realtime,
        watch_points=watch_points,
        discipline_advice=discipline_advice,
        candidate_etfs=candidate_etfs,
    )


def _build_watch_points_from_spot(
    spot_df,
    market_script_key: MarketScriptKey,
) -> MarketStructureWatchPointsResponse:
    sectors = _build_sector_watch_points(spot_df, market_script_key)
    return _build_watch_points_response(
        market_script=MARKET_SCRIPTS[market_script_key],
        source=WatchPointSource(
            etf_codes=_observed_etf_codes(sectors),
            update_time=_latest_observation_update_time(sectors),
            provider=ETF_SPOT_SOURCE,
        ),
        sectors=sectors,
    )


def _build_strategy_etf_quote(spot_df, config: StrategyEtfConfig) -> StrategyEtfQuote:
    row = _find_row_by_code(spot_df, config.etf_code)
    if row is None:
        raise NotFoundError(f"Strategy ETF quote not found: {config.etf_code}")

    return _build_quote_from_row(row, config.line_key, config.line_name)


def _build_quote_from_row(
    row,
    line_key: StrategyLineKey,
    line_name: str,
) -> StrategyEtfQuote:
    return StrategyEtfQuote(
        line_key=line_key,
        line_name=line_name,
        etf_code=str(row.get("代码", "")),
        etf_name=str(row.get("名称", "")),
        latest_price=_parse_float(row.get("最新价")),
        iopv=_parse_float(row.get("IOPV实时估值")),
        discount_rate=_parse_float(row.get("基金折价率")),
        change_amount=_parse_float(row.get("涨跌额")),
        change_percent=_parse_float(row.get("涨跌幅")),
        volume=_parse_float(row.get("成交量")),
        turnover=_parse_float(row.get("成交额")),
        open_price=_parse_float(row.get("开盘价")),
        high_price=_parse_float(row.get("最高价")),
        low_price=_parse_float(row.get("最低价")),
        previous_close=_parse_float(row.get("昨收")),
        trade_date=str(row.get("数据日期", "")),
        update_time=str(row.get("更新时间", "")),
        source=ETF_SPOT_SOURCE,
    )


def _find_row_by_code(spot_df, etf_code: str):
    for _, row in spot_df.iterrows():
        if str(row.get("代码", "")) == etf_code:
            return row
    return None


def _parse_float(value: object) -> float | None:
    if value is None:
        return None

    text = str(value).strip().replace(",", "").replace("%", "")
    if not text or text in {"-", "--", "---"}:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def _build_market_script(quotes: list[StrategyEtfQuote]) -> MarketScript:
    quote_by_line = {quote.line_key: quote for quote in quotes}
    domestic_change = quote_by_line["domestic"].change_percent
    overseas_change = quote_by_line["overseas"].change_percent

    if domestic_change is None or overseas_change is None:
        return MARKET_SCRIPTS["unknown"]

    if domestic_change > 0 and overseas_change <= 0:
        return MARKET_SCRIPTS["domestic_story"]

    if domestic_change <= 0 < overseas_change:
        return MARKET_SCRIPTS["overseas_earnings"]

    if domestic_change > 0 and overseas_change > 0:
        return MARKET_SCRIPTS["hard_tech_siphon"]

    return MARKET_SCRIPTS["rotation_other"]


def _build_dynamic_discipline_advice(
    market_script: MarketScript,
    quotes: list[StrategyEtfQuote],
) -> DisciplineAdvice:
    base = DISCIPLINE_ADVICE[market_script.key]
    quote_by_line = {quote.line_key: quote for quote in quotes}
    domestic = quote_by_line.get("domestic")
    overseas = quote_by_line.get("overseas")
    return DisciplineAdvice(
        action=base.action,
        risk_level=_discipline_risk_level(market_script.key),
        position_hint=_build_position_hint(
            base.position_hint, market_script.key, quotes
        ),
        reason=_build_discipline_reason(base.reason, market_script, quotes),
        evidence_quotes=_build_evidence_quotes(quotes),
        trigger_conditions=_build_trigger_conditions(
            market_script.key, domestic, overseas
        ),
        invalidation_conditions=_build_invalidation_conditions(market_script.key),
        risk_controls=base.risk_controls,
    )


def _discipline_risk_level(market_script_key: MarketScriptKey) -> DisciplineRiskLevel:
    risk_levels: dict[MarketScriptKey, DisciplineRiskLevel] = {
        "domestic_story": "medium",
        "overseas_earnings": "medium",
        "hard_tech_siphon": "medium",
        "rotation_other": "high",
        "unknown": "unknown",
    }
    return risk_levels[market_script_key]


def _build_position_hint(
    base_position_hint: str,
    market_script_key: MarketScriptKey,
    quotes: list[StrategyEtfQuote],
) -> str:
    quote_text = "，".join(_format_quote_change(quote) for quote in quotes)
    if market_script_key == "rotation_other":
        return f"{base_position_hint} 实时核心 ETF：{quote_text}，新增仓位先停。"
    if market_script_key == "hard_tech_siphon":
        return f"{base_position_hint} 实时核心 ETF：{quote_text}，只接受回踩承接。"
    if market_script_key == "unknown":
        return f"{base_position_hint} 实时核心 ETF：{quote_text}。"
    return f"{base_position_hint} 实时核心 ETF：{quote_text}，不追高开急拉。"


def _build_discipline_reason(
    base_reason: str,
    market_script: MarketScript,
    quotes: list[StrategyEtfQuote],
) -> str:
    quote_text = "；".join(_format_quote_change(quote) for quote in quotes)
    return f"{base_reason} 当前剧本为“{market_script.label}”，实时证据为 {quote_text}。"


def _build_evidence_quotes(quotes: list[StrategyEtfQuote]) -> list[str]:
    return [_format_quote_change(quote) for quote in quotes]


def _format_quote_change(quote: StrategyEtfQuote) -> str:
    change_text = (
        f"{quote.change_percent:+.2f}%"
        if quote.change_percent is not None
        else "涨跌幅缺失"
    )
    return f"{quote.etf_code} {quote.etf_name} {change_text}"


def _build_trigger_conditions(
    market_script_key: MarketScriptKey,
    domestic: StrategyEtfQuote | None,
    overseas: StrategyEtfQuote | None,
) -> list[str]:
    if market_script_key == "domestic_story":
        return [
            "国产硬科技 ETF 走强且海外算力 ETF 走弱或滞涨",
            "国产半导体、华为链前排仍有承接",
            "十点半前基金重仓方向没有明显兑现式下杀",
        ]
    if market_script_key == "overseas_earnings":
        return [
            "海外算力 ETF 走强且国产硬科技 ETF 走弱或滞涨",
            "存储、液冷、电源等业绩线候选 ETF 有承接",
            "高开急拉后没有放量滞涨",
        ]
    if market_script_key == "hard_tech_siphon":
        return [
            "两条核心 ETF 同步走强",
            "硬科技前排成交额维持在候选方向前列",
            "其他方向被抽血但核心 ETF 未出现冲高回落",
        ]
    if market_script_key == "rotation_other":
        return [
            "两条核心 ETF 同步走弱",
            "硬科技前排无法维持承接",
            "机器人或生物医药候选 ETF 出现相对强度",
        ]
    if _missing_change(domestic) or _missing_change(overseas):
        return ["核心 ETF 涨跌幅缺失，无法确认四象限剧本"]
    return ["四象限剧本未形成稳定方向"]


def _build_invalidation_conditions(
    market_script_key: MarketScriptKey,
) -> list[str]:
    if market_script_key == "domestic_story":
        return [
            "国产硬科技 ETF 翻绿并放量走弱",
            "海外算力 ETF 重新转强导致剧本切换",
            "前排冲高回落且后排开始补跌",
        ]
    if market_script_key == "overseas_earnings":
        return [
            "海外算力 ETF 翻绿并放量走弱",
            "业绩线候选 ETF 高开低走",
            "国产硬科技 ETF 重新转强导致剧本切换",
        ]
    if market_script_key == "hard_tech_siphon":
        return [
            "任一核心 ETF 翻绿",
            "核心 ETF 放量滞涨或冲高回落",
            "前排承接失效导致后排补跌",
        ]
    if market_script_key == "rotation_other":
        return [
            "任一核心 ETF 放量翻红并站稳",
            "机器人和生物医药候选 ETF 同步转弱",
            "硬科技重新形成箱体或 34 日线修复",
        ]
    return ["核心 ETF 数据恢复后需要重新判断"]


def _missing_change(quote: StrategyEtfQuote | None) -> bool:
    return quote is None or quote.change_percent is None


def _param_market_script_key(params: dict[str, object]) -> MarketScriptKey | None:
    value = params.get("market_script_key")
    if value is None:
        return None
    text = str(value).strip()
    if text in MARKET_SCRIPTS:
        return text  # type: ignore[return-value]
    return None


def _build_watch_points_response(
    market_script: MarketScript,
    source: WatchPointSource,
    sectors: list[SectorWatchPoint],
) -> MarketStructureWatchPointsResponse:
    return MarketStructureWatchPointsResponse(
        market_script=market_script,
        sectors=sectors,
        source=source,
    )


def _latest_update_time(quotes: list[StrategyEtfQuote]) -> str:
    for quote in quotes:
        if quote.update_time:
            return quote.update_time
    return ""


def _build_sector_watch_points(
    spot_df,
    market_script_key: MarketScriptKey,
) -> list[SectorWatchPoint]:
    return [
        _build_sector_watch_point(spot_df, config)
        for config in WATCH_POINT_SECTORS[market_script_key]
    ]


def _build_sector_watch_point(spot_df, config: WatchSectorConfig) -> SectorWatchPoint:
    observed_etfs = _search_quotes_in_df(
        spot_df,
        keywords=[
            config.label,
            *SECTOR_ETF_KEYWORDS.get(config.label, []),
            *config.keywords,
        ],
        limit=5,
    )
    change_values = [
        item.change_percent for item in observed_etfs if item.change_percent is not None
    ]
    turnover_values = [
        item.turnover for item in observed_etfs if item.turnover is not None
    ]
    average_change = (
        round(sum(change_values) / len(change_values), 2) if change_values else None
    )
    total_turnover = round(sum(turnover_values), 2) if turnover_values else None
    direction = _observation_direction(change_values)
    return SectorWatchPoint(
        label=config.label,
        direction=direction,
        observation=_build_observation_text(
            config.label, direction, observed_etfs, average_change
        ),
        average_change_percent=average_change,
        total_turnover=total_turnover,
        observed_etfs=observed_etfs,
    )


def _search_quotes_in_df(
    spot_df,
    keywords: list[str],
    limit: int,
) -> list[StrategyEtfQuote]:
    normalized_keywords = [keyword for keyword in keywords if keyword]
    items: list[StrategyEtfQuote] = []
    seen_codes: set[str] = set()
    for _, row in spot_df.iterrows():
        code = str(row.get("代码", ""))
        name = str(row.get("名称", ""))
        searchable = f"{code} {name}"
        if not any(keyword in searchable for keyword in normalized_keywords):
            continue
        if code in seen_codes:
            continue
        seen_codes.add(code)
        items.append(
            _build_quote_from_row(row, line_key="candidate", line_name="候选ETF")
        )
        if len(items) >= limit:
            break
    return items


def _observation_direction(change_values: list[float]) -> ObservationDirection:
    if not change_values:
        return "no_data"
    positive_count = sum(1 for value in change_values if value > 0)
    negative_count = sum(1 for value in change_values if value < 0)
    if positive_count and not negative_count:
        return "strengthening"
    if negative_count and not positive_count:
        return "weakening"
    return "mixed"


def _build_observation_text(
    label: str,
    direction: ObservationDirection,
    observed_etfs: list[StrategyEtfQuote],
    average_change: float | None,
) -> str:
    if not observed_etfs:
        return f"{label} 暂未匹配到 ETF 实时行情，先不下观察结论。"

    leader = max(
        observed_etfs,
        key=lambda item: item.turnover if item.turnover is not None else 0,
    )
    direction_text = {
        "strengthening": "整体走强",
        "weakening": "整体走弱",
        "mixed": "内部分化",
        "no_data": "数据不足",
    }[direction]
    average_text = f"{average_change:+.2f}%" if average_change is not None else "--"
    if leader.change_percent is None:
        return (
            f"{label} 当前{direction_text}，候选 ETF 平均涨跌幅 {average_text}；"
            f"成交额最高的是 {leader.etf_code} {leader.etf_name}。"
        )
    return (
        f"{label} 当前{direction_text}，候选 ETF 平均涨跌幅 {average_text}；"
        f"成交额最高的是 {leader.etf_code} {leader.etf_name}，"
        f"涨跌幅 {leader.change_percent:+.2f}%。"
    )


def _observed_etf_codes(sectors: list[SectorWatchPoint]) -> list[str]:
    codes: list[str] = []
    for sector in sectors:
        for item in sector.observed_etfs:
            if item.etf_code not in codes:
                codes.append(item.etf_code)
    return codes


def _latest_observation_update_time(sectors: list[SectorWatchPoint]) -> str:
    for sector in sectors:
        for item in sector.observed_etfs:
            if item.update_time:
                return item.update_time
    return ""
