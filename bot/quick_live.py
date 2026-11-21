"""Live 'Quick 1h long/short' paper account (perp-style: can bet for AND against the market).

Every hourly run:
  1. re-check open positions against every 1 minute candle since the last run (stop-loss,
     take-profit, or close at the 1 hour mark) and settle profit/loss
  2. score last hour's predictions against what actually happened
  3. retrain on recent 15m history (window chosen by walk-forward research) and predict, for each
     coin, LONG and SHORT outcome odds for the next hour
  4. open at most MAX_TRADES positions where expected value beats the walk-forward margin
"""
import json
import os
import time

import numpy as np

import quick as Q

CFG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "quick", "live_config.json")
MAX_TRADES = 3
RISK_PCT = 0.01


def _cfg():
    try:
        with open(CFG) as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {"window_days": Q.TRAIN_DAYS, "margin": None}


def _settle(md, memo, now, equity_now):
    from journal import new_candles
    events = []
    pos = memo.setdefault("pos", {})
    since = memo.get("last_t", now - 3600)
    for c, p in list(pos.items()):
        exit_px, why = None, None
        for b in new_candles(md[c], since):
            if b["t"] >= p["expire"]:
                exit_px, why = b["o"], "1h time exit"
                break
            hit_sl = b["l"] <= p["sl"] if p["side"] == 1 else b["h"] >= p["sl"]
            hit_tp = b["h"] >= p["tp"] if p["side"] == 1 else b["l"] <= p["tp"]
            if hit_sl:  # same minute as target: assume the stop (conservative)
                exit_px = (min(p["sl"], b["o"]) if p["side"] == 1 else max(p["sl"], b["o"]))
                why = "stop-loss"
                break
            if hit_tp:
                exit_px, why = p["tp"], "take-profit"
                break
        if exit_px is None and now >= p["expire"]:
            exit_px, why = md[c]["price"], "1h time exit"
        if exit_px is None:
            continue
        pnl = p["notional"] * p["side"] * (exit_px / p["entry"] - 1)
        fee = p["notional"] * Q.FEE_RT
        r = (pnl - fee) / (p["notional"] * p["sl_pct"])
        events.append({"type": "close", "t": now, "asset": c, "side": "close " + ("long" if p["side"] == 1 else "short"),
                       "price": exit_px, "notional": p["notional"], "pnl": pnl, "fee": fee,
                       "reason": f"Quick {why}: {r:+.2f}R"})
        memo.setdefault("closed", []).append({**p, "coin": c, "exit": exit_px, "why": why, "r": round(r, 3),
                                              "pnl": round(pnl - fee, 4), "exit_t": now})
        memo["closed"] = memo["closed"][-150:]
        del pos[c]
    return events


def _score(memo, md, now):
    """Score each previous hourly prediction once its hour is over: did the favoured side work?"""
    st = memo.setdefault("score", {"n": 0, "dir_right": 0, "sum_r_best": 0.0, "buckets": {}})
    keep = []
    for pr in memo.get("pending", []):
        if now < pr["t"] + 3600:
            keep.append(pr)
            continue
        rows = [b for b in md[pr["coin"]].get("5m", md[pr["coin"]]["1h"]) if pr["t"] <= b["t"] < pr["t"] + 3600]
        if not rows:
            continue
        side, e, slp = pr["side"], pr["price"], pr["sl_pct"]
        sl, tp = e * (1 - side * slp), e * (1 + side * slp * Q.RR)
        r = side * (rows[-1]["c"] / e - 1) / slp
        for b in rows:
            if (b["l"] <= sl) if side == 1 else (b["h"] >= sl):
                r = -1.0
                break
            if (b["h"] >= tp) if side == 1 else (b["l"] <= tp):
                r = Q.RR
                break
        r -= Q.FEE_RT / slp
        st["n"] += 1
        st["dir_right"] += int(side * (rows[-1]["c"] - e) > 0)
        st["sum_r_best"] += r
        k = "≥0.15" if pr["ev"] >= 0.15 else "0–0.15" if pr["ev"] >= 0 else "−0.3–0" if pr["ev"] >= -0.3 else "<−0.3"
        b = st["buckets"].setdefault(k, {"n": 0, "sum_ev": 0.0, "sum_r": 0.0})
        b["n"] += 1
        b["sum_ev"] += pr["ev"]
        b["sum_r"] += r
    memo["pending"] = keep


