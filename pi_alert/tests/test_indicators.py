import time
import unittest

from pi_alert import indicators as ind
from pi_alert.alerts import State, detect
from pi_alert.analysis import build_snapshot
from pi_alert.config import Config
from pi_alert.demo import DemoMarket


class TestIndicators(unittest.TestCase):
    def test_sma_ema(self):
        v = [1, 2, 3, 4, 5]
        self.assertEqual(ind.sma(v, 3), [None, None, 2, 3, 4])
        e = ind.ema(v, 3)
        self.assertAlmostEqual(e[2], 2)
        self.assertAlmostEqual(e[4], 4)

    def test_rsi_bounds(self):
        up = [float(i) for i in range(1, 40)]
        self.assertEqual(ind.rsi(up, 14)[-1], 100.0)
        down = list(reversed(up))
        self.assertAlmostEqual(ind.rsi(down, 14)[-1], 0.0)

    def test_ut_bot_flip(self):
        closes = [1.0] * 10 + [1.2] * 5 + [0.8] * 5
        highs = [c * 1.01 for c in closes]
        lows = [c * 0.99 for c in closes]
        stop, sig = ind.ut_bot(closes, highs, lows, 2, 1)
        self.assertIn("SELL", sig[15:])
        self.assertTrue(closes[-1] < stop[-1])

    def test_step_channel_trend(self):
        closes = [1 + 0.05 * ((i % 6) - 3) for i in range(60)] + [2.0 + 0.01 * i for i in range(20)]
        highs = [c * 1.01 for c in closes]
        lows = [c * 0.99 for c in closes]
        _, _, _, tr = ind.step_channel(closes, highs, lows, 3, 0.6)
        self.assertEqual(tr[-1], 1)


class TestPipeline(unittest.TestCase):
    def test_demo_alerts(self):
        cfg = Config(price_levels=[0.11, 0.12])
        md = DemoMarket()
        st = State("/nonexistent/dir/state.json")
        snap = build_snapshot(md, cfg)
        self.assertTrue(0 <= snap["score"] <= 100)
        detect(snap, cfg, st)
        md.advance()
        items = detect(build_snapshot(md, cfg), cfg, st)
        self.assertTrue(any("MẠNH" in t for _, t in items))
        # gửi lại ngay không được trùng cảnh báo biến động (cooldown)
        items2 = detect(build_snapshot(md, cfg), cfg, st)
        self.assertFalse(any("MẠNH" in t for _, t in items2))


if __name__ == "__main__":
    unittest.main()
