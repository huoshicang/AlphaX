from enum import IntEnum

class AdjustType(IntEnum):
    """复权类型枚举"""
    bfq = 0        # 不复权
    qfq = 1   # 前复权
    hfq = 2  # 后复权

class KlinePeriod(IntEnum):
    """K线周期枚举"""
    min5 = 5      # 5分钟K线
    min15 = 15    # 15分钟K线
    min30 = 30    # 30分钟K线
    min60 = 60    # 60分钟K线
    day = 101      # 日K线
    week = 102     # 周K线
    month = 103    # 月K线

