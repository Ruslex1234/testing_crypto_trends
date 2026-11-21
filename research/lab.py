"""Strategy Lab: replay ~2 years of real hourly history through the SAME engine the live bot uses
(same strategies, fees 0.4% + slippage, stops, cooldowns, CRT resting orders), one hour at a time.

No lookahead: at each step a strategy sees completed hourly candles plus a 'forming' candle that
only contains the current price (as the live bot does), and daily candles completed so far.
Writes docs/lab/results.json (read by docs/lab/index.html).
Run: python3 research/lab.py      (uses data/ml/<COIN>_1h.csv, no network needed)
"""
import bisect
import json
import math
import multiprocessing as mp
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bot"))
sys.path.insert(0, os.path.join(ROOT, "research"))

COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK"]
WARM_DAYS = 80
OUT = os.path.join(ROOT, "docs", "lab")


def load():
    """Long history (data/history, since 2019) when present, else the 2-year ML cache."""
    import history
    import ml
    out = {}
    for c in COINS:
        rows = history.load(c)
        out[c] = rows if rows else ml.load_cache(c)
    return {c: r for c, r in out.items() if r}


def daily(rows):
    out = []
    for r in rows:
        d = r["t"] - r["t"] % 86400
        if out and out[-1]["t"] == d:
            o = out[-1]
            o["h"] = max(o["h"], r["h"]); o["l"] = min(o["l"], r["l"]); o["c"] = r["c"]; o["v"] += r["v"]
        else:
            out.append({"t": d, "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"], "v": r["v"]})
    return out


class Market:
    """Builds the md dict the engine expects, as of `now` (just after an hourly candle closed)."""

    def __init__(self, data):
        from market import resample
        self.resample = resample
        self.h = data
        self.ht = {c: [r["t"] for r in rows] for c, rows in data.items()}
        self.d = {c: daily(rows) for c, rows in data.items()}
        self.dt = {c: [r["t"] for r in rows] for c, rows in self.d.items()}

    def at(self, now):
        md = {}
        for c in COINS:
            k = bisect.bisect_left(self.ht[c], now) - 1  # last hourly candle closed by now
            if k < 300:
                continue
            last = self.h[c][k]
            if now - (last["t"] + 3600) > 3 * 3600:
                continue  # gap in data
            px = last["c"]
            forming = {"t": last["t"] + 3600, "o": px, "h": px, "l": px, "c": px, "v": 0.0}
            h = self.h[c][k - 298:k + 1] + [forming]
            day0 = now - now % 86400
            j = bisect.bisect_left(self.dt[c], day0)  # completed days are < day0
            today = [r for r in self.h[c][max(0, k - 30):k + 1] if r["t"] >= day0]
            part = ({"t": day0, "o": today[0]["o"], "h": max(r["h"] for r in today),
                     "l": min(r["l"] for r in today), "c": today[-1]["c"], "v": 0.0}
                    if today else {"t": day0, "o": px, "h": px, "l": px, "c": px, "v": 0.0})
            d = self.d[c][max(0, j - 299):j] + [part]
            md[c] = {"1h": h, "1d": d, "6h": self.resample(h, 6), "price": px}
        return md


def run_one(sid):
    import engine
    import strategies
    allfn = {s[0]: s for s in strategies.STRATEGIES}
    extra = {  # retired on day 1 for redundancy in that week's market: judged fairly here
        "trend_sma50": ("trend_sma50", "Trend: BTC above 50 day SMA", strategies.trend_sma50, "", ["BTC"]),
        "donchian": ("donchian", "Turtle breakout 20/10 (BTC+ETH)", strategies.donchian_turtle, "", ["BTC", "ETH"]),
        "vol_target": ("vol_target", "Volatility targeted trend (BTC+ETH)", strategies.vol_target, "", ["BTC", "ETH"]),
        "basket_trend": ("basket_trend", "Basket trend: 8 coins above 50d SMA", strategies.basket_trend, "", None),
        "btc_sma200": ("btc_sma200", "BTC above 200 day SMA", strategies.btc_sma200, "", ["BTC"]),
        "btc_eth_5050": ("btc_eth_5050", "BTC/ETH 50/50 rebalanced", strategies.btc_eth_5050, "", ["BTC", "ETH"]),
    }
    spec = allfn.get(sid) or extra[sid]
    engine.STRATEGIES = [spec]
    data = load()
    mkt = Market(data)
    # start when BTC has warm-up history; coins listed later simply join when they have data
    t_start = data["BTC"][0]["t"] + WARM_DAYS * 86400
    t_start -= t_start % 3600
    t_end = data["BTC"][-1]["t"] + 3600
    state = {"started": None, "accounts": {}, "runs": 0, "config": {}}
    curve, now = [], t_start
    while now <= t_end:
        md = mkt.at(now)
        if "BTC" in md:
            engine.step(state, md, now)
            a = state["accounts"][sid]
            curve.append((now, round(a["equity"], 4), round(sum(
                q * md[x]["price"] for x, q in a["holdings"].items() if x in md) / max(a["equity"], 1e-9), 3)))
            a["history"] = a["history"][-50:]
            state["btc_history"] = state["btc_history"][-10:]
            j = a.get("journal")
            if j:
                j["pending"] = j["pending"][-30:]
        now += 3600
    a = state["accounts"][sid]
    return {"id": sid, "name": spec[1], "curve": curve, "trades": len(a["trades"]),
            "fees": round(a["fees_paid"], 2), "error": a.get("error")}


