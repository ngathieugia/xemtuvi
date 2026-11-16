"""Phát hiện các sự kiện cần cảnh báo, có chống gửi trùng (lưu trạng thái ra file JSON)."""
import json
import time
from pathlib import Path

from .analysis import fmt_price, fmt_time


class State:
    def __init__(self, path):
        self.path = Path(path)
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            self.data = {}

    def get(self, k, default=None):
        return self.data.get(k, default)

    def set(self, k, v):
        self.data[k] = v

    def save(self):
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf-8")


def _once(state, key, value):
    """True nếu (key, value) chưa từng được gửi."""
    if state.get(key) == value:
        return False
    state.set(key, value)
    return True


def _cooldown(state, key, minutes):
    now = time.time()
    if now - state.get(key, 0) < minutes * 60:
        return False
    state.set(key, now)
    return True


def detect(snap, cfg, state):
    """Trả về list (mức_độ, nội_dung). mức_độ: 🚨 khẩn, ⚠️ chú ý, ℹ️ thông tin."""
    out = []
    p, s, t = snap["price"], snap["sig"], snap["trend"]
    tf, ttf = cfg.signal_tf, cfg.trend_tf
    first_run = state.get("initialized") is None

    # 1. Biến động giá mạnh
    for key, chg, thr, label in (("mv15", snap["chg_15m"], cfg.move_15m_pct, "15 phút"),
                                 ("mv1h", snap["chg_1h"], cfg.move_1h_pct, "1 giờ"),
                                 ("mv24", snap["chg_24h"], cfg.move_24h_pct, "24 giờ")):
        if abs(chg) >= thr and _cooldown(state, f"{key}_{'up' if chg > 0 else 'dn'}", cfg.move_cooldown_min):
            icon = "🚀 TĂNG MẠNH" if chg > 0 else "🩸 GIẢM MẠNH"
            out.append(("🚨", f"{icon} {chg:+.2f}% trong {label} → giá {fmt_price(p)}"))

    # 2. Cắt qua mốc giá
    prev_p = state.get("last_price")
    if prev_p is not None:
        for lv in cfg.price_levels:
            if prev_p < lv <= p:
                out.append(("⚠️", f"⬆️ Giá VƯỢT LÊN mốc {fmt_price(lv)} (hiện {fmt_price(p)})"))
            elif prev_p > lv >= p:
                out.append(("⚠️", f"⬇️ Giá THỦNG mốc {fmt_price(lv)} (hiện {fmt_price(p)})"))
    state.set("last_price", p)

    # 3. UT Bot (tín hiệu trên nến đã đóng, mỗi nến chỉ báo 1 lần)
    for name, d, frame in (("sig", s, tf), ("trend", t, ttf)):
        if d["ut_signal"] and _once(state, f"ut_{name}", d["ts"]) and not first_run:
            if d["ut_signal"] == "BUY":
                out.append(("🚨" if name == "trend" else "⚠️",
                            f"🟢 UT Bot {frame}: tín hiệu MUA tại {fmt_price(d['close'])} "
                            f"(trailing stop {fmt_price(d['ut_stop'])})"))
            else:
                out.append(("🚨" if name == "trend" else "⚠️",
                            f"🔴 UT Bot {frame}: tín hiệu BÁN tại {fmt_price(d['close'])} "
                            f"(trailing stop {fmt_price(d['ut_stop'])})"))

    # 4. Step Channel đổi xu hướng
    for name, d, frame in (("sig", s, tf), ("trend", t, ttf)):
        cur = d["sc_trend"]
        prev = state.get(f"sc_{name}")
        if cur is not None and prev is not None and cur != prev and cur != 0:
            txt = "TĂNG 📈 (giá phá lên kênh trên)" if cur == 1 else "GIẢM 📉 (giá thủng kênh dưới)"
            out.append(("⚠️", f"Step Channel {frame} đổi xu hướng sang {txt}. "
                              f"Kênh: {fmt_price(d['sc_lo'])} – {fmt_price(d['sc_up'])}"))
        if cur is not None:
            state.set(f"sc_{name}", cur)

    # 5. RSI vào vùng quá bán / quá mua (khung tín hiệu và khung lớn)
    for name, d, frame in (("sig", s, tf), ("trend", t, ttf)):
        r, rp = d["rsi"], d["rsi_prev"]
        if r is None or rp is None:
            continue
        if rp >= cfg.rsi_low > r and _once(state, f"rsi_lo_{name}", d["ts"]):
            out.append(("⚠️", f"🧊 RSI {frame} = {r:.1f} → QUÁ BÁN (có thể sắp hồi, chú ý vùng mua)"))
        if rp <= cfg.rsi_high < r and _once(state, f"rsi_hi_{name}", d["ts"]):
            out.append(("⚠️", f"🔥 RSI {frame} = {r:.1f} → QUÁ MUA (rủi ro điều chỉnh, tránh mua đuổi)"))

    # 6. Khối lượng đột biến
    if s["vol_avg"] and s["volume"] >= cfg.vol_spike * s["vol_avg"] and _once(state, "vol", s["ts"]):
        x = s["volume"] / s["vol_avg"]
        out.append(("⚠️", f"📊 Khối lượng nến {tf} lúc {fmt_time(s['ts'])} gấp {x:.1f} lần trung bình "
                          f"– dòng tiền lớn đang vào/ra"))

    # 7. Phá dải Bollinger khung tín hiệu
    if s["bb_up"] and s["close"] > s["bb_up"] and _once(state, "bb", f"up{s['ts']}"):
        out.append(("ℹ️", f"Giá đóng cửa {tf} vượt dải Bollinger trên {fmt_price(s['bb_up'])}"))
    elif s["bb_lo"] and s["close"] < s["bb_lo"] and _once(state, "bb", f"lo{s['ts']}"):
        out.append(("ℹ️", f"Giá đóng cửa {tf} thủng dải Bollinger dưới {fmt_price(s['bb_lo'])}"))

    # 8. Funding rate cực đoan
    f = snap["funding"]
    if f is not None and abs(f) * 100 >= cfg.funding_alert_pct and _cooldown(state, "funding", 240):
        side = "phe LONG trả phí – thị trường hưng phấn quá mức" if f > 0 else \
            "phe SHORT trả phí – nhiều người bán khống, dễ short squeeze"
        out.append(("⚠️", f"💸 Funding rate {f*100:+.3f}%/8h: {side}"))

    # 9. Điểm cơ hội vượt ngưỡng
    zone = "good" if snap["score"] >= 70 else "bad" if snap["score"] < 40 else "mid"
    prev_zone = state.get("zone")
    if prev_zone and zone != prev_zone and zone == "good":
        out.append(("🚨", f"🎯 ĐIỂM CƠ HỘI MUA tăng lên {snap['score']}/100 – {snap['verdict']}"))
    state.set("zone", zone)

    if first_run:
        state.set("initialized", int(time.time()))
        # lần chạy đầu chỉ ghi nhận trạng thái, không bắn cảnh báo cũ
        out = [o for o in out if o[0] == "🚨" and "trong" in o[1]]
    return out
