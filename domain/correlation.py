import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import TIMEFRAME, LOOKBACK_DAYS

# Correlated instrument pairs and their expected relationship
# key: (symbol, direction) -> (correlated ticker, expected_correlated_direction)
# "same" = correlated should move same direction as signal
# "inverse" = correlated should move opposite direction

PAIRS = {
    "EURUSD": {"ticker": "GBPUSD=X", "relation": "same"},
    "GBPUSD": {"ticker": "EURUSD=X", "relation": "same"},
    "USDJPY": {"ticker": "DX-Y.NYB", "relation": "same"},
    "GOLD":   {"ticker": "DX-Y.NYB", "relation": "inverse"},
    "NAS100": {"ticker": "^NDX",     "relation": "same"},
    "BTC":    {"ticker": "DX-Y.NYB", "relation": "inverse"},
}

def _fetch_trend(ticker: str):
    """Return 'up' / 'down' / None based on 5 vs 20 SMA on the configured timeframe."""
    try:
        end = datetime.now()
        start = end - timedelta(days=LOOKBACK_DAYS)
        df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                         end=end.strftime("%Y-%m-%d"),
                         interval=TIMEFRAME, progress=False, auto_adjust=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        close = df["Close"].dropna()
        if len(close) < 20:
            return None
        sma5 = close.rolling(5).mean().iloc[-1]
        sma20 = close.rolling(20).mean().iloc[-1]
        return "up" if sma5 > sma20 else "down"
    except Exception as e:
        print(f"[WARN] correlation fetch {ticker} failed: {e}")
        return None

def check_correlation(symbol: str, direction: str) -> tuple:
    """
    Returns (score_delta, reason_string).
    score_delta: +10 if correlated agrees, -10 if disagrees, 0 if unknown.
    """
    pair = PAIRS.get(symbol)
    if not pair:
        return 0, "+0 no correlation pair defined"

    corr_trend = _fetch_trend(pair["ticker"])
    if corr_trend is None:
        return 0, "+0 correlation data unavailable"

    signal_trend = "up" if direction == "Long" else "down"
    relation = pair["relation"]

    if relation == "same":
        agrees = (corr_trend == signal_trend)
    else:  # inverse
        agrees = (corr_trend != signal_trend)

    if agrees:
        return 10, f"+10 correlation agrees ({pair['ticker']} {corr_trend})"
    else:
        return -10, f"-10 correlation diverges ({pair['ticker']} {corr_trend})"
