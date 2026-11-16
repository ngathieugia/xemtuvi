"""Bot theo dõi giá Pi Network (PI/USDT) và cảnh báo qua Telegram.

Chạy:
    python -m pi_alert.main                 # chạy liên tục
    python -m pi_alert.main --once          # quét 1 lần (dùng cho cron)
    python -m pi_alert.main --report        # gửi báo cáo phân tích ngay
    python -m pi_alert.main --demo          # chạy thử với dữ liệu giả lập, không cần mạng
    python -m pi_alert.main --get-chat-id   # xem chat_id sau khi nhắn /start cho bot
"""
import argparse
import html
import time
import traceback

from .alerts import State, detect
from .analysis import build_snapshot, fmt_price, fmt_time
from .config import load_config
from .exchanges import MarketData
from .telegram_bot import Telegram

DISCLAIMER = "<i>⚠️ Chỉ mang tính tham khảo, không phải khuyến nghị đầu tư. Tự chịu trách nhiệm với quyết định của mình.</i>"


def trend_txt(v):
    return {1: "TĂNG 📈", -1: "GIẢM 📉", 0: "ĐI NGANG ➖"}.get(v, "chưa đủ dữ liệu")


def format_alerts(snap, items):
    head = f"<b>🔔 CẢNH BÁO PI/USDT</b> ({snap['source']} {snap['market']})\n" \
           f"Giá: <b>{fmt_price(snap['price'])}</b> | 1h {snap['chg_1h']:+.2f}% | 24h {snap['chg_24h']:+.2f}%\n"
    body = "\n".join(f"{lvl} {html.escape(t)}" for lvl, t in items)
    return f"{head}\n{body}\n\n🎯 Điểm cơ hội mua: <b>{snap['score']}/100</b>"


def format_report(snap, cfg):
    s, t, sr, tk = snap["sig"], snap["trend"], snap["sr"], snap["ticker"]
    lines = [
        f"<b>📊 BÁO CÁO PI NETWORK (PI/USDT)</b>",
        f"Nguồn: {snap['source']} – {'Hợp đồng vĩnh cửu' if snap['market'] == 'swap' else 'Giao ngay'}",
        "",
        f"💰 Giá hiện tại: <b>{fmt_price(snap['price'])} USDT</b>",
        f"   15p {snap['chg_15m']:+.2f}% | 1h {snap['chg_1h']:+.2f}% | 24h {snap['chg_24h']:+.2f}%",
        f"   Cao/Thấp 24h: {fmt_price(tk['high24h'])} / {fmt_price(tk['low24h'])}",
    ]
    if snap["funding"] is not None:
        lines.append(f"   Funding: {snap['funding']*100:+.4f}%/8h")
    lines += ["", f"<b>📈 Chỉ báo khung {cfg.signal_tf}</b>"]
    lines.append(f"• UT Bot ({cfg.ut_key:g},{cfg.ut_atr}): {'🟢 MUA' if s['ut_pos'] == 'LONG' else '🔴 BÁN'} – "
                 f"trailing stop {fmt_price(s['ut_stop'])}")
    if s["ut_last_signal"]:
        lines.append(f"   Tín hiệu gần nhất: {s['ut_last_signal']} @ {fmt_price(s['ut_last_signal_price'])} "
                     f"({fmt_time(s['ut_last_signal_ts'])})")
    lines.append(f"• Step Channel ({cfg.scmt_len},{cfg.scmt_mult:g}): {trend_txt(s['sc_trend'])} – "
                 f"kênh {fmt_price(s['sc_lo'])} → {fmt_price(s['sc_up'])}")
    lines.append(f"• RSI14: {s['rsi']:.1f}" if s["rsi"] is not None else "• RSI14: -")
    if s["macd_hist"] is not None:
        lines.append(f"• MACD hist: {s['macd_hist']:+.5f} ({'tăng' if s['macd_hist'] > (s['macd_hist_prev'] or 0) else 'giảm'})")
    lines.append(f"• Bollinger: {fmt_price(s['bb_lo'])} | {fmt_price(s['bb_mid'])} | {fmt_price(s['bb_up'])}")

    lines += ["", f"<b>🧭 Xu hướng khung {cfg.trend_tf}</b>"]
    lines.append(f"• UT Bot: {'🟢 MUA' if t['ut_pos'] == 'LONG' else '🔴 BÁN'} (stop {fmt_price(t['ut_stop'])})")
    lines.append(f"• Step Channel: {trend_txt(t['sc_trend'])}")
    lines.append(f"• EMA20/50/200: {fmt_price(t['ema20'])} / {fmt_price(t['ema50'])} / {fmt_price(t['ema200'])}")
    lines.append(f"• RSI14: {t['rsi']:.1f}" if t["rsi"] is not None else "• RSI14: -")

    lines += ["", "<b>🧱 Hỗ trợ / Kháng cự (khung ngày, 60 phiên)</b>",
              "• Hỗ trợ: " + (", ".join(fmt_price(x) for x in sr["supports"]) or "-"),
              "• Kháng cự: " + (", ".join(fmt_price(x) for x in sr["resistances"]) or "-"),
              f"• Biên độ 60 ngày: {fmt_price(sr['low_range'])} – {fmt_price(sr['high_range'])}"]

    lines += ["", f"<b>🎯 ĐIỂM CƠ HỘI MUA: {snap['score']}/100</b>", html.escape(snap["verdict"])]
    lines += [f"   {html.escape(w)}" for w in snap["why"]]

    plan = buy_plan(snap)
    if plan:
        lines += ["", "<b>📝 Gợi ý kế hoạch mua tham khảo</b>"] + [f"   {html.escape(x)}" for x in plan]
    lines += ["", DISCLAIMER]
    return "\n".join(lines)


