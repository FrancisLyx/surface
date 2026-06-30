from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.clients import akshare_client
from app.core.security import get_current_user


class EmptyDailyNavData:
    def fillna(self, value):
        return self

    @property
    def columns(self):
        return ["基金代码", "基金简称"]

    def iterrows(self):
        yield from enumerate([])


@pytest.fixture(autouse=True)
def override_current_user():
    app.dependency_overrides[get_current_user] = lambda: object()
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_list_funds_filters_by_keyword(monkeypatch):
    class FundNameData:
        def fillna(self, value):
            return self

        def iterrows(self):
            rows = [
                {
                    "基金代码": "000001",
                    "拼音缩写": "HXCZHH",
                    "基金简称": "华夏成长混合",
                    "基金类型": "混合型-灵活",
                    "拼音全称": "HUAXIACHENGZHANGHUNHE",
                },
                {
                    "基金代码": "000003",
                    "拼音缩写": "ZHKZZZQA",
                    "基金简称": "中海可转债债券A",
                    "基金类型": "债券型-混合二级",
                    "拼音全称": "ZHONGHAIKEZHUANZHAIZHAIQUANA",
                },
            ]
            yield from enumerate(rows)

    monkeypatch.setattr(akshare_client, "get_fund_names", lambda: FundNameData())

    response = TestClient(app).post(
        "/api/v1/funds/list",
        json={"keyword": "华夏", "page": 1, "page_size": 10},
    )

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["message"] == "success"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert response.json()["data"] == {
        "page": 1,
        "page_size": 10,
        "total": 1,
        "pages": 1,
        "items": [
            {
                "code": "000001",
                "abbreviation": "HXCZHH",
                "name": "华夏成长混合",
                "fund_type": "混合型-灵活",
                "pinyin": "HUAXIACHENGZHANGHUNHE",
            }
        ],
    }


def test_get_fund_detail(monkeypatch):
    class FundDetailData:
        def fillna(self, value):
            return self

        def iterrows(self):
            rows = [
                {"item": "基金代码", "value": "000001"},
                {"item": "基金名称", "value": "华夏成长混合"},
            ]
            yield from enumerate(rows)

    monkeypatch.setattr(akshare_client, "get_fund_detail", lambda symbol: FundDetailData())

    response = TestClient(app).post("/api/v1/funds/detail", json={"symbol": "000001"})

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["message"] == "success"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert response.json()["data"] == {
        "symbol": "000001",
        "items": [
            {"item": "基金代码", "value": "000001"},
            {"item": "基金名称", "value": "华夏成长混合"},
        ],
    }


def test_list_fund_estimations_filters_by_keyword(monkeypatch):
    class FundEstimationData:
        def fillna(self, value):
            return self

        @property
        def columns(self):
            return [
                "序号",
                "基金代码",
                "基金名称",
                "2026-06-29-估算数据-估算值",
                "2026-06-29-估算数据-估算增长率",
                "2026-06-29-公布数据-单位净值",
                "2026-06-29-公布数据-日增长率",
                "估算偏差",
                "2026-06-26-单位净值",
            ]

        def iterrows(self):
            rows = [
                {
                    "基金代码": "000001",
                    "基金名称": "华夏成长混合",
                    "2026-06-29-估算数据-估算值": "1.2345",
                    "2026-06-29-估算数据-估算增长率": "1.23%",
                    "2026-06-29-公布数据-单位净值": "---",
                    "2026-06-29-公布数据-日增长率": "---",
                    "估算偏差": "---",
                    "2026-06-26-单位净值": "1.2200",
                },
                {
                    "基金代码": "000003",
                    "基金名称": "中海可转债债券A",
                    "2026-06-29-估算数据-估算值": "1.0001",
                    "2026-06-29-估算数据-估算增长率": "0.01%",
                    "2026-06-29-公布数据-单位净值": "---",
                    "2026-06-29-公布数据-日增长率": "---",
                    "估算偏差": "---",
                    "2026-06-26-单位净值": "1.0000",
                },
            ]
            yield from enumerate(rows)

    monkeypatch.setattr(
        akshare_client,
        "get_fund_estimations",
        lambda category="全部": FundEstimationData(),
    )
    monkeypatch.setattr(akshare_client, "get_open_fund_daily", lambda: EmptyDailyNavData())

    response = TestClient(app).post(
        "/api/v1/funds/estimations/search",
        json={"keyword": "华夏", "page": 1, "page_size": 10},
    )

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["message"] == "success"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert response.json()["data"] == {
        "page": 1,
        "page_size": 10,
        "total": 1,
        "pages": 1,
        "items": [
            {
                "code": "000001",
                "name": "华夏成长混合",
                "estimate_date": "2026-06-29",
                "estimated_nav": "1.2345",
                "estimated_growth_rate": "1.23%",
                "published_date": "2026-06-29",
                "published_nav": "---",
                "published_growth_rate": "---",
                "estimate_deviation": "---",
                "previous_nav_date": "2026-06-26",
                "previous_nav": "1.2200",
            }
        ],
    }


