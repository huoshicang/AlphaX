import json
from datetime import datetime

import pandas as pd
import requests

from tx.bar import get_tqdm
from tx.enums import AdjustType, KlinePeriod
from tx.gen_random_same_length import gen_random_same_length
from utils.csv import overwrite_csv
from utils.indicators import indicators
from utils.transition_secid import to_eastmoney_secid


URL = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
DATE_FMT = "%Y-%m-%d"

COL_INDEX_MAP = {
    0: "日期", 1: "开盘", 2: "收盘", 3: "最高",
    4: "最低", 5: "金额", 8: "成交量"
}


# ==================== 请求 ====================

def fetch_year(symbol, period, year, adjust, timeout) -> pd.DataFrame:
    params = {
        "_var": f"kline_{period}{adjust}",
        "param": f"{symbol},{period},{year}-01-01,{year+1}-12-31,640,{adjust}",
        "r": f"0.{gen_random_same_length()}",
    }

    try:
        r = requests.get(URL, params=params, timeout=timeout)
        r.raise_for_status()
        data = json.loads(r.text[r.text.find("={") + 1:])
        raw = data.get("data", {}).get(symbol, {})
    except Exception as e:
        print(f"{year}-{adjust}失败: {e}")
        return pd.DataFrame()

    for k in ("day", "hfqday", "qfqday"):
        if k in raw:
            df = pd.DataFrame(raw[k])
            break
    else:
        return pd.DataFrame()

    if df.empty:
        return df

    df = df[list(COL_INDEX_MAP)].rename(columns=COL_INDEX_MAP)
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df = df.dropna(subset=["日期"]).set_index("日期")
    return df


# ==================== 主逻辑 ====================

def init_stock_tx(
        code: str,
        period: KlinePeriod = KlinePeriod.day,
        adjust: AdjustType = AdjustType.qfq,
        begin_date: str = datetime.now().strftime(DATE_FMT),
        end_date: str = datetime.now().strftime(DATE_FMT),
        timeout: float = 10.0,
        include_bfq: bool = True,
):
    symbol = to_eastmoney_secid(code).replace(".", "")

    t_begin = pd.to_datetime(begin_date, errors="coerce")
    t_end = pd.to_datetime(end_date, errors="coerce")
    if pd.isna(t_begin) or pd.isna(t_end):
        raise ValueError("日期格式错误")

    years = range(t_begin.year, t_end.year + 1)

    adjusts = [AdjustType.qfq, AdjustType.hfq] if include_bfq else [adjust]
    frames = {a: [] for a in adjusts}

    tqdm = get_tqdm()

    for y in tqdm(years, desc=f"{code}-{period}", leave=False):
        for a in adjusts:
            df = fetch_year(symbol, period, y, a, timeout)
            if not df.empty:
                frames[a].append(df)

    parts = []
    for a, dfs in frames.items():
        if not dfs:
            continue

        df = pd.concat(dfs)
        suf = f"_{a}"

        df = df.rename(columns={
            "开盘": f"开盘{suf}",
            "收盘": f"收盘{suf}",
            "最高": f"最高{suf}",
            "最低": f"最低{suf}",
            "金额": f"金额{suf}",
            "成交量": f"成交量{suf}"
        })

        parts.append(df)

    if not parts:
        return pd.DataFrame()

    # === 合并 ===
    df = parts[0]
    for other in parts[1:]:
        df = df.join(other, how="outer")

    # === 收尾整理 ===
    df = (
        df.sort_index()
        .drop_duplicates()
        .reset_index(names="日期")
    )

    df.insert(0, "股票代码", code)
    df = df.loc[:, ~df.columns.duplicated()]

    # 金额/成交量放最后
    tail_cols = [c for c in ("金额_qfq", "成交量_qfq", "金额_hfq", "成交量_hfq") if c in df.columns]

    return df[[c for c in df.columns if c not in tail_cols] + tail_cols]


# ==================== 示例 ====================

if __name__ == '__main__':
    df = init_stock_tx(
        code="300308",
        begin_date="20100101",
        end_date="20260424",
    )

    overwrite_csv(indicators(df), "1-300308.csv")