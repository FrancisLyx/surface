from fastapi.testclient import TestClient

from app.main import app
from app.clients import akshare_client


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
        "/funds/search",
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

    response = TestClient(app).post("/funds/detail", json={"symbol": "000001"})

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

    response = TestClient(app).post(
        "/funds/estimations/search",
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
                "published_nav": "---",
                "published_growth_rate": "---",
                "estimate_deviation": "---",
                "previous_nav_date": "2026-06-26",
                "previous_nav": "1.2200",
            }
        ],
    }


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

    response = TestClient(app).post("/funds/estimation", json={"symbol": "000001"})

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
        "/funds/value",
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
        "/funds/value",
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
