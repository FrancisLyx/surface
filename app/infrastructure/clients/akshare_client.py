import json
import threading
import time
import urllib.request

import akshare as ak

ETF_SPOT_QUOTES_CACHE_TTL_SECONDS = 20.0
_etf_spot_quotes_cache = None
_etf_spot_quotes_cache_expires_at = 0.0
_etf_spot_quotes_cache_lock = threading.Lock()


def get_fund_names():
    return ak.fund_name_em().fillna("")


def get_fund_detail(symbol: str):
    return ak.fund_individual_basic_info_xq(symbol=symbol).fillna("")


def get_fund_estimations(category: str = "全部"):
    return ak.fund_value_estimation_em(symbol=category).fillna("")


def get_etf_spot_quotes(force_refresh: bool = False):
    global _etf_spot_quotes_cache, _etf_spot_quotes_cache_expires_at

    now = time.monotonic()
    if (
        not force_refresh
        and _etf_spot_quotes_cache is not None
        and now < _etf_spot_quotes_cache_expires_at
    ):
        return _etf_spot_quotes_cache

    with _etf_spot_quotes_cache_lock:
        now = time.monotonic()
        if (
            not force_refresh
            and _etf_spot_quotes_cache is not None
            and now < _etf_spot_quotes_cache_expires_at
        ):
            return _etf_spot_quotes_cache

        _etf_spot_quotes_cache = ak.fund_etf_spot_em().fillna("")
        _etf_spot_quotes_cache_expires_at = now + ETF_SPOT_QUOTES_CACHE_TTL_SECONDS
        return _etf_spot_quotes_cache


def clear_etf_spot_quotes_cache() -> None:
    global _etf_spot_quotes_cache, _etf_spot_quotes_cache_expires_at

    with _etf_spot_quotes_cache_lock:
        _etf_spot_quotes_cache = None
        _etf_spot_quotes_cache_expires_at = 0.0


def get_fund_realtime_estimation(symbol: str) -> dict[str, str]:
    url = f"https://fundgz.1234567.com.cn/js/{symbol}.js?rt={int(time.time() * 1000)}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://fund.eastmoney.com/",
        },
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        text = response.read().decode("utf-8", errors="replace").strip()

    prefix = "jsonpgz("
    suffix = ");"
    if not text.startswith(prefix) or not text.endswith(suffix):
        raise ValueError("unexpected fund realtime estimation response")

    return json.loads(text[len(prefix) : -len(suffix)])


def get_open_fund_daily():
    return ak.fund_open_fund_daily_em().fillna("")


def get_open_fund_rank(category: str = "全部"):
    return ak.fund_open_fund_rank_em(symbol=category).fillna("")


def get_fund_fee(symbol: str, indicator: str):
    return ak.fund_fee_em(symbol=symbol, indicator=indicator).fillna("")


def get_fund_portfolio_hold(symbol: str, year: str):
    return ak.fund_portfolio_hold_em(symbol=symbol, date=year).fillna("")


def get_fund_industry_allocation(symbol: str, year: str):
    return ak.fund_portfolio_industry_allocation_em(symbol=symbol, date=year).fillna("")


def get_fund_nav_trend(symbol: str):
    return ak.fund_open_fund_info_em(
        symbol=symbol, indicator="单位净值走势", period="成立来"
    ).fillna("")
