import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import TIMEFRAME, LOOKBACK_DAYS

def fetch_intraday(ticker: str):
    try:
        end = datetime.now()
        start = end - timedelta(days=LOOKBACK_DAYS)
        df = yf.download(
            ticker,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval=TIMEFRAME,
            progress=False,
            auto_adjust=False,
        )
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        df = df[["High", "Low", "Close"]].dropna()
        return df if len(df) >= 25 else None
    except Exception as e:
        print(f"[WARN] fetch {ticker} failed: {e}")
        return None
