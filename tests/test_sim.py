"""Simulate 45 days of hourly runs on synthetic random-walk prices. Run: python tests/test_sim.py"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bot"))
import engine  # noqa: E402
from market import ASSETS, resample  # noqa: E402

random.seed(7)
H = 3600
START = 1_700_000_000 - 1_700_000_000 % 86400
TOTAL_H = 24 * 345
series = {}
for i, a in enumerate(ASSETS):
    p, rows = 100.0 * (i + 1), []
    for k in range(TOTAL_H):
        o = p
        p *= math.exp(random.gauss(0.00005, 0.008 + 0.002 * i))
        rows.append({"t": START + k * H, "o": o, "h": max(o, p) * 1.002,
                     "l": min(o, p) * 0.998, "c": p, "v": 1})
    series[a] = rows


def md_at(k):
    md = {}
    for a, rows in series.items():
        h = rows[max(0, k - 299):k + 1]
        md[a] = {"1h": h, "6h": resample(h, 6), "1d": resample(rows[:k + 1], 24)[-300:],
                 "price": rows[k]["c"]}
    return md


state = {"started": None, "accounts": {}, "runs": 0, "config": {}}
first = 24 * 300
for k in range(first, TOTAL_H):
    engine.step(state, md_at(k), START + k * H)

ok = True
for acct in state["accounts"].values():
    assert acct["cash"] >= -1e-9, acct["id"]
    assert all(q >= 0 for q in acct["holdings"].values()), acct["id"]
    if acct["error"]:
        ok = False
    print(f"{acct['name']:<42} ${acct['equity']:8.2f} trades={len(acct['trades']):4d} "
          f"fees=${acct['fees_paid']:.2f} err={acct['error']}")
assert ok
print("runs:", state["runs"], "OK")

if os.environ.get("SIM_OUT"):
    import json
    state["data_sources"] = ["synthetic"]
    with open(os.environ["SIM_OUT"], "w") as f:
        json.dump(state, f)
