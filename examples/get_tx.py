import time
from collections import Counter
from utils.logger import log
import akshare as ak
from utils.csv import overwrite_csv
from utils.indicators import indicators
from tx import get_stock_tx



index_stock_cons_list = ak.index_stock_cons(symbol="000510")['品种代码'].to_list()

log.info(index_stock_cons_list)
log.info(f"共{len(index_stock_cons_list)}只股票")
log.info(f"统计：{Counter(index_stock_cons_list)}")
log.info(f"去重：{len(set(index_stock_cons_list))}")

for idx, i in enumerate(set(index_stock_cons_list)):
    log.info(idx+1)
    df = get_stock_tx(code=i, begin_date="20100101", end_date="20260417", is_init=True)
    overwrite_csv(indicators(df), f"{i}.csv")
