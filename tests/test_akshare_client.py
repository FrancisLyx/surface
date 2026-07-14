from app.infrastructure.clients import akshare_client


class FakeAkshareData:
    def __init__(self, value: str) -> None:
        self.value = value

    def fillna(self, value):
        return self


def test_get_etf_spot_quotes_reuses_short_ttl_cache(monkeypatch):
    calls: list[str] = []
    now = 1000.0

    def fake_fund_etf_spot_em():
        calls.append("called")
        return FakeAkshareData(f"data-{len(calls)}")

    monkeypatch.setattr(akshare_client.ak, "fund_etf_spot_em", fake_fund_etf_spot_em)
    monkeypatch.setattr(akshare_client.time, "monotonic", lambda: now)
    akshare_client.clear_etf_spot_quotes_cache()

    first = akshare_client.get_etf_spot_quotes()
    second = akshare_client.get_etf_spot_quotes()

    assert first is second
    assert first.value == "data-1"
    assert len(calls) == 1


def test_get_etf_spot_quotes_refreshes_after_ttl(monkeypatch):
    calls: list[str] = []
    current_time = {"value": 1000.0}

    def fake_fund_etf_spot_em():
        calls.append("called")
        return FakeAkshareData(f"data-{len(calls)}")

    monkeypatch.setattr(akshare_client.ak, "fund_etf_spot_em", fake_fund_etf_spot_em)
    monkeypatch.setattr(akshare_client.time, "monotonic", lambda: current_time["value"])
    akshare_client.clear_etf_spot_quotes_cache()

    first = akshare_client.get_etf_spot_quotes()
    current_time["value"] += akshare_client.ETF_SPOT_QUOTES_CACHE_TTL_SECONDS + 1
    second = akshare_client.get_etf_spot_quotes()

    assert first.value == "data-1"
    assert second.value == "data-2"
    assert len(calls) == 2
