import time
import unittest
from unittest import mock

from pi_alert import exchanges


class TestParsers(unittest.TestCase):
    def test_okx_candles_sorted_and_closed(self):
        now = int(time.time() * 1000) // 900_000 * 900_000
        data = {"data": [[str(now), "1", "1", "1", "1", "5"],            # nến đang chạy -> bỏ
                         [str(now - 900_000), "0.12", "0.13", "0.11", "0.125", "10"],
                         [str(now - 1_800_000), "0.11", "0.12", "0.10", "0.12", "9"]]}
        with mock.patch.object(exchanges, "_get", return_value=data):
            c = exchanges.OKX("swap").candles("15m")
        self.assertEqual(len(c), 2)
        self.assertLess(c[0]["ts"], c[1]["ts"])
        self.assertEqual(c[1]["close"], 0.125)

    def test_gate_column_order(self):
        ts = int(time.time()) - 3600
        row = [str(ts), "1000", "0.125", "0.13", "0.11", "0.12", "8000", "true"]
        with mock.patch.object(exchanges, "_get", return_value=[row]):
            c = exchanges.Gate("spot").candles("15m")[0]
        self.assertEqual((c["open"], c["high"], c["low"], c["close"]), (0.12, 0.13, 0.11, 0.125))

    def test_fallback(self):
        md = exchanges.MarketData("okx", "swap")
        with mock.patch.object(exchanges.OKX, "ticker", side_effect=RuntimeError("down")), \
             mock.patch.object(exchanges.Bitget, "ticker", return_value={"last": 0.12}):
            self.assertEqual(md.ticker()["last"], 0.12)
        self.assertEqual(md.active.name, "Bitget")


if __name__ == "__main__":
    unittest.main()
