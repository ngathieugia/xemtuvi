"""Giao diện web (Flask Blueprint) để chạy bot trên hosting cPanel "Setup Python App".

Hosting dạng Passenger chỉ chạy code khi có request, không giữ được vòng lặp nền, nên:
  • /pi/webhook  – Telegram gọi vào mỗi khi bạn nhắn lệnh cho bot (/gia, /phantich…)
  • /pi/cron     – dự phòng nếu hosting không có Cron Jobs: dịch vụ ngoài (cron-job.org)
                   gọi https://tenmien/pi/cron?key=CRON_SECRET mỗi 1–2 phút
  • /pi/         – kiểm tra bot còn sống
  • /pi/app/     – dashboard React (thư mục pi_alert/dashboard_dist, build từ dashboard/)
  • /pi/api/data – dữ liệu JSON cho dashboard (?tf=15m, ?demo=1 để xem dữ liệu giả lập)
Quét giá định kỳ nên ưu tiên dùng Cron Jobs của cPanel:  python -m pi_alert.main --once
"""
import hmac
import traceback
from pathlib import Path

from flask import Blueprint, Flask, jsonify, redirect, request, send_from_directory

from .alerts import State
from .config import load_config
from .exchanges import MarketData
from .main import handle_command, run_once_locked
from .telegram_bot import Telegram, parse_update

bp = Blueprint("pi_alert", __name__, url_prefix="/pi")


def _same(a, b):
    return bool(a) and bool(b) and hmac.compare_digest(str(a), str(b))


@bp.get("/")
def status():
    cfg = load_config()
    st = State(cfg.state_file)
    return jsonify(ok=True, last_price=st.get("last_price"), zone=st.get("zone"),
                   telegram_configured=bool(cfg.bot_token and cfg.chat_id))


@bp.post("/webhook")
def webhook():
    cfg = load_config()
    if not _same(request.headers.get("X-Telegram-Bot-Api-Secret-Token"), cfg.webhook_secret):
        return "forbidden", 403
    try:
        cid, cmd = parse_update(request.get_json(force=True, silent=True) or {})
        tg = Telegram(cfg.bot_token, cfg.chat_id)
        if not cmd:
            return "ok"
        if not cfg.chat_id:
            # chưa cấu hình: báo chat_id để người dùng điền vào .env
            tg.send(f"chat_id của bạn là <code>{cid}</code>\nĐiền vào TELEGRAM_CHAT_ID trong pi_alert/.env "
                    f"rồi bấm Restart app trong cPanel.", cid)
        elif cid == cfg.chat_id:
            handle_command(cmd, MarketData(cfg.exchange, cfg.market), cfg, tg, cid)
    except Exception:  # noqa: BLE001 - luôn trả 200 để Telegram không gửi lại liên tục
        traceback.print_exc()
    return "ok"


@bp.route("/cron", methods=["GET", "POST"])
def cron():
    cfg = load_config()
    if not _same(request.args.get("key"), cfg.cron_secret):
        return "forbidden", 403
    try:
        snap = run_once_locked(cfg)
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        return jsonify(ok=False, error=str(e)), 500
    if snap is None:
        return jsonify(ok=True, skipped=True)
    return jsonify(ok=True, price=snap["price"], score=snap["score"], source=snap["source"])


DIST = Path(__file__).resolve().parent / "dashboard_dist"
_demo = None


@bp.get("/api/data")
def api_data():
    global _demo
    from .api import dashboard_payload
    cfg = load_config()
    if request.args.get("demo") == "1":
        from .demo import DemoMarket
        _demo = _demo or DemoMarket()
        md = _demo
    else:
        md = MarketData(cfg.exchange, cfg.market)
    try:
        resp = jsonify(dashboard_payload(md, cfg, request.args.get("tf")))
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        resp = jsonify(error=f"Không lấy được dữ liệu: {e}")
        resp.status_code = 502
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@bp.get("/app")
def app_redirect():
    return redirect(request.path + "/" + (("?" + request.query_string.decode()) if request.query_string else ""))


@bp.get("/app/")
@bp.get("/app/<path:name>")
def dashboard(name="index.html"):
    if not (DIST / "index.html").exists():
        return "Chưa build dashboard: cd dashboard && npm install && npm run build", 404
    if not (DIST / name).is_file():
        name = "index.html"
    resp = send_from_directory(DIST, name)
    if name == "index.html":
        resp.headers["Cache-Control"] = "no-cache"
    return resp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    create_app().run(port=5000, debug=False)