def quick_trader(md, memo, now=None):
    now = now or int(time.time())
    cfg = _cfg()
    margin = cfg.get("margin")
    eq_now = None
    events = _settle(md, memo, now, eq_now)
    _score(memo, md, now)
    days = (cfg.get("window_days") or 60) + 3
    series = {c: Q.fetch_15m(c, days) for c in Q.COINS if c in md}
    D = Q.dataset(series)
    models, n = Q.fit(D, now, cfg.get("window_days"))
    latest = {}
    for ci, c in enumerate(series):
        idx = np.flatnonzero(D["coin"] == ci)
        if not len(idx):
            continue
        i = idx[-1]
        out = Q.predict_ev(models, D["X"][i:i + 1], D["slp"][i:i + 1])
        evl, pl = out[1][0][0], out[1][1][0]
        evs, ps = out[-1][0][0], out[-1][1][0]
        side = 1 if evl >= evs else -1
        latest[c] = {"t": int(D["t"][i]), "coin": c, "price": float(md[c]["price"]),
                     "sl_pct": float(D["slp"][i]),
                     "long": {"tp": round(float(pl[0]), 3), "sl": round(float(pl[1]), 3), "ev": round(float(evl), 3)},
                     "short": {"tp": round(float(ps[0]), 3), "sl": round(float(ps[1]), 3), "ev": round(float(evs), 3)},
                     "side": side, "ev": round(float(max(evl, evs)), 3)}
    memo.setdefault("pending", []).extend(
        {"t": now, "coin": v["coin"], "side": v["side"], "ev": v["ev"], "price": v["price"], "sl_pct": v["sl_pct"]}
        for v in latest.values())
    # entries
    pos = memo.setdefault("pos", {})
    cash_like = memo.get("equity_hint", 100.0)
    cands = sorted((v for v in latest.values() if margin is not None and v["ev"] > margin
                    and v["coin"] not in pos), key=lambda v: -v["ev"])
    for v in cands[:max(0, MAX_TRADES - len(pos))]:
        c, side, slp, px = v["coin"], v["side"], v["sl_pct"], v["price"]
        notional = min(cash_like / MAX_TRADES, RISK_PCT * cash_like / slp)
        pos[c] = {"side": side, "entry": px, "sl": px * (1 - side * slp), "tp": px * (1 + side * slp * Q.RR),
                  "sl_pct": slp, "notional": notional, "t": now, "expire": now + 3600, "ev": v["ev"]}
        events.append({"type": "open", "t": now, "asset": c, "side": "open " + ("long" if side == 1 else "short"),
                       "price": px, "notional": notional, "fee": 0.0,
                       "reason": f"Quick {'LONG' if side == 1 else 'SHORT'}: EV {v['ev']:+.2f}R, "
                                 f"P(TP) {v['long' if side == 1 else 'short']['tp'] * 100:.0f}%"})
    # unrealized P&L of open positions at the latest price
    memo["unrealized"] = sum(p["notional"] * p["side"] * (md[c]["price"] / p["entry"] - 1) for c, p in pos.items())
    memo["last_t"] = now
    memo["latest"] = latest
    memo["model"] = {"trained_on": n, "trained_at": now, "margin": margin, "window": cfg.get("window")}
    memo["stops"] = {c: p["sl"] for c, p in pos.items()}
    memo["stop_type"] = "quick trade stop"
    memo["levels"] = [{"name": "quick take-profit", "asset": c, "price": p["tp"],
                       "dir": "above" if p["side"] == 1 else "below"} for c, p in pos.items()]
    if margin is None:
        memo["why"] = "Predicting long/short odds every hour, NOT trading: research found no edge after costs yet"
    elif pos:
        memo["why"] = "Open: " + ", ".join(f"{'LONG' if p['side'] == 1 else 'SHORT'} {c}" for c, p in pos.items())
    else:
        b = max(latest.values(), key=lambda v: v["ev"]) if latest else None
        memo["why"] = (f"No trade this hour: best {('LONG' if b['side'] == 1 else 'SHORT')} {b['coin']} "
                       f"EV {b['ev']:+.2f}R vs margin {margin}R") if b else "No data"
    return events


quick_trader.broker = True
