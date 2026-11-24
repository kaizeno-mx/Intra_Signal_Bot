import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import DXY_TICKER, VIX_TICKER

def fetch_macro_regime() -> dict:
    out = {"regime": "Unclear", "dxy_trend": "flat", "vix_level": 0.0,
           "vix_trend": "flat", "yield_10y": 0.0, "yield_trend": "flat",
           "irx_13w": 0.0, "curve_slope": 0.0, "curve_trend": "flat"}
    end = datetime.now()
    start = end - timedelta(days=30)

    try:
        dxy = yf.download(DXY_TICKER, start=start.strftime("%Y-%m-%d"),
                          end=end.strftime("%Y-%m-%d"), interval="1d",
                          progress=False, auto_adjust=False)
        if dxy is not None and not dxy.empty:
            if isinstance(dxy.columns, pd.MultiIndex):
                dxy.columns = dxy.columns.droplevel(1)
            close = dxy["Close"].dropna()
            if len(close) >= 20:
                sma5 = close.rolling(5).mean().iloc[-1]
                sma20 = close.rolling(20).mean().iloc[-1]
                out["dxy_trend"] = "up" if sma5 > sma20 else "down"
    except Exception as e:
        print(f"[WARN] DXY fetch failed: {e}")

    try:
        vix = yf.download(VIX_TICKER, start=start.strftime("%Y-%m-%d"),
                          end=end.strftime("%Y-%m-%d"), interval="1d",
                          progress=False, auto_adjust=False)
        if vix is not None and not vix.empty:
            if isinstance(vix.columns, pd.MultiIndex):
                vix.columns = vix.columns.droplevel(1)
            v = vix["Close"].dropna()
            if len(v) >= 5:
                out["vix_level"] = float(v.iloc[-1])
                delta = float(v.iloc[-1] - v.iloc[-5])
                if delta > 1.0:
                    out["vix_trend"] = "rising"
                elif delta < -1.0:
                    out["vix_trend"] = "falling"
    except Exception as e:
        print(f"[WARN] VIX fetch failed: {e}")

    # 10Y Treasury Yield
    try:
        tnx = yf.download("^TNX", start=start.strftime("%Y-%m-%d"),
                          end=end.strftime("%Y-%m-%d"), interval="1d",
                          progress=False, auto_adjust=False)
        if tnx is not None and not tnx.empty:
            if isinstance(tnx.columns, pd.MultiIndex):
                tnx.columns = tnx.columns.droplevel(1)
            y = tnx["Close"].dropna()
            if len(y) >= 5:
                out["yield_10y"] = float(y.iloc[-1])
                delta = float(y.iloc[-1] - y.iloc[-5])
                if delta > 0.05:
                    out["yield_trend"] = "rising"
                elif delta < -0.05:
                    out["yield_trend"] = "falling"
                else:
                    out["yield_trend"] = "flat"
    except Exception as e:
        print(f"[WARN] TNX fetch failed: {e}")

    # 13-week T-bill (^IRX) — for yield curve
    try:
        irx = yf.download("^IRX", start=start.strftime("%Y-%m-%d"),
                          end=end.strftime("%Y-%m-%d"), interval="1d",
                          progress=False, auto_adjust=False)
        if irx is not None and not irx.empty:
            if isinstance(irx.columns, pd.MultiIndex):
                irx.columns = irx.columns.droplevel(1)
            r = irx["Close"].dropna()
            if len(r) >= 1:
                out["irx_13w"] = float(r.iloc[-1])
                if out["yield_10y"] > 0:
                    slope = round(out["yield_10y"] - out["irx_13w"], 2)
                    out["curve_slope"] = slope
                    if slope > 0.5:
                        out["curve_trend"] = "steep"
                    elif slope < -0.1:
                        out["curve_trend"] = "inverted"
                    else:
                        out["curve_trend"] = "flat"
    except Exception as e:
        print(f"[WARN] IRX fetch failed: {e}")

    vix_lvl = out["vix_level"]
    if vix_lvl == 0.0:
        out["regime"] = "Unclear"
    elif vix_lvl > 25:
        out["regime"] = "Risk-Off"
    elif vix_lvl < 18:
        out["regime"] = "Risk-On"
    else:
        out["regime"] = "Neutral"

    return out
