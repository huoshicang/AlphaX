# 导入所需模块
from tx.init_stock_tx import init_stock_tx
from tx.updata_stock_tx import updata_stock_tx
from tx.enums import AdjustType, KlinePeriod  # 导入调整类型和K线周期枚举

from datetime import datetime  # 导入日期时间模块

# 日期格式定义
date_format = "%Y-%m-%d"



def get_stock_tx(
        code: str = "",  # 股票代码
        period: KlinePeriod = KlinePeriod.day,  # K线周期，默认日线
        adjust: AdjustType = AdjustType.qfq,  # 复权类型，默认前复权
        begin_date: str = datetime.now().strftime(date_format),  # 开始日期，默认当天
        end_date: str = datetime.now().strftime(date_format),  # 结束日期，默认当天
        timeout: float = 10.0,  # 请求超时时间，默认10秒
        is_init: bool = False):

    if is_init:
        return init_stock_tx(code, period, adjust, begin_date, end_date, timeout)

    return updata_stock_tx(period, adjust, begin_date, end_date, timeout)
