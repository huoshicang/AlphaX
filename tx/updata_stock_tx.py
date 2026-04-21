"""
腾讯财经股票数据更新模块

本模块负责从腾讯财经API获取股票K线数据，并更新本地CSV文件。
支持多种K线周期（日/周/月）和复权方式（前复权/后复权/不复权）。

主要功能:
- 检查更新时间（必须在交易日15点后）
- 批量更新所有股票的日线数据
- 自动计算技术指标（均线、EMA等）
- 增量更新（只获取最新数据）

使用示例:
    from tx.updata_stock_tx import update_all_stocks_tx
    update_all_stocks_tx()  # 使用默认参数更新
"""

import json
import os
import re
from datetime import datetime, timedelta, date
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

# ==================== 常量定义 ====================

# 腾讯财经股票K线数据API接口地址
TENCENT_STOCK_API_URL = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"

# 日期格式字符串，用于日期与字符串的相互转换
DATE_FORMAT = "%Y-%m-%d"

# 最小数据行数要求：股票数据必须至少有114行才能进行更新
# 这是为了确保有足够的数据计算技术指标（如MA114）
MIN_DATA_ROWS = 114

# HTTP请求超时时间（秒），避免网络请求长时间阻塞
REQUEST_TIMEOUT = 10.0

# API返回数据的列名映射字典
# 腾讯API返回的数据列索引对应的中文含义
# 索引6、7、9、10为空字段，后续会被删除
COLUMN_RENAME_MAP = {
    0: '日期',  # 交易日期
    1: '开盘',  # 开盘价
    2: '收盘',  # 收盘价
    3: '最高',  # 最高价
    4: '最低',  # 最低价
    5: '金额',  # 成交金额
    6: '空',  # 保留字段（无用）
    7: '空',  # 保留字段（无用）
    8: '成交量',  # 成交量（手）
    9: '空',  # 保留字段（无用）
    10: "空"  # 保留字段（无用）
}


# ==================== 时间检查函数 ====================

def check_update_time() -> bool:
    """
    检查当前是否允许更新股票数据

    为了防止在交易期间更新数据导致数据不一致，设置了以下限制：
    1. 当前时间必须已过下午15点（A股收盘时间）
    2. 当前日期必须是交易日（排除周末和节假日）

    Returns:
        bool: 是否允许更新
            - True: 满足更新条件
            - False: 不满足更新条件

    Note:
        此函数会在每次批量更新前被调用，确保数据更新的时效性和准确性
    """
    current_time = datetime.now()

    # 检查当前小时是否小于15点（即下午3点前）
    if current_time.hour < 15:
        log.warning(f"当前时间 {current_time.strftime('%H:%M')} 未到下午15点，不允许更新")
        return False

    log.info(f"当前时间 {current_time.strftime('%H:%M:%S')} 已过下午15点，允许更新")

    # 获取交易日列表并检查当前日期是否为交易日
    _, trade_dates_set = get_trade_dates()
    current_date = current_time.date()

    if current_date not in trade_dates_set:
        log.warning(f"当前日期 {current_date} 不是交易日，不允许更新")
        return False

    return True


# ==================== 工具函数 ====================

def extract_stock_code(filename: str) -> Optional[str]:
    """
    从文件名中提取6位股票代码

    使用正则表达式匹配文件名中的6位连续数字，这通常是A股股票代码。
    例如: "600519.csv" -> "600519", "sh600519.csv" -> "600519"

    Args:
        filename: CSV文件名，如 "600519.csv" 或 "sz000001.csv"

    Returns:
        Optional[str]: 6位股票代码字符串
            - 成功: 返回6位数字字符串
            - 失败: 返回None（文件名中不包含6位数字）

    Examples:
        >>> extract_stock_code("600519.csv")
        '600519'
        >>> extract_stock_code("readme.txt")
        None
    """
    match = re.search(r'(\d{6})', filename)
    return match.group(1) if match else None


def get_next_date(df: pd.DataFrame) -> str:
    """
    获取DataFrame最后一行日期的下一天

    用于确定增量更新的起始日期。通过读取已有数据的最后一条记录的日期，
    计算出下一天作为新数据的开始日期，实现增量更新。

    Args:
        df: 包含'日期'列的DataFrame，日期格式为 "YYYY-MM-DD"

    Returns:
        str: 下一天的日期字符串，格式为 "YYYY-MM-DD"

    Example:
        如果最后一行日期是 "2024-01-15"，则返回 "2024-01-16"

    Note:
        这里简单加1天，后续会通过compute_date函数调整为最近的交易日
    """
    last_date = pd.to_datetime(df.iloc[-1]['日期'])
    next_date = last_date + timedelta(days=1)
    return next_date.strftime(DATE_FORMAT)


