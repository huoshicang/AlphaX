from enum import IntEnum

class AdjustType(IntEnum):
    """复权类型枚举"""
    bfq = 0        # 不复权
    qfq = 1   # 前复权
    hfq = 2  # 后复权

class KlinePeriod(IntEnum):
    """K线周期枚举"""
    MIN_5 = 5      # 5分钟K线
    MIN_15 = 15    # 15分钟K线
    MIN_30 = 30    # 30分钟K线
    MIN_60 = 60    # 60分钟K线
    DAY = 101      # 日K线
    WEEK = 102     # 周K线
    MONTH = 103    # 月K线