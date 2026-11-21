"""Walk-forward backtest of the AI predictor on ~2 years of hourly data for 8 coins.

Strictly no lookahead:
  * the model for month k is trained only on trades whose outcome was known before month k starts
  * the trading threshold for month k is chosen only from out-of-sample results of months < k
  * one open position per coin, at most MAX_OPEN at once, entries at the candle close
Writes docs/ml/results.json, docs/ml/REPORT.md and docs/ml/live_config.json (threshold for live).
Also builds/updates the hourly cache in data/ml/ (Coinbase, 2 years).
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bot"))
import ml  # noqa: E402

OUT = os.path.join(ROOT, "docs", "ml")
MARGINS = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4]
MAX_OPEN = 3
MIN_TRAIN_DAYS = 180


def _get(url):
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper-trader-bot/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


def update_cache(coin, days=730):
    """Append completed hourly candles to data/ml/<COIN>_1h.csv (bootstraps 2 years)."""
    os.makedirs(ml.CACHE, exist_ok=True)
    rows = ml.load_cache(coin)
    now = int(time.time()) // 3600 * 3600
    t = rows[-1]["t"] + 3600 if rows else now - days * 86400
    new = {}
    while t < now:
        t2 = min(t + 300 * 3600, now)
        iso = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for r in _get(f"https://api.exchange.coinbase.com/products/{coin}-USD/candles"
                      f"?granularity=3600&start={iso(t)}&end={iso(t2)}"):
            if int(r[0]) < now:  # completed candles only
                new[int(r[0])] = {"t": int(r[0]), "o": r[3], "h": r[2], "l": r[1], "c": r[4], "v": r[5]}
        t = t2
        time.sleep(0.3)
    add = [new[k] for k in sorted(new) if not rows or k > rows[-1]["t"]]
    p = os.path.join(ml.CACHE, f"{coin}_1h.csv")
    write_header = not os.path.exists(p)
    with open(p, "a") as f:
        if write_header:
            f.write("t,o,h,l,c,v\n")
        for r in add:
            f.write(f"{r['t']},{r['o']},{r['h']},{r['l']},{r['c']},{r['v']}\n")
    return len(rows) + len(add), len(add)


def month_starts(t0, t1):
    d = datetime.fromtimestamp(t0, timezone.utc).replace(day=1, hour=0, minute=0, second=0)
    out = []
    while d.timestamp() < t1:
        out.append(int(d.timestamp()))
        d = d.replace(year=d.year + (d.month == 12), month=d.month % 12 + 1)
    return out


def simulate(sel, t, coin, rr_net, hold, win):
    """Take selected signals in time order, one per coin, at most MAX_OPEN open."""
    order = np.argsort(t[sel], kind="stable")
    idx = np.flatnonzero(sel)[order]
    busy = {}
    trades = []
    for i in idx:
        busy = {c: e for c, e in busy.items() if e > t[i]}
        if coin[i] in busy or len(busy) >= MAX_OPEN:
            continue
        busy[coin[i]] = t[i] + hold[i] * 3600
        trades.append(i)
    return np.array(trades, dtype=int)


def summary(tr, t, rr_net, win, coin):
    if len(tr) == 0:
        return {"n": 0}
    r = rr_net[tr]
    eq = np.cumsum(r)
    dd = float(np.max(np.maximum.accumulate(eq) - eq)) if len(eq) else 0.0
    days = max(1.0, (t[tr].max() - t[tr].min()) / 86400)
    by_coin = {ml.COINS[c]: {"n": int((coin[tr] == c).sum()), "exp": float(r[coin[tr] == c].mean())}
               for c in np.unique(coin[tr])}
    acc = 1.0
    for x in r:
        acc *= 1 + 0.02 * x  # $100 account risking 2% per trade
    return {"n": int(len(tr)), "win_rate": float((win[tr] == 1).mean()), "exp_r": float(r.mean()),
            "net_r": float(r.sum()), "max_dd_r": dd, "trades_per_day": len(tr) / days,
            "pf": float(r[r > 0].sum() / max(1e-9, -r[r <= 0].sum())), "by_coin": by_coin,
            "account_100_at_2pct": round(100 * acc, 2)}


def main():
    os.makedirs(OUT, exist_ok=True)
    cache = {c: update_cache(c) for c in ml.COINS}
    print("cache", cache, flush=True)
    series = {c: ml.load_cache(c) for c in ml.COINS}
    X, y, rr, t, coin, slp, price, hold = ml.dataset(series)
    valid = np.all(np.isfinite(X), axis=1) & (y >= 0)
    cost_r = ml.FEE_RT / slp
    rr_net = rr - cost_r
    p = np.full(len(y), np.nan)
    months = month_starts(t.min() + MIN_TRAIN_DAYS * 86400, t.max())
    for k, m0 in enumerate(months):
        m1 = months[k + 1] if k + 1 < len(months) else t.max() + 1
        model, n = ml.train(X, y, t, m0)
        f = valid & (t >= m0) & (t < m1)
        if f.any():
            p[f] = model.predict_proba(X[f])[:, 1]
        print(f"fold {datetime.fromtimestamp(m0, timezone.utc):%Y-%m} trained on {n}", flush=True)
    oos = valid & np.isfinite(p)
    ev = np.where(oos, ml.ev_r(np.nan_to_num(p), slp), -9)
    # walk-forward threshold: for each month use only earlier OOS months
    sel = np.zeros(len(y), dtype=bool)
    chosen = []
    for k, m0 in enumerate(months):
        m1 = months[k + 1] if k + 1 < len(months) else t.max() + 1
        past = oos & (t < m0)
        best, best_v = None, 0.0
        for mg in MARGINS:
            s = past & (ev > mg)
            if s.sum() >= 50 and rr_net[s].mean() > best_v:
                best, best_v = mg, rr_net[s].mean()
        chosen.append({"month": datetime.fromtimestamp(m0, timezone.utc).strftime("%Y-%m"), "margin": best})
        if best is not None:
            sel |= oos & (t >= m0) & (t < m1) & (ev > best)
    trades = simulate(sel, t, coin, rr_net, hold, y)
    naive = simulate(oos & (p > 0.5), t, coin, rr_net, hold, y)
    every = simulate(oos, t, coin, rr_net, hold, y)
    # model quality
    from sklearn.metrics import roc_auc_score, brier_score_loss
    auc = float(roc_auc_score(y[oos], p[oos]))
    brier = float(brier_score_loss(y[oos], p[oos]))
    base = float(y[oos].mean())
    buckets = []
    for lo in np.arange(0.0, 1.0, 0.1):
        b = oos & (p >= lo) & (p < lo + 0.1)
        if b.sum() >= 30:
            buckets.append({"p": f"{lo:.1f}-{lo + 0.1:.1f}", "n": int(b.sum()),
                            "predicted": float(p[b].mean()), "actual": float(y[b].mean()),
                            "net_r": float(rr_net[b].mean())})
    # final model + live threshold from ALL out-of-sample history
    best, best_v = None, 0.0
    for mg in MARGINS:
        s = oos & (ev > mg)
        if s.sum() >= 50 and rr_net[s].mean() > best_v:
            best, best_v = mg, rr_net[s].mean()
    halves = {}
    if len(trades):
        mid = np.median(t[trades])
        halves = {"first_half": summary(trades[t[trades] < mid], t, rr_net, y, coin),
                  "second_half": summary(trades[t[trades] >= mid], t, rr_net, y, coin)}
    res = {"generated": int(time.time()), "span": [int(t.min()), int(t.max())],
           "samples_oos": int(oos.sum()), "auc": auc, "brier": brier, "base_rate": base,
           "required_p_typical": float(np.median((1 + cost_r[oos]) / (1 + ml.K_TP / ml.K_SL))),
           "strategy": summary(trades, t, rr_net, y, coin), **halves,
           "naive_p_over_50": summary(naive, t, rr_net, y, coin),
           "every_hour": summary(every, t, rr_net, y, coin),
           "calibration": buckets, "monthly_margin": chosen,
           "live_margin": best, "params": {"horizon_h": ml.HORIZON, "k_sl": ml.K_SL, "k_tp": ml.K_TP,
                                           "fee_rt": ml.FEE_RT, "max_open": MAX_OPEN}}
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(res, f, indent=1)
    with open(os.path.join(OUT, "live_config.json"), "w") as f:
        json.dump({"margin": best, "generated": res["generated"], "auc": auc}, f, indent=1)
    s = res["strategy"]

    def line(name, x):
        if not x.get("n"):
            return f"| {name} | 0 | – | – | – | – | – |"
        return (f"| {name} | {x['n']} | {x['win_rate'] * 100:.0f}% | {x['exp_r']:+.3f}R | {x['net_r']:+.1f}R | "
                f"{x['max_dd_r']:.1f}R | ${x['account_100_at_2pct']:.2f} |")
    md = [
        "# AI predictor: walk-forward results (auto-generated)", "",
        f"{datetime.fromtimestamp(t.min(), timezone.utc):%Y-%m-%d} to {datetime.fromtimestamp(t.max(), timezone.utc):%Y-%m-%d}, "
        f"8 coins, hourly. Model retrained monthly on past data only; threshold chosen from earlier months only. "
        f"Costs {ml.FEE_RT * 100:.1f}% round trip. Trade = TP {ml.K_TP:.0f}xATR / SL {ml.K_SL:.0f}xATR / {ml.HORIZON}h.", "",
        f"**Model quality (out of sample):** AUC {auc:.3f} (0.5 = coin flip), Brier {brier:.4f}, "
        f"base win rate {base * 100:.1f}%, typical win probability needed to beat fees {res['required_p_typical'] * 100:.0f}%.", "",
        "| Approach | Trades | Win rate | Avg R/trade | Net R | Max DD | $100 @ 2% risk |",
        "|---|---|---|---|---|---|---|",
        line("**Cost-aware AI (the strategy)**", s),
        line("…first half of the period", halves.get("first_half", {})),
        line("…second half of the period", halves.get("second_half", {})),
        line("AI, trade whenever p > 50%", res["naive_p_over_50"]),
        line("No AI: take every hour", res["every_hour"]), "",
        "**Calibration (does a predicted 40% win rate really win 40%?):**", "",
        "| Predicted | Samples | Avg predicted | Actual win rate | Avg net R |", "|---|---|---|---|---|",
    ] + [f"| {b['p']} | {b['n']} | {b['predicted'] * 100:.1f}% | {b['actual'] * 100:.1f}% | {b['net_r']:+.3f} |"
         for b in buckets] + ["", f"Live margin (EV must exceed, in R): {best}"]
    with open(os.path.join(OUT, "REPORT.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
