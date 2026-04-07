import time
import math
import random
import akshare as ak
from eastmoney import get_day, indicators, overwrite_csv, to_eastmoney_secid

index_stock_cons_df = ak.index_stock_cons(symbol="000510")

for i in index_stock_cons_df['品种代码'].to_list():
    df = get_day(i, begin_date="20100101", to_df=True)
    print(overwrite_csv(indicators(df), f"{to_eastmoney_secid(i)}.csv"))
    time.sleep(math.floor(random.random() * 99 + 1))





