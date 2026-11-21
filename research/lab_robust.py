"""Robustness check for the lab's best ideas: run many parameter variations through the same engine.
If most neighbours of a winning setting also make money, the idea is real; if only one does, luck.
Writes docs/lab/robust.json.
"""
import itertools
import json
import math
import multiprocessing as mp
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bot"))
sys.path.insert(0, os.path.join(ROOT, "research"))
import lab  # noqa: E402

BASKETS = {"BTC": ["BTC"], "BTC+ETH": ["BTC", "ETH"], "BTC+ETH+SOL+XRP": ["BTC", "ETH", "SOL", "XRP"]}


def make(kind, coins, look, target):
    from strategies import closes, done, sma, stdev

    def vol_trend(md, memo):
        w = {}
        avail = [a for a in coins if a in md]
        for a in avail:
            c = closes(done(md[a]["1d"]))
            if len(c) <= max(look, 21) or c[-1] / c[-1 - look] - 1 <= 0:
                continue
            rets = [math.log(b / a_) for a_, b in zip(c[-21:-1], c[-20:])]
            vol = stdev(rets) * math.sqrt(365)
            w[a] = (1 / len(coins)) * min(1.0, target / max(vol, 1e-9))
        return w

    def sma_trend(md, memo):
        w = {}
        for a in [a for a in coins if a in md]:
            c = closes(done(md[a]["1d"]))
            if len(c) > look and c[-1] > sma(c, look):
                w[a] = 1 / len(coins)
        return w
    return vol_trend if kind == "vol" else sma_trend


def run(p):
    import engine
    kind, bname, look, target = p
    sid = f"{kind}|{bname}|{look}|{target}"
    fn = make(kind, BASKETS[bname], look, target)
    engine.STRATEGIES = [(sid, sid, fn, "", BASKETS[bname])]
    data = lab.load()
    mkt = lab.Market(data)
    t = data["BTC"][0]["t"] + lab.WARM_DAYS * 86400
    t -= t % 3600
    end = data["BTC"][-1]["t"] + 3600
    state = {"started": None, "accounts": {}, "runs": 0, "config": {}}
    curve = []
    while t <= end:
        md = mkt.at(t)
        if "BTC" in md:
            engine.step(state, md, t)
            a = state["accounts"][sid]
            curve.append((t, a["equity"], 0))
            a["history"] = a["history"][-5:]
            state["btc_history"] = state["btc_history"][-5:]
            if a.get("journal"):
                a["journal"]["pending"] = a["journal"]["pending"][-30:]
        t += 3600
    m = lab.metrics(curve, None, {})
    return {"kind": kind, "basket": bname, "look": look, "target": target, "cagr": m["cagr"],
            "max_dd": m["max_dd"], "sharpe": m["sharpe"], "first_half": m["first_half"],
            "second_half": m["second_half"], "win30": m["rolling"]["30d"]["p_positive"],
            "trades": len(state["accounts"][sid]["trades"])}


def main():
    grid = [("vol", b, L, T) for b, L, T in itertools.product(BASKETS, (20, 30, 60, 90), (0.3, 0.5, 0.8))]
    grid += [("sma", b, L, None) for b, L in itertools.product(BASKETS, (20, 50, 100))]
    t0 = time.time()
    with mp.Pool(os.cpu_count() or 2) as pool:
        res = pool.map(run, grid)
    for r in sorted(res, key=lambda r: -r["cagr"]):
        print(f"{r['kind']:3} {r['basket']:16} look {r['look']:3} tgt {r['target']}  CAGR {r['cagr'] * 100:+6.1f}%  "
              f"DD {r['max_dd'] * 100:4.0f}%  halves {r['first_half'] * 100:+5.0f}/{r['second_half'] * 100:+5.0f}%")
    summ = {}
    for kind in ("vol", "sma"):
        rs = [r for r in res if r["kind"] == kind]
        summ[kind] = {"n": len(rs), "positive": sum(r["cagr"] > 0 for r in rs),
                      "both_halves_positive": sum(r["first_half"] > 0 and r["second_half"] > 0 for r in rs),
                      "median_cagr": sorted(r["cagr"] for r in rs)[len(rs) // 2]}
    print(summ, "runtime", round(time.time() - t0))
    os.makedirs(lab.OUT, exist_ok=True)
    with open(os.path.join(lab.OUT, "robust.json"), "w") as f:
        json.dump({"generated": int(time.time()), "summary": summ, "runs": res}, f, indent=1)


if __name__ == "__main__":
    main()
