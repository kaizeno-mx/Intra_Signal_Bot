import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

TIMEFRAME = "1h"
LOOKBACK_DAYS = 10
SWING_WINDOW = 3
FVG_MIN_GAP_PCT = 0.0001
SWEEP_LOOKBACK = 40
CONFIDENCE_THRESHOLD = 30
DEDUP_MINUTES = 360

UNIVERSE = {
    "EURUSD": {"ticker": "EURUSD=X",  "class": "fx",     "sessions": ["London", "NewYork"]},
    "USDJPY": {"ticker": "USDJPY=X",  "class": "fx",     "sessions": ["Asian", "London"]},
    "GBPUSD": {"ticker": "GBPUSD=X",  "class": "fx",     "sessions": ["London", "NewYork"]},
    "GOLD":   {"ticker": "GC=F",      "class": "metal",  "sessions": ["London", "NewYork"]},
    "NAS100": {"ticker": "^NDX",      "class": "index",  "sessions": ["NewYork"]},
    "EU50":   {"ticker": "^STOXX50E", "class": "index",  "sessions": ["London"]},
    "JP225":  {"ticker": "^N225",     "class": "index",  "sessions": ["Asian"]},
    "BRENT":  {"ticker": "BZ=F",      "class": "energy", "sessions": ["London", "NewYork"]},
    "BTC":    {"ticker": "BTC-USD",   "class": "crypto", "sessions": ["Asian", "London", "NewYork"]},
}

DXY_TICKER = "DX-Y.NYB"
VIX_TICKER = "^VIX"

SESSIONS = {}
for sym, meta in UNIVERSE.items():
    for s in meta["sessions"]:
        SESSIONS.setdefault(s, []).append(sym)
