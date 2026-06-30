import akshare as ak


def get_fund_names():
    return ak.fund_name_em().fillna("")


def get_fund_detail(symbol: str):
    return ak.fund_individual_basic_info_xq(symbol=symbol).fillna("")


def get_fund_estimations(category: str = "全部"):
    return ak.fund_value_estimation_em(symbol=category).fillna("")


def get_open_fund_daily():
    return ak.fund_open_fund_daily_em().fillna("")
