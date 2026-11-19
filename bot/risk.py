"""Stop-loss layer, enforced by the engine every hourly run, plus a scorecard that checks
whether each stop-out actually helped (price 24h and 72h after the exit).

Stop types:
  trail  -> ATR trailing stop: highest price since entry minus K x ATR(14, daily).
            Only ever moves up, so it locks in gains as a trade works.
  own    -> the strategy publishes its own stop levels in memo["stops"] (RSI, Bollinger, box).
  crash  -> fixed disaster stop at 55% of the crash buyer's reference high.
None     -> no stop (benchmark, DCA, grid).
"""

STOP_RULES = {
    "trw_tpi": ("trail", 2.5),
    "ema_cross_6h": ("trail", 2.5),
    "momentum_rotation": ("trail", 3.0),
    "rsi_reversion": ("own", None),
    "bollinger": ("own", None),
    "trw_box": ("own", None),
    "crash_buyer": ("crash", None),
}
COOLDOWN = {"crash_buyer": 7 * 86400}
DEFAULT_COOLDOWN = 24 * 3600
EVAL_HOURS = (24, 72)


def atr(rows, n=14):
    d = rows[:-1]  # completed candles
    trs = [max(r["h"] - r["l"], abs(r["h"] - p["c"]), abs(r["l"] - p["c"]))
           for p, r in zip(d[-n - 1:-1], d[-n:])]
    return sum(trs) / len(trs)


def check_stops(acct, md, prev, prices):
    """Before the strategy runs: which stops were hit since the last run?
    Uses the real hourly lows (not just the price at wake-up), like a resting stop order.
    Returns [(asset, fill_price)]; a candle that opens below the stop fills at its open (gap)."""
    from journal import new_candles
    hit = []
    for a, st in acct.get("stops", {}).items():
        if a not in acct["holdings"] or a not in prices:
            continue
        fill = None
        for r in new_candles(md[a], prev):
            if r["o"] <= st["stop"]:
                fill = r["o"]
                break
            if r["l"] <= st["stop"]:
                fill = st["stop"]
                break
        if fill is None and prices[a] <= st["stop"]:
            fill = prices[a]
        if fill is not None:
            hit.append((a, fill))
    return hit


def record_stop(acct, sid, asset, price, now):
    st = acct["stops"].pop(asset)
    acct.setdefault("stop_events", []).append({
        "t": now, "asset": asset, "stop": round(st["stop"], 6), "exit": price,
        "entry": st.get("entry"), "after": {}})
    acct.setdefault("cooldown", {})[asset] = now + COOLDOWN.get(sid, DEFAULT_COOLDOWN)


def apply_cooldown(acct, target, now):
    """Block re-entry into an asset that was just stopped out."""
    cd = acct.get("cooldown", {})
    for a in list(target):
        if cd.get(a, 0) > now and a not in acct["holdings"]:
            target.pop(a)
    acct["cooldown"] = {a: t for a, t in cd.items() if t > now}
    return target


def update_stops(acct, sid, md, prices):
    """After trading: set or trail stops for every held asset, drop stops for sold assets."""
    rule = STOP_RULES.get(sid)
    stops = acct.setdefault("stops", {})
    for a in list(stops):
        if a not in acct["holdings"]:
            stops.pop(a)
    if not rule:
        return
    kind, k = rule
    for a in acct["holdings"]:
        p = prices[a]
        st = stops.get(a)
        if kind == "trail":
            dist = k * atr(md[a]["1d"])
            if not st:
                st = {"entry": p, "high": p, "stop": p - dist, "type": f"{k}x ATR trailing"}
            st["high"] = max(st["high"], p)
            st["stop"] = max(st["stop"], st["high"] - dist)
        elif kind == "own":
            lvl = acct["memo"].get("stops", {}).get(a)
            if lvl is None:
                continue
            st = st or {"entry": p, "type": "strategy stop"}
            st["stop"] = lvl
        elif kind == "crash":
            ref = acct["memo"].get("ref_high")
            if not ref:
                continue
            st = st or {"entry": p, "type": "disaster stop (45% below ref high)"}
            st["stop"] = ref * 0.55
        st["dist"] = round(st["stop"] / p - 1, 4)
        stops[a] = st


def evaluate_stop_events(acct, prices, now):
    """Fill in how price moved 24h/72h after each stop. Negative move = the stop saved money."""
    for ev in acct.get("stop_events", []):
        for h in EVAL_HOURS:
            key = f"{h}h"
            if key not in ev["after"] and now - ev["t"] >= h * 3600 and ev["asset"] in prices:
                ev["after"][key] = round(prices[ev["asset"]] / ev["exit"] - 1, 4)