def test_list_fund_estimations_omits_deviation_when_published_date_differs(monkeypatch):
    class FundEstimationData:
        def fillna(self, value):
            return self

        @property
        def columns(self):
            return [
                "基金代码",
                "基金名称",
                "2026-06-30-估算数据-估算值",
                "2026-06-30-估算数据-估算增长率",
                "2026-06-29-公布数据-单位净值",
                "2026-06-29-公布数据-日增长率",
                "估算偏差",
                "2026-06-29-单位净值",
            ]

        def iterrows(self):
            rows = [
                {
                    "基金代码": "000001",
                    "基金名称": "华夏成长混合",
                    "2026-06-30-估算数据-估算值": "1.2345",
                    "2026-06-30-估算数据-估算增长率": "1.23%",
                    "2026-06-29-公布数据-单位净值": "1.2200",
                    "2026-06-29-公布数据-日增长率": "0.33%",
                    "估算偏差": "0.88%",
                    "2026-06-29-单位净值": "1.2200",
                }
            ]
            yield from enumerate(rows)

    monkeypatch.setattr(
        akshare_client,
        "get_fund_estimations",
        lambda category="全部": FundEstimationData(),
    )
    monkeypatch.setattr(akshare_client, "get_open_fund_daily", lambda: EmptyDailyNavData())

    class DailyNavData:
        def fillna(self, value):
            return self

        @property
        def columns(self):
            return [
                "基金代码",
                "基金简称",
                "2026-06-30-单位净值",
                "2026-06-30-累计净值",
                "2026-06-29-单位净值",
                "2026-06-29-累计净值",
                "日增长值",
                "日增长率",
                "申购状态",
                "赎回状态",
                "手续费",
            ]

        def iterrows(self):
            rows = [
                {
                    "基金代码": "000001",
                    "基金简称": "华夏成长混合",
                    "2026-06-30-单位净值": "",
                    "2026-06-30-累计净值": "",
                    "2026-06-29-单位净值": "1.2200",
                    "2026-06-29-累计净值": "1.2200",
                    "日增长值": "",
                    "日增长率": "0.33%",
                    "申购状态": "开放申购",
                    "赎回状态": "开放赎回",
                    "手续费": "0.15%",
                }
            ]
            yield from enumerate(rows)

    monkeypatch.setattr(akshare_client, "get_open_fund_daily", lambda: DailyNavData())

    response = TestClient(app).post(
        "/api/v1/funds/estimations/search",
        json={"keyword": "华夏", "page": 1, "page_size": 10},
    )

    assert response.status_code == 200
    item = response.json()["data"]["items"][0]
    assert item["estimate_date"] == "2026-06-30"
    assert item["published_date"] == "2026-06-29"
    assert item["estimate_deviation"] == ""


def test_get_fund_estimation_by_symbol(monkeypatch):
    class FundEstimationData:
        def fillna(self, value):
            return self

        @property
        def columns(self):
            return [
                "基金代码",
                "基金名称",
                "2026-06-29-估算数据-估算值",
                "2026-06-29-估算数据-估算增长率",
                "2026-06-29-公布数据-单位净值",
                "2026-06-29-公布数据-日增长率",
                "估算偏差",
                "2026-06-26-单位净值",
            ]

        def iterrows(self):
            rows = [
                {
                    "基金代码": "000001",
                    "基金名称": "华夏成长混合",
                    "2026-06-29-估算数据-估算值": "1.2345",
                    "2026-06-29-估算数据-估算增长率": "1.23%",
                    "2026-06-29-公布数据-单位净值": "---",
                    "2026-06-29-公布数据-日增长率": "---",
                    "估算偏差": "---",
                    "2026-06-26-单位净值": "1.2200",
                }
            ]
            yield from enumerate(rows)

    monkeypatch.setattr(
        akshare_client,
        "get_fund_estimations",
        lambda category="全部": FundEstimationData(),
    )

    response = TestClient(app).post("/api/v1/funds/estimation", json={"symbol": "000001"})

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["message"] == "success"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert response.json()["data"]["code"] == "000001"
    assert response.json()["data"]["estimate_date"] == "2026-06-29"


