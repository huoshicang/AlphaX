import json
import os
import re
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd
import requests

from tx.compute_date import compute_date, get_trade_dates
from tx.enums import AdjustType, KlinePeriod
from tx.gen_random_same_length import gen_random_same_length
from utils.config_manager import get_data_dir
from utils.csv import append_row_csv, read_csv
from utils.indicators import indicators
from utils.logger import log
from utils.transition_secid import to_eastmoney_secid


TENCENT_STOCK_API_URL = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
DATE_FORMAT = "%Y-%m-%d"
MIN_DATA_ROWS = 114
REQUEST_TIMEOUT = 10.0

COL_INDEX_MAP = {
    0: "日期",
    1: "开盘",
    2: "收盘",
    3: "最高",
    4: "最低",
    5: "金额",
    8: "成交量"
}


# ==================== 时间控制 ====================

def check_update_time() -> bool:
    now = datetime.now()

    if now.hour < 15:
        log.warning(f"未到15点: {now.strftime('%H:%M')}")
        return False

    _, trade_dates = get_trade_dates()
    if now.date() not in trade_dates:
        log.warning(f"非交易日: {now.date()}")
        return False

    return True


# ==================== 工具 ====================

def extract_stock_code(filename: str) -> Optional[str]:
    m = re.search(r'(\d{6})', filename)
    return m.group(1) if m else None


def get_next_date(df: pd.DataFrame) -> str:
    last = pd.to_datetime(df.iloc[-1]["日期"])
    return (last + timedelta(days=1)).strftime(DATE_FORMAT)


# ==================== 核心请求 ====================

def fetch_stock_data(symbol, period, adjust, begin, end, timeout) -> pd.DataFrame:
    try:
        begin, end, days = compute_date(begin, end)

        params = {
            "_var": f"kline_{period}{adjust}",
            "param": f"{symbol},{period},{begin},{end},{days},{adjust}",
            "r": f"0.{gen_random_same_length()}",
        }

        resp = requests.get(TENCENT_STOCK_API_URL, params=params, timeout=timeout)
        resp.raise_for_status()

        text = resp.text
        data = json.loads(text[text.find("={") + 1:])

        raw = data.get("data", {}).get(symbol, {})
        for key in ("day", "hfqday", "qfqday"):
            if key in raw:
                return pd.DataFrame(raw[key])

        return pd.DataFrame()

    except Exception as e:
        log.error(f"{symbol} 获取失败: {e}")
        return pd.DataFrame()


def get_data(begin, end, symbol, period, adjust) -> pd.DataFrame:
    include_today = date.fromisoformat(end) == date.today()

    dfs = []

    if include_today:
        yesterday = (date.fromisoformat(end) - timedelta(days=1)).strftime(DATE_FORMAT)

        if begin <= yesterday:
            df = fetch_stock_data(symbol, period, adjust, begin, yesterday, REQUEST_TIMEOUT)
            if not df.empty:
                dfs.append(df)

        df = fetch_stock_data(symbol, period, adjust, end, end, REQUEST_TIMEOUT)
        if not df.empty:
            dfs.append(df)
    else:
        df = fetch_stock_data(symbol, period, adjust, begin, end, REQUEST_TIMEOUT)
        if not df.empty:
            dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)
    return df[list(COL_INDEX_MAP.keys())].rename(columns=COL_INDEX_MAP)


# ==================== 数据处理 ====================

def process_stock_data(df: pd.DataFrame, code: str) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df["股票代码"] = code
    df["日期"] = pd.to_datetime(df["日期"]).dt.strftime("%Y/%m/%d")
    return df


# ==================== 单只股票 ====================

def update_single_stock(filename, end_date, period, adjust, timeout) -> bool:
    code = extract_stock_code(filename)
    if not code:
        return False

    df = read_csv(filename)
    if df is None or df.empty or len(df) < MIN_DATA_ROWS:
        log.warning(f"{code} 数据不足")
        return False

    begin = get_next_date(df)
    if begin > end_date:
        return False

    symbol = to_eastmoney_secid(code).replace('.', '')

    # === 核心优化点：统一获取 + 合并 ===
    qfq = get_data(begin, end_date, symbol, period, AdjustType.qfq)
    hfq = get_data(begin, end_date, symbol, period, AdjustType.hfq)

    if qfq.empty or hfq.empty:
        return False

    qfq = qfq.rename(columns={
        "开盘": "开盘_qfq",
        "收盘": "收盘_qfq",
        "最高": "最高_qfq",
        "最低": "最低_qfq",
        "金额": "金额_qfq",
        "成交量": "成交量_qfq"
    })

    merged = pd.concat([qfq, hfq[["开盘", "收盘", "最高", "最低", "金额", "成交量"]]], axis=1)
    merged.columns = list(qfq.columns) + ["开盘_hfq", "收盘_hfq", "最高_hfq", "最低_hfq", "金额_hfq", "成交量_hfq"]

    new_data = process_stock_data(merged, code)
    if new_data.empty:
        return False

    full = pd.concat([df, new_data], ignore_index=True)
    full = indicators(full)

    new_rows = full.tail(len(new_data))

    if append_row_csv(new_rows, filename):
        log.info(f"{code} 更新成功")
        return True

    return False


# ==================== 批量更新 ====================

def updata_stock_tx(
        period: KlinePeriod = KlinePeriod.day,
        adjust: AdjustType = AdjustType.qfq,
        begin_date: str = "",
        end_date: str = "",
        timeout: float = REQUEST_TIMEOUT,
):
    if not check_update_time():
        return

    if not end_date:
        end_date = date.today().strftime(DATE_FORMAT)

    data_dir = get_data_dir()

    total, success = 0, 0

    for f in os.listdir(data_dir):
        if not f.endswith(".csv"):
            continue

        total += 1
        if update_single_stock(f, end_date, period, adjust, timeout):
            success += 1

    log.info(f"完成: {success}/{total}")


if __name__ == "__main__":
    updata_stock_tx()