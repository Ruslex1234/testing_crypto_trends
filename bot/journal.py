"""Hourly decision journal and scenario log.

Every run is a decision point for every strategy (be in, be out, change nothing). Each run:
  1. Uses the newly completed candles (data the previous run did not have) to score past
     decisions at 1h and 24h, and to check whether any planned price level was touched.
  2. Records this run's decision and the levels it is watching, to be scored next time.

"With"    = what following the strategy earned (its exposure x the move).
"Against" = what doing the opposite earned (out when it was in, in when it was out).
"""

HORIZONS = {"1h": 3600, "24h": 86400}
SLACK = 600  # runs can drift by a few minutes
MAX_SCENARIOS = 80


def new_candles(mda, since):
    """Candles that started after `since` (the previous run): data the previous run never saw.
    Prefers 1 minute candles (same fills a person watching every minute would get), then 5m, then 1h."""
    if since is None:
        return []
    fine = mda.get("1m") or []
    coarse = mda.get("5m") or mda["1h"]
    if not fine:
        return [r for r in coarse if r["t"] >= since]
    start = fine[0]["t"]  # 1m history is ~5h; fill any older gap with coarser candles
    gap = [r for r in coarse if r["t"] >= since and r["t"] + 300 <= start]
    return gap + [r for r in fine if r["t"] >= since]


def _stats(acct):
    j = acct.setdefault("journal", {"pending": [], "runs": 0, "moves": 0})
    for h in HORIZONS:
        j.setdefault(h, {"n": 0, "right": 0, "with": 0.0, "against": 0.0})
    return j


def score_decisions(acct, prices, now):
    j = _stats(acct)
    keep = []
    for d in j["pending"]:
        assets = [a for a in d["p"] if a in prices]
        if not assets:
            continue
        rets = {a: prices[a] / d["p"][a] - 1 for a in assets}
        move = sum(rets.values()) / len(rets)
        expo = sum(d["x"].get(a, 0) for a in assets)
        for h, secs in HORIZONS.items():
            if h in d["done"] or now - d["t"] < secs - SLACK:
                continue
            s = j[h]
            s["n"] += 1
            s["with"] += sum(d["x"].get(a, 0) * r for a, r in rets.items())
            s["against"] += (1 - min(expo, 1)) * move
            in_mkt = expo >= 0.5
            if (in_mkt and move > 0) or (not in_mkt and move <= 0):
                s["right"] += 1
            d["done"].append(h)
        if len(d["done"]) < len(HORIZONS):
            keep.append(d)
    j["pending"] = keep


def record_decision(acct, assets, prices, now, traded):
    j = _stats(acct)
    eq = acct["cash"] + sum(q * prices[a] for a, q in acct["holdings"].items())
    x = {a: round(acct["holdings"].get(a, 0) * prices[a] / eq, 4) for a in assets if a in prices}
    j["pending"].append({"t": now, "p": {a: prices[a] for a in x}, "x": x, "done": []})
    j["runs"] += 1
    j["moves"] += 1 if traded else 0
    j["last"] = {"t": now, "exposure": round(sum(x.values()), 3), "traded": traded}


def check_scenarios(acct, md, prev, prices, now):
    """Did price touch any level the strategy was watching last run? Uses real highs/lows."""
    log = acct.setdefault("scenarios", [])
    for lv in acct.get("watch", []):
        a = lv["asset"]
        if a not in md:
            continue
        ref = lv.get("ref")  # price when the level was set: only count real crossings
        if ref is not None and ((lv["dir"] == "above" and ref >= lv["price"]) or
                                (lv["dir"] == "below" and ref <= lv["price"])):
            continue
        for r in new_candles(md[a], prev):
            hit = r["h"] >= lv["price"] if lv["dir"] == "above" else r["l"] <= lv["price"]
            if hit:
                log.append({"t": r["t"], "name": lv["name"], "asset": a,
                            "level": lv["price"], "dir": lv["dir"], "after": {}})
                break
    for ev in log:
        if "24h" not in ev["after"] and now - ev["t"] >= 86400 - SLACK and ev["asset"] in prices:
            ev["after"]["24h"] = round(prices[ev["asset"]] / ev["level"] - 1, 4)
    acct["scenarios"] = log[-MAX_SCENARIOS:]


def set_watch(acct, prices):
    acct["watch"] = [{**lv, "price": round(lv["price"], 6), "ref": prices.get(lv["asset"])}
                     for lv in acct["memo"].get("levels", []) if lv.get("price")]
