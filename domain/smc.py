import numpy as np
from config import SWING_WINDOW, SWEEP_LOOKBACK, FVG_MIN_GAP_PCT

def detect_swings(high, low):
    n = len(high)
    sh = np.zeros(n, dtype=bool)
    sl = np.zeros(n, dtype=bool)
    w = SWING_WINDOW
    for i in range(w, n - w):
        if high[i] == max(high[i-w:i+w+1]):
            sh[i] = True
        if low[i] == min(low[i-w:i+w+1]):
            sl[i] = True
    return sh, sl

def detect_liquidity_sweep(high, low, close, sh, sl):
    idx = len(high) - 2
    if idx < SWEEP_LOOKBACK:
        return None
    for i in range(idx - 1, max(0, idx - SWEEP_LOOKBACK), -1):
        if sl[i]:
            level = low[i]
            if low[idx] < level and close[idx] > level:
                return "bullish"
    for i in range(idx - 1, max(0, idx - SWEEP_LOOKBACK), -1):
        if sh[i]:
            level = high[i]
            if high[idx] > level and close[idx] < level:
                return "bearish"
    return None

def detect_fvg(high, low, close):
    if len(high) < 3:
        return None
    i = len(high) - 2
    c = close[i] if close[i] != 0 else 1e-9
    gap_bull = (low[i] - high[i-2]) / c
    gap_bear = (low[i-2] - high[i]) / c
    if gap_bull > FVG_MIN_GAP_PCT:
        return "bullish"
    if gap_bear > FVG_MIN_GAP_PCT:
        return "bearish"
    return None

def find_nearest_swing(high, low, sh, sl, direction):
    idx = len(high) - 2
    if direction == "Long":
        levels = [low[i] for i in range(max(0, idx-SWEEP_LOOKBACK), idx) if sl[i]]
        return float(min(levels)) if levels else None
    else:
        levels = [high[i] for i in range(max(0, idx-SWEEP_LOOKBACK), idx) if sh[i]]
        return float(max(levels)) if levels else None

def compute_trade_plan(signal: dict, high, low, sh, sl, direction: str):
    """
    Compute suggested entry, SL, TP1/TP2/TP3 from structure.
    Safe structural stop (widest swing) + R-based targets at 3R, 4.5R, 5R.
    """
    entry = signal["price"]
    idx = len(high) - 2

    if direction == "Long":
        swing_levels = [low[i] for i in range(max(0, idx - SWEEP_LOOKBACK), idx) if sl[i] and low[i] < entry]
        if not swing_levels:
            return None
        stop = min(swing_levels)  # safest = lowest swing low
        risk = entry - stop
        if risk <= 0:
            return None
        tp1 = entry + 3.0 * risk
        tp2 = entry + 4.5 * risk
        tp3 = entry + 5.0 * risk
    else:
        swing_levels = [high[i] for i in range(max(0, idx - SWEEP_LOOKBACK), idx) if sh[i] and high[i] > entry]
        if not swing_levels:
            return None
        stop = max(swing_levels)  # safest = highest swing high
        risk = stop - entry
        if risk <= 0:
            return None
        tp1 = entry - 3.0 * risk
        tp2 = entry - 4.5 * risk
        tp3 = entry - 5.0 * risk

    return {
        "entry": round(entry, 5),
        "stop": round(stop, 5),
        "tp1": round(tp1, 5),
        "tp2": round(tp2, 5),
        "tp3": round(tp3, 5),
        "risk_points": round(risk, 5),
        "r_tp1": 3.0,
        "r_tp2": 4.5,
        "r_tp3": 5.0,
    }
