def compute_confidence(signal: dict, regime: dict, asset_class: str, session: str):
    score = 0
    reasons = []

    score += 40
    reasons.append("+40 structure (sweep+FVG aligned)")

    r = regime.get("regime", "Unclear")
    direction = signal["direction"]
    if r == "Risk-On" and direction == "Long":
        score += 20; reasons.append("+20 regime risk-on aligns long")
    elif r == "Risk-Off" and direction == "Short":
        score += 20; reasons.append("+20 regime risk-off aligns short")
    elif r == "Risk-On" and direction == "Short" and asset_class == "metal":
        score += 10; reasons.append("+10 short gold in risk-on (partial)")
    elif r == "Risk-Off" and direction == "Long" and signal["symbol"] in ("GOLD", "USDJPY"):
        score += 10; reasons.append("+10 safe-haven long in risk-off")
    else:
        reasons.append("+0 regime neutral/misaligned")

    primary = {
        "EURUSD": "London", "USDJPY": "Asian", "GBPUSD": "London",
        "GOLD": "NewYork", "NAS100": "NewYork", "EU50": "London",
        "JP225": "Asian", "BRENT": "London", "BTC": "NewYork",
    }.get(signal["symbol"])
    if session == primary:
        score += 10; reasons.append(f"+10 primary session ({session})")
    else:
        reasons.append(f"+0 secondary session ({session})")

    dxy = regime.get("dxy_trend", "flat")
    sym = signal["symbol"]
    if dxy == "up":
        if sym in ("EURUSD", "GBPUSD") and direction == "Short":
            score += 15; reasons.append("+15 DXY up supports short EUR/GBP")
        elif sym == "USDJPY" and direction == "Long":
            score += 15; reasons.append("+15 DXY up supports long USDJPY")
        elif sym == "GOLD" and direction == "Short":
            score += 10; reasons.append("+10 DXY up mildly supports short gold")
        else:
            reasons.append("+0 DXY up not aligned")
    elif dxy == "down":
        if sym in ("EURUSD", "GBPUSD") and direction == "Long":
            score += 15; reasons.append("+15 DXY down supports long EUR/GBP")
        elif sym == "GOLD" and direction == "Long":
            score += 15; reasons.append("+15 DXY down supports long gold")
        elif sym == "USDJPY" and direction == "Short":
            score += 15; reasons.append("+15 DXY down supports short USDJPY")
        else:
            reasons.append("+0 DXY down not aligned")
    else:
        reasons.append("+0 DXY flat")

    vt = regime.get("vix_trend", "flat")
    if vt == "rising" and direction == "Short":
        score += 15; reasons.append("+15 VIX rising confirms short")
    elif vt == "falling" and direction == "Long":
        score += 15; reasons.append("+15 VIX falling confirms long")
    elif vt == "rising" and direction == "Long" and sym in ("GOLD", "USDJPY"):
        score += 10; reasons.append("+10 VIX rising supports safe-haven long")
    else:
        reasons.append("+0 VIX trend neutral/misaligned")

    return min(100, score), reasons
