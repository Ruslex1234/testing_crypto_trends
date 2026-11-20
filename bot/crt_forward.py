"""Forward test of the research-selected NQ CRT model on live Nasdaq futures data.

Every hourly run pulls the last 5 days of NQ=F 5 minute candles (Yahoo), runs the exact backtest
rules, and records trades that ENTERED after the forward test started. This is genuine
out-of-sample evidence: none of it existed when the model was chosen.
Results are in R (after MNQ costs) and as a $100 account risking 2% per trade.
"""
import json
import urllib.request

import crt

MODELS = [
    # survived train, validation AND test with the largest sample (379 trades)
    crt.Config(tf=30, entry="aggr", stop="sweep", target="2R",
               name="30M aggressive, stop beyond sweep, 2R"),
    # pick of the pre-registered max(min(train, val)) rule (46 trades)
    crt.Config(tf=30, entry="eq", stop="ob", target="3R",
               name="30M limit at 50%, stop beyond order block, 3R"),
]
RISK_PCT = 0.02


def cost_mnq(entry, risk, market):
    return 0.62 + 0.25 + (0.25 if market else 0)


def _nq_5m():
    req = urllib.request.Request(
        "https://query1.finance.yahoo.com/v8/finance/chart/NQ=F?interval=5m&range=5d",
        headers={"User-Agent": "Mozilla/5.0 (paper-trader)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        res = json.loads(r.read().decode())["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    rows = []
    for i, t in enumerate(res["timestamp"]):
        o, h, l, c = (q[k][i] for k in ("open", "high", "low", "close"))
        if None not in (o, h, l, c):
            rows.append({"t": int(t), "o": o, "h": h, "l": l, "c": c, "v": q["volume"][i] or 0})
    return rows[:-1]  # drop the forming candle


def update(state, now):
    fw = state.setdefault("crt_forward", {"start": now})
    fw.pop("trades", None)  # older single-model layout
    models = fw.setdefault("models", {})
    try:
        base = _nq_5m()
        fw.update(last_price=base[-1]["c"], last_t=base[-1]["t"], error=None)
        for cfg in MODELS:
            m = models.setdefault(cfg.name, {"trades": {}})
            for t in crt.run(base, cfg, cost_mnq):
                if t.entry_t >= fw["start"]:
                    m["trades"][str(t.entry_t)] = {
                        "entry_t": t.entry_t, "exit_t": t.exit_t, "side": t.side,
                        "entry": t.entry, "stop": round(t.stop, 2), "target": round(t.target, 2),
                        "exit": t.exit, "r": round(t.r_net, 3), "risk_pts": round(t.risk_pts, 2),
                        "session": t.session, "reason": t.reason}
            tr = sorted(m["trades"].values(), key=lambda x: x["entry_t"])
            eq = 100.0
            for x in tr:
                eq *= 1 + RISK_PCT * x["r"]
            m.update(n=len(tr), net_r=round(sum(x["r"] for x in tr), 3),
                     wins=sum(1 for x in tr if x["r"] > 0), equity=round(eq, 2))
    except Exception as e:  # noqa: BLE001  (never break the trading run)
        fw["error"] = f"{type(e).__name__}: {e}"
