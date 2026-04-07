import pandas as pd

# ---------------------- 1. 数据预处理 ----------------------
def preprocess_data(df):
    df = df.copy()
    # 转换日期格式 + 按股票+日期排序（必须，否则均线计算错误）
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values(by=['股票代码', '日期'], ascending=[True, True]).reset_index(drop=True)
    return df


# ---------------------- 2. 均线函数（数据不足返回NaN） ----------------------
def MA(series, n):
    """
    简单移动平均线 MA
    min_periods=n：数据长度不足n时，返回NaN
    """
    return series.rolling(window=n, min_periods=n).mean()


def EMA(series, n):
    """
    指数移动平均线 EMA（通达信标准算法）
    数据不足时自动返回NaN
    """
    return series.ewm(span=n, adjust=False).mean()


# ---------------------- 3. 计算知行指标（最终参数+保留2位小数） ----------------------
def indicators(df):
    df = preprocess_data(df)
    # 按股票分组计算（支持多只股票）
    grouped = df.groupby('股票代码', group_keys=False)

    # ✅ 你指定的核心参数
    M1, M2, M3, M4 = 14, 28, 57, 114

    # 1. 知行短期趋势线：EMA(EMA(收盘,10),10)
    df['zsqs'] = grouped['收盘'].transform(lambda x: EMA(EMA(x, 10), 10)).round(2)

    # 2. 备用均线：60日MA、13日EMA
    df['MA60'] = grouped['收盘'].transform(lambda x: MA(x, 60)).round(2)
    df['EMA13'] = grouped['收盘'].transform(lambda x: EMA(x, 13)).round(2)

    # 3. ✅ 知行多空线：(MA14+MA28+MA57+MA114)/4
    ma14 = grouped['收盘'].transform(lambda x: MA(x, M1))
    ma28 = grouped['收盘'].transform(lambda x: MA(x, M2))
    ma57 = grouped['收盘'].transform(lambda x: MA(x, M3))
    ma114 = grouped['收盘'].transform(lambda x: MA(x, M4))
    df['zxdk'] = ((ma14 + ma28 + ma57 + ma114) / 4).round(2)

    return df