from enum import IntEnum, StrEnum

class AdjustType(StrEnum):
    """复权类型枚举"""
    bfq = "bfq"   # 不复权
    qfq = "qfq"   # 前复权
    hfq = "hfq"   # 后复权

class KlinePeriod(StrEnum):
    """K线周期枚举"""
    day = "day"      # 日K线
    week = "week"      # 周K线
    month = "month"    # 月K线