def buy_plan(snap):
    """Gợi ý chia vốn mua theo vùng hỗ trợ (DCA) và mức cắt lỗ tham khảo."""
    p, sr, s = snap["price"], snap["sr"], snap["sig"]
    sups = sr["supports"][:2]
    z1 = min(p, s["ut_stop"]) if s["ut_pos"] == "LONG" else (sups[0] if sups else p)
    zones = [z1] + [x for x in sups if x < z1 * 0.97][:2]
    # Thiếu vùng hỗ trợ (giá sát đáy) -> thêm vùng mua dự phòng thấp hơn 5% mỗi bậc
    while len(zones) < 3:
        zones.append(zones[-1] * 0.95)
    plan = []
    if snap["score"] < 40:
        plan.append("Điểm đang thấp: chỉ đặt lệnh CHỜ ở các vùng dưới, không mua đuổi.")
    plan += [f"Phần {i+1}: ~{w}% vốn quanh {fmt_price(z)}" for i, (w, z) in enumerate(zip((30, 30, 40), zones))]
    stop = zones[-1] * 0.94
    plan.append(f"Cắt lỗ tham khảo: đóng cửa ngày dưới {fmt_price(stop)} (≈ -6% dưới vùng mua cuối)")
    if sr["resistances"]:
        plan.append(f"Chốt lời từng phần ở kháng cự: {', '.join(fmt_price(x) for x in sr['resistances'][:2])}")
    plan.append("Không dùng đòn bẩy cao; chỉ dùng tiền nhàn rỗi.")
    return plan


def run_cycle(md, cfg, tg, state):
    snap = build_snapshot(md, cfg)
    items = detect(snap, cfg, state)
    if items:
        tg.send(format_alerts(snap, items))
    if cfg.summary_hours > 0 and time.time() - state.get("last_summary", 0) >= cfg.summary_hours * 3600:
        tg.send(format_report(snap, cfg))
        state.set("last_summary", time.time())
    state.save()
    print(f"[{time.strftime('%H:%M:%S')}] {snap['source']} giá={snap['price']} "
          f"điểm={snap['score']} cảnh_báo={len(items)}")
    return snap


HELP = ("<b>Lệnh hỗ trợ</b>\n/gia – giá nhanh\n/phantich – báo cáo đầy đủ + điểm cơ hội\n"
        "/help – hướng dẫn")