# ==================== 数据获取函数 ====================

def fetch_stock_data(
        symbol: str,
        period: KlinePeriod = KlinePeriod.day,
        adjust: AdjustType = AdjustType.qfq,
        begin_date: str = "",
        end_date: str = "",
        timeout: float = REQUEST_TIMEOUT,
) -> pd.DataFrame:
    """
    从腾讯财经API获取股票K线数据

    该函数封装了腾讯财经API的调用逻辑，包括：
    1. 计算交易日范围
    2. 构建请求参数
    3. 发送HTTP请求
    4. 解析JSONP格式的响应数据
    5. 根据复权类型选择正确的数据源

    Args:
        symbol: 股票代码（东方财富格式，不含点号）
               例如: "sh600519" 或 "sz000001"
        period: K线周期枚举值
               - KlinePeriod.day: 日K线
               - KlinePeriod.week: 周K线
               - KlinePeriod.month: 月K线
        adjust: 复权类型枚举值
               - AdjustType.qfq: 前复权（默认）
               - AdjustType.hfq: 后复权
               - AdjustType.bfq: 不复权
        begin_date: 开始日期，格式 "YYYY-MM-DD"
                   空字符串表示从最早可用数据开始
        end_date: 结束日期，格式 "YYYY-MM-DD"
                 空字符串表示到今天
        timeout: HTTP请求超时时间（秒），默认10秒

    Returns:
        pd.DataFrame: 股票K线数据
            - 成功: 返回包含原始数据的DataFrame（列名为数字索引）
            - 失败: 返回空的DataFrame

    Raises:
        不会抛出异常，所有错误都在内部捕获并记录日志

    Note:
        - API返回的是JSONP格式，需要提取 "= {" 后的JSON部分
        - 不同复权类型的数据存储在不同的键中（day/qfqday/hfqday）
        - 返回的数据列还未重命名，需要调用process_stock_data处理
    """
    try:
        # 计算实际的交易日范围和交易日数量
        # compute_date会自动调整非交易日为最近的交易日
        begin_date, end_date, trade_days = compute_date(begin_date, end_date)

        # 构建API请求参数
        params = {
            "_var": f"kline_{period}{adjust}",  # JSONP回调变量名
            "param": f"{symbol},{period},{begin_date},{end_date},{trade_days},{adjust}",  # 核心参数
            "r": f"0.{gen_random_same_length()}",  # 随机数，防止浏览器缓存
        }

        # 发送GET请求获取数据
        response = requests.get(TENCENT_STOCK_API_URL, params=params, timeout=timeout)
        response.raise_for_status()  # 如果HTTP状态码表示错误，抛出异常

        # 解析JSONP响应：提取 "= {" 之后的JSON部分
        data_text = response.text
        json_start = data_text.find("={") + 1
        data_json = json.loads(data_text[json_start:])

        # 获取指定股票的数据
        stock_data = data_json.get("data", {}).get(symbol, [])

        # 根据可用的数据类型选择数据源
        # 优先级：不复权 > 后复权 > 前复权
        if "day" in stock_data:
            df = pd.DataFrame(stock_data["day"])
        elif "hfqday" in stock_data:
            df = pd.DataFrame(stock_data["hfqday"])
        else:
            df = pd.DataFrame(stock_data["qfqday"])

        return df

    except requests.RequestException as e:
        # 网络请求相关错误（连接超时、DNS解析失败等）
        log.error(f"请求股票数据失败 {symbol}: {e}")
        return pd.DataFrame()
    except (json.JSONDecodeError, KeyError) as e:
        # JSON解析错误或数据结构不符合预期
        log.error(f"解析股票数据失败 {symbol}: {e}")
        return pd.DataFrame()


# ==================== 数据处理函数 ====================

