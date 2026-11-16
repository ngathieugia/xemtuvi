"""Lấy dữ liệu giá PI/USDT từ các sàn công khai (không cần API key).

Mỗi nến trả về dạng dict: {ts (ms), open, high, low, close, volume}, sắp xếp cũ -> mới,
CHỈ gồm các nến đã đóng (tránh tín hiệu "vẽ lại" của nến đang chạy).
"""
import time

import requests

TIMEOUT = 15
HEADERS = {"User-Agent": "pi-price-alert/1.0"}
TF_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
         "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}


def _get(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _closed_only(candles, tf):
    now = int(time.time() * 1000)
    step = TF_MS[tf]
    return [c for c in candles if c["ts"] + step <= now]


def _c(ts, o, h, l, cl, v):
    return {"ts": int(ts), "open": float(o), "high": float(h), "low": float(l),
            "close": float(cl), "volume": float(v)}


class OKX:
    name = "OKX"
    BASE = "https://www.okx.com"
    BAR = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1H", "4h": "4H", "1d": "1Dutc"}

    def __init__(self, market):
        self.inst = "PI-USDT-SWAP" if market == "swap" else "PI-USDT"
        self.market = market

    def candles(self, tf, limit=300):
        d = _get(f"{self.BASE}/api/v5/market/candles",
                 {"instId": self.inst, "bar": self.BAR[tf], "limit": min(limit, 300)})
        rows = [_c(r[0], r[1], r[2], r[3], r[4], r[5]) for r in d.get("data", [])]
        rows.reverse()
        return _closed_only(rows, tf)

    def ticker(self):
        d = _get(f"{self.BASE}/api/v5/market/ticker", {"instId": self.inst})["data"][0]
        return {"last": float(d["last"]), "open24h": float(d["open24h"]),
                "high24h": float(d["high24h"]), "low24h": float(d["low24h"]),
                "vol24h": float(d.get("volCcy24h") or d.get("vol24h") or 0)}

    def funding_rate(self):
        if self.market != "swap":
            return None
        d = _get(f"{self.BASE}/api/v5/public/funding-rate", {"instId": self.inst})["data"][0]
        return float(d["fundingRate"])


class Bitget:
    name = "Bitget"
    BASE = "https://api.bitget.com"
    GRAN = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1H", "4h": "4H", "1d": "1D"}
    GRAN_SPOT = {"1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
                 "1h": "1h", "4h": "4h", "1d": "1day"}

    def __init__(self, market):
        self.market = market

    def candles(self, tf, limit=300):
        if self.market == "swap":
            d = _get(f"{self.BASE}/api/v2/mix/market/candles",
                     {"symbol": "PIUSDT", "productType": "USDT-FUTURES",
                      "granularity": self.GRAN[tf], "limit": min(limit, 1000)})
        else:
            d = _get(f"{self.BASE}/api/v2/spot/market/candles",
                     {"symbol": "PIUSDT", "granularity": self.GRAN_SPOT[tf], "limit": min(limit, 1000)})
        rows = [_c(r[0], r[1], r[2], r[3], r[4], r[5]) for r in d.get("data", [])]
        rows.sort(key=lambda x: x["ts"])
        return _closed_only(rows, tf)

    def ticker(self):
        if self.market == "swap":
            d = _get(f"{self.BASE}/api/v2/mix/market/ticker",
                     {"symbol": "PIUSDT", "productType": "USDT-FUTURES"})["data"][0]
            last = float(d["lastPr"])
            open24 = float(d.get("open24h") or last)
        else:
            d = _get(f"{self.BASE}/api/v2/spot/market/tickers", {"symbol": "PIUSDT"})["data"][0]
            last = float(d["lastPr"])
            open24 = float(d.get("open") or last)
        return {"last": last, "open24h": open24, "high24h": float(d["high24h"]),
                "low24h": float(d["low24h"]), "vol24h": float(d.get("quoteVolume") or 0)}

    def funding_rate(self):
        if self.market != "swap":
            return None
        d = _get(f"{self.BASE}/api/v2/mix/market/current-fund-rate",
                 {"symbol": "PIUSDT", "productType": "USDT-FUTURES"})["data"][0]
        return float(d["fundingRate"])


class MEXC:
    """Giao ngay MEXC (không hỗ trợ funding)."""
    name = "MEXC"
    BASE = "https://api.mexc.com"
    IV = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "60m", "4h": "4h", "1d": "1d"}

    def __init__(self, market):
        self.market = "spot"

    def candles(self, tf, limit=300):
        d = _get(f"{self.BASE}/api/v3/klines",
                 {"symbol": "PIUSDT", "interval": self.IV[tf], "limit": min(limit, 1000)})
        return _closed_only([_c(r[0], r[1], r[2], r[3], r[4], r[5]) for r in d], tf)

    def ticker(self):
        d = _get(f"{self.BASE}/api/v3/ticker/24hr", {"symbol": "PIUSDT"})
        return {"last": float(d["lastPrice"]), "open24h": float(d["openPrice"]),
                "high24h": float(d["highPrice"]), "low24h": float(d["lowPrice"]),
                "vol24h": float(d.get("quoteVolume") or 0)}

    def funding_rate(self):
        return None


class Gate:
    """Giao ngay Gate.io (không hỗ trợ funding)."""
    name = "Gate"
    BASE = "https://api.gateio.ws/api/v4"

    def __init__(self, market):
        self.market = "spot"

    def candles(self, tf, limit=300):
        d = _get(f"{self.BASE}/spot/candlesticks",
                 {"currency_pair": "PI_USDT", "interval": tf, "limit": min(limit, 1000)})
        # [ts_giây, quote_vol, close, high, low, open, base_vol, closed]
        rows = [_c(int(r[0]) * 1000, r[5], r[3], r[4], r[2], r[6]) for r in d]
        return _closed_only(rows, tf)

    def ticker(self):
        d = _get(f"{self.BASE}/spot/tickers", {"currency_pair": "PI_USDT"})[0]
        last = float(d["last"])
        pct = float(d.get("change_percentage") or 0)
        return {"last": last, "open24h": last / (1 + pct / 100), "high24h": float(d["high_24h"]),
                "low24h": float(d["low_24h"]), "vol24h": float(d.get("quote_volume") or 0)}

    def funding_rate(self):
        return None


EXCHANGES = {"okx": OKX, "bitget": Bitget, "mexc": MEXC, "gate": Gate}


class MarketData:
    """Thử sàn ưu tiên trước, lỗi thì tự chuyển sang sàn dự phòng."""

    def __init__(self, preferred, market):
        order = [preferred] + [k for k in EXCHANGES if k != preferred]
        self.sources = [EXCHANGES[k](market) for k in order if k in EXCHANGES]
        self.active = self.sources[0]

    def _try(self, method, *args):
        last_err = None
        for src in [self.active] + [s for s in self.sources if s is not self.active]:
            try:
                res = getattr(src, method)(*args)
                self.active = src
                return res
            except Exception as e:  # noqa: BLE001 - thử sàn khác
                last_err = e
        raise RuntimeError(f"Không lấy được dữ liệu ({method}) từ mọi sàn: {last_err}")

    def candles(self, tf, limit=300):
        return self._try("candles", tf, limit)

    def ticker(self):
        return self._try("ticker")

    def funding_rate(self):
        try:
            return self.active.funding_rate()
        except Exception:  # noqa: BLE001
            return None