def handle_command(cmd, md, cfg, tg, chat_id=None):
    if cmd in ("/start", "/help"):
        tg.send(HELP, chat_id)
        return
    snap = build_snapshot(md, cfg)
    if cmd == "/gia":
        tg.send(f"💰 PI/USDT: <b>{fmt_price(snap['price'])}</b>\n1h {snap['chg_1h']:+.2f}% | "
                f"24h {snap['chg_24h']:+.2f}%\nĐiểm cơ hội: {snap['score']}/100", chat_id)
    elif cmd in ("/phantich", "/baocao"):
        tg.send(format_report(snap, cfg), chat_id)
    else:
        tg.send(HELP, chat_id)


def run_once_locked(cfg, md=None, tg=None):
    """Quét 1 lần, có khóa file để 2 lần cron chạy chồng nhau không gửi trùng.

    Trả về snapshot, hoặc None nếu đang có tiến trình khác chạy.
    """
    import fcntl
    with open(cfg.state_file + ".lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("Đang có tiến trình khác quét, bỏ qua lần này.")
            return None
        md = md or MarketData(cfg.exchange, cfg.market)
        tg = tg or Telegram(cfg.bot_token, cfg.chat_id, cfg.dry_run)
        return run_cycle(md, cfg, tg, State(cfg.state_file))


def main():
    ap = argparse.ArgumentParser(description="Cảnh báo giá Pi Network qua Telegram")
    ap.add_argument("--env", default=None, help="đường dẫn file .env (mặc định pi_alert/.env)")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--get-chat-id", action="store_true")
    ap.add_argument("--set-webhook", metavar="URL_GOC",
                    help="đăng ký webhook, VD: https://tenmien.com (bot tự thêm /pi/webhook)")
    ap.add_argument("--delete-webhook", action="store_true")
    a = ap.parse_args()
    cfg = load_config(a.env)

    if a.get_chat_id:
        Telegram(cfg.bot_token, "").print_chat_ids()
        return
    if a.set_webhook or a.delete_webhook:
        tg = Telegram(cfg.bot_token, cfg.chat_id)
        if a.delete_webhook:
            print(tg.delete_webhook())
        else:
            if not cfg.webhook_secret:
                raise SystemExit("Hãy đặt WEBHOOK_SECRET trong pi_alert/.env trước.")
            url = a.set_webhook.rstrip("/") + "/pi/webhook"
            print(tg.set_webhook(url, cfg.webhook_secret))
        print(tg.webhook_info())
        return
    if a.demo:
        from .demo import DemoMarket
        md, cfg.dry_run = DemoMarket(), True
    else:
        md = MarketData(cfg.exchange, cfg.market)
    tg = Telegram(cfg.bot_token, cfg.chat_id, cfg.dry_run)
    state = State(cfg.state_file)

    if a.report or a.demo:
        tg.send(format_report(build_snapshot(md, cfg), cfg))
        if a.demo:
            state = State(cfg.state_file + ".demo")
            for _ in range(3):
                run_cycle(md, cfg, tg, state)
                md.advance()
        return
    if a.once:
        run_once_locked(cfg, md, tg)
        return

    tg.send(f"✅ Bot cảnh báo PI đã khởi động (quét mỗi {cfg.check_interval}s).\n{HELP}")
    while True:
        start = time.time()
        try:
            run_cycle(md, cfg, tg, state)
        except Exception:  # noqa: BLE001 - không để bot chết vì lỗi mạng
            traceback.print_exc()
        while time.time() - start < cfg.check_interval:
            try:
                remain = int(cfg.check_interval - (time.time() - start))
                for _, cmd in tg.poll_commands(timeout=max(1, min(20, remain))):
                    handle_command(cmd, md, cfg, tg)
            except Exception:  # noqa: BLE001
                traceback.print_exc()
                time.sleep(5)
            if tg.dry_run or not tg.token:
                time.sleep(max(0, cfg.check_interval - (time.time() - start)))


if __name__ == "__main__":
    main()
