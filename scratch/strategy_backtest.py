import pandas as pd
import numpy as np

# ======================
# 参数
# ======================
FILE_PATH = r"D:\code_project\pythonProject\data\300308.csv"
INIT_CASH = 1_000_000
SLIPPAGE = 0.001  # 0.1%

# ======================
# 读取数据
# ======================
df = pd.read_csv(FILE_PATH, encoding="gbk")
df.replace('-', np.nan, inplace=True)

# 日期处理
df['日期'] = pd.to_datetime(df['日期'], format='mixed', errors='coerce')
df = df.sort_values('日期').reset_index(drop=True)
df['日期'] = df['日期'].dt.strftime('%Y/%m/%d')

# 数值列
cols = [
    '开盘_qfq','收盘_qfq','最高_qfq','最低_qfq',
    '开盘_hfq','收盘_hfq','最高_hfq','最低_hfq',
    'zsqs','zxdk'
]
df[cols] = df[cols].astype(float)

# ======================
# 复权因子
# ======================
df['adj_factor'] = df['收盘_hfq'] / df['收盘_hfq']

# ======================
# KDJ
# ======================
N = 9
low_n = df['最低_hfq'].rolling(N).min()
high_n = df['最高_hfq'].rolling(N).max()

rsv = np.where(
    (high_n - low_n) == 0,
    0,
    (df['收盘_hfq'] - low_n) / (high_n - low_n) * 100
)

df['K'] = pd.Series(rsv).ewm(alpha=1/3).mean()
df['D'] = df['K'].ewm(alpha=1/3).mean()
df['J'] = 3 * df['K'] - 2 * df['D']

# ======================
# 初始化
# ======================
cash = INIT_CASH
position = 0
holding = False

df['signal'] = np.nan
df['position'] = 0
df['cash'] = 0.0
df['equity_value'] = 0.0
df['total_asset'] = 0.0

# ======================
# 回测主循环
# ======================
for i in range(len(df)):
    today = df.loc[i]

    # ======================
    # 1️⃣ 复权调仓（最先执行）
    # ======================
    if i > 0 and position > 0:
        prev_factor = df.loc[i - 1, 'adj_factor']
        curr_factor = df.loc[i, 'adj_factor']

        if not pd.isna(prev_factor) and not pd.isna(curr_factor):
            ratio = curr_factor / prev_factor

            if abs(ratio - 1) > 1e-6:
                position = int(position * ratio)

    # ======================
    # 2️⃣ 记录资产（收盘）
    # ======================
    close_price = today['收盘_qfq']
    equity_value = position * close_price
    total_asset = cash + equity_value

    df.loc[i, 'position'] = position
    df.loc[i, 'cash'] = cash
    df.loc[i, 'equity_value'] = equity_value
    df.loc[i, 'total_asset'] = total_asset

    # 最后一行不交易
    if i == len(df) - 1:
        break

    tomorrow = df.loc[i + 1]

    # 跳过无效数据
    if pd.isna(today['J']) or pd.isna(today['zxdk']) or pd.isna(today['zsqs']):
        continue

    prev_close = today['收盘_hfq']
    open_price = tomorrow['开盘_hfq']

    # 创业板涨跌停 20%
    limit_up = prev_close * 1.2
    limit_down = prev_close * 0.8

    # ======================
    # 买入逻辑（T判断 → T+1执行）
    # ======================
    if not holding:
        cond_buy = (
            today['J'] <= 13 and
            today['收盘_hfq'] >= today['zxdk'] and
            today['zsqs'] > today['zxdk']
        )

        if cond_buy:
            if open_price < limit_up:
                buy_price = open_price * (1 + SLIPPAGE)

                shares = int(cash / buy_price / 100) * 100
                if shares > 0:
                    cost = shares * buy_price

                    cash -= cost
                    position = shares
                    holding = True

                    df.loc[i + 1, 'signal'] = 1

    # ======================
    # 卖出逻辑（T判断 → T+1执行）
    # ======================
    else:
        cond_sell = today['收盘_hfq'] < today['zxdk']

        if cond_sell:
            if open_price > limit_down:
                sell_price = open_price * (1 - SLIPPAGE)

                cash += position * sell_price
                position = 0
                holding = False

                df.loc[i + 1, 'signal'] = 0

# ======================
# 保留两位小数（输出用）
# ======================
cols_round = [
    'K','D','J',
    'position','cash',
    'equity_value','total_asset','adj_factor'
]
df[cols_round] = df[cols_round].round(2)

# ======================
# 最终资金
# ======================
final_value = cash + position * df.iloc[-1]['收盘_hfq']
print(f"最终资金: {final_value:.2f}")

# ======================
# 保存
# ======================
output_path = FILE_PATH.replace('.csv', '_result.csv')
cols_round = ['K', 'D', 'J', 'position', 'cash', 'equity_value', 'total_asset']
df[cols_round] = df[cols_round].round(2)
df.to_csv(output_path, index=False, encoding='gbk')

print(f"结果已保存到: {output_path}")