def metrics(curve, btc_by_t, btc_trend):
    t = [x[0] for x in curve]
    eq = [x[1] for x in curve]
    expo = [x[2] for x in curve]
    days = (t[-1] - t[0]) / 86400
    tot = eq[-1] / eq[0] - 1
    cagr = (eq[-1] / eq[0]) ** (365 / days) - 1 if days > 0 else 0
    peak, dd = eq[0], 0.0
    for v in eq:
        peak = max(peak, v)
        dd = max(dd, 1 - v / peak)
    # daily returns for Sharpe / rolling windows
    dly = [eq[i] for i in range(0, len(eq), 24)]
    rets = [dly[i] / dly[i - 1] - 1 for i in range(1, len(dly))]
    m = sum(rets) / len(rets)
    sd = math.sqrt(sum((r - m) ** 2 for r in rets) / len(rets)) or 1e-12
    sharpe = m / sd * math.sqrt(365)
    roll = {}
    for w in (7, 30, 90):
        rr = sorted(dly[i] / dly[i - w] - 1 for i in range(w, len(dly)))
        if rr:
            roll[f"{w}d"] = {"p_positive": sum(1 for r in rr if r > 0) / len(rr), "median": rr[len(rr) // 2],
                             "worst": rr[0], "best": rr[-1], "p10": rr[len(rr) // 10], "p90": rr[9 * len(rr) // 10]}
    # regimes: BTC above / below its 200 day average at each day
    reg = {"bull": [], "bear": []}
    for i in range(1, len(dly)):
        k = "bull" if btc_trend.get(t[(i - 1) * 24] - t[(i - 1) * 24] % 86400, True) else "bear"
        reg[k].append(rets[i - 1])
    regimes = {k: {"days": len(v), "avg_daily": sum(v) / len(v) if v else None,
                   "compounded": (math.prod(1 + x for x in v) - 1) if v else None} for k, v in reg.items()}
    half = len(eq) // 2
    monthly = {}
    for i in range(len(t)):
        mkey = time.strftime("%Y-%m", time.gmtime(t[i]))
        monthly.setdefault(mkey, [eq[i], eq[i]])
        monthly[mkey][1] = eq[i]
    mrets = {k: v[1] / v[0] - 1 for k, v in monthly.items()}
    return {"total": tot, "cagr": cagr, "max_dd": dd, "sharpe": sharpe, "days": days,
            "exposure": sum(expo) / len(expo), "first_half": eq[half] / eq[0] - 1,
            "second_half": eq[-1] / eq[half] - 1, "rolling": roll, "regimes": regimes,
            "monthly": mrets, "pos_months": sum(1 for v in mrets.values() if v > 0) / max(1, len(mrets)),
            "per_day_at": {str(cap): cap * cagr / 365 for cap in (1000, 10000, 75000)}}


def main(ids=None):
    import strategies
    ids = ids or [s[0] for s in strategies.STRATEGIES if s[0] not in ("ml_predictor", "quick_trader")] + \
        ["trend_sma50", "donchian", "vol_target", "basket_trend", "btc_sma200", "btc_eth_5050"]
    t0 = time.time()
    with mp.Pool(min(len(ids), os.cpu_count() or 2)) as pool:
        runs = pool.map(run_one, ids)
    data = load()
    btc = data["BTC"]
    bd = daily(btc)
    btc_trend, closes = {}, []
    for r in bd:
        closes.append(r["c"])
        btc_trend[r["t"]] = len(closes) < 200 or closes[-1] > sum(closes[-200:]) / 200
    out = {"generated": int(time.time()), "runtime_s": round(time.time() - t0),
           "fee": "0.40% per fill + 0.05-0.15% slippage", "strategies": []}
    for r in runs:
        if not r["curve"]:
            continue
        m = metrics(r["curve"], None, btc_trend)
        thin = [(t, e) for t, e, _ in r["curve"][::24]]
        out["strategies"].append({"id": r["id"], "name": r["name"], "trades": r["trades"], "fees": r["fees"],
                                  "error": r["error"], **m, "curve": thin})
        print(f"{r['name']:<42} total {m['total'] * 100:+7.1f}%  CAGR {m['cagr'] * 100:+6.1f}%  "
              f"maxDD {m['max_dd'] * 100:5.1f}%  sharpe {m['sharpe']:5.2f}  trades {r['trades']:4d}  "
              f"30d>0 {m['rolling']['30d']['p_positive'] * 100:3.0f}%", flush=True)
    prev_path = os.path.join(OUT, "results.json")
    if os.path.exists(prev_path):  # merge: a partial re-run keeps the other strategies
        with open(prev_path) as f:
            old = json.load(f)
        new_ids = {x["id"] for x in out["strategies"]}
        out["strategies"] = [x for x in old.get("strategies", []) if x["id"] not in new_ids] + out["strategies"]
    s0 = out["strategies"][0]["curve"]
    out["span"] = [s0[0][0], s0[-1][0]]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("runtime", out["runtime_s"], "s")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
