import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid
from pyecharts.options import MarkPointItem


# =========================
# 数据加载
# =========================
def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, encoding="gbk")
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期")
    df["日期_str"] = df["日期"].dt.strftime("%Y-%m-%d")
    return df


# =========================
# 买卖点构建
# =========================
def build_signal_points(df: pd.DataFrame):
    buy_points = []
    sell_points = []

    for _, row in df.iterrows():
        if row["signal"] == 1:
            buy_points.append(
                MarkPointItem(
                    coord=[row["日期_str"], row["最低_qfq"]],
                    value="买",
                    symbol="triangle",
                    symbol_size=12,
                    itemstyle_opts=opts.ItemStyleOpts(color="red"),
                )
            )
        elif row["signal"] == 0:
            sell_points.append(
                MarkPointItem(
                    coord=[row["日期_str"], row["最高_qfq"]],
                    value="卖",
                    symbol="triangle",
                    symbol_rotate=180,
                    symbol_size=12,
                    itemstyle_opts=opts.ItemStyleOpts(color="blue"),
                )
            )

    return buy_points, sell_points


# =========================
# K线图
# =========================
def build_kline(df: pd.DataFrame, buy_points, sell_points):
    kline_data = df[["开盘_qfq", "收盘_qfq", "最低_qfq", "最高_qfq"]].values.tolist()

    kline = (
        Kline()
        .add_xaxis(df["日期_str"].tolist())
        .add_yaxis(
            "K线",
            kline_data,
            markpoint_opts=opts.MarkPointOpts(data=buy_points + sell_points),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="K线 + 策略"),
            datazoom_opts=[
                opts.DataZoomOpts(type_="inside", range_start=60, range_end=100),
                opts.DataZoomOpts(range_start=60, range_end=100),
            ],
            yaxis_opts=opts.AxisOpts(is_scale=True),
        )
    )

    # MA / EMA
    ma_line = (
        Line()
        .add_xaxis(df["日期_str"].tolist())
        .add_yaxis("MA60", df["MA60"].tolist(), is_smooth=True)
        .add_yaxis("EMA13", df["EMA13"].tolist(), is_smooth=True)
    )

    return kline.overlap(ma_line)


# =========================
# 成交量
# =========================
def build_volume(df: pd.DataFrame):
    return (
        Bar()
        .add_xaxis(df["日期_str"].tolist())
        .add_yaxis("成交量", df["成交量"].tolist())
    )


# =========================
# KDJ
# =========================
def build_kdj(df: pd.DataFrame):
    return (
        Line()
        .add_xaxis(df["日期_str"].tolist())
        .add_yaxis("K", df["K"].tolist())
        .add_yaxis("D", df["D"].tolist())
        .add_yaxis("J", df["J"].tolist())
    )


# =========================
# 资金曲线
# =========================
def build_asset(df: pd.DataFrame):
    return (
        Line()
        .add_xaxis(df["日期_str"].tolist())
        .add_yaxis("总资产", df["total_asset"].tolist(), is_smooth=True)
    )


# =========================
# Grid组合
# =========================
def build_grid(kline, volume, kdj, asset):
    grid = Grid(init_opts=opts.InitOpts(width="1400px", height="900px"))

    grid.add(
        kline,
        grid_opts=opts.GridOpts(pos_left="8%", pos_right="5%", height="50%"),
    )

    grid.add(
        volume,
        grid_opts=opts.GridOpts(pos_left="8%", pos_right="5%", pos_top="55%", height="12%"),
    )

    grid.add(
        kdj,
        grid_opts=opts.GridOpts(pos_left="8%", pos_right="5%", pos_top="70%", height="12%"),
    )

    grid.add(
        asset,
        grid_opts=opts.GridOpts(pos_left="8%", pos_right="5%", pos_top="85%", height="12%"),
    )

    return grid


# =========================
# 主入口
# =========================
def main():
    file_path = r"D:\code_project\pythonProject\data\300308_result.csv"

    df = load_data(file_path)

    buy_points, sell_points = build_signal_points(df)

    kline = build_kline(df, buy_points, sell_points)
    volume = build_volume(df)
    kdj = build_kdj(df)
    asset = build_asset(df)

    grid = build_grid(kline, volume, kdj, asset)

    grid.render("result.html")


if __name__ == "__main__":
    main()