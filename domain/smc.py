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

    # Bullish sweep: current low breaks BELOW any prior swing low,
    # but close comes back ABOVE that same level (wick rejection)
    for i in range(idx - 1, max(0, idx - SWEEP_LOOKBACK), -1):
        if sl[i]:
            level = low[i]
            if low[idx] < level and close[idx] > level:
                return "bullish"

    # Bearish sweep: current high breaks ABOVE any prior swing high,
    # but close comes back BELOW that level
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
