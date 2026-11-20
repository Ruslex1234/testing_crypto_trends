"""Forward test of the research-selected NQ CRT model on live Nasdaq futures data.

Every hourly run pulls the last 5 days of NQ=F 5 minute candles (Yahoo), runs the exact backtest
rules, and records trades that ENTERED after the forward test started. This is genuine
out-of-sample evidence: none of it existed when the model was chosen.
Results are in R (after MNQ costs) and as a $100 account risking 2% per trade.
"""
import json
import urllib.request

import crt

FWD_CFG = crt.Config(tf=30, entry="aggr", stop="sweep", target="2R",
                     name="NQ 30M CRT, aggressive, stop beyond sweep, 2R")
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
    fw = state.setdefault("crt_forward", {"start": now, "trades": {}, "config": FWD_CFG.name})
    try:
        base = _nq_5m()
        for t in crt.run(base, FWD_CFG, cost_mnq):
            if t.entry_t >= fw["start"]:
                fw["trades"][str(t.entry_t)] = {
                    "entry_t": t.entry_t, "exit_t": t.exit_t, "side": t.side, "entry": t.entry,
                    "stop": round(t.stop, 2), "target": round(t.target, 2), "exit": t.exit,
                    "r": round(t.r_net, 3), "risk_pts": round(t.risk_pts, 2),
                    "session": t.session, "reason": t.reason}
        tr = sorted(fw["trades"].values(), key=lambda x: x["entry_t"])
        eq = 100.0
        for x in tr:
            eq *= 1 + RISK_PCT * x["r"]
        fw.update(n=len(tr), net_r=round(sum(x["r"] for x in tr), 3),
                  wins=sum(1 for x in tr if x["r"] > 0), equity=round(eq, 2),
                  last_price=base[-1]["c"], last_t=base[-1]["t"], error=None)
    except Exception as e:  # noqa: BLE001  (never break the trading run)
        fw["error"] = f"{type(e).__name__}: {e}"
