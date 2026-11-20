"""CRT research: backtests 15M / 30M / 1H CRT on Nasdaq futures (NQ=F, costed as NQ and MNQ)
and on BTC-USD, with a chronological 50/25/25 train / validation / out-of-sample split.

Run: python3 research/crt_research.py   (needs network; runs in GitHub Actions)
Writes docs/crt/results.json and docs/crt/results.md
"""
import itertools
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bot"))
import crt  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (research script)", "Accept": "application/json"}
OUT = os.path.join(ROOT, "docs", "crt")


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


def yahoo(symbol, interval, rng):
    d = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={rng}")
    res = d["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    rows = []
    for i, t in enumerate(res["timestamp"]):
        o, h, l, c, v = (q[k][i] for k in ("open", "high", "low", "close", "volume"))
        if None in (o, h, l, c):
            continue
        rows.append({"t": int(t), "o": o, "h": h, "l": l, "c": c, "v": v or 0})
    return rows


def coinbase_5m(product, days, gran=300):
    end = int(time.time()) // gran * gran
    start = end - days * 86400
    rows = {}
    t = start
    while t < end:
        t2 = min(t + 300 * gran, end)
        iso = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = get(f"https://api.exchange.coinbase.com/products/{product}/candles"
                   f"?granularity={gran}&start={iso(t)}&end={iso(t2)}")
        for r in data:
            rows[int(r[0])] = {"t": int(r[0]), "o": r[3], "h": r[2], "l": r[1], "c": r[4], "v": r[5]}
        t = t2
        time.sleep(0.35)
    return [rows[k] for k in sorted(rows)][:-1]  # drop forming candle


# ---------- execution costs (round trip, in price points) ----------
def cost_nq(entry, risk, market):
    # NQ: $20/pt, ~$4.20 commission+fees round trip = 0.21 pt; 1 tick (0.25) slippage on the
    # exit (stops are market orders) and on market entries; limit entries fill at price.
    return 0.21 + 0.25 + (0.25 if market else 0)


def cost_mnq(entry, risk, market):
    # MNQ: $2/pt, ~$1.24 round trip = 0.62 pt; same tick slippage.
    return 0.62 + 0.25 + (0.25 if market else 0)


def cost_btc(entry, risk, market):
    # Spot retail: 0.40% taker / 0.25% maker, 0.05% slippage on market orders.
    fee_in = 0.0045 if market else 0.0025
    return entry * (fee_in + 0.0045)


ENTRIES = ["aggr", "fvg", "eq", "ob"]
STOPS = ["sweep", "rejection", "atr", "ob"]
TARGETS = ["range", "2R", "3R", "4R", "5R", "partial"]
FILTERS = ["pd_level", "session_level", "vwap", "daily_open", "killzone", "high_vol", "low_vol"]


def split_bounds(base):
    t0, t1 = base[0]["t"], base[-1]["t"]
    span = t1 - t0
    return t0 + span * 0.5, t0 + span * 0.75


def part(trades, a, b):
    return [t for t in trades if a <= t.entry_t < b]


def evaluate(base, cfg, cost, ctx, bounds):
    trades = crt.run(base, cfg, cost, ctx)
    tv, vt = bounds
    return {
        "all": crt.stats(trades), "train": crt.stats(part(trades, 0, tv)),
        "val": crt.stats(part(trades, tv, vt)), "test": crt.stats(part(trades, vt, 1e12)),
    }, trades


def key(cfg):
    return f"{cfg.tf}m|{cfg.entry}|{cfg.stop}|{cfg.target}|{'+'.join(cfg.filters) or '-'}|bias{cfg.bias_tf}"


def pick(results, tf, min_n=8, entries=None):
    """Best config on TRAIN expectancy only (validation/test untouched by selection)."""
    best = None
    for k, r in results.items():
        if not k.startswith(f"{tf}m|"):
            continue
        if entries and k.split("|")[1] not in entries:
            continue
        tr = r["train"]
        if tr.get("n", 0) < min_n:
            continue
        if best is None or tr["expectancy_r"] > results[best]["train"]["expectancy_r"]:
            best = k
    return best


def cfg_from(k, **over):
    tf, e, s, t, f, b = k.split("|")
    c = crt.Config(tf=int(tf[:-1]), entry=e, stop=s, target=t,
                   filters=tuple(x for x in f.split("+") if x and x != "-"), bias_tf=int(b[4:]))
    for a, v in over.items():
        setattr(c, a, v)
    return c


def study(name, base, cost, tfs=(15, 30, 60), longs=True, shorts=True):
    print(f"== {name}: {len(base)} base candles", flush=True)
    ctx = crt.Context(base)
    bounds = split_bounds(base)
    results = {}
    for tf, e, s, t in itertools.product(tfs, ENTRIES, STOPS, TARGETS):
        cfg = crt.Config(tf=tf, entry=e, stop=s, target=t, longs=longs, shorts=shorts)
        results[key(cfg)], _ = evaluate(base, cfg, cost, ctx, bounds)
    chosen = {tf: pick(results, tf) for tf in tfs}
    aggr_vs_conf = {tf: {"aggressive": pick(results, tf, entries=["aggr"]),
                         "confirmed": pick(results, tf, entries=["fvg", "eq", "ob"])} for tf in tfs}
    filt, mtf, sessions = {}, {}, {}
    for tf in tfs:
        k = chosen[tf]
        if not k:
            continue
        sessions[tf] = results[k]["all"].get("sessions")
        for f in FILTERS:
            c = cfg_from(k, filters=(f,), longs=longs, shorts=shorts)
            filt[key(c)], _ = evaluate(base, c, cost, ctx, bounds)
        # combine filters that improved train AND validation expectancy without starving trades
        good = []
        for f in FILTERS:
            r = filt[key(cfg_from(k, filters=(f,)))]
            if (r["train"].get("n", 0) >= 5 and r["val"].get("n", 0) >= 3 and
                    r["train"]["expectancy_r"] > results[k]["train"]["expectancy_r"] and
                    r["val"]["expectancy_r"] > results[k]["val"].get("expectancy_r", -9)):
                good.append(f)
        if len(good) > 1:
            c = cfg_from(k, filters=tuple(good), longs=longs, shorts=shorts)
            filt[key(c)], _ = evaluate(base, c, cost, ctx, bounds)
    for label, (htf, ltf) in {"A: 1H bias + 15M exec": (60, 15), "B: 1H bias + 30M exec": (60, 30),
                              "C: 30M bias + 15M exec": (30, 15)}.items():
        if ltf in tfs and chosen.get(ltf):
            c = cfg_from(chosen[ltf], bias_tf=htf, longs=longs, shorts=shorts)
            mtf[label] = {"config": key(c), **evaluate(base, c, cost, ctx, bounds)[0]}
    span = (base[0]["t"], base[-1]["t"])
    return {"name": name, "span": span, "bounds": bounds, "base_candles": len(base),
            "grid": results, "chosen": chosen, "aggr_vs_conf": aggr_vs_conf,
            "filters": filt, "mtf": mtf, "sessions": sessions}


def fmt(x, pct=False, d=2):
    if x is None:
        return "–"
    return f"{x * 100:.0f}%" if pct else f"{x:.{d}f}"


def md_report(studies):
    L = ["# CRT research results (auto-generated)", "",
         f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC. All figures are **R multiples after costs** "
         "(1R = the risk to the stop). Selection uses the TRAIN period only; VAL and TEST are untouched.", ""]
    for st in studies:
        a, b = st["span"]
        L += [f"## {st['name']}",
              f"{datetime.fromtimestamp(a, timezone.utc):%Y-%m-%d} to {datetime.fromtimestamp(b, timezone.utc):%Y-%m-%d}, "
              f"{st['base_candles']} base candles. Split 50/25/25 train/val/test.", "",
              "| Metric | " + " | ".join(f"CRT {tf}M" if tf < 60 else f"CRT {tf // 60}H" for tf in st["chosen"]) + " |",
              "|---|" + "---|" * len(st["chosen"])]
        rows = {"Chosen config (train)": [], "Train n / exp": [], "Val n / exp": [], "TEST n / exp": [],
                "Win rate (all)": [], "Profit factor (all)": [], "Expectancy R (all)": [],
                "Avg winner R": [], "Max DD R (all)": [], "Max losing streak": [], "Trades/day": [],
                "Avg stop (pts)": [], "Best session (n≥3)": [], "Long exp / Short exp": []}
        for tf, k in st["chosen"].items():
            if not k:
                for v in rows.values():
                    v.append("not enough trades")
                continue
            r = st["grid"][k]
            al = r["all"]
            sess = {s: v for s, v in (al.get("sessions") or {}).items() if v["n"] >= 3}
            best = max(sess, key=lambda s: sess[s]["exp"]) if sess else "–"
            rows["Chosen config (train)"].append(" ".join(k.split("|")[1:4]))
            for lab, sp in (("Train n / exp", "train"), ("Val n / exp", "val"), ("TEST n / exp", "test")):
                x = r[sp]
                rows[lab].append(f"{x.get('n', 0)} / {fmt(x.get('expectancy_r'))}")
            rows["Win rate (all)"].append(fmt(al.get("win_rate"), True))
            rows["Profit factor (all)"].append(fmt(al.get("profit_factor")))
            rows["Expectancy R (all)"].append(fmt(al.get("expectancy_r")))
            rows["Avg winner R"].append(fmt(al.get("avg_rr_realized_win")))
            rows["Max DD R (all)"].append(fmt(al.get("max_dd_r")))
            rows["Max losing streak"].append(str(al.get("max_consec_losses", "–")))
            rows["Trades/day"].append(fmt(al.get("trades_per_day")))
            rows["Avg stop (pts)"].append(fmt(al.get("avg_risk_pts")))
            rows["Best session (n≥3)"].append(f"{best} ({fmt(sess[best]['exp'])})" if sess else "–")
            rows["Long exp / Short exp"].append(f"{fmt(al['long']['exp'])} / {fmt(al['short']['exp'])}")
        for lab, v in rows.items():
            L.append(f"| {lab} | " + " | ".join(v) + " |")
        L += ["", "**Aggressive vs confirmed (best of each on train → val / test expectancy):**", ""]
        for tf, d in st["aggr_vs_conf"].items():
            parts = []
            for lab, k in d.items():
                if k:
                    r = st["grid"][k]
                    parts.append(f"{lab} `{' '.join(k.split('|')[1:4])}` train {fmt(r['train'].get('expectancy_r'))} "
                                 f"(n {r['train'].get('n')}), val {fmt(r['val'].get('expectancy_r'))} (n {r['val'].get('n', 0)}), "
                                 f"test {fmt(r['test'].get('expectancy_r'))} (n {r['test'].get('n', 0)})")
                else:
                    parts.append(f"{lab}: too few trades")
            L.append(f"- {tf}M: " + "; ".join(parts))
        L += ["", "**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**", ""]
        for k, r in st["filters"].items():
            L.append(f"- `{k}`: {r['all'].get('n', 0)} / {fmt(r['all'].get('expectancy_r'))}, test {fmt(r['test'].get('expectancy_r'))} (n {r['test'].get('n', 0)})")
        L += ["", "**Multi-timeframe:**", ""]
        for lab, r in st["mtf"].items():
            L.append(f"- {lab} `{r['config']}`: all {r['all'].get('n', 0)} / {fmt(r['all'].get('expectancy_r'))}, "
                     f"test {fmt(r['test'].get('expectancy_r'))} (n {r['test'].get('n', 0)})")
        L.append("")
    return "\n".join(L)


def slim(st):
    """Drop per-config session detail from the grid to keep the JSON small."""
    g = {}
    for k, r in st["grid"].items():
        g[k] = {sp: {m: v for m, v in x.items() if m not in ("sessions",)} for sp, x in r.items()}
    return {**st, "grid": g}


def main():
    os.makedirs(OUT, exist_ok=True)
    studies, errors = [], {}
    try:
        nq5 = yahoo("NQ=F", "5m", "60d")
        studies.append(study("NQ futures, 5m data (MNQ costs)", nq5, cost_mnq))
        studies.append(study("NQ futures, 5m data (NQ costs)", nq5, cost_nq))
    except Exception as e:  # noqa: BLE001
        errors["nq5"] = str(e)
    try:
        nq60 = yahoo("NQ=F", "60m", "730d")
        studies.append(study("NQ futures, 1H CRT on 2 years of hourly data (MNQ costs)", nq60, cost_mnq, tfs=(60,)))
    except Exception as e:  # noqa: BLE001
        errors["nq60"] = str(e)
    try:
        btc = coinbase_5m("BTC-USD", 60)
        studies.append(study("BTC-USD spot, 5m data, retail fees, both directions", btc, cost_btc,
                             tfs=(15, 30, 60, 240)))
        studies.append(study("BTC-USD spot, 5m data, retail fees, LONG ONLY (what the $100 account can do)",
                             btc, cost_btc, tfs=(15, 30, 60, 240), shorts=False))
    except Exception as e:  # noqa: BLE001
        errors["btc"] = str(e)
    try:
        btc1h = coinbase_5m("BTC-USD", 730, gran=3600)
        studies.append(study("BTC-USD spot, 2 years of hourly data, LONG ONLY, 1H and 4H CRT",
                             btc1h, cost_btc, tfs=(60, 240), shorts=False))
    except Exception as e:  # noqa: BLE001
        errors["btc1h"] = str(e)
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump({"generated": int(time.time()), "errors": errors,
                   "studies": [slim(s) for s in studies]}, f, separators=(",", ":"))
    with open(os.path.join(OUT, "results.md"), "w") as f:
        f.write(md_report(studies) + ("\n\nData errors: " + json.dumps(errors) if errors else ""))
    print("errors:", errors)


if __name__ == "__main__":
    main()
