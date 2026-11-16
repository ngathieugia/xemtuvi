"""Tổng hợp chỉ báo, phát hiện biến động và chấm điểm cơ hội mua tham khảo."""
from datetime import datetime, timedelta, timezone

from . import indicators as ind

VN_TZ = timezone(timedelta(hours=7))


def _cols(candles):
    return ([c["close"] for c in candles], [c["high"] for c in candles],
            [c["low"] for c in candles], [c["volume"] for c in candles])


def fmt_price(p):
    return "-" if p is None else f"{p:.4f}"


def fmt_time(ts_ms):
    return datetime.fromtimestamp(ts_ms / 1000, VN_TZ).strftime("%H:%M %d/%m")


def pct(a, b):
    return (a / b - 1) * 100 if a and b else 0.0


def analyze_tf(candles, cfg):
    """Tính toàn bộ chỉ báo trên một khung thời gian."""
    c, h, l, v = _cols(candles)
    ut_stop, ut_sig = ind.ut_bot(c, h, l, cfg.ut_key, cfg.ut_atr)
    _, sc_up, sc_lo, sc_tr = ind.step_channel(c, h, l, cfg.scmt_len, cfg.scmt_mult)
    r = ind.rsi(c, 14)
    ml, ms, mh = ind.macd(c)
    bm, bu, bl = ind.bollinger(c, 20, 2)
    e20, e50, e200 = ind.ema(c, 20), ind.ema(c, 50), ind.ema(c, min(200, max(2, len(c) - 1)))
    vavg = ind.sma(v, 20)
    a14 = ind.atr(h, l, c, 14)

    last_sig_idx = next((i for i in range(len(ut_sig) - 1, -1, -1) if ut_sig[i]), None)
    return {
        "ts": candles[-1]["ts"], "close": c[-1], "volume": v[-1],
        "ut_stop": ut_stop[-1], "ut_signal": ut_sig[-1],
        "ut_pos": "LONG" if c[-1] > ut_stop[-1] else "SHORT",
        "ut_last_signal": ut_sig[last_sig_idx] if last_sig_idx is not None else None,
        "ut_last_signal_ts": candles[last_sig_idx]["ts"] if last_sig_idx is not None else None,
        "ut_last_signal_price": c[last_sig_idx] if last_sig_idx is not None else None,
        "sc_up": sc_up[-1], "sc_lo": sc_lo[-1], "sc_trend": sc_tr[-1],
        "sc_trend_prev": sc_tr[-2] if len(sc_tr) > 1 else None,
        "rsi": r[-1], "rsi_prev": r[-2] if len(r) > 1 else None,
        "macd": ml[-1], "macd_sig": ms[-1], "macd_hist": mh[-1],
        "macd_hist_prev": mh[-2] if len(mh) > 1 else None,
        "bb_mid": bm[-1], "bb_up": bu[-1], "bb_lo": bl[-1],
        "ema20": e20[-1], "ema50": e50[-1], "ema200": e200[-1],
        "vol_avg": vavg[-2] if len(vavg) > 1 else None,  # TB 20 nến trước đó
        "atr": a14[-1],
    }


def support_resistance(daily, price, lookback=60, length=3):
    """Hỗ trợ / kháng cự gần nhất từ pivot khung ngày."""
    d = daily[-lookback:]
    c, h, l, _ = _cols(d)
    ph, pl = ind.pivots(h, l, length)
    lows = sorted({round(x, 4) for x in pl if x is not None} | {round(min(l), 4)})
    highs = sorted({round(x, 4) for x in ph if x is not None} | {round(max(h), 4)})
    sup = [x for x in lows if x < price]
    res = [x for x in highs if x > price]
    return {
        "supports": sorted(sup, reverse=True)[:3],
        "resistances": res[:3],
        "low_range": min(l), "high_range": max(h),
    }


