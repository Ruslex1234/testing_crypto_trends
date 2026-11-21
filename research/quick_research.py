"""Walk-forward test of 1-hour long/short quick trades on the last DAYS days of 15m candles.

Each day the models are retrained using only decisions whose outcome was known before that day:
  * "last 14 days" window (the idea being tested) vs "all history so far"
The EV margin for each day is chosen only from earlier out-of-sample days.
Per hour: at most MAX_TRADES trades (best EV first), one side per coin, exits within the hour.
Writes docs/quick/results.json, REPORT.md, live_config.json.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bot"))
import quick as Q  # noqa: E402

OUT = os.path.join(ROOT, "docs", "quick")
DAYS = 75
WARM_DAYS = 16          # first days only train
MARGINS = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3]
MAX_TRADES = 3


def walk(D, window):
    days = np.unique((D["t"] // 86400))
    start = days.min() + WARM_DAYS
    ev = {1: np.full(len(D["t"]), np.nan), -1: np.full(len(D["t"]), np.nan)}
    prob = {1: np.full((len(D["t"]), 3), np.nan), -1: np.full((len(D["t"]), 3), np.nan)}
    for d in days[days >= start]:
        until = int(d * 86400)
        models, n = Q.fit(D, until, window)
        m = (D["t"] // 86400) == d
        if not m.any() or n < 500:
            continue
        out = Q.predict_ev(models, D["X"][m], D["slp"][m])
        for side in (1, -1):
            ev[side][m], prob[side][m] = out[side]
    return ev, prob


def trades_for(D, ev, mask):
    """Pick per hour up to MAX_TRADES best (coin, side) with EV above per-row threshold mask."""
    best_side = np.where(np.nan_to_num(ev[1], nan=-9) >= np.nan_to_num(ev[-1], nan=-9), 1, -1)
    best_ev = np.where(best_side == 1, ev[1], ev[-1])
    r_net = np.where(best_side == 1, D["rl"], D["rs"]) - Q.FEE_RT / D["slp"]
    won = np.where(best_side == 1, D["yl"], D["ys"]) == 0
    ok = mask(best_ev) & np.isfinite(r_net) & (D["yl"] >= 0)
    picked = []
    for hour in np.unique(D["t"][ok]):
        idx = np.flatnonzero(ok & (D["t"] == hour))
        picked += list(idx[np.argsort(-best_ev[idx])][:MAX_TRADES])
    picked = np.array(sorted(picked, key=lambda i: D["t"][i]), dtype=int)
    return picked, r_net, won, best_side


def summarize(D, picked, r_net, won, side):
    if len(picked) == 0:
        return {"n": 0}
    r = r_net[picked]
    eq = np.cumsum(r)
    acct = 100.0
    for x in r:
        acct *= 1 + 0.01 * x  # $100 account risking 1% per quick trade
    span = max(1.0, (D["t"][picked].max() - D["t"][picked].min()) / 86400)
    return {"n": int(len(r)), "win_rate": float(won[picked].mean()), "exp_r": float(r.mean()),
            "net_r": float(r.sum()), "max_dd_r": float(np.max(np.maximum.accumulate(eq) - eq)),
            "per_day": len(r) / span, "longs": int((side[picked] == 1).sum()),
            "shorts": int((side[picked] == -1).sum()),
            "long_exp": float(r[side[picked] == 1].mean()) if (side[picked] == 1).any() else None,
            "short_exp": float(r[side[picked] == -1].mean()) if (side[picked] == -1).any() else None,
            "account_100_at_1pct": round(acct, 2)}


def evaluate(D, ev):
    """Walk-forward margin: each day uses the margin that worked best on earlier OOS days."""
    have = np.isfinite(ev[1])
    days = np.unique(D["t"][have] // 86400)
    sel = np.zeros(len(D["t"]), dtype=bool)
    margins = []
    for d in days:
        past = have & (D["t"] // 86400 < d)
        best, bv = None, 0.0
        for mg in MARGINS:
            p, r, _, _ = trades_for(D, ev, lambda e, mg=mg: past & (e > mg))
            if len(p) >= 100 and r[p].mean() > bv:
                best, bv = mg, r[p].mean()
        margins.append(best)
        if best is not None:
            today = have & (D["t"] // 86400 == d)
            p, _, _, _ = trades_for(D, ev, lambda e, b=best, td=today: td & (e > b))
            sel[p] = True
    picked, r_net, won, side = trades_for(D, ev, lambda e: sel)
    all_hours, _, _, _ = trades_for(D, ev, lambda e: have)  # no filter: always trade top 3
    final, fv = None, 0.0
    for mg in MARGINS:
        p, r, _, _ = trades_for(D, ev, lambda e, mg=mg: have & (e > mg))
        if len(p) >= 100 and r[p].mean() > fv:
            final, fv = mg, r[p].mean()
    mid = np.median(D["t"][picked]) if len(picked) else 0
    return {"strategy": summarize(D, picked, r_net, won, side),
            "first_half": summarize(D, picked[D["t"][picked] < mid], r_net, won, side),
            "second_half": summarize(D, picked[D["t"][picked] >= mid], r_net, won, side),
            "no_filter_top3_every_hour": summarize(D, all_hours, r_net, won, side),
            "daily_margins": margins, "final_margin": final}


def main():
    os.makedirs(OUT, exist_ok=True)
    series = {}
    for c in Q.COINS:
        series[c] = Q.fetch_15m(c, DAYS)
        print(c, len(series[c]), flush=True)
    D = Q.dataset(series)
    res = {"generated": int(time.time()), "span": [int(D["t"].min()), int(D["t"].max())],
           "decisions": int(len(D["t"])),
           "base_rates": {"long_tp": float((D["yl"] == 0).mean()), "short_tp": float((D["ys"] == 0).mean())},
           "params": {"bar_min": Q.BAR // 60, "hold_h": Q.HOLD * Q.BAR / 3600, "k_sl": Q.K_SL, "rr": Q.RR,
                      "fee_rt": Q.FEE_RT, "max_trades_per_hour": MAX_TRADES}}
    for name, window in (("last_14_days", Q.TRAIN_DAYS), ("all_history", None)):
        ev, _ = walk(D, window)
        res[name] = evaluate(D, ev)
        print(name, res[name]["strategy"], flush=True)
    # choose the live window by which was better out of sample (both are walk-forward results)
    a, b = res["last_14_days"]["strategy"], res["all_history"]["strategy"]
    pick = "last_14_days" if a.get("exp_r", -9) * a.get("n", 0) >= b.get("exp_r", -9) * b.get("n", 0) else "all_history"
    live = {"window_days": Q.TRAIN_DAYS if pick == "last_14_days" else None, "window": pick,
            "margin": res[pick]["final_margin"] if res[pick]["strategy"].get("n", 0) and
            res[pick]["strategy"]["exp_r"] > 0 else None, "generated": res["generated"]}
    res["live"] = live
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(res, f, indent=1)
    with open(os.path.join(OUT, "live_config.json"), "w") as f:
        json.dump(live, f, indent=1)

    def row(n, x):
        if not x.get("n"):
            return f"| {n} | 0 | – | – | – | – | – | – |"
        return (f"| {n} | {x['n']} ({x['per_day']:.1f}/day) | {x['win_rate'] * 100:.0f}% | {x['exp_r']:+.3f}R | "
                f"{x['net_r']:+.1f}R | {x['max_dd_r']:.1f}R | {x['longs']}L / {x['shorts']}S | ${x['account_100_at_1pct']:.2f} |")
    md = ["# Quick 1-hour long/short trades: walk-forward results (auto-generated)", "",
          f"{datetime.fromtimestamp(D['t'].min(), timezone.utc):%Y-%m-%d} to "
          f"{datetime.fromtimestamp(D['t'].max(), timezone.utc):%Y-%m-%d}, 8 coins, decisions every hour. "
          f"Stop {Q.K_SL}x ATR(15m), take-profit {Q.RR}x the stop, exit after 1h. Costs {Q.FEE_RT * 100:.2f}% "
          "round trip (perp-style). Retrained daily on past data only; margin chosen from earlier days only.", "",
          "| Approach | Trades | Win rate | Avg per trade | Net | Max DD | Long/Short | $100 @ 1% risk |",
          "|---|---|---|---|---|---|---|---|"]
    for name in ("last_14_days", "all_history"):
        r = res[name]
        md += [row(f"**Train on {name.replace('_', ' ')}**", r["strategy"]),
               row("…first half", r["first_half"]), row("…second half", r["second_half"]),
               row("…no filter, top 3 every hour", r["no_filter_top3_every_hour"])]
    md += ["", f"Live: window = {pick}, margin = {live['margin']} "
           f"({'trading' if live['margin'] is not None else 'NOT trading: no edge after costs'})"]
    with open(os.path.join(OUT, "REPORT.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
