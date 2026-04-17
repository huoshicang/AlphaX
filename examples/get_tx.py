import os

import akshare as ak
from utils.config_manager import get_data_dir
from utils.logger import log
from utils.csv import overwrite_csv
from utils.indicators import indicators
from tx import get_stock_tx


index_stock_cons_df = ak.index_stock_cons(symbol="000510")

for idx, i in enumerate(index_stock_cons_df['品种代码'].to_list()):
    log.info(idx+1)
    df = get_stock_tx(code=i, begin_date="20100101", end_date="20260417", is_init=True)
    overwrite_csv(indicators(df), f"{i}.csv")

    data_dir = get_data_dir()
    if idx+1 != len(os.listdir(data_dir)):
        break
    # break
    # time.sleep(math.floor(random.random() * 120))