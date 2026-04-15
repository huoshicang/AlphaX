#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富股票K线数据获取模块

该模块提供了从东方财富API获取股票K线数据的功能，支持不同周期和复权类型的数据获取。
"""

import math
import random
import time
import pandas as pd
import requests
from dfcf.enums import AdjustType, KlinePeriod
from utils.logger import log
from cooike import generate_cookie_string
from utils.transition_secid import convert_to_secid, to_eastmoney_secid
from kline_to_dataframe import kline_to_dataframe

# ======================
# 全局配置
# ======================
# 请求头信息
HEADERS = {
    "cookie": "qgqp_b_id=a081e13cc5e6a01d01d0875c943caa2e; st_nvi=sw-unRDxP7fhDkghhPSc8-; st_si=85010178484468; websitepoptg_api_time=1775628577969; nid18=ddedcca6abccffb3545d5cf32f90c3ca; nid18_create_time=1775628577969; gviem=dS3I5LaCilRT6gJDbIDr; gviem_create_time=1775628577969; fullscreengg=1; fullscreengg2=1; wsc_checkuser_ok=1; st_pvi=55479826781385; st_sp=2026-04-08%2014%3A09%3A37; st_inirUrl=https%3A//cn.bing.com/; st_sn=8; st_psi=20260408140937-438714995153-1251114506; st_asi=delete"
}

# User-Agent列表，用于随机选择
USERAGENT = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/100.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 360SE"
]

# ======================
# 固定请求参数
# ======================
BASE_REQUEST_PARAMS = {
    "fields1": "f1,f2,f3,f4,f5,f6",  # 基础字段
    "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",  # K线字段
    "ut": "7eea3edcaed734bea9cbfc24409ed989",  # 加密参数
    "smplmt": 1000000,  # 采样限制
    "lmt": 1000000,  # 数据限制
}


def get_stock_dfcf(
        code: str,
        period: KlinePeriod = KlinePeriod['day'],
        adjust: AdjustType = AdjustType['qfq'],
        begin_date: str = "20100101",
        end_date: str = "20500101",
        last_n_records: int = None,
        to_df: bool = True,
        timeout: float = 10.0
):
    """
    获取股票K线数据

    Args:
        code (str): 股票代码，如 '600000' 或 '000001'
        period (KlinePeriod): K线周期，默认为日线
        adjust (AdjustType): 复权类型，默认为前复权
        begin_date (str): 开始日期，格式为 'YYYYMMDD'，默认为 '20100101'
        end_date (str): 结束日期，格式为 'YYYYMMDD'，默认为 '20500101'
        last_n_records (int, optional): 仅获取最后N条记录，优先级高于日期范围
        to_df (bool): 是否返回DataFrame，默认为True
        timeout (float): 请求超时时间，默认为10.0秒

    Returns:
        pd.DataFrame or list: 如果to_df为True，返回DataFrame；否则返回原始K线数据列表
    """
    # 生成随机请求索引
    rdn = str(math.floor(random.random() * 99 + 1))
    # 构建请求URL
    url = f'http://{rdn}.push2his.eastmoney.com/api/qt/stock/kline/get'

    # 转换股票代码为secid
    secid = convert_to_secid(code)

    # 合并基础参数和动态参数
    params = {
        **BASE_REQUEST_PARAMS,
        "klt": int(period),  # K线周期
        "fqt": int(adjust),  # 复权类型
        "secid": secid,  # 股票ID
        "beg": begin_date,  # 开始日期
        "end": end_date,  # 结束日期
    }

    # 处理「仅获取最后N条」逻辑
    if last_n_records:
        params["lmt"] = last_n_records
        del params["beg"]  # 移除开始日期
        del params["smplmt"]  # 移除采样限制

    # 添加时间戳参数
    params["_"] = str(int(time.time() * 1000))

    # 更新请求头
    HEADERS["Referer"] = f"https://quote.eastmoney.com/{to_eastmoney_secid(code)}.html"
    HEADERS["User-Agent"] = random.choice(USERAGENT)
    HEADERS["cookie"] = generate_cookie_string()

    # 发送请求
    log.debug(f"请求索引: {rdn}")
    r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    r.raise_for_status()  # 检查请求是否成功

    # 解析响应数据
    klines = r.json().get("data", {}).get("klines", [])

    # 处理空数据情况
    if not klines:
        return pd.DataFrame() if to_df else {}

    # 返回数据
    return kline_to_dataframe(klines, code) if to_df else klines


if __name__ == '__main__':
    a = get_stock_dfcf("300502")
    print()