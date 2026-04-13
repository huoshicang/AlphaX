import pandas as pd
from collections import deque
from typing import List, Union

class ZhiXingIncremental:
    """
    知行指标增量计算器
    只计算最新一行数据，历史数据不重复计算
    """

    def __init__(self, hist_close_series: List[Union[float, int, str]], max_period: int = 114):
        """
        参数:
            hist_close_series: 历史收盘价序列（长度应 >= max_period，否则部分指标为None）
            max_period: 最大均线周期（默认114）
        """
        # 将所有收盘价转为 float
        self.close_list = [float(x) for x in hist_close_series]
        self.max_period = max_period

        # 1. 收盘价队列（用于 MA114 及切片）
        self.close_deque = deque(self.close_list[-max_period:], maxlen=max_period)

        # 2. 各均线窗口的 deque 与当前和（用于 O(1) 增量更新）
        self.ma_windows = {}
        for window in [14, 28, 57, 60, 114]:
            if len(self.close_list) >= window:
                window_deque = deque(self.close_list[-window:], maxlen=window)
                window_sum = sum(window_deque)
            else:
                window_deque = None
                window_sum = None
            self.ma_windows[window] = {'deque': window_deque, 'sum': window_sum}

        # 3. EMA 状态初始化
        self.ema13_prev = None          # EMA(close,13) 上一值
        self.ema10_prev = None          # 第一层 EMA(close,10) 上一值
        self.ema10_2_prev = None        # 第二层 EMA(ema10,10) 上一值

        self._init_ema(self.close_list)

    def _init_ema(self, close_list: List[float]):
        """根据完整历史序列初始化 EMA 递推状态"""
        alpha13 = 2 / (13 + 1)
        alpha10 = 2 / (10 + 1)

        # 计算 EMA13 和双重 EMA
        for price in close_list:
            # EMA13
            if self.ema13_prev is None:
                ema13 = price
            else:
                ema13 = price * alpha13 + self.ema13_prev * (1 - alpha13)
            self.ema13_prev = ema13

            # 第一层 EMA(close,10)
            if self.ema10_prev is None:
                ema10 = price
            else:
                ema10 = price * alpha10 + self.ema10_prev * (1 - alpha10)
            self.ema10_prev = ema10

            # 第二层 EMA(ema10,10)
            if self.ema10_2_prev is None:
                ema10_2 = ema10
            else:
                ema10_2 = ema10 * alpha10 + self.ema10_2_prev * (1 - alpha10)
            self.ema10_2_prev = ema10_2

    def _update_ma(self, window: int, new_price: float):
        """
        增量更新指定窗口的移动平均和
        返回更新后的平均值，若窗口未就绪返回 None
        """
        win = self.ma_windows.get(window)
        if win is None or win['deque'] is None:
            return None
        dq = win['deque']
        old_sum = win['sum']
        # 如果队列已满，需要弹出最旧值
        if len(dq) == dq.maxlen:
            old_price = dq[0]
            new_sum = old_sum - old_price + new_price
        else:
            new_sum = old_sum + new_price
        dq.append(new_price)
        win['sum'] = new_sum
        return new_sum / len(dq)

    def add_new(self, new_close: Union[float, int, str]) -> dict:
        """
        追加一条新收盘价，返回新行的指标字典
        """
        new_close = float(new_close)

        # 1. 更新收盘价主队列（用于后续计算）
        old_price_for_114 = None
        if len(self.close_deque) == self.close_deque.maxlen:
            old_price_for_114 = self.close_deque[0]
        self.close_deque.append(new_close)

        # 2. 增量更新各均线
        ma14 = self._update_ma(14, new_close)
        ma28 = self._update_ma(28, new_close)
        ma57 = self._update_ma(57, new_close)
        ma60 = self._update_ma(60, new_close)
        ma114 = self._update_ma(114, new_close)

        # 3. 增量更新 EMA13
        alpha13 = 2 / (13 + 1)
        if self.ema13_prev is None:
            ema13 = new_close
        else:
            ema13 = new_close * alpha13 + self.ema13_prev * (1 - alpha13)
        self.ema13_prev = ema13

        # 4. 增量更新双重 EMA(EMA(close,10),10)
        alpha10 = 2 / (10 + 1)
        if self.ema10_prev is None:
            ema10 = new_close
        else:
            ema10 = new_close * alpha10 + self.ema10_prev * (1 - alpha10)
        self.ema10_prev = ema10

        if self.ema10_2_prev is None:
            ema10_2 = ema10
        else:
            ema10_2 = ema10 * alpha10 + self.ema10_2_prev * (1 - alpha10)
        self.ema10_2_prev = ema10_2
        zsqs = ema10_2

        # 5. 计算 zxdk = (MA14+MA28+MA57+MA114)/4
        if None in (ma14, ma28, ma57, ma114):
            zxdk = None
        else:
            zxdk = (ma14 + ma28 + ma57 + ma114) / 4

        return {
            'zsqs': round(zsqs, 2),
            'MA60': round(ma60, 2) if ma60 is not None else None,
            'EMA13': round(ema13, 2),
            'zxdk': round(zxdk, 2) if zxdk is not None else None,
        }


# ------------------- 使用示例 -------------------
if __name__ == '__main__':
    # 假设已有114行历史数据（包含收盘价，可能为字符串）
    df_history = pd.DataFrame({
        '日期': pd.date_range('2024-01-01', periods=114),
        '收盘': [str(10 + i * 0.1) for i in range(114)]  # 模拟字符串收盘价
    })

    # 初始化增量器（自动转换字符串为浮点数）
    hist_close = df_history['收盘'].tolist()
    inc = ZhiXingIncremental(hist_close, max_period=114)

    # 新的一行数据（只有收盘价）
    new_close = '21.5'   # 也可以是 21.5 或 21.5
    new_indicators = inc.add_new(new_close)

    # 将新行和指标合并到原DataFrame（可选）
    new_row = pd.DataFrame([{'日期': pd.Timestamp('2024-04-28'), '收盘': float(new_close), **new_indicators}])
    df_updated = pd.concat([df_history, new_row], ignore_index=True)

    print(df_updated.tail())
    print("\n最新一行指标：", new_indicators)