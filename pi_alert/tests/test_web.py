import os
import tempfile
import unittest
from unittest import mock

try:
    import flask  # noqa: F401
except ImportError:  # pragma: no cover
    flask = None


@unittest.skipIf(flask is None, "chưa cài flask")
class TestWeb(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = mock.patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": "999", "WEBHOOK_SECRET": "abc",
            "CRON_SECRET": "k1", "DRY_RUN": "1", "STATE_FILE": os.path.join(self.tmp, "s.json")})
        self.env.start()
        from pi_alert import web
        self.web = web
        self.c = web.create_app().test_client()

    def tearDown(self):
        self.env.stop()

    def test_auth(self):
        self.assertEqual(self.c.post("/pi/webhook", json={}).status_code, 403)
        self.assertEqual(self.c.get("/pi/cron?key=x").status_code, 403)

    def test_webhook_only_owner(self):
        from pi_alert.demo import DemoMarket
        sent = []
        with mock.patch.object(self.web, "MarketData", lambda *a: DemoMarket()), \
             mock.patch.object(self.web.Telegram, "send", lambda s, t, cid=None: sent.append(cid)):
            h = {"X-Telegram-Bot-Api-Secret-Token": "abc"}
            self.c.post("/pi/webhook", json={"message": {"text": "/gia", "chat": {"id": 1}}}, headers=h)
            self.assertEqual(sent, [])  # người lạ bị bỏ qua
            self.c.post("/pi/webhook", json={"message": {"text": "/gia", "chat": {"id": 999}}}, headers=h)
            self.assertEqual(sent, ["999"])

    def test_cron(self):
        from pi_alert import main as m
        from pi_alert.demo import DemoMarket
        with mock.patch.object(m, "MarketData", lambda *a: DemoMarket()), \
             mock.patch("builtins.print"):
            r = self.c.get("/pi/cron?key=k1")
        self.assertEqual(r.status_code, 200)
        self.assertIn("score", r.json)


if __name__ == "__main__":
    unittest.main()
