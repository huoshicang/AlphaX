import math
import random
import time
import json
import pandas as pd
import requests
from .logger import log
from utils import generate_cookie_string
from .enums import KlinePeriod, AdjustType
from .utils import convert_to_secid, kline_to_dataframe, to_eastmoney_secid

# ======================
# 1. 全局接口配置（原配置保留）
# ======================
HEADERS = {
    "cookie": "qgqp_b_id=a081e13cc5e6a01d01d0875c943caa2e; st_nvi=sw-unRDxP7fhDkghhPSc8-; st_si=85010178484468; websitepoptg_api_time=1775628577969; nid18=ddedcca6abccffb3545d5cf32f90c3ca; nid18_create_time=1775628577969; gviem=dS3I5LaCilRT6gJDbIDr; gviem_create_time=1775628577969; fullscreengg=1; fullscreengg2=1; wsc_checkuser_ok=1; st_pvi=55479826781385; st_sp=2026-04-08%2014%3A09%3A37; st_inirUrl=https%3A//cn.bing.com/; st_sn=8; st_psi=20260408140937-438714995153-1251114506; st_asi=delete"
}
USERAGENT = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/100.0.0.0"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 360SE"
]

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
# 辅助函数：生成 cb 参数
# ======================
def generate_cb_param():
    """生成 JSONP 回调参数，格式：jQuery{随机数字}_{秒级时间戳}"""
    random_num = str(random.randint(100000000000000000000, 999999999999999999999))
    timestamp = str(int(time.time() * 1000))
    return f"jQuery{random_num}_{timestamp}"


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
    # url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

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

    # 添加必选参数
    params["cb"] = generate_cb_param()
    params["_"] = str(int(time.time() * 1000))

    HEADERS["Referer"] = f"https://quote.eastmoney.com/{to_eastmoney_secid(code)}.html"
    HEADERS["User-Agent"] = random.choice(USERAGENT)
    HEADERS["cookie"] = generate_cookie_string()

    log.debug(f"请求索引: {rdn}")
    r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    r.raise_for_status()

    # 处理 JSONP 响应
    response_text = r.text
    # 提取 JSONP 回调中的 JSON 数据
    # 格式：jQuery351033499065011608153_1775714430675({...})
    start_idx = response_text.find('(')
    end_idx = response_text.rfind(')')
    if start_idx != -1 and end_idx != -1:
        json_str = response_text[start_idx + 1:end_idx]
        data = json.loads(json_str)
    else:
        data = {}

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
    return get_kline(code, period=KlinePeriod.MIN_15, **kwargs)


def get_30min(code: str, **kwargs):
    return get_kline(code, period=KlinePeriod.MIN_30, **kwargs)


def get_60min(code: str, **kwargs):
    return get_kline(code, period=KlinePeriod.MIN_60, **kwargs)


def get_day(code: str, **kwargs):
    return get_kline(code, period=KlinePeriod.DAY, **kwargs)


def get_week(code: str, **kwargs):
    return get_kline(code, period=KlinePeriod.WEEK, **kwargs)


def get_month(code: str, **kwargs):
    return get_kline(code, period=KlinePeriod.MONTH, **kwargs)