def opportunity_score(sig, trend, sr, price, funding):
    """Chấm điểm 0-100 mức độ hấp dẫn để MUA tham khảo (không phải lời khuyên đầu tư).

    Nguyên tắc: ưu tiên mua khi giá về vùng hỗ trợ/quá bán và có tín hiệu đảo chiều,
    tránh mua đuổi khi giá đã tăng nóng, quá mua.
    """
    score, why = 50, []

    def add(points, text):
        nonlocal score
        score += points
        why.append(("+" if points > 0 else "") + f"{points} {text}")

    # 1. Xu hướng lớn
    if trend["ema50"] and trend["ema200"]:
        if price > trend["ema50"] > trend["ema200"]:
            add(10, f"Xu hướng lớn TĂNG: giá > EMA50 > EMA200")
        elif price < trend["ema50"] < trend["ema200"]:
            add(-10, "Xu hướng lớn GIẢM: giá < EMA50 < EMA200")
    if trend["sc_trend"] == 1:
        add(5, "Step Channel khung lớn: TĂNG")
    elif trend["sc_trend"] == -1:
        add(-5, "Step Channel khung lớn: GIẢM")

    # 2. Tín hiệu khung nhỏ
    if sig["ut_pos"] == "LONG":
        add(8, "UT Bot đang ở trạng thái MUA")
    else:
        add(-8, "UT Bot đang ở trạng thái BÁN")
    if sig["sc_trend"] == 1:
        add(5, "Step Channel khung tín hiệu: TĂNG")
    elif sig["sc_trend"] == -1:
        add(-5, "Step Channel khung tín hiệu: GIẢM")
    if sig["macd_hist"] is not None and sig["macd_hist_prev"] is not None:
        if sig["macd_hist"] > 0 and sig["macd_hist"] > sig["macd_hist_prev"]:
            add(4, "MACD động lượng tăng")
        elif sig["macd_hist"] < 0 and sig["macd_hist"] < sig["macd_hist_prev"]:
            add(-4, "MACD động lượng giảm")

    # 3. Vùng giá (mua rẻ, không mua đuổi)
    r = trend["rsi"]
    if r is not None:
        if r < 30:
            add(12, f"RSI khung lớn {r:.0f} - QUÁ BÁN (vùng giá rẻ)")
        elif r < 40:
            add(6, f"RSI khung lớn {r:.0f} - thấp")
        elif r > 75:
            add(-15, f"RSI khung lớn {r:.0f} - QUÁ MUA, tránh mua đuổi")
        elif r > 65:
            add(-7, f"RSI khung lớn {r:.0f} - khá cao")
    rs = sig["rsi"]
    if rs is not None and rs > 70:
        add(-10, f"RSI khung tín hiệu {rs:.0f} - vừa tăng nóng, chờ nhịp chỉnh")
    elif rs is not None and rs < 30:
        add(5, f"RSI khung tín hiệu {rs:.0f} - quá bán ngắn hạn")
    if sig["bb_lo"] and price <= sig["bb_lo"]:
        add(6, "Giá chạm/thủng dải Bollinger dưới")
    elif sig["bb_up"] and price >= sig["bb_up"]:
        add(-6, "Giá vượt dải Bollinger trên (nóng)")
    rng = sr["high_range"] - sr["low_range"]
    if rng > 0:
        posr = (price - sr["low_range"]) / rng
        if posr < 0.25:
            add(8, f"Giá ở {posr*100:.0f}% đáy biên độ 60 ngày (gần đáy)")
        elif posr > 0.8:
            add(-8, f"Giá ở {posr*100:.0f}% biên độ 60 ngày (gần đỉnh)")
    if sr["supports"]:
        dist = pct(price, sr["supports"][0])
        if dist < 3:
            add(5, f"Sát hỗ trợ {fmt_price(sr['supports'][0])} (cách {dist:.1f}%)")

    # 4. Funding (thị trường phái sinh)
    if funding is not None:
        if funding < -0.0005:
            add(4, f"Funding âm {funding*100:.3f}% - phe bán đông, dễ bật ngược")
        elif funding > 0.001:
            add(-4, f"Funding dương cao {funding*100:.3f}% - phe mua quá đông")

    score = max(0, min(100, score))
    if score >= 70:
        verdict = "🟢 THUẬN LỢI - có thể mua rải từng phần (DCA), đặt cắt lỗ dưới hỗ trợ"
    elif score >= 55:
        verdict = "🟡 KHÁ - mua thăm dò lượng nhỏ, chờ xác nhận thêm"
    elif score >= 40:
        verdict = "⚪ TRUNG TÍNH - quan sát, chưa nên vào lệnh lớn"
    else:
        verdict = "🔴 BẤT LỢI - đứng ngoài, chờ giá về hỗ trợ / tín hiệu đảo chiều"
    return score, verdict, why


def build_snapshot(md, cfg):
    tk = md.ticker()
    c5 = md.candles("5m", 300)
    sig_c = md.candles(cfg.signal_tf, 300)
    tr_c = md.candles(cfg.trend_tf, 300)
    d1 = md.candles("1d", 120)
    funding = md.funding_rate()
    price = tk["last"]

    def change(mins):
        target = c5[-1]["ts"] + 300_000 - mins * 60_000
        ref = next((x for x in reversed(c5) if x["ts"] <= target), None)
        return pct(price, ref["open"]) if ref else 0.0

    sig = analyze_tf(sig_c, cfg)
    trend = analyze_tf(tr_c, cfg)
    sr = support_resistance(d1, price)
    score, verdict, why = opportunity_score(sig, trend, sr, price, funding)
    return {
        "source": md.active.name, "market": cfg.market, "price": price, "ticker": tk,
        "chg_15m": change(15), "chg_1h": change(60), "chg_24h": pct(price, tk["open24h"]),
        "funding": funding, "sig": sig, "trend": trend, "sr": sr,
        "score": score, "verdict": verdict, "why": why,
        "c5": c5,
    }