def process_stock_data(
        raw_data: pd.DataFrame,
        stock_code: str,
) -> pd.DataFrame:
    """
    处理原始股票数据：重命名列、删除无用列、添加股票代码

    将API返回的原始数据转换为标准格式：
    1. 将数字列名映射为中文列名
    2. 删除标记为"空"的无用列
    3. 添加"股票代码"列以便后续识别

    Args:
        raw_data: 从API获取的原始DataFrame，列名为数字索引（0-10）
        stock_code: 6位股票代码，如 "600519"

    Returns:
        pd.DataFrame: 处理后的标准格式数据
            包含列：日期、开盘、收盘、最高、最低、金额、成交量、股票代码

    Note:
        - 如果输入数据为空，直接返回原数据
        - 使用copy()避免修改原始数据
        - "空"列可能有多个，drop会删除所有同名列
    """
    if raw_data.empty:
        return raw_data

    # 创建副本，避免修改原始数据
    processed = raw_data.copy()

    # 将数字列名映射为有意义的中文列名
    processed.rename(columns=COLUMN_RENAME_MAP, inplace=True)

    # 删除所有标记为"空"的无用列（索引6、7、9、10对应的列）
    if '空' in processed.columns:
        processed.drop(columns=['空'], inplace=True)

    # 添加股票代码列，方便后续数据合并和查询
    processed["股票代码"] = stock_code

    return processed


# ==================== 单股票更新函数 ====================

def update_single_stock(
        filename: str,
        end_date: str,
        period: KlinePeriod,
        adjust: AdjustType,
        timeout: float,
) -> bool:
    """
    更新单只股票的数据到CSV文件

    这是核心的增量更新逻辑，执行以下步骤：
    1. 从文件名提取股票代码
    2. 读取本地CSV文件
    3. 计算需要更新的日期范围
    4. 分情况获取新数据（是否包含今天）
    5. 合并新旧数据并计算技术指标
    6. 追加新数据到CSV文件

    Args:
        filename: CSV文件名，如 "600519.csv"
        end_date: 更新的结束日期，格式 "YYYY-MM-DD"
        period: K线周期（日/周/月）
        adjust: 复权类型（前复权/后复权/不复权）
        timeout: HTTP请求超时时间（秒）

    Returns:
        bool: 是否更新成功
            - True: 成功获取并保存了新数据
            - False: 跳过更新或更新失败

    Note:
        - 如果end_date是今天，会分两次请求：历史数据 + 今天数据
          这是因为今天的实时数据可能需要单独获取
        - 新数据会与旧数据合并后重新计算所有技术指标
        - 只提取新增行的指标数据追加到CSV，避免重复计算
    """
    # 步骤1: 从文件名提取股票代码
    stock_code = extract_stock_code(filename)

    if not stock_code:
        log.debug(f"跳过非股票代码文件: {filename}")
        return False

    log.info(f"处理股票: {stock_code}")

    # 步骤2: 读取本地CSV文件
    df = read_csv(filename)

    # 验证数据有效性：不能为空且必须有足够的历史数据
    if df is None or df.empty or len(df) < MIN_DATA_ROWS:
        log.warning(f"{stock_code} 数据不足{MIN_DATA_ROWS}行，跳过更新")
        return False

    # 步骤3: 计算增量更新的起始日期（最后一行日期的下一天）
    begin_date = get_next_date(df)

    # 如果起始日期已经超过结束日期，说明数据已是最新
    if begin_date > end_date:
        log.warning(f"{stock_code} 数据已更新至最新，跳过更新")
        return False

    log.info(f"{stock_code} 最后日期: {df.iloc[-1]['日期']}, 起始日期: {begin_date}, 结束日期: {end_date}")

    # 步骤4: 转换股票代码为腾讯API需要的格式
    # to_eastmoney_secid返回带点号的格式（如"sh.600519"），需要移除点号
    symbol = to_eastmoney_secid(stock_code).replace('.', '')

    # 判断结束日期是否是今天，决定是否需要特殊处理今日数据
    include_today = date.fromisoformat(end_date) == date.today()

    all_new_data = []  # 用于收集所有新获取的数据块

    if include_today:
        # 情况A: 更新包含今天的数据，需要分两次请求

        # 4a. 获取昨天及之前的历史数据
        yesterday = (date.fromisoformat(end_date) - timedelta(days=1)).strftime(DATE_FORMAT)

        if begin_date <= yesterday:
            # 只有当起始日期早于或等于昨天时才需要获取历史数据
            historical_data = fetch_stock_data(symbol, period, adjust, begin_date, yesterday, timeout)
            if not historical_data.empty:
                all_new_data.append(historical_data)

        # 4b. 单独获取今天的实时数据
        today_str = date.today().strftime(DATE_FORMAT)
        today_data = fetch_stock_data(symbol, period, adjust, today_str, today_str, timeout)
        if not today_data.empty:
            all_new_data.append(today_data)
    else:
        # 情况B: 更新历史数据（不包含今天），一次性获取
        historical_data = fetch_stock_data(symbol, period, adjust, begin_date, end_date, timeout)
        if not historical_data.empty:
            all_new_data.append(historical_data)

    # 步骤5: 检查是否获取到新数据
    if not all_new_data:
        log.warning(f"{stock_code} 未获取到新数据")
        return False

    # 步骤6: 合并所有新数据块
    new_data = pd.concat(all_new_data, ignore_index=True)

    # 步骤7: 格式化新数据（重命名列、删除无用列、添加股票代码）
    new_data = process_stock_data(new_data, stock_code)

    # 步骤8: 合并旧数据和新数据
    merged_df = pd.concat([df, new_data], ignore_index=True)

    # 步骤9: 基于完整数据计算技术指标
    # indicators函数会计算MA、EMA等指标，需要完整的历史数据才能准确计算
    df_with_indicators = indicators(merged_df)

    # 步骤10: 只提取新增行对应的指标数据
    # 因为旧数据的指标已经存在，只需要追加新行的数据
    new_rows = df_with_indicators.tail(len(new_data))

    # 步骤11: 追加新数据到CSV文件
    if append_row_csv(new_rows, filename):
        log.info(f"{stock_code} 更新成功")
        return True
    else:
        log.error(f"{stock_code} 更新失败")
        return False


