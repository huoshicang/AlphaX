import re

import akshare as ak
from datetime import datetime, timedelta

date_format = "%Y-%m-%d"
# 缓存交易日数据
TRADE_DATES_CACHE = None
TRADE_DATES_SET = None


def get_trade_dates():
    """获取交易日列表并缓存"""
    global TRADE_DATES_CACHE, TRADE_DATES_SET
    if TRADE_DATES_CACHE is None:
        trade_dates_df = ak.tool_trade_date_hist_sina()
        TRADE_DATES_CACHE = trade_dates_df['trade_date'].to_list()
        TRADE_DATES_SET = set(TRADE_DATES_CACHE)
    return TRADE_DATES_CACHE, TRADE_DATES_SET


def normalize_date(date_str):
    """
    将各种格式的日期字符串统一转换为 %Y-%m-%d 格式

    Args:
        date_str: 日期字符串，支持多种格式：
            - "2023-01-01" (标准格式)
            - "20230101" (紧凑格式)
            - "2023/01/01" (斜杠分隔)
            - "2023.01.01" (点号分隔)

    Returns:
        str: 标准化后的日期字符串，格式为 "%Y-%m-%d"
    """
    # 去除可能的空格
    date_str = date_str.strip()

    # 尝试匹配常见的日期格式
    patterns = [
        (r'^\d{4}-\d{2}-\d{2}$', '%Y-%m-%d'),  # 2023-01-01
        (r'^\d{8}$', '%Y%m%d'),  # 20230101
        (r'^\d{4}/\d{2}/\d{2}$', '%Y/%m/%d'),  # 2023/01/01
        (r'^\d{4}\.\d{2}\.\d{2}$', '%Y.%m.%d'),  # 2023.01.01
    ]

    for pattern, fmt in patterns:
        if re.match(pattern, date_str):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime(date_format)
            except ValueError:
                continue

    # 如果都不匹配，抛出异常
    raise ValueError(f"无法解析的日期格式: {date_str}，支持的格式：YYYY-MM-DD, YYYYMMDD, YYYY/MM/DD, YYYY.MM.DD")


def compute_date(begin_date, end_date):
    """
    计算两个日期之间的交易日数量

    Args:
        begin_date: 开始日期字符串，格式为 "%Y-%m-%d"
        end_date: 结束日期字符串，格式为 "%Y-%m-%d"

    Returns:
        tuple: (调整后的开始交易日, 调整后的结束交易日, 交易日数量)
    """
    # 转换日期格式为标准格式
    begin_date = normalize_date(begin_date)
    end_date = normalize_date(end_date)

    # 如果begin_date = end_date 返回 "" "" 1
    if begin_date == end_date:
        return "", "", 0

    # 转换日期格式
    begin = datetime.strptime(begin_date, date_format).date()
    end = datetime.strptime(end_date, date_format).date()

    # 验证日期范围
    if begin > end:
        raise ValueError("开始日期不能晚于结束日期")

    # 获取交易日数据
    trade_dates, trade_dates_set = get_trade_dates()

    # 调整开始日期为交易日
    while begin not in trade_dates_set:
        begin += timedelta(days=1)

    # 调整结束日期为交易日
    while end not in trade_dates_set:
        end -= timedelta(days=1)

    # 计算交易日数量
    begin_idx = trade_dates.index(begin)
    end_idx = trade_dates.index(end)
    trade_days = end_idx - begin_idx + 1

    return  begin.strftime(date_format), end.strftime(date_format), trade_days


if __name__ == "__main__":
    print(compute_date("2026-04-18", "2026-04-25"))