import time
import math
import random
import akshare as ak
from tenacity import retry

from eastmoney import get_day, indicators, overwrite_csv, to_eastmoney_secid, log

index_stock_cons_df = ak.index_stock_cons(symbol="000510")

for idx, i in enumerate(index_stock_cons_df['品种代码'].to_list()):
    log.info(idx+1)
    df = get_day(code=i, begin_date="20100101", to_df=True)
    overwrite_csv(indicators(df), f"{to_eastmoney_secid(i)}.csv")
    break
    time.sleep(math.floor(random.random() * 120))