# ==================== 批量更新主函数 ====================

def update_all_stocks_tx(
        period: KlinePeriod = KlinePeriod.day,
        adjust: AdjustType = AdjustType.qfq,
        begin_date: str = "",
        end_date: str = "",
        timeout: float = REQUEST_TIMEOUT,
) -> None:
    """
    批量更新所有股票的腾讯财经数据

    这是主要的入口函数，会遍历数据目录中的所有CSV文件，
    逐个调用update_single_stock进行增量更新。

    Args:
        period: K线周期，默认日线（KlinePeriod.day）
               可选: KlinePeriod.week（周线）、KlinePeriod.month（月线）
        adjust: 复权类型，默认前复权（AdjustType.qfq）
               可选: AdjustType.hfq（后复权）、AdjustType.bfq（不复权）
        begin_date: 开始日期（未使用，保留用于向后兼容）
                   实际起始日期由每个股票的最后更新日期决定
        end_date: 结束日期，默认为今天
                 格式: "YYYY-MM-DD"，空字符串表示今天
        timeout: HTTP请求超时时间，默认10秒

    Returns:
        None

    Warning:
        禁止更新多天的数据！此函数设计为每日收盘后运行，
        仅更新从上次更新到当前的增量数据。

    Note:
        - 更新前会检查当前时间是否在交易日15点后
        - 会统计总处理数量和成功更新数量
        - 单个股票更新失败不会影响其他股票的更新

    Usage:
        # 使用默认参数（日线、前复权、今天）
        update_all_stocks_tx()

        # 自定义参数
        from tx.enums import KlinePeriod, AdjustType
        update_all_stocks_tx(
            period=KlinePeriod.week,
            adjust=AdjustType.hfq,
            timeout=15.0
        )
    """
    # 前置检查：确认当前时间允许更新
    if not check_update_time():
        return

    # 如果未指定结束日期，默认为今天
    if not end_date:
        end_date = date.today().strftime(DATE_FORMAT)

    # 获取数据存储目录
    data_dir = get_data_dir()
    log.info(f"数据目录: {data_dir}")

    # 初始化计数器
    updated_count = 0  # 成功更新的股票数量
    total_count = 0  # 总共处理的股票数量

    # 遍历数据目录中的所有文件
    for filename in os.listdir(data_dir):
        # 只处理CSV文件
        if not filename.endswith('.csv'):
            continue

        total_count += 1

        # 更新单只股票
        success = update_single_stock(filename, end_date, period, adjust, timeout)
        if success:
            updated_count += 1

    # 输出最终统计信息
    log.info(f"更新完成，共处理 {total_count} 只股票，成功更新 {updated_count} 只")


# ==================== 主程序入口 ====================

if __name__ == '__main__':
    # 直接运行此脚本时，执行批量更新
    update_all_stocks_tx()