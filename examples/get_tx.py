import time
import math
import random
import akshare as ak

from utils.logger import log
from utils.csv import overwrite_csv
from utils.indicators import indicators
from tx import get_stock_tx


index_stock_cons_df = ak.index_stock_cons(symbol="000510")

for idx, i in enumerate(index_stock_cons_df['品种代码'].to_list()):
    log.info(idx+1)
    df = get_stock_tx(code=i, begin_date="20230101", end_date="20260415")
    overwrite_csv(indicators(df), f"{i}.csv")
    break
    time.sleep(math.floor(random.random() * 120))