def test_post_fund_value_returns_estimation_source(monkeypatch):
    class FundEstimationData:
        def fillna(self, value):
            return self

        @property
        def columns(self):
            return [
                "基金代码",
                "基金名称",
                "2026-06-29-估算数据-估算值",
                "2026-06-29-估算数据-估算增长率",
                "2026-06-29-公布数据-单位净值",
                "2026-06-29-公布数据-日增长率",
                "估算偏差",
                "2026-06-26-单位净值",
            ]

        def iterrows(self):
            rows = [
                {
                    "基金代码": "000001",
                    "基金名称": "华夏成长混合",
                    "2026-06-29-估算数据-估算值": "1.2345",
                    "2026-06-29-估算数据-估算增长率": "1.23%",
                    "2026-06-29-公布数据-单位净值": "---",
                    "2026-06-29-公布数据-日增长率": "---",
                    "估算偏差": "---",
                    "2026-06-26-单位净值": "1.2200",
                }
            ]
            yield from enumerate(rows)

    monkeypatch.setattr(
        akshare_client,
        "get_fund_estimations",
        lambda category="全部": FundEstimationData(),
    )

    response = TestClient(app).post(
        "/api/v1/funds/value",
        json={"fund_code": "000001", "source": "estimation"},
    )

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["message"] == "success"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert response.json()["data"]["fund_code"] == "000001"
    assert response.json()["data"]["source"] == "estimation"
    assert response.json()["data"]["estimation"]["estimated_nav"] == "1.2345"
    assert response.json()["data"]["latest_nav"] is None


def test_post_fund_value_auto_falls_back_to_daily_nav(monkeypatch):
    class EmptyEstimationData:
        def fillna(self, value):
            return self

        @property
        def columns(self):
            return ["基金代码", "基金名称"]

        def iterrows(self):
            yield from enumerate([])

    class DailyNavData:
        def fillna(self, value):
            return self

        @property
        def columns(self):
            return [
                "基金代码",
                "基金简称",
                "2026-06-29-单位净值",
                "2026-06-29-累计净值",
                "2026-06-26-单位净值",
                "2026-06-26-累计净值",
                "日增长值",
                "日增长率",
                "申购状态",
                "赎回状态",
                "手续费",
            ]

        def iterrows(self):
            rows = [
                {
                    "基金代码": "110029",
                    "基金简称": "易方达科讯混合",
                    "2026-06-29-单位净值": "",
                    "2026-06-29-累计净值": "",
                    "2026-06-26-单位净值": "4.5973",
                    "2026-06-26-累计净值": "17.0481",
                    "日增长值": "",
                    "日增长率": "-3.62%",
                    "申购状态": "开放申购",
                    "赎回状态": "开放赎回",
                    "手续费": "0.15%",
                }
            ]
            yield from enumerate(rows)

    monkeypatch.setattr(
        akshare_client,
        "get_fund_estimations",
        lambda category="全部": EmptyEstimationData(),
    )
    monkeypatch.setattr(akshare_client, "get_open_fund_daily", lambda: DailyNavData())

    response = TestClient(app).post(
        "/api/v1/funds/value",
        json={"fund_code": "110029", "source": "auto"},
    )

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["message"] == "success"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert response.json()["data"]["fund_code"] == "110029"
    assert response.json()["data"]["source"] == "daily"
    assert response.json()["data"]["estimation"] is None
    assert response.json()["data"]["latest_nav"] == {
        "code": "110029",
        "name": "易方达科讯混合",
        "nav_date": "2026-06-26",
        "unit_nav": "4.5973",
        "accumulated_nav": "17.0481",
        "daily_growth_value": "",
        "daily_growth_rate": "-3.62%",
        "subscription_status": "开放申购",
        "redemption_status": "开放赎回",
        "fee": "0.15%",
    }


