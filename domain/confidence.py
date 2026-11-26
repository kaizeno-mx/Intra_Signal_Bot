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

    # ---- DXY block (with USDJPY override) ----
    dxy = regime.get("dxy_trend", "flat")
    sym = signal["symbol"]
    if sym == "USDJPY":
        # USDJPY is yield-differential driven; DXY strength alone is not enough
        yt_check = regime.get("yield_trend", "flat")
        if dxy == "up" and direction == "Long" and yt_check == "falling":
            score -= 10; reasons.append("-10 USDJPY long: DXY up but yields falling (conflict)")
        elif dxy == "down" and direction == "Short" and yt_check == "rising":
            score -= 10; reasons.append("-10 USDJPY short: DXY down but yields rising (conflict)")
        elif dxy == "up" and direction == "Long":
            score += 15; reasons.append("+15 DXY up supports long USDJPY")
        elif dxy == "down" and direction == "Short":
            score += 15; reasons.append("+15 DXY down supports short USDJPY")
        else:
            reasons.append("+0 USDJPY DXY not aligned")
    else:
        if dxy == "up":
            if sym in ("EURUSD", "GBPUSD") and direction == "Short":
                score += 15; reasons.append("+15 DXY up supports short EUR/GBP")
            elif sym == "GOLD" and direction == "Short":
                score += 10; reasons.append("+10 DXY up mildly supports short gold")
            else:
                reasons.append("+0 DXY up not aligned")
        elif dxy == "down":
            if sym in ("EURUSD", "GBPUSD") and direction == "Long":
                score += 15; reasons.append("+15 DXY down supports long EUR/GBP")
            elif sym == "GOLD" and direction == "Long":
                score += 15; reasons.append("+15 DXY down supports long gold")
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

    # ---- USDJPY yield-specific override ----
    yt = regime.get("yield_trend", "flat")
    if sym == "USDJPY":
        if yt == "falling" and direction == "Long":
            score -= 15; reasons.append("-15 USDJPY long against falling US yields")
        elif yt == "rising" and direction == "Short":
            score -= 15; reasons.append("-15 USDJPY short against rising US yields")
        elif yt == "rising" and direction == "Long":
            score += 10; reasons.append("+10 USDJPY long aligned with rising yields")
        elif yt == "falling" and direction == "Short":
            score += 10; reasons.append("+10 USDJPY short aligned with falling yields")
        else:
            reasons.append("+0 USDJPY yield neutral")

    # ---- Generic 10Y yield alignment (non-USDJPY) ----
    if sym != "USDJPY":
        if yt == "rising" and direction == "Short":
            score += 10; reasons.append("+10 yields rising supports short")
        elif yt == "falling" and direction == "Long":
            score += 10; reasons.append("+10 yields falling supports long")
        elif yt == "falling" and direction == "Short" and sym in ("GOLD", "NAS100", "BTC"):
            score += 5; reasons.append("+5 yields falling mildly supports short risk")
        else:
            reasons.append("+0 yield trend neutral/misaligned")

    # Yield curve
    ct = regime.get("curve_trend", "flat")
    if ct == "steep" and direction == "Long" and asset_class in ("index", "crypto"):
        score += 5; reasons.append("+5 steep curve supports risk-on long")
    elif ct == "inverted" and direction == "Short":
        score += 5; reasons.append("+5 inverted curve supports short")
    else:
        reasons.append("+0 curve neutral")

    # Copper
    cop = regime.get("copper_trend", "flat")
    if cop == "up" and direction == "Long" and asset_class in ("index", "crypto", "fx"):
        score += 5; reasons.append("+5 copper up confirms risk-on")
    elif cop == "down" and direction == "Short" and asset_class in ("index", "crypto", "fx"):
        score += 5; reasons.append("+5 copper down confirms risk-off")
    elif cop == "down" and direction == "Long" and sym == "GOLD":
        score += 5; reasons.append("+5 copper down supports gold long (inflation hedge)")
    else:
        reasons.append("+0 copper neutral")

    # Brent
    br = regime.get("brent_trend", "flat")
    if br == "up" and direction == "Long" and sym in ("BRENT", "GOLD"):
        score += 5; reasons.append("+5 Brent up supports energy/gold long")
    elif br == "down" and direction == "Short" and sym in ("BRENT", "NAS100"):
        score += 5; reasons.append("+5 Brent down supports short energy/risk")
    elif br == "up" and direction == "Long" and asset_class == "index":
        score += 3; reasons.append("+3 Brent up mildly supports index long")
    else:
        reasons.append("+0 Brent neutral")

    # Correlation consistency
    try:
        from domain.correlation import check_correlation
        corr_delta, corr_reason = check_correlation(signal["symbol"], direction)
        score += corr_delta
        reasons.append(corr_reason)
    except Exception as e:
        reasons.append(f"+0 correlation check failed ({e})")

    # Higher timeframe alignment
    try:
        from domain.htf import check_htf_alignment
        htf_delta, htf_reason = check_htf_alignment(signal.get("ticker", signal["symbol"]), direction)
        score += htf_delta
        reasons.append(htf_reason)
    except Exception as e:
        reasons.append(f"+0 HTF check failed ({e})")

    return min(100, score), reasons
