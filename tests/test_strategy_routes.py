from fastapi.testclient import TestClient
import pytest

from app.api.dependencies import get_current_user_context
from app.core.current_user import CurrentUser
from app.infrastructure.clients import akshare_client
from app.main import app
from app.modules.strategy import service as strategy_service


class EtfSpotData:
    def __init__(
        self,
        domestic_change: str = "-4.02",
        overseas_change: str = "-4.11",
    ) -> None:
        self.domestic_change = domestic_change
        self.overseas_change = overseas_change

    def fillna(self, value):
        return self

    def iterrows(self):
        rows = [
            {
                "代码": "588710",
                "名称": "科创半导体设备ETF华泰柏瑞",
                "最新价": "3.824",
                "IOPV实时估值": "3.8171",
                "基金折价率": "-0.18",
                "涨跌额": "-0.16",
                "涨跌幅": self.domestic_change,
                "成交量": "2793462",
                "成交额": "1094325830",
                "开盘价": "3.8",
                "最高价": "4.034",
                "最低价": "3.8",
                "昨收": "3.984",
                "数据日期": "2026-07-13",
                "更新时间": "14:59:59",
            },
            {
                "代码": "516950",
                "名称": "机器人ETF",
                "最新价": "1.236",
                "IOPV实时估值": "1.235",
                "基金折价率": "-0.08",
                "涨跌额": "0.036",
                "涨跌幅": "3.00",
                "成交量": "1200000",
                "成交额": "150000000",
                "开盘价": "1.201",
                "最高价": "1.248",
                "最低价": "1.198",
                "昨收": "1.200",
                "数据日期": "2026-07-13",
                "更新时间": "14:59:59",
            },
            {
                "代码": "512170",
                "名称": "医疗ETF",
                "最新价": "0.482",
                "IOPV实时估值": "0.481",
                "基金折价率": "-0.20",
                "涨跌额": "0.012",
                "涨跌幅": "2.55",
                "成交量": "900000",
                "成交额": "43000000",
                "开盘价": "0.470",
                "最高价": "0.485",
                "最低价": "0.469",
                "昨收": "0.470",
                "数据日期": "2026-07-13",
                "更新时间": "14:59:59",
            },
            {
                "代码": "588200",
                "名称": "科创芯片ETF",
                "最新价": "1.820",
                "IOPV实时估值": "1.819",
                "基金折价率": "-0.05",
                "涨跌额": "-0.030",
                "涨跌幅": "-1.62",
                "成交量": "2100000",
                "成交额": "382000000",
                "开盘价": "1.850",
                "最高价": "1.870",
                "最低价": "1.810",
                "昨收": "1.850",
                "数据日期": "2026-07-13",
                "更新时间": "14:59:59",
            },
            {
                "代码": "515880",
                "名称": "通信ETF国泰",
                "最新价": "0.747",
                "IOPV实时估值": "0.7471",
                "基金折价率": "0.01",
                "涨跌额": "-0.032",
                "涨跌幅": self.overseas_change,
                "成交量": "30285044",
                "成交额": "2311196404",
                "开盘价": "0.761",
                "最高价": "0.783",
                "最低价": "0.745",
                "昨收": "0.779",
                "数据日期": "2026-07-13",
                "更新时间": "14:59:59",
            },
        ]
        yield from enumerate(rows)


@pytest.fixture(autouse=True)
def override_current_user():
    app.dependency_overrides[get_current_user_context] = lambda: CurrentUser(
        id=1, username="admin"
    )
    yield
    app.dependency_overrides.pop(get_current_user_context, None)


