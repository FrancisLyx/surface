from app.modules.fund.schemas import (
    FundDetailItem,
    FundEstimationItem,
    FundProfileRequest,
    FundProfileResponse,
    FundValueRequest,
    FundValueResponse,
)
from app.modules.ai import service as ai_fund_service
from app.modules.fund import service as fund_service
from app.modules.fund.public import FundQueryFacade


def test_summarize_fund_builds_professional_analysis_prompt(monkeypatch):
    captured: dict[str, str] = {}

    def fake_get_fund_value(request: FundValueRequest):
        assert request.fund_code == "110010"
        assert request.source == "auto"
        return FundValueResponse(
            fund_code="110010",
            source="estimation",
            estimation=FundEstimationItem(
                code="110010",
                name="易方达价值成长混合",
                estimate_date="2026-06-30",
                estimated_nav="2.9221",
                estimated_growth_rate="4.32%",
                published_date="2026-06-29",
                published_nav="2.8012",
                published_growth_rate="-2.24%",
                estimate_deviation="",
                previous_nav_date="2026-06-29",
                previous_nav="2.8012",
            ),
            latest_nav=None,
        )

    def fake_get_fund_profile(request: FundProfileRequest):
        assert request.symbol == "110010"
        return FundProfileResponse(
            symbol="110010",
            year=request.year,
            basic_info=[
                FundDetailItem(item="基金名称", value="易方达价值成长混合"),
                FundDetailItem(item="基金类型", value="混合型"),
                FundDetailItem(item="基金经理", value="张三"),
            ],
            fee_sections=[],
            holdings=[
                {"股票名称": "贵州茅台", "占净值比例": "8.12%"},
                {"股票名称": "宁德时代", "占净值比例": "6.20%"},
            ],
            industry_allocations=[
                {"行业类别": "食品饮料", "占净值比例": "18.00%"},
                {"行业类别": "电力设备", "占净值比例": "12.00%"},
            ],
        )

    def fake_get_fund_nav_trend_summary(fund_code: str):
        assert fund_code == "110010"
        return {
            "period": "近一年",
            "start_date": "2025-06-30",
            "end_date": "2026-06-30",
            "start_nav": "2.5000",
            "end_nav": "2.9221",
            "period_return": "16.88%",
            "max_drawdown": "-8.20%",
            "latest_points": [
                {"净值日期": "2026-06-28", "单位净值": "2.8500"},
                {"净值日期": "2026-06-30", "单位净值": "2.9221"},
            ],
        }

    def fake_chat(prompt: str):
        captured["prompt"] = prompt
        return "AI analysis"

    monkeypatch.setattr(
        FundQueryFacade,
        "get_fund_value",
        lambda self, request: fake_get_fund_value(request),
    )
    monkeypatch.setattr(
        FundQueryFacade,
        "get_fund_profile",
        lambda self, request: fake_get_fund_profile(request),
    )
    monkeypatch.setattr(
        FundQueryFacade,
        "get_fund_nav_trend_summary",
        lambda self, fund_code: fake_get_fund_nav_trend_summary(fund_code),
    )
    monkeypatch.setattr(ai_fund_service, "chat", fake_chat)

    assert ai_fund_service.summarize_fund(" 110010 ") == "AI analysis"

    prompt = captured["prompt"]
    assert "基金画像" in prompt
    assert "行业/板块" in prompt
    assert "近一年" in prompt
    assert "当日操作建议" in prompt
    assert "收盘前操作" in prompt
    assert "历史信息" in prompt
    assert "当日估值信息" in prompt
    assert "盘后净值" in prompt
    assert "只用于复核" in prompt
    assert "动作结论" in prompt
    assert "仓位建议" in prompt
    assert "触发条件" in prompt
    assert "盘后复核" in prompt
    assert "估算日期与公布日期不一致" in prompt
    assert "风险提示" in prompt
    assert "免责声明" in prompt
    assert "易方达价值成长混合" in prompt
    assert "贵州茅台" in prompt
    assert "食品饮料" in prompt
    assert "16.88%" in prompt


def test_get_fund_nav_trend_summary_calculates_recent_year_metrics(monkeypatch):
    class FundNavTrendData:
        def fillna(self, value):
            return self

        def iterrows(self):
            rows = [
                {"净值日期": "2025-06-30", "单位净值": "1.0000"},
                {"净值日期": "2025-09-30", "单位净值": "1.2000"},
                {"净值日期": "2025-12-31", "单位净值": "0.9000"},
                {"净值日期": "2026-06-30", "单位净值": "1.1000"},
            ]
            yield from enumerate(rows)

    monkeypatch.setattr(
        fund_service.akshare_client,
        "get_fund_nav_trend",
        lambda symbol: FundNavTrendData(),
        raising=False,
    )

    summary = fund_service.get_fund_nav_trend_summary("110010")

    assert summary["period"] == "近一年"
    assert summary["start_date"] == "2025-06-30"
    assert summary["end_date"] == "2026-06-30"
    assert summary["period_return"] == "10.00%"
    assert summary["max_drawdown"] == "-25.00%"
    assert summary["latest_points"][-1] == {
        "净值日期": "2026-06-30",
        "单位净值": "1.1000",
    }
