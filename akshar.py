import akshare as ak
import pandas as pd
from eastmoney import get_day, indicators, overwrite_csv, to_eastmoney_secid

# 1. 设置显示，方便查看完整数据
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

index_stock_cons_df = ak.index_stock_cons(symbol="000510")

for i in index_stock_cons_df['品种代码'].to_list():
    df = ak.stock_zh_a_hist(
        symbol=i,       # 6位股票代码，不带.SH/.SZ
        period="daily",         # 周期：daily(日线)、weekly(周线)、monthly(月线)
        start_date="20100101",  # 开始日期，格式YYYYMMDD
        adjust="qfq"            # 复权：qfq(前复权)、hfq(后复权)、""(不复权)
    )
    print(overwrite_csv(indicators(df), f"{to_eastmoney_secid(i)}.csv"))