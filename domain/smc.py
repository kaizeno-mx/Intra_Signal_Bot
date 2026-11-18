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
    prior_lows = [i for i in range(idx - SWEEP_LOOKBACK, idx) if sl[i]]
    prior_highs = [i for i in range(idx - SWEEP_LOOKBACK, idx) if sh[i]]
    if prior_lows:
        last_low = low[prior_lows[-1]]
        if low[idx] < last_low and close[idx] > last_low:
            return "bullish"
    if prior_highs:
        last_high = high[prior_highs[-1]]
        if high[idx] > last_high and close[idx] < last_high:
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
