"""Các chỉ báo kỹ thuật viết bằng Python thuần (mô phỏng cách tính của TradingView/Pine).

Mọi hàm nhận list số (cũ -> mới) và trả về list cùng độ dài; vị trí chưa đủ dữ liệu = None.
"""
import math


def sma(values, n):
    out, s = [None] * len(values), 0.0
    for i, v in enumerate(values):
        s += v
        if i >= n:
            s -= values[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def ema(values, n):
    out, k, prev = [None] * len(values), 2 / (n + 1), None
    for i, v in enumerate(values):
        if i == n - 1:
            prev = sum(values[:n]) / n
        elif i >= n:
            prev = v * k + prev * (1 - k)
        out[i] = prev
    return out


def rma(values, n):
    """Wilder's moving average (ta.rma) - dùng cho RSI, ATR."""
    out, prev = [None] * len(values), None
    for i, v in enumerate(values):
        if v is None:
            continue
        if prev is None:
            if i >= n - 1 and all(x is not None for x in values[i - n + 1:i + 1]):
                prev = sum(values[i - n + 1:i + 1]) / n
        else:
            prev = (prev * (n - 1) + v) / n
        out[i] = prev
    return out


def true_range(highs, lows, closes):
    tr = []
    for i in range(len(closes)):
        if i == 0:
            tr.append(highs[i] - lows[i])
        else:
            pc = closes[i - 1]
            tr.append(max(highs[i] - lows[i], abs(highs[i] - pc), abs(lows[i] - pc)))
    return tr


def atr(highs, lows, closes, n=14):
    return rma(true_range(highs, lows, closes), n)


def rsi(closes, n=14):
    gains, losses = [None], [None]
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    ag, al = rma(gains, n), rma(losses, n)
    out = [None] * len(closes)
    for i in range(len(closes)):
        if ag[i] is None or al[i] is None:
            continue
        out[i] = 100.0 if al[i] == 0 else 100 - 100 / (1 + ag[i] / al[i])
    return out


def macd(closes, fast=12, slow=26, signal=9):
    ef, es = ema(closes, fast), ema(closes, slow)
    line = [a - b if a is not None and b is not None else None for a, b in zip(ef, es)]
    start = next((i for i, v in enumerate(line) if v is not None), len(line))
    sig_part = ema(line[start:], signal) if len(line) - start >= signal else [None] * (len(line) - start)
    sig = [None] * start + sig_part
    hist = [a - b if a is not None and b is not None else None for a, b in zip(line, sig)]
    return line, sig, hist


def bollinger(closes, n=20, k=2.0):
    mid = sma(closes, n)
    up, lo = [None] * len(closes), [None] * len(closes)
    for i in range(n - 1, len(closes)):
        w = closes[i - n + 1:i + 1]
        m = mid[i]
        sd = math.sqrt(sum((x - m) ** 2 for x in w) / n)
        up[i], lo[i] = m + k * sd, m - k * sd
    return mid, up, lo


def ut_bot(closes, highs, lows, key=2.0, atr_period=1):
    """UT Bot Alerts (QuantNomad) - đường ATR Trailing Stop.

    Trả về (trailing_stop, signals) với signals[i] in {'BUY','SELL',None}.
    BUY: giá cắt lên trên trailing stop; SELL: giá cắt xuống dưới.
    """
    xatr = atr(highs, lows, closes, atr_period)
    stop = [0.0] * len(closes)
    sig = [None] * len(closes)
    for i in range(len(closes)):
        src = closes[i]
        if xatr[i] is None:
            stop[i] = src
            continue
        nloss = key * xatr[i]
        prev = stop[i - 1] if i > 0 else 0.0
        src1 = closes[i - 1] if i > 0 else src
        if src > prev and src1 > prev:
            stop[i] = max(prev, src - nloss)
        elif src < prev and src1 < prev:
            stop[i] = min(prev, src + nloss)
        elif src > prev:
            stop[i] = src - nloss
        else:
            stop[i] = src + nloss
        if i > 0 and xatr[i - 1] is not None:
            if src > stop[i] and src1 <= stop[i - 1]:
                sig[i] = "BUY"
            elif src < stop[i] and src1 >= stop[i - 1]:
                sig[i] = "SELL"
    return stop, sig


def pivots(highs, lows, length):
    """Pivot high/low kiểu ta.pivothigh(len,len): xác nhận sau `length` nến."""
    ph, pl = [None] * len(highs), [None] * len(lows)
    for i in range(length, len(highs) - length):
        wh = highs[i - length:i + length + 1]
        wl = lows[i - length:i + length + 1]
        if highs[i] == max(wh):
            ph[i + length] = highs[i]  # chỉ "biết" tại thời điểm xác nhận
        if lows[i] == min(wl):
            pl[i + length] = lows[i]
    return ph, pl


def step_channel(closes, highs, lows, length=3, mult=0.6, atr_len=100):
    """Step Channel Momentum Trend (mô phỏng theo ý tưởng ChartPrime).

    - Đường giữa dạng bậc thang = trung bình của pivot high & pivot low gần nhất.
    - Kênh trên/dưới = đường giữa ± ATR * mult.
    - Xu hướng: giá đóng cửa trên kênh trên -> TĂNG, dưới kênh dưới -> GIẢM,
      còn lại giữ xu hướng trước (đi ngang trong kênh).
    Lưu ý: đây là bản mô phỏng, giá trị có thể lệch nhẹ so với script gốc trên TradingView.
    """
    n = len(closes)
    ph, pl = pivots(highs, lows, length)
    a = atr(highs, lows, closes, min(atr_len, max(2, n // 2)))
    mid, up, lo, trend = [None] * n, [None] * n, [None] * n, [None] * n
    last_h = last_l = None
    cur = 0
    for i in range(n):
        if ph[i] is not None:
            last_h = ph[i]
        if pl[i] is not None:
            last_l = pl[i]
        if last_h is None or last_l is None or a[i] is None:
            continue
        mid[i] = (last_h + last_l) / 2
        up[i] = mid[i] + a[i] * mult
        lo[i] = mid[i] - a[i] * mult
        if closes[i] > up[i]:
            cur = 1
        elif closes[i] < lo[i]:
            cur = -1
        trend[i] = cur
    return mid, up, lo, trend


def last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None
