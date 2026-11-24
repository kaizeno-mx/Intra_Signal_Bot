import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def _fetch_htf_trend(ticker: str, interval: str, sma_period: int):
    """Return 'up' / 'down' / None for a higher timeframe."""
    try:
        end = datetime.now()
        if interval == "1wk":
            start = end - timedelta(days=365)
        else:  # 1d
            start = end - timedelta(days=120)
        df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                         end=end.strftime("%Y-%m-%d"),
                         interval=interval, progress=False, auto_adjust=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        close = df["Close"].dropna()
        if len(close) < sma_period:
            return None
        sma = close.rolling(sma_period).mean().iloc[-1]
        return "up" if float(close.iloc[-1]) > float(sma) else "down"
    except Exception as e:
        print(f"[WARN] HTF fetch {ticker} {interval} failed: {e}")
        return None

def check_htf_alignment(ticker: str, direction: str) -> tuple:
    """
    Returns (score_delta, reason_string).
    Weekly trend (20-SMA) + Daily trend (50-SMA).
    Both align = +10, both oppose = -10, mixed = +0.
    """
    weekly = _fetch_htf_trend(ticker, "1wk", 20)
    daily = _fetch_htf_trend(ticker, "1d", 50)

    if weekly is None and daily is None:
        return 0, "+0 HTF data unavailable"

    signal_trend = "up" if direction == "Long" else "down"

    # Count alignment
    alignments = 0
    total = 0
    parts = []
    if weekly is not None:
        total += 1
        if weekly == signal_trend:
            alignments += 1
            parts.append(f"W:{weekly}✓")
        else:
            parts.append(f"W:{weekly}✗")
    if daily is not None:
        total += 1
        if daily == signal_trend:
            alignments += 1
            parts.append(f"D:{daily}✓")
        else:
            parts.append(f"D:{daily}✗")

    detail = " ".join(parts)

    if total == 0:
        return 0, "+0 HTF data unavailable"
    if alignments == total:
        return 10, f"+10 HTF aligned ({detail})"
    if alignments == 0:
        return -10, f"-10 HTF opposed ({detail})"
    return 0, f"+0 HTF mixed ({detail})"
