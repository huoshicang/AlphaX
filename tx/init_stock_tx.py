# 导入所需模块
import json
from datetime import datetime  # 导入日期时间模块

import pandas as pd  # 导入数据分析库
import requests  # 导入网络请求库

from tx.enums import AdjustType, KlinePeriod  # 导入调整类型和K线周期枚举
from tx.bar import get_tqdm  # 导入进度条工具
from tx.gen_random_same_length import gen_random_same_length
from utils.transition_secid import to_eastmoney_secid  # 导入股票代码转换函数

# 腾讯股票数据API地址
url = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
# 日期格式定义
date_format = "%Y-%m-%d"


def init_stock_tx(
        code: str,  # 股票代码
        period: KlinePeriod = KlinePeriod.day,  # K线周期，默认日线
        adjust: AdjustType = AdjustType.qfq,  # 复权类型，默认前复权
        begin_date: str = datetime.now().strftime(date_format),  # 开始日期，默认当天
        end_date: str = datetime.now().strftime(date_format),  # 结束日期，默认当天
        timeout: float = 10.0,  # 请求超时时间，默认10秒
):
    """
    获取腾讯股票历史K线数据

    该函数通过腾讯财经API获取指定股票的历史K线数据，支持不同周期和复权方式。
    数据会按年份分段获取，然后合并成完整的DataFrame。

    Args:
        code: 股票代码，如 "300502" 或 "sh600000"
        period: K线周期，可选值包括日线、周线、月线等（来自KlinePeriod枚举）
        adjust: 复权类型，可选前复权(qfq)、后复权(hfq)或不复权（来自AdjustType枚举）
        begin_date: 开始日期，格式为 "YYYY-MM-DD"，默认为当天
        end_date: 开始日期，格式为 "YYYY-MM-DD"，默认为当天
        timeout: HTTP请求超时时间（秒），默认10秒

    Returns:
        DataFrame: 包含股票K线数据的DataFrame，列包括：
                   - 股票代码: 股票标识
                   - 日期: 交易日期
                   - 开盘: 开盘价
                   - 收盘: 收盘价
                   - 最高: 最高价
                   - 最低: 最低价
                   - 金额: 成交金额
                   - 成交量: 成交量

    Example:
        >>> df = init_stock_tx("300502", begin_date="2020-01-01", end_date="2024-12-31")
        >>> print(df.head())
    """
    # 将股票代码转换为东方财富格式并移除点号分隔符
    # 例如: "sh600000" -> "sh600000", "sz000001" -> "sz000001"
    symbol = to_eastmoney_secid(code).replace('.', '')

    # 提取开始年份和结束年份
    # 结束年份+1是为了确保覆盖完整的时间范围
    range_start = int(begin_date[:4])  # 提取开始日期的年份部分
    range_end = int(end_date[:4]) + 1  # 提取结束日期的年份部分并加1

    # 初始化空的DataFrame用于存储所有年份的数据
    df = pd.DataFrame()

    # 获取进度条对象，用于显示数据获取进度
    tqdm = get_tqdm()

    # 遍历年份范围，逐年获取K线数据
    # leave=False表示进度条完成后不保留显示
    for year in tqdm(range(range_start, range_end), leave=False, desc=f"获取{code} {period} {adjust} 数据"):
        # 构建API请求参数
        params = {
            "_var": f"kline_{period}{adjust}",  # 回调变量名，根据周期和复权类型动态生成
            "param": f"{symbol},{period},{year}-01-01,{year + 1}-12-31,640,{adjust}",  # 请求参数：股票代码、周期、起止日期、数据条数、复权类型
            "r": f"0.{gen_random_same_length()}",
        }

        # 发送HTTP GET请求获取数据
        r = requests.get(url, params=params, timeout=timeout)
        data_text = r.text

        # 解析JSON数据
        data_json = json.loads(data_text[data_text.find("={") + 1:]).get("data", {}).get(symbol, {})

        # 根据复权类型选择对应的数据字段
        # 优先级：普通日线 > 后复权日线 > 前复权日线
        if "day" in data_json.keys():
            # 不复权的日线数据
            temp_df = pd.DataFrame(data_json["day"])
        elif "hfqday" in data_json.keys():
            # 后复权的日线数据
            temp_df = pd.DataFrame(data_json["hfqday"])
        else:
            # 前复权的日线数据（默认）
            temp_df = pd.DataFrame(data_json["qfqday"])

        # 将当前年份的数据合并到总DataFrame中
        df = pd.concat([df, temp_df], ignore_index=True)

    # 在DataFrame的第一列插入股票代码列
    df.insert(0, "股票代码", code)

    # 重命名列名为中文描述
    # 0: 日期, 1: 开盘价, 2: 收盘价, 3: 最高价, 4: 最低价 5: 成交金额, 6-7: 预留字段, 8: 成交量, 9: 预留字段
    df.rename(
        columns={
            0: '日期',
            1: '开盘',
            2: '收盘',
            3: '最高',
            4: '最低',
            5: '金额',
            6: '空1',
            7: '空2',
            8: '成交量',
            9: '空3'
        },
        inplace=True
    )

    # 删除无用的预留列（空1、空2、空3）
    df.drop(columns=['空1', '空2', '空3'], inplace=True)

    # 去除重复的行数据，并重置索引
    df.drop_duplicates(inplace=True, ignore_index=True)

    # 将日期列转换为datetime类型，并设置为索引
    # errors="coerce"表示无法转换的值会被设为NaT
    df.index = pd.to_datetime(df["日期"], errors="coerce")

    # 按日期索引排序，确保时间顺序正确
    df.sort_index(inplace=True)

    # 根据用户指定的日期范围筛选数据
    df = df[begin_date:end_date]

    # 重置索引，drop=True表示丢弃旧索引
    df.reset_index(inplace=True, drop=True)

    # 返回处理完成的股票K线数据
    return df


if __name__ == '__main__':
    # 测试代码：获取股票代码为300502的历史数据
    # 时间范围：2010-01-01 至 2026-04-15
    # 使用默认的日线周期和前复权方式
    init_stock_tx("300502", begin_date="2010-01-01", end_date="2026-04-15")