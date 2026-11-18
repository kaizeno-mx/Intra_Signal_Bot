import sys, json, os
from datetime import datetime
from config import UNIVERSE, SESSIONS, CONFIDENCE_THRESHOLD, DEDUP_MINUTES
from domain.data import fetch_intraday
from domain.macro import fetch_macro_regime
from domain.smc import detect_swings, detect_liquidity_sweep, detect_fvg, find_nearest_swing
from domain.confidence import compute_confidence
from domain.telegram import send, format_signal

DEDUP_PATH = "dedup.json"

def load_dedup():
    if os.path.exists(DEDUP_PATH):
        try:
            with open(DEDUP_PATH) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_dedup(d):
    with open(DEDUP_PATH, "w") as f:
        json.dump(d, f, indent=2)

def should_send(key, dedup):
    last = dedup.get(key)
    if last is None:
        return True
    try:
        last_dt = datetime.strptime(last, "%Y-%m-%d %H:%M")
    except Exception:
        return True
    return (datetime.now() - last_dt).total_seconds() / 60 > DEDUP_MINUTES

def scan_symbol(symbol, meta, regime, session):
    df = fetch_intraday(meta["ticker"])
    if df is None:
        return None
    high = df["High"].values
    low = df["Low"].values
    close = df["Close"].values
    sh, sl = detect_swings(high, low)
    sweep = detect_liquidity_sweep(high, low, close, sh, sl)
    fvg = detect_fvg(high, low, close)
    print(f"  [STRUCT] {symbol}: bars={len(high)} swings_h={int(sh.sum())} swings_
    l={int(sl.sum())} sweep={sweep} fvg={fvg}")
    if sweep is None:
        return None
    if fvg is not None and fvg != sweep:
        return None  
    direction = "Long" if sweep == "bullish" else "Short"
    target = find_nearest_swing(high, low, sh, sl, direction)
    signal = {
        "symbol": symbol, "direction": direction,
        "price": round(float(close[-2]), 5),
        "sweep": sweep, "fvg": fvg,
        "regime": regime["regime"], "dxy_trend": regime["dxy_trend"],
        "vix": round(regime["vix_level"], 1), "vix_trend": regime["vix_trend"],
        "session": session, "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "timeframe": "1h", "target": round(target, 5) if target else None,
    }
    conf, reasons = compute_confidence(signal, regime, meta["class"], session)
    signal["confidence"] = conf
    signal["reasons"] = reasons
    return signal

def main(session):
    print(f"[{datetime.now()}] === {session} session scan ===")
    regime = fetch_macro_regime()
    print(f"Regime: {regime}")
    dedup = load_dedup()
    signals_sent = 0
    evaluated = 0
    for symbol in SESSIONS.get(session, []):
        meta = UNIVERSE[symbol]
        evaluated += 1
        sig = scan_symbol(symbol, meta, regime, session)
        if sig is None:
            print(f"  {symbol}: no structure")
            continue
        print(f"  {symbol}: {sig['direction']} conf={sig['confidence']}%")
        if sig["confidence"] < CONFIDENCE_THRESHOLD:
            print(f"    -> below threshold")
            continue
        key = f"{symbol}_{sig['direction']}"
        if not should_send(key, dedup):
            print(f"    -> dedup skip")
            continue
        if send(format_signal(sig)):
            dedup[key] = sig["time"]
            signals_sent += 1
    save_dedup(dedup)
    if signals_sent == 0:
        send(f"ℹ️ *{session} scan complete*\nEvaluated: {evaluated} | Signals: 0 (threshold {CONFIDENCE_THRESHOLD}%)")
    print(f"[DONE] Sent {signals_sent} signal(s)")

if __name__ == "__main__":
    session = sys.argv[1] if len(sys.argv) > 1 else "NewYork"
    if session not in SESSIONS:
        print(f"Unknown session '{session}'. Valid: {list(SESSIONS.keys())}")
        sys.exit(1)
    main(session)
