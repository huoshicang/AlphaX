import pandas as pd



def kline_to_dataframe(klines: list, code: str) -> pd.DataFrame:
    """
    把东方财富原始K线数据转为标准 pandas DataFrame
    字段、顺序、类型完全对齐行业规范
    """
    if not klines:
        return pd.DataFrame()

    temp_df = pd.DataFrame([item.split(",") for item in klines])
    temp_df["股票代码"] = code
    temp_df.columns = [
        "日期", "开盘", "收盘", "最高", "最低",
        "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率", "股票代码"
    ]

    # 类型转换
    temp_df["日期"] = pd.to_datetime(temp_df["日期"], errors="coerce").dt.strftime("%Y/%m/%d")
    temp_df["开盘"] = pd.to_numeric(temp_df["开盘"], errors="coerce")
    temp_df["收盘"] = pd.to_numeric(temp_df["收盘"], errors="coerce")
    temp_df["最高"] = pd.to_numeric(temp_df["最高"], errors="coerce")
    temp_df["最低"] = pd.to_numeric(temp_df["最低"], errors="coerce")
    temp_df["成交量"] = pd.to_numeric(temp_df["成交量"], errors="coerce")
    temp_df["成交额"] = pd.to_numeric(temp_df["成交额"], errors="coerce")
    temp_df["振幅"] = pd.to_numeric(temp_df["振幅"], errors="coerce")
    temp_df["涨跌幅"] = pd.to_numeric(temp_df["涨跌幅"], errors="coerce")
    temp_df["涨跌额"] = pd.to_numeric(temp_df["涨跌额"], errors="coerce")
    temp_df["换手率"] = pd.to_numeric(temp_df["换手率"], errors="coerce")

    # 添加自定义列，默认值为 "-"
    temp_df["zsqs"] = "-"
    temp_df["MA60"] = "-"
    temp_df["EMA13"] = "-"
    temp_df["zxdk"] = "-"

    # 最终列顺序
    return temp_df[[
        "日期", "股票代码", "开盘", "收盘", "最高",
        "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率", "zsqs", "MA60", "EMA13", "zxdk"
    ]]