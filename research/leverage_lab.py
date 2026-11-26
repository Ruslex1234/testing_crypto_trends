"""Leverage Lab: what if each lab strategy were run with 1x..20x leverage (perp style)?
Uses the 8 year daily equity curves in docs/lab/results.json. Leveraged daily return =
L * strategy return - funding/borrow on the extra exposure (about 11%/yr). An account that
loses 90% or more in a day is liquidated (stays at 0). Answers:
  * how often does $100 become $200+ (or $20 or less) within 7 / 30 days?
  * in an arena of all strategies, how often does at least one double in a week?
  * does last week's winner keep winning next week (skill) or not (luck)?
  * what happens over the full 8 years (ruin)?
Writes docs/lab/leverage.json and prints a summary."""
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVS = [1, 2, 3, 5, 10, 20]
FUND = 0.11 / 365


def main():
    d = json.load(open(os.path.join(ROOT, "docs", "lab", "results.json")))
    S = [s for s in d["strategies"] if len(s["curve"]) > 400]
    # align on common days
    days = sorted(set.intersection(*[set(int(t) // 86400 for t, _ in s["curve"]) for s in S]))
    R = {}
    for s in S:
        m = {int(t) // 86400: e for t, e in s["curve"]}
        e = np.array([m[x] for x in days])
        R[s["name"]] = e[1:] / e[:-1] - 1
    names = list(R)
    n = len(days) - 1
    out = {"days": n, "strategies": {}, "arena": {}}
    for L in LEVS:
        rows = {}
        for nm in names:
            r = np.maximum(L * R[nm] - (L - 1) * FUND * (np.abs(R[nm]) > 0), -1.0)
            r = np.where(r <= -0.9, -1.0, r)
            lg = np.log(np.maximum(1 + r, 1e-12))
            cs = np.insert(np.cumsum(lg), 0, 0)
            res = {}
            for w in (7, 30):
                win = np.exp(cs[w:] - cs[:-w])
                # liquidation inside the window: any day at -100% zeroes it
                dead = np.convolve((r <= -0.999).astype(float), np.ones(w), "valid") > 0
                win = np.where(dead, 0.0, win)
                res[f"{w}d"] = {"p_double": float((win >= 2).mean()), "p_20_or_less": float((win <= 0.2).mean()),
                                "p_up": float((win > 1).mean()), "median": float(np.median(win))}
            eq = np.exp(cs)
            dead_at = np.where(r <= -0.999)[0]
            final = 0.0 if len(dead_at) else float(eq[-1])
            res["8y_final_of_100"] = round(100 * final, 2)
            res["liquidated_day"] = int(dead_at[0]) if len(dead_at) else None
            res["best_week"] = float(np.max(np.exp(cs[7:] - cs[:-7])))
            rows[nm] = res
        out["strategies"][str(L)] = rows
        # arena: per non-overlapping week, did any account double? did any hit <=$20?
        W = np.array([[np.exp(np.sum(np.log(np.maximum(1 + np.maximum(L * R[nm][i:i + 7] - (L - 1) * FUND, -1), 1e-12))))
                       for nm in names] for i in range(0, n - 7, 7)])
        top = W.argmax(1)
        nxt_rank = []
        for k in range(len(W) - 1):  # where does last week's winner rank next week? 0 best .. 1 worst
            order = np.argsort(-W[k + 1])
            nxt_rank.append(float(np.where(order == top[k])[0][0]) / (len(names) - 1))
        out["arena"][str(L)] = {"weeks": len(W), "p_any_double": float((W.max(1) >= 2).mean()),
                                "p_any_20_or_less": float((W.min(1) <= 0.2).mean()),
                                "winner_next_week_rank": float(np.mean(nxt_rank)),
                                "winner_next_week_avg": float(np.mean([W[k + 1, top[k]] for k in range(len(W) - 1)])),
                                "everyone_next_week_avg": float(np.mean(W[1:]))}
    json.dump(out, open(os.path.join(ROOT, "docs", "lab", "leverage.json"), "w"), indent=1)
    print("days", n, "strategies", len(names))
    for L in LEVS:
        a = out["arena"][str(L)]
        print(f"\n=== {L}x  arena weeks {a['weeks']}: any account doubles {a['p_any_double']*100:.1f}% of weeks, "
              f"any at $20 or less {a['p_any_20_or_less']*100:.1f}%; last week's winner ranks "
              f"{a['winner_next_week_rank']:.2f} next week (0.50 = pure luck), its next week x{a['winner_next_week_avg']:.3f} "
              f"vs average x{a['everyone_next_week_avg']:.3f}")
        for nm, v in sorted(out["strategies"][str(L)].items(), key=lambda x: -x[1]["8y_final_of_100"]):
            print(f"  {nm[:38]:38} 8y $100->${v['8y_final_of_100']:>14,.0f}  week: double {v['7d']['p_double']*100:4.1f}% "
                  f"<=$20 {v['7d']['p_20_or_less']*100:4.1f}%  month: double {v['30d']['p_double']*100:4.1f}% "
                  f"<=$20 {v['30d']['p_20_or_less']*100:4.1f}%  best week x{v['best_week']:.2f}"
                  + (f"  LIQUIDATED day {v['liquidated_day']}" if v['liquidated_day'] is not None else ""))


if __name__ == "__main__":
    main()