def test_list_fund_rank_filters_by_keyword_and_category(monkeypatch):
    class FundRankData:
        def fillna(self, value):
            return self

        def iterrows(self):
            rows = [
                {
                    "基金代码": "000001",
                    "基金简称": "华夏成长混合",
                    "基金类型": "混合型",
                    "单位净值": "1.2345",
                    "累计净值": "3.4567",
                    "日增长率": "1.23%",
                    "近1周": "2.34%",
                    "近1月": "3.45%",
                    "近3月": "4.56%",
                    "近6月": "5.67%",
                    "近1年": "6.78%",
                    "今年来": "7.89%",
                    "成立来": "88.88%",
                    "手续费": "0.15%",
                },
                {
                    "基金代码": "000003",
                    "基金简称": "中海可转债债券A",
                    "基金类型": "债券型",
                    "单位净值": "1.0001",
                    "累计净值": "1.1001",
                    "日增长率": "0.01%",
                    "近1周": "0.02%",
                    "近1月": "0.03%",
                    "近3月": "0.04%",
                    "近6月": "0.05%",
                    "近1年": "0.06%",
                    "今年来": "0.07%",
                    "成立来": "0.08%",
                    "手续费": "0.10%",
                },
            ]
            yield from enumerate(rows)

    captured_categories = []
    monkeypatch.setattr(
        akshare_client,
        "get_open_fund_rank",
        lambda category="全部": captured_categories.append(category) or FundRankData(),
    )

    response = TestClient(app).post(
        "/api/v1/funds/rank",
        json={"category": "混合型", "keyword": "华夏", "page": 1, "page_size": 10},
    )

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert captured_categories == ["混合型"]
    assert response.json()["data"] == {
        "page": 1,
        "page_size": 10,
        "total": 1,
        "pages": 1,
        "items": [
            {
                "code": "000001",
                "name": "华夏成长混合",
                "fund_type": "混合型",
                "unit_nav": "1.2345",
                "accumulated_nav": "3.4567",
                "daily_growth_rate": "1.23%",
                "weekly_growth_rate": "2.34%",
                "monthly_growth_rate": "3.45%",
                "quarterly_growth_rate": "4.56%",
                "half_year_growth_rate": "5.67%",
                "yearly_growth_rate": "6.78%",
                "current_year_growth_rate": "7.89%",
                "since_inception_growth_rate": "88.88%",
                "fee": "0.15%",
            }
        ],
    }


def test_get_fund_profile_returns_aggregated_sections_when_child_query_fails(monkeypatch):
    class FundDetailData:
        def fillna(self, value):
            return self

        def iterrows(self):
            rows = [
                {"item": "基金名称", "value": "华夏成长混合"},
                {"item": "基金类型", "value": "混合型"},
            ]
            yield from enumerate(rows)

    class FeeData:
        def fillna(self, value):
            return self

        def iterrows(self):
            rows = [{"费用类型": "申购金额<100万", "费率": "0.15%"}]
            yield from enumerate(rows)

    class HoldingData:
        def fillna(self, value):
            return self

        def iterrows(self):
            rows = [
                {
                    "股票代码": "600519",
                    "股票名称": "贵州茅台",
                    "占净值比例": "8.88%",
                    "持股数": "10000",
                    "持仓市值": "18000000",
                }
            ]
            yield from enumerate(rows)

    monkeypatch.setattr(akshare_client, "get_fund_detail", lambda symbol: FundDetailData())
    monkeypatch.setattr(akshare_client, "get_fund_fee", lambda symbol, indicator: FeeData())
    monkeypatch.setattr(akshare_client, "get_fund_portfolio_hold", lambda symbol, year: HoldingData())

    def raise_industry_error(symbol, year):
        raise RuntimeError("industry source down")

    monkeypatch.setattr(akshare_client, "get_fund_industry_allocation", raise_industry_error)

    response = TestClient(app).post(
        "/api/v1/funds/profile",
        json={"symbol": "000001", "year": "2024"},
    )

    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert response.json()["data"] == {
        "symbol": "000001",
        "year": "2024",
        "basic_info": [
            {"item": "基金名称", "value": "华夏成长混合"},
            {"item": "基金类型", "value": "混合型"},
        ],
        "fee_sections": [
            {
                "title": "申购费率（前端）",
                "rows": [{"费用类型": "申购金额<100万", "费率": "0.15%"}],
            },
            {
                "title": "赎回费率",
                "rows": [{"费用类型": "申购金额<100万", "费率": "0.15%"}],
            },
            {
                "title": "运作费用",
                "rows": [{"费用类型": "申购金额<100万", "费率": "0.15%"}],
            },
        ],
        "holdings": [
            {
                "股票代码": "600519",
                "股票名称": "贵州茅台",
                "占净值比例": "8.88%",
                "持股数": "10000",
                "持仓市值": "18000000",
            }
        ],
        "industry_allocations": [],
    }
