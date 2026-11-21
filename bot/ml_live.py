"""Live 'AI predictor' paper account. Every hour:
  1. retrain on all hourly history (cache + latest candles), purged so no label peeks ahead
  2. predict P(take-profit before stop-loss within 24h) for each of 8 coins
  3. score earlier predictions against what actually happened (live calibration)
  4. manage open positions against every 1 minute candle since the last run
  5. open new positions only where expected value beats fees by the walk-forward margin
"""
import json
import os
import time

import ml

LIVE_CFG = os.path.join(ml.ROOT, "docs", "ml", "live_config.json")
MAX_OPEN = 3
RISK_PCT = 0.02
KEEP_PREDS = 400


def _margin():
    try:
        with open(LIVE_CFG) as f:
            return json.load(f).get("margin")
    except Exception:  # noqa: BLE001
        return None


def _hourly(md, coin, now):
    live = [r for r in md[coin]["1h"] if r["t"] + 3600 <= now]  # completed candles only
    return ml.merge(ml.load_cache(coin), live)


def _resolve(memo, series):
    """Score predictions whose 24h window has fully passed, with the same rules as training."""
    stats = memo.setdefault("calib", {})
    keep = []
    for pr in memo.get("preds", []):
        if pr.get("outcome") is not None:
            keep.append(pr)
            continue
        rows = series.get(pr["coin"], [])
        fut = [r for r in rows if pr["t"] < r["t"] <= pr["t"] + ml.HORIZON * 3600]
        if len(fut) < ml.HORIZON:
            keep.append(pr)
            continue
        out, r = "timeout", (fut[-1]["c"] / pr["price"] - 1) / pr["sl_pct"]
        for b in fut:
            if b["l"] <= pr["sl"]:
                out, r = "loss", -1.0
                break
            if b["h"] >= pr["tp"]:
                out, r = "win", ml.K_TP / ml.K_SL
                break
        pr["outcome"], pr["r"] = out, round(r - ml.FEE_RT / pr["sl_pct"], 3)
        b = f"{min(int(pr['p'] * 10), 9) / 10:.1f}"
        s = stats.setdefault(b, {"n": 0, "wins": 0, "sum_p": 0.0, "sum_r": 0.0})
        s["n"] += 1
        s["wins"] += out == "win"
        s["sum_p"] += pr["p"]
        s["sum_r"] += pr["r"]
        keep.append(pr)
    memo["preds"] = keep[-KEEP_PREDS:]


def ml_predictor(md, memo, now=None):
    from journal import new_candles
    now = now or int(time.time())
    events = []
    series = {c: _hourly(md, c, now) for c in ml.COINS if c in md}
    if min((len(s) for s in series.values()), default=0) < 24 * 60:
        memo["why"] = "Building price history for training (needs the hourly cache in data/ml)"
        return events
    # 1-2: train and predict
    X, y, rr, t, coin, slp, price, hold = ml.dataset(series)
    model, n_train = ml.train(X, y, t, now)
    margin = _margin()
    memo["model"] = {"trained_on": n_train, "trained_at": now, "margin": margin}
    latest = {}
    import numpy as np
    for ci, c in enumerate(series):
        m = np.flatnonzero(coin == ci)
        i = m[-1]
        if not np.all(np.isfinite(X[i])):
            continue
        p = float(model.predict_proba(X[i:i + 1])[0, 1])
        sl_pct = float(slp[i])
        px = float(price[i])
        ev = float(ml.ev_r(p, sl_pct))
        need = (1 + ml.FEE_RT / sl_pct) / (1 + ml.K_TP / ml.K_SL)
        latest[c] = {"t": int(t[i]), "coin": c, "p": round(p, 4), "need": round(need, 4),
                     "ev": round(ev, 3), "price": px, "sl_pct": sl_pct,
                     "sl": px * (1 - sl_pct), "tp": px * (1 + sl_pct * ml.K_TP / ml.K_SL)}
    # 3: record + score predictions (one per coin per hour)
    seen = {(x["coin"], x["t"]) for x in memo.get("preds", [])}
    memo.setdefault("preds", []).extend(v for v in latest.values() if (v["coin"], v["t"]) not in seen)
    _resolve(memo, series)
    # 4: manage open positions on every minute since last run
    pos = memo.setdefault("pos", {})
    since = memo.get("last_t", now - 3600)
    for c, ps in list(pos.items()):
        for b in new_candles(md[c], since):
            if b["l"] <= ps["sl"]:
                events.append({"t": b["t"], "asset": c, "side": "sell", "frac": 1.0,
                               "price": min(ps["sl"], b["o"]), "reason": "AI stop-loss"})
                ps["closed"] = "loss"
                break
            if b["h"] >= ps["tp"]:
                events.append({"t": b["t"], "asset": c, "side": "sell", "frac": 1.0,
                               "price": ps["tp"], "reason": "AI take-profit"})
                ps["closed"] = "win"
                break
            if b["t"] >= ps["expire"]:
                events.append({"t": b["t"], "asset": c, "side": "sell", "frac": 1.0,
                               "price": b["o"], "reason": "AI time exit (24h)"})
                ps["closed"] = "timeout"
                break
        if ps.get("closed"):
            memo.setdefault("closed", []).append({**ps, "coin": c, "exit_t": events[-1]["t"],
                                                  "exit": events[-1]["price"]})
            memo["closed"] = memo["closed"][-100:]
            del pos[c]
    # 5: new entries
    cands = sorted((v for v in latest.values() if margin is not None and v["ev"] > margin
                    and v["coin"] not in pos), key=lambda v: -v["ev"])
    for v in cands:
        if len(pos) >= MAX_OPEN:
            break
        c = v["coin"]
        live_px = md[c]["price"]
        frac = min(1.0 / MAX_OPEN, RISK_PCT / v["sl_pct"])
        events.append({"t": now, "asset": c, "side": "buy", "price": live_px, "frac": frac,
                       "reason": f"AI entry: P(win) {v['p'] * 100:.0f}% vs {v['need'] * 100:.0f}% needed, EV {v['ev']:+.2f}R"})
        pos[c] = {"entry": live_px, "sl": live_px * (1 - v["sl_pct"]),
                  "tp": live_px * (1 + v["sl_pct"] * ml.K_TP / ml.K_SL), "t": now,
                  "expire": now + ml.HORIZON * 3600, "p": v["p"], "ev": v["ev"]}
    memo["last_t"] = now
    memo["latest"] = latest
    memo["stops"] = {c: ps["sl"] for c, ps in pos.items()}
    memo["levels"] = [{"name": "AI take-profit", "asset": c, "price": ps["tp"], "dir": "above"}
                      for c, ps in pos.items()]
    best = max(latest.values(), key=lambda v: v["ev"]) if latest else None
    if margin is None:
        memo["why"] = ("Predicting every hour, NOT trading: the walk-forward backtest has not found "
                       "a threshold that beats fees yet")
    elif pos:
        memo["why"] = "Holding " + ", ".join(f"{c} (TP ${p['tp']:,.4g}, SL ${p['sl']:,.4g})" for c, p in pos.items())
    elif best:
        memo["why"] = (f"No trade: best is {best['coin']} P(win) {best['p'] * 100:.0f}% "
                       f"(needs {best['need'] * 100:.0f}%), EV {best['ev']:+.2f}R vs margin {margin}R")
    return events


ml_predictor.broker = True
