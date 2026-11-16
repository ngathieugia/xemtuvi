"""Đọc cấu hình từ biến môi trường và file .env (không cần thư viện ngoài)."""
import os
from dataclasses import dataclass, field
from pathlib import Path


def load_env_file(path):
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        val = val.split(" #", 1)[0].strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), val)


def _f(name, default):
    v = os.environ.get(name, "")
    return float(v) if v.strip() else float(default)


def _i(name, default):
    v = os.environ.get(name, "")
    return int(float(v)) if v.strip() else int(default)


def _s(name, default):
    v = os.environ.get(name, "").strip()
    return v or default


@dataclass
class Config:
    bot_token: str = ""
    chat_id: str = ""
    exchange: str = "okx"
    market: str = "swap"
    check_interval: int = 60
    signal_tf: str = "15m"
    trend_tf: str = "4h"
    summary_hours: float = 4
    move_15m_pct: float = 3
    move_1h_pct: float = 5
    move_24h_pct: float = 10
    move_cooldown_min: int = 30
    price_levels: list = field(default_factory=list)
    ut_key: float = 2
    ut_atr: int = 1
    scmt_len: int = 3
    scmt_mult: float = 0.6
    rsi_low: float = 30
    rsi_high: float = 70
    vol_spike: float = 3
    funding_alert_pct: float = 0.1
    dry_run: bool = False
    state_file: str = "pi_alert_state.json"
    webhook_secret: str = ""
    cron_secret: str = ""


PKG_DIR = Path(__file__).resolve().parent


def load_config(env_path=None):
    load_env_file(env_path or PKG_DIR / ".env")
    levels = [float(x) for x in _s("PRICE_LEVELS", "").replace(";", ",").split(",") if x.strip()]
    return Config(
        bot_token=_s("TELEGRAM_BOT_TOKEN", ""),
        chat_id=_s("TELEGRAM_CHAT_ID", ""),
        exchange=_s("EXCHANGE", "okx").lower(),
        market=_s("MARKET", "swap").lower(),
        check_interval=_i("CHECK_INTERVAL", 60),
        signal_tf=_s("SIGNAL_TF", "15m"),
        trend_tf=_s("TREND_TF", "4h"),
        summary_hours=_f("SUMMARY_HOURS", 4),
        move_15m_pct=_f("MOVE_15M_PCT", 3),
        move_1h_pct=_f("MOVE_1H_PCT", 5),
        move_24h_pct=_f("MOVE_24H_PCT", 10),
        move_cooldown_min=_i("MOVE_COOLDOWN_MIN", 30),
        price_levels=sorted(levels),
        ut_key=_f("UT_KEY", 2),
        ut_atr=_i("UT_ATR", 1),
        scmt_len=_i("SCMT_LEN", 3),
        scmt_mult=_f("SCMT_MULT", 0.6),
        rsi_low=_f("RSI_LOW", 30),
        rsi_high=_f("RSI_HIGH", 70),
        vol_spike=_f("VOL_SPIKE", 3),
        funding_alert_pct=_f("FUNDING_ALERT_PCT", 0.1),
        dry_run=_s("DRY_RUN", "0") in ("1", "true", "yes"),
        state_file=_s("STATE_FILE", str(PKG_DIR / "state.json")),
        webhook_secret=_s("WEBHOOK_SECRET", ""),
        cron_secret=_s("CRON_SECRET", ""),
    )
