# 导入所需模块
import json
import os
import re
from datetime import datetime, timedelta  # 导入日期时间模块

import pandas as pd  # 导入数据分析库
import requests  # 导入网络请求库

from tx.compute_date import compute_date  # 导入日期计算函数
from tx.enums import AdjustType, KlinePeriod
from tx.gen_random_same_length import gen_random_same_length
from utils.config_manager import get_data_dir
from utils.csv import append_row_csv, read_csv
from utils.indicators import indicators
from utils.logger import log
from utils.transition_secid import to_eastmoney_secid  # 导入股票代码转换函数

# 腾讯股票数据API地址
url = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
# 日期格式定义
date_format = "%Y-%m-%d"
# 获取最后N行数据
TAIL = 114


def check_time():
    """检查当前时间是否已过下午15点"""
    current_time = datetime.now()
    if current_time.hour < 15:
        log.warning(f"当前时间 {current_time.strftime('%H:%M')} 未到下午15点，不允许更新")
        return False
    log.info(f"当前时间 {current_time.strftime('%H:%M:%S')} 已过下午15点，允许更新")
    return True


def extract_stock_code(filename):
    """从文件名中提取6位股票代码"""
    match = re.search(r'(\d{6})', filename)
    if match:
        return match.group(1)
    return None


def get_last_date_plus_one(df):
    """获取最后一行日期并加一天"""
    last_row = df.iloc[-1]
    last_date_str = last_row['日期']
    last_date = pd.to_datetime(last_date_str)
    next_date = last_date + timedelta(days=1)
    return next_date.strftime(date_format)


def updata_stock_tx(
        period: KlinePeriod = KlinePeriod.day,  # K线周期，默认日线
        adjust: AdjustType = AdjustType.qfq,  # 复权类型，默认前复权
        begin_date: str = datetime.now().strftime(date_format),  # 开始日期，默认当天
        end_date: str = datetime.now().strftime(date_format),  # 结束日期，默认当天
        timeout: float = 10.0,  # 请求超时时间，默认10秒
):
    """
    获取腾讯股票数据
    禁止更新多天！！！

    Args:
        code: 股票代码
        period: K线周期
        adjust: 复权类型
        begin_date: 开始日期
        end_date: 结束日期
        timeout: 请求超时时间
        is_init: 是否为初始化请求，默认False
    Returns:
        DataFrame: 包含股票数据的DataFrame
    """

    """更新所有股票数据"""
    if not check_time():
        return None

    data_dir = get_data_dir()
    log.info(f"数据目录: {data_dir}")

    updated_count = 0

    for filename in os.listdir(data_dir):
        if not filename.endswith('.csv'):
            continue

        stock_code = extract_stock_code(filename)

        if not stock_code:
            log.debug(f"跳过非股票代码文件: {filename}")
            continue

        log.info(f"处理股票: {stock_code}")

        df = read_csv(filename)
        if df is None or len(df) == 0:
            log.warning(f"文件为空或读取失败: {filename}")
            continue

        if len(df) < TAIL:
            log.warning(f"{stock_code} 数据不足114行，跳过更新")
            continue

        last_114_rows = df

        begin_date = get_last_date_plus_one(last_114_rows)
        end_date = datetime.now().strftime(date_format)

        log.info(
            f"{stock_code} 最后日期: {last_114_rows.iloc[-1]['日期']}, 起始日期: {begin_date}, 结束日期: {end_date}")

        # 将股票代码转换为东方财富格式并移除点号
        symbol = to_eastmoney_secid(stock_code).replace('.', '')

        # 计算日期范围和交易日数量
        begin_date, end_date, trade_days = compute_date(begin_date, end_date)

        # 构建请求参数
        params = {
            "_var": f"kline_{period}{adjust}",  # 变量名，根据周期和复权类型生成
            "param": f"{symbol},{period},{begin_date},{end_date},{trade_days},{adjust}",  # 参数
            "r": f"0.{gen_random_same_length()}",  # 随机数，用于避免缓存
        }

        # 发送HTTP请求
        r = requests.get(url, params=params, timeout=timeout)
        # 获取响应文本
        data_text = r.text
        # 解析JSON数据
        data_json = json.loads(data_text[data_text.find("={") + 1:]).get("data", {}).get(symbol, {})

        # 根据复权类型选择对应的数据
        if "day" in data_json.keys():
            new_data = pd.DataFrame(data_json["day"])
        elif "hfqday" in data_json.keys():
            new_data = pd.DataFrame(data_json["hfqday"])
        else:
            new_data = pd.DataFrame(data_json["qfqday"])

        # 重命名列名
        new_data.rename(
            columns={0: '日期', 1: '开盘', 2: '收盘', 3: '最高', 4: '最低', 5: '金额', 6: '空', 7: '空', 8: '成交量',
                     9: '空', 10: "空" }, inplace=True)

        # 删除无用的列
        new_data.drop(columns=['空'], inplace=True)

        # 添加股票代码列
        new_data["股票代码"] = stock_code

        # 合并数据
        merged_df = pd.concat([last_114_rows, new_data], ignore_index=True)

        # 计算指标
        df_with_indicators = indicators(merged_df)

        # 提取新数据
        new_rows = df_with_indicators.tail(len(new_data))

        # 保存数据
        if append_row_csv(new_rows, filename):
            log.info(f"{stock_code} 更新成功")
            updated_count += 1
        else:
            log.error(f"{stock_code} 更新失败")

    log.info(f"更新完成，共更新 {updated_count} 只股票")
    return None


if __name__ == '__main__':
    # 测试函数
    updata_stock_tx()
