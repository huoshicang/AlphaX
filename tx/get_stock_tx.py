import requests
from dateutil import parser
from utils.transition_secid import to_eastmoney_secid
from tx.enums import AdjustType, KlinePeriod
import pandas as pd
import tx.demjson as demjson
import datetime
import akshare as ak
from datetime import datetime

url = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
# 日期格式
date_format = "%Y-%m-%d"


def get_stock_tx(
        code: str,
        period: KlinePeriod = KlinePeriod.day,
        adjust: AdjustType = AdjustType.qfq,
        begin_date: str = datetime.now().strftime(date_format),
        end_date: str = datetime.now().strftime(date_format),
        timeout: float = 10.0
):
    symbol = to_eastmoney_secid(code).replace('.', '')

    begin_date = parser.parse(begin_date).strftime(date_format)
    end_date = parser.parse(end_date).strftime(date_format)

    # 获取交易日列表
    trade_dates_df = ak.tool_trade_date_hist_sina()

    trade_dates_list = trade_dates_df['trade_date'].to_list()

    begin = trade_dates_list.index(datetime.strptime(begin_date, date_format).date())
    end = trade_dates_list.index(datetime.strptime(end_date, date_format).date())


    params = {
        "_var": f"kline_{period}{adjust}",
        "param": f"{symbol},{period},{begin_date},{end_date},,{adjust}",
        "r": "0.8205512681390605",
    }

    r = requests.get(url, params=params, timeout=timeout)
    data_text = r.text
    data_json = demjson.decode(data_text[data_text.find("={") + 1:])["data"][symbol]
    if "day" in data_json.keys():
        df = pd.DataFrame(data_json["day"])
    elif "hfqday" in data_json.keys():
        df = pd.DataFrame(data_json["hfqday"])
    else:
        df = pd.DataFrame(data_json["qfqday"])

    df.rename(columns={0: '日期', 1: '开盘', 2: '收盘', 3: '最高', 4: '最低', 5: '金额', 6: '空1', 7: '空2', 8: '成交量', 9: '空3',}, inplace=True)

    df.drop(columns=['空1', '空2', '空3'], inplace=True)

    df["股票代码"] = code

    return df


if __name__ == '__main__':
    get_stock_tx("300502", begin_date="2026-04-15", end_date="2026-04-15")
