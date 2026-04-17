import akshare as ak
import pandas as pd

from utils.csv import overwrite_csv
from utils.indicators import  indicators
from utils.transition_secid import convert_to_secid, to_eastmoney_secid

# 1. 设置显示，方便查看完整数据
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

index_stock_cons_df = ak.index_stock_cons(symbol="000510")

print(index_stock_cons_df)

for i in index_stock_cons_df['品种代码'].to_list():
    df = ak.stock_zh_a_hist_tx(
        symbol=to_eastmoney_secid(i).replace(".", ""),
        start_date="20100101",
        adjust="qfq"
    )
    print(i)
    # print(overwrite_csv(indicators(df), f"{to_eastmoney_secid(i)}.csv"))