def test_get_market_structure_realtime_quotes(monkeypatch):
    monkeypatch.setattr(
        akshare_client, "get_etf_spot_quotes", lambda: EtfSpotData(), raising=False
    )

    data = strategy_service.get_market_structure_realtime().model_dump()

    assert data == {
        "items": [
            {
                "line_key": "domestic",
                "line_name": "国产硬科技线",
                "etf_code": "588710",
                "etf_name": "科创半导体设备ETF华泰柏瑞",
                "latest_price": 3.824,
                "iopv": 3.8171,
                "discount_rate": -0.18,
                "change_amount": -0.16,
                "change_percent": -4.02,
                "volume": 2793462.0,
                "turnover": 1094325830.0,
                "open_price": 3.8,
                "high_price": 4.034,
                "low_price": 3.8,
                "previous_close": 3.984,
                "trade_date": "2026-07-13",
                "update_time": "14:59:59",
                "source": "akshare.fund_etf_spot_em",
            },
            {
                "line_key": "overseas",
                "line_name": "海外算力链",
                "etf_code": "515880",
                "etf_name": "通信ETF国泰",
                "latest_price": 0.747,
                "iopv": 0.7471,
                "discount_rate": 0.01,
                "change_amount": -0.032,
                "change_percent": -4.11,
                "volume": 30285044.0,
                "turnover": 2311196404.0,
                "open_price": 0.761,
                "high_price": 0.783,
                "low_price": 0.745,
                "previous_close": 0.779,
                "trade_date": "2026-07-13",
                "update_time": "14:59:59",
                "source": "akshare.fund_etf_spot_em",
            },
        ],
        "market_script": {
            "key": "rotation_other",
            "label": "轮动他处",
            "description": "两条硬科技主线同步走弱，观察机器人、生物医药等轮动方向。",
        },
    }


def test_strategy_router_only_exposes_analyze_http_endpoint(monkeypatch):
    monkeypatch.setattr(
        akshare_client, "get_etf_spot_quotes", lambda: EtfSpotData(), raising=False
    )

    client = TestClient(app)

    assert client.get("/api/v1/strategies/market-structure/realtime").status_code == 404
    assert (
        client.get("/api/v1/strategies/market-structure/watch-points").status_code
        == 404
    )
    assert (
        client.get("/api/v1/strategies/market-structure/discipline-advice").status_code
        == 404
    )
    assert (
        client.get("/api/v1/strategies/market-structure/tool-context").status_code
        == 404
    )
    assert (
        client.get("/api/v1/strategies/market-structure/etfs/search").status_code == 404
    )


def test_analyze_market_structure_intraday_watch_returns_agent_bound_data(
    monkeypatch,
):
    monkeypatch.setattr(
        akshare_client,
        "get_etf_spot_quotes",
        lambda: EtfSpotData("-2.10", "-1.20"),
        raising=False,
    )

    response = TestClient(app).post(
        "/api/v1/strategies/analyze",
        json={"analyze_type": "market_structure_intraday_watch", "params": {}},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analyze_type"] == "market_structure_intraday_watch"
    assert data["strategy_code"] == "market_structure"
    assert data["strategy_name"] == "市场格局风向标"
    assert data["agent_code"] == "market_intraday_watch"
    assert data["agent_name"] == "盘中观察员"
    assert data["data"]["realtime"]["market_script"]["key"] == "rotation_other"
    assert [sector["label"] for sector in data["data"]["watch_points"]["sectors"]] == [
        "机器人",
        "生物医药",
    ]


def test_analyze_market_structure_intraday_watch_reuses_single_quote_query(
    monkeypatch,
):
    calls: list[str] = []

    def get_etf_spot_quotes():
        calls.append("called")
        return EtfSpotData("-2.10", "-1.20")

    monkeypatch.setattr(
        akshare_client,
        "get_etf_spot_quotes",
        get_etf_spot_quotes,
        raising=False,
    )

    response = TestClient(app).post(
        "/api/v1/strategies/analyze",
        json={"analyze_type": "market_structure_intraday_watch", "params": {}},
    )

    assert response.status_code == 200
    assert calls == ["called"]


def test_analyze_market_structure_discipline_advice_returns_agent_bound_data(
    monkeypatch,
):
    monkeypatch.setattr(
        akshare_client,
        "get_etf_spot_quotes",
        lambda: EtfSpotData("-4.02", "-4.11"),
        raising=False,
    )

    response = TestClient(app).post(
        "/api/v1/strategies/analyze",
        json={"analyze_type": "market_structure_discipline_advice", "params": {}},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analyze_type"] == "market_structure_discipline_advice"
    assert data["strategy_code"] == "market_structure"
    assert data["agent_code"] == "market_discipline_advisor"
    assert data["agent_name"] == "纪律风控官"
    assert data["data"]["discipline_advice"]["market_script"]["key"] == "rotation_other"
    assert data["data"]["discipline_advice"]["advice"]["risk_level"] == "high"


def test_analyze_rejects_unknown_analyze_type():
    response = TestClient(app).post(
        "/api/v1/strategies/analyze",
        json={"analyze_type": "unknown_strategy", "params": {}},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "unsupported analyze_type: unknown_strategy"


@pytest.mark.parametrize(
    ("domestic_change", "overseas_change", "script_key", "sector_labels"),
    [
        ("2.10", "-1.20", "domestic_story", ["国产半导体", "华为链"]),
        ("-1.20", "2.10", "overseas_earnings", ["海外算力链", "存储链"]),
        ("2.10", "1.20", "hard_tech_siphon", ["硬科技前排", "成交额核心 ETF"]),
        ("-2.10", "-1.20", "rotation_other", ["机器人", "生物医药"]),
    ],
)
def test_get_market_structure_watch_points_by_quadrant(
    monkeypatch,
    domestic_change,
    overseas_change,
    script_key,
    sector_labels,
):
    monkeypatch.setattr(
        akshare_client,
        "get_etf_spot_quotes",
        lambda: EtfSpotData(domestic_change, overseas_change),
        raising=False,
    )

    data = strategy_service.get_market_structure_watch_points().model_dump()

    assert data["market_script"]["key"] == script_key
    assert [sector["label"] for sector in data["sectors"]] == sector_labels
    for sector in data["sectors"]:
        assert sector["direction"] in {
            "strengthening",
            "weakening",
            "mixed",
            "no_data",
        }
        assert isinstance(sector["observation"], str)
        assert "observed_etfs" in sector
    assert "signals" not in data
    assert "execution_notes" not in data
    assert data["source"]["provider"] == "akshare.fund_etf_spot_em"
    assert data["source"]["update_time"] == "14:59:59"


def test_query_market_structure_watch_points_by_script_key_uses_realtime_quotes(
    monkeypatch,
):
    monkeypatch.setattr(
        akshare_client,
        "get_etf_spot_quotes",
        lambda: EtfSpotData(),
        raising=False,
    )

    data = strategy_service.get_market_structure_watch_points(
        "domestic_story"
    ).model_dump()

    assert data["market_script"] == {
        "key": "domestic_story",
        "label": "国产替代主线",
        "description": "国产硬科技线强、海外算力链弱，资金继续讲国产替代故事。",
    }
    assert [sector["label"] for sector in data["sectors"]] == [
        "国产半导体",
        "华为链",
    ]
    assert data["sectors"][0]["observed_etfs"][0]["etf_code"] == "588710"
    assert data["sectors"][0]["observed_etfs"][0]["line_key"] == "candidate"
    assert "588710" in data["source"]["etf_codes"]
    assert data["source"]["provider"] == "akshare.fund_etf_spot_em"


def test_watch_points_return_realtime_observation_results(monkeypatch):
    monkeypatch.setattr(
        akshare_client, "get_etf_spot_quotes", lambda: EtfSpotData(), raising=False
    )

    data = strategy_service.get_market_structure_watch_points(
        "rotation_other"
    ).model_dump()

    robot_sector = data["sectors"][0]
    medical_sector = data["sectors"][1]

    assert robot_sector["label"] == "机器人"
    assert robot_sector["direction"] == "strengthening"
    assert robot_sector["average_change_percent"] == 3.0
    assert robot_sector["total_turnover"] == 150000000.0
    assert "机器人 当前整体走强" in robot_sector["observation"]
    assert "516950 机器人ETF" in robot_sector["observation"]
    assert robot_sector["observed_etfs"][0]["etf_code"] == "516950"

    assert medical_sector["label"] == "生物医药"
    assert medical_sector["direction"] == "strengthening"
    assert medical_sector["observed_etfs"][0]["etf_code"] == "512170"


def test_discipline_advice_returns_dynamic_realtime_operation_plan(monkeypatch):
    monkeypatch.setattr(
        akshare_client,
        "get_etf_spot_quotes",
        lambda: EtfSpotData("-4.02", "-4.11"),
        raising=False,
    )

    data = strategy_service.get_market_structure_discipline_advice(
        "rotation_other"
    ).model_dump()

    assert data["market_script"]["key"] == "rotation_other"
    assert data["advice"]["action"] == "降低仓位"
    assert data["advice"]["risk_level"] == "high"
    assert (
        "588710 科创半导体设备ETF华泰柏瑞 -4.02%" in data["advice"]["evidence_quotes"]
    )
    assert "515880 通信ETF国泰 -4.11%" in data["advice"]["evidence_quotes"]
    assert "两条核心 ETF 同步走弱" in data["advice"]["trigger_conditions"]
    assert "任一核心 ETF 放量翻红并站稳" in data["advice"]["invalidation_conditions"]
    assert "21 日线不抵抗就走" in data["advice"]["risk_controls"]
    assert "跌破 60 日线后，只看是否形成小平台抵抗" in data["advice"]["risk_controls"]
    assert (
        "不抵抗且放量杀，等待破位后重新形成箱体或 34 日线修复"
        in data["advice"]["risk_controls"]
    )
    assert data["source"] == {
        "etf_codes": ["588710", "515880"],
        "update_time": "14:59:59",
        "provider": "akshare.fund_etf_spot_em",
    }


def test_search_strategy_etfs_by_keyword(monkeypatch):
    monkeypatch.setattr(
        akshare_client, "get_etf_spot_quotes", lambda: EtfSpotData(), raising=False
    )

    data = strategy_service.search_strategy_etfs("机器人", limit=5).model_dump()

    assert data["keyword"] == "机器人"
    assert data["total"] == 1
    assert data["items"][0]["etf_code"] == "516950"
    assert data["items"][0]["etf_name"] == "机器人ETF"
    assert data["items"][0]["change_percent"] == 3.0


def test_market_structure_tool_context_contains_rules_quotes_and_candidates(
    monkeypatch,
):
    monkeypatch.setattr(
        akshare_client,
        "get_etf_spot_quotes",
        lambda: EtfSpotData("-2.10", "-1.20"),
        raising=False,
    )

    data = strategy_service.get_market_structure_tool_context().model_dump()

    assert data["realtime"]["market_script"]["key"] == "rotation_other"
    assert [sector["label"] for sector in data["watch_points"]["sectors"]] == [
        "机器人",
        "生物医药",
    ]
    assert data["discipline_advice"]["advice"]["action"] == "降低仓位"
    assert data["discipline_advice"]["advice"]["risk_level"] == "high"
    assert (
        "两条核心 ETF 同步走弱"
        in data["discipline_advice"]["advice"]["trigger_conditions"]
    )
    assert (
        "515880 通信ETF国泰 -1.20%"
        in data["discipline_advice"]["advice"]["evidence_quotes"]
    )
    assert "机器人" in data["candidate_etfs"]
    assert data["candidate_etfs"]["机器人"]["items"][0]["etf_code"] == "516950"
    assert "生物医药" in data["candidate_etfs"]
    assert data["candidate_etfs"]["生物医药"]["items"][0]["etf_code"] == "512170"
