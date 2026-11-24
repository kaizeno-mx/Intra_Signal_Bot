import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

def send(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print("[ERROR] Telegram credentials missing")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"[ERROR] Telegram: {r.text}")
            return False
        return True
    except Exception as e:
        print(f"[ERROR] Telegram request: {e}")
        return False

def format_signal(s: dict) -> str:
    emoji = "🟢" if s["direction"] == "Long" else "🔴"
    conf_bar = "█" * (s["confidence"] // 10) + "░" * (10 - s["confidence"] // 10)
    reasons = "\n".join(f"  • {r}" for r in s["reasons"] if not r.startswith("+0"))

    plan_text = ""
    if "plan" in s and s["plan"]:
        p = s["plan"]
        plan_text = (
            f"\n━━━━━━━━━━━━━━━━━━\n"
            f"📋 *Suggested Trade Plan*\n"
            f"  Entry: `{p['entry']}`\n"
            f"  Stop Loss: `{p['stop']}`\n"
            f"  TP1 (+3R): `{p['tp1']}`\n"
            f"  TP2 (+4.5R): `{p['tp2']}`\n"
            f"  TP3 (+5R): `{p['tp3']}`\n"
            f"  Risk: `{p['risk_points']}` points\n"
            f"  _Scale out: 50% at TP1, 30% at TP2, 20% at TP3_\n"
        )

    return (
        f"{emoji} *{s['symbol']}* {s['direction']}  —  *{s['confidence']}% confidence*\n"
        f"`{conf_bar}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Session: {s['session']} open\n"
        f"💰 Price: `{s['price']}`\n"
        f"📊 Regime: {s['regime']} | VIX {s['vix']} ({s['vix_trend']})\n"
        f"💵 DXY: {s['dxy_trend']}\n"
        f"🔄 Sweep: {s['sweep']} | FVG: {s['fvg']}\n"
        f"⏱ {s['timeframe']} | {s['time']}\n"
        f"{plan_text}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"*Confidence breakdown:*\n{reasons}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"_Human filter required. Confirm before entry._"
    )
