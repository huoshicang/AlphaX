import math
import random
import requests
import pandas as pd
from .enums import KlinePeriod, AdjustType
from .utils import convert_to_secid, kline_to_dataframe, to_eastmoney_secid

# ======================
# 1. 全局接口配置（原配置保留）
# ======================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
}

# ======================
# 2. ✅ 抽离：全局公共参数默认值（所有函数复用）
# 后续修改默认参数，只改这里！
# ======================
# K线/复权默认值
DEFAULT_PERIOD = KlinePeriod.DAY
DEFAULT_ADJUST_TYPE = AdjustType.bfq
# 时间范围默认值
DEFAULT_BEGIN_DATE = "20100101"
DEFAULT_END_DATE = "20500101"
# 请求超时默认值
DEFAULT_TIMEOUT = 10.0
# 数据保存默认目录
DEFAULT_SAVE_DIR = "./stock_data"

# ======================
# 3. ✅ 抽离：固定请求参数（接口固定不变的参数）
# ======================
BASE_REQUEST_PARAMS = {
    "fields1": "f1,f2,f3,f4,f5,f6",
    "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
    "ut": "7eea3edcaed734bea9cbfc24409ed989",
    "smplmt": 1000000,
    "lmt": 1000000,
}

# ======================
# 核心K线函数（使用抽离的公共默认值）
# ======================
def get_kline(
    code: str,
    period: KlinePeriod = DEFAULT_PERIOD,
    adjust_type: AdjustType = DEFAULT_ADJUST_TYPE,
    begin_date: str = DEFAULT_BEGIN_DATE,
    end_date: str = DEFAULT_END_DATE,
    last_n_records: int = None,
    to_df: bool = False,
    timeout: float = DEFAULT_TIMEOUT
):
    rdn = str(math.floor(random.random() * 99 + 1))
    url = 'http://' + rdn + '.push2his.eastmoney.com/api/qt/stock/kline/get'

    secid = convert_to_secid(code)

    # 合并基础参数 + 动态参数
    params = {
        **BASE_REQUEST_PARAMS,
        "klt": int(period),
        "fqt": int(adjust_type),
        "secid": secid,
        "beg": begin_date,
        "end": end_date,
    }

    # 处理「仅获取最后N条」逻辑
    if last_n_records:
        params["lmt"] = last_n_records
        del params["beg"]
        del params["smplmt"]

    # HEADERS["Referer"] = f"https://quote.eastmoney.com/{to_eastmoney_secid(code)}.html"

    print(f"请求索引: {rdn}")
    r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    klines = data.get("data", {}).get("klines", [])
    if not klines:
        return pd.DataFrame() if to_df else data

    return kline_to_dataframe(klines, code) if to_df else data

# ======================
# 快捷函数（极简写法，无冗余代码）
# 仅指定周期，其余参数全部继承公共默认值
# ======================
def get_5min(code: str, **kwargs):
    return get_kline(code, period=KlinePeriod.MIN_5, **kwargs)

def get_15min(code: str, **kwargs):
    return get_kline(code, period=KlinePeriod.MIN_15,** kwargs)

def get_30min(code: str, **kwargs):
    return get_kline(code, period=KlinePeriod.MIN_30, **kwargs)

def get_60min(code: str,** kwargs):
    return get_kline(code, period=KlinePeriod.MIN_60, **kwargs)

def get_day(code: str, **kwargs):
    return get_kline(code, period=KlinePeriod.DAY,** kwargs)

def get_week(code: str, **kwargs):
    return get_kline(code, period=KlinePeriod.WEEK, **kwargs)

def get_month(code: str,** kwargs):
    return get_kline(code, period=KlinePeriod.MONTH, **kwargs)