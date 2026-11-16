"""Thị trường giả lập để chạy thử bot mà không cần mạng (python -m pi_alert.main --demo)."""
import math
import random
import time

from .exchanges import TF_MS


class DemoMarket:
    name = "DEMO"

    def __init__(self, seed=7, start=0.115):
        self.active = self
        rnd = random.Random(seed)
        n = 120 * 288  # 120 ngày nến 5 phút
        now = int(time.time() * 1000) // 300_000 * 300_000
        self.c5, p = [], start
        for i in range(n):
            drift = 0.00015 * math.sin(i / 3000)
            o = p
            p = max(0.01, p * (1 + drift + rnd.gauss(0, 0.004)))
            hi, lo = max(o, p) * (1 + abs(rnd.gauss(0, 0.002))), min(o, p) * (1 - abs(rnd.gauss(0, 0.002)))
            self.c5.append({"ts": now - (n - i) * 300_000, "open": o, "high": hi, "low": lo,
                            "close": p, "volume": rnd.uniform(5e5, 1.5e6)})
        self.rnd = rnd

    def advance(self):
        """Thêm 1 nến 5 phút biến động mạnh để kích hoạt cảnh báo."""
        last = self.c5[-1]
        o = last["close"]
        c = o * (1 + self.rnd.choice([-1, 1]) * 0.06)
        self.c5.append({"ts": last["ts"] + 300_000, "open": o, "high": max(o, c) * 1.005,
                        "low": min(o, c) * 0.995, "close": c, "volume": 9e6})

    def candles(self, tf, limit=300):
        step = TF_MS[tf]
        out = {}
        for c in self.c5:
            k = c["ts"] // step * step
            if k not in out:
                out[k] = dict(c, ts=k)
            else:
                b = out[k]
                b["high"] = max(b["high"], c["high"])
                b["low"] = min(b["low"], c["low"])
                b["close"] = c["close"]
                b["volume"] += c["volume"]
        return list(out.values())[-limit:]

    def ticker(self):
        d = self.candles("5m", 288)
        return {"last": d[-1]["close"], "open24h": d[0]["open"],
                "high24h": max(x["high"] for x in d), "low24h": min(x["low"] for x in d),
                "vol24h": sum(x["volume"] for x in d)}

    def funding_rate(self):
        return -0.0012
