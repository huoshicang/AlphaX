import os
import re
from datetime import datetime, timedelta
import pandas as pd
from utils.indicators import indicators
from get_stock_dfcf import get_stock_dfcf
from utils.csv import read_csv, append_row_csv
from utils.logger import log
from utils.config_manager import get_data_dir

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
    return next_date.strftime('%Y%m%d')


def update_stock_dfcf():
    """更新所有股票数据"""
    if not check_time():
        return
    
    data_dir = get_data_dir()
    log.info(f"数据目录: {data_dir}")
    
    current_date = datetime.now().strftime('%Y%m%d')
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
        
        # last_114_rows = df.tail(TAIL)
        last_114_rows = df
        begin_date = get_last_date_plus_one(last_114_rows)
        
        log.info(f"{stock_code} 最后日期: {last_114_rows.iloc[-1]['日期']}, 起始日期: {begin_date}, 结束日期: {current_date}")
        
        new_data = get_stock_dfcf(stock_code, begin_date=begin_date, end_date=current_date, to_df=True)
        
        if new_data is None or len(new_data) == 0:
            log.info(f"{stock_code} 没有新数据")
            continue
        
        log.info(f"{stock_code} 获取到 {len(new_data)} 条新数据")
        
        merged_df = pd.concat([last_114_rows, new_data], ignore_index=True)
        
        df_with_indicators = indicators(merged_df)
        
        new_rows = df_with_indicators.tail(len(new_data))
        
        if append_row_csv(new_rows, filename):
            log.info(f"{stock_code} 更新成功")
            updated_count += 1
        else:
            log.error(f"{stock_code} 更新失败")
    
    log.info(f"更新完成，共更新 {updated_count} 只股票")


if __name__ == '__main__':
    update_stock_dfcf()