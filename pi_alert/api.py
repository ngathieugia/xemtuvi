"""Dữ liệu JSON cho dashboard React: snapshot + chuỗi nến và chỉ báo để vẽ biểu đồ."""
import time

from . import indicators as ind
from .analysis import build_snapshot
from .main import buy_plan

TFS = ("5m", "15m", "1h", "4h", "1d")
_cache = {}


def _r(x, n=6):
    return None if x is None else round(x, n)


def chart_series(candles, cfg):
    c = [x["close"] for x in candles]
    h = [x["high"] for x in candles]
    lo = [x["low"] for x in candles]
    v = [x["volume"] for x in candles]
    ut_stop, ut_sig = ind.ut_bot(c, h, lo, cfg.ut_key, cfg.ut_atr)
    _, sc_up, sc_lo, sc_tr = ind.step_channel(c, h, lo, cfg.scmt_len, cfg.scmt_mult)
    e20, e50 = ind.ema(c, 20), ind.ema(c, 50)
    _, bb_up, bb_lo = ind.bollinger(c, 20, 2)
    r = ind.rsi(c, 14)
    _, _, mh = ind.macd(c)
    rows = []
    for i, k in enumerate(candles):
        rows.append({
            "t": k["ts"] // 1000, "o": _r(k["open"]), "h": _r(k["high"]), "l": _r(k["low"]),
            "c": _r(k["close"]), "v": round(v[i], 2),
            "ut": _r(ut_stop[i]), "sig": ut_sig[i],
            "scu": _r(sc_up[i]), "scl": _r(sc_lo[i]), "sct": sc_tr[i],
            "e20": _r(e20[i]), "e50": _r(e50[i]), "bbu": _r(bb_up[i]), "bbl": _r(bb_lo[i]),
            "rsi": _r(r[i], 2), "mh": _r(mh[i], 7),
        })
    return rows[-250:]


def dashboard_payload(md, cfg, tf=None, ttl=20):
    """Có cache `ttl` giây để nhiều người mở trang cũng không gọi sàn liên tục."""
    tf = tf if tf in TFS else cfg.signal_tf
    key = (id(md) if getattr(md, "name", "") == "DEMO" else "live", tf)
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    snap = build_snapshot(md, cfg)
    candles = md.candles(tf, 300)
    out = {
        "updated": int(time.time()), "source": snap["source"], "market": snap["market"], "tf": tf,
        "price": snap["price"], "ticker": snap["ticker"], "funding": snap["funding"],
        "chg": {"15m": snap["chg_15m"], "1h": snap["chg_1h"], "24h": snap["chg_24h"]},
        "signal_tf": cfg.signal_tf, "trend_tf": cfg.trend_tf,
        "sig": snap["sig"], "trend": snap["trend"], "sr": snap["sr"],
        "score": snap["score"], "verdict": snap["verdict"], "why": snap["why"],
        "plan": buy_plan(snap), "levels": cfg.price_levels,
        "params": {"ut_key": cfg.ut_key, "ut_atr": cfg.ut_atr,
                   "scmt_len": cfg.scmt_len, "scmt_mult": cfg.scmt_mult},
        "candles": chart_series(candles, cfg),
    }
    _cache[key] = (time.time(), out)
    return out
