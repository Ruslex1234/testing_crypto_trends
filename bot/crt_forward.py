"""Multi-market forward test of the research-selected CRT models.

Every hourly run pulls the last 5 days of 5 minute candles for each market (Yahoo), runs the exact
backtest rules from crt.py, and records trades that ENTERED after that model/market pair started
being tracked. None of it existed when the models were chosen, so it is genuine out-of-sample
evidence. Running the same rules on 13 markets gives in one month the sample size one market
would need a year for.

Costs are modelled per market for the cheapest realistic retail vehicle (micro futures, FX
spread, low-fee crypto perpetuals). Results in R after costs, and as a $100 account risking 2%.
"""
import json
import time
import urllib.request

import crt

MODELS = [
    # survived train, validation AND test on NQ with the largest sample (379 trades)
    crt.Config(tf=30, entry="aggr", stop="sweep", target="2R",
               name="30M aggressive, stop beyond sweep, 2R"),
    # same, New York hours only: pre-registered on 2026-11-20 after research showed Asia losing
    crt.Config(tf=30, entry="aggr", stop="sweep", target="2R", filters=("ny_hours",),
               name="30M aggressive, NY hours only, 2R"),
    # pick of the pre-registered max(min(train, val)) rule (46 trades)
    crt.Config(tf=30, entry="eq", stop="ob", target="3R",
               name="30M limit at 50%, stop beyond order block, 3R"),
]
RISK_PCT = 0.02

# symbol: (label, commission/spread in price units round trip, 1 tick, % of price round trip)
MARKETS = {
    "NQ=F": ("Nasdaq (MNQ)", 0.62, 0.25, 0),        # $2/pt, $1.24 RT
    "ES=F": ("S&P 500 (MES)", 0.248, 0.25, 0),      # $5/pt
    "YM=F": ("Dow (MYM)", 2.48, 1.0, 0),            # $0.50/pt
    "RTY=F": ("Russell (M2K)", 0.248, 0.1, 0),      # $5/pt
    "GC=F": ("Gold (MGC)", 0.124, 0.1, 0),          # $10/pt
    "CL=F": ("Crude oil (MCL)", 0.0124, 0.01, 0),   # $100/pt
    "EURUSD=X": ("EUR/USD", 0.00008, 0.00002, 0),   # ~0.8 pip spread
    "GBPUSD=X": ("GBP/USD", 0.00012, 0.00002, 0),
    "USDJPY=X": ("USD/JPY", 0.010, 0.002, 0),
    "AUDUSD=X": ("AUD/USD", 0.0001, 0.00002, 0),
    "BTC-USD": ("Bitcoin (perp fees)", 0, 0, 0.0014),  # 0.05% taker x2 + slippage
    "ETH-USD": ("Ether (perp fees)", 0, 0, 0.0014),
    "SOL-USD": ("Solana (perp fees)", 0, 0, 0.0020),
}


def make_cost(comm, tick, pct):
    def cost(entry, risk, market):
        return comm + tick * (1 + (1 if market else 0)) + entry * pct
    return cost


def yahoo_5m(symbol):
    req = urllib.request.Request(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=5d",
        headers={"User-Agent": "Mozilla/5.0 (paper-trader)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        res = json.loads(r.read().decode())["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    rows = []
    for i, t in enumerate(res.get("timestamp") or []):
        o, h, l, c = (q[k][i] for k in ("open", "high", "low", "close"))
        if None not in (o, h, l, c):
            rows.append({"t": int(t), "o": o, "h": h, "l": l, "c": c, "v": q["volume"][i] or 0})
    return rows[:-1]  # drop the forming candle


def _migrate(fw):
    """Older layout kept NQ trades under fw['models'][name]['trades']; move them."""
    old = fw.pop("models", None)
    if not old:
        return
    for name, m in old.items():
        for k, t in (m.get("trades") or {}).items():
            fw["trades"][f"{name}|NQ=F|{k}"] = {**t, "model": name, "market": "NQ=F"}
        fw["starts"].setdefault(f"{name}|NQ=F", fw.get("start"))


def summarize(trades):
    tr = sorted(trades, key=lambda x: x["entry_t"])
    eq = 100.0
    for x in tr:
        eq *= 1 + RISK_PCT * x["r"]
    n = len(tr)
    net = sum(x["r"] for x in tr)
    return {"n": n, "wins": sum(1 for x in tr if x["r"] > 0), "net_r": round(net, 3),
            "exp_r": round(net / n, 3) if n else None, "equity": round(eq, 2)}


def update(state, now):
    fw = state.setdefault("crt_forward", {})
    fw.setdefault("start", now)
    fw.setdefault("trades", {})
    fw.setdefault("starts", {})
    _migrate(fw)
    errors, last = {}, {}
    for sym, (label, comm, tick, pct) in MARKETS.items():
        try:
            base = yahoo_5m(sym)
            if len(base) < 200:
                raise RuntimeError(f"only {len(base)} candles")
            last[sym] = {"price": base[-1]["c"], "t": base[-1]["t"]}
            cost = make_cost(comm, tick, pct)
            for cfg in MODELS:
                key = f"{cfg.name}|{sym}"
                start = fw["starts"].setdefault(key, now)
                for t in crt.run(base, cfg, cost):
                    if t.entry_t >= start:
                        fw["trades"][f"{key}|{t.entry_t}"] = {
                            "model": cfg.name, "market": sym, "entry_t": t.entry_t,
                            "exit_t": t.exit_t, "side": t.side, "entry": t.entry,
                            "stop": t.stop, "target": t.target, "exit": t.exit,
                            "r": round(t.r_net, 3), "risk": t.risk_pts,
                            "session": t.session, "reason": t.reason}
        except Exception as e:  # noqa: BLE001  (one market failing never breaks the run)
            errors[sym] = f"{type(e).__name__}: {e}"[:160]
        time.sleep(0.4)
    trades = list(fw["trades"].values())
    fw["by_model"] = {m.name: summarize([t for t in trades if t["model"] == m.name]) for m in MODELS}
    fw["by_market"] = {sym: {"label": MARKETS[sym][0], **summarize([t for t in trades if t["market"] == sym]),
                             "models": {m.name: summarize([t for t in trades if t["market"] == sym
                                                           and t["model"] == m.name]) for m in MODELS}}
                       for sym in MARKETS}
    fw.update(errors=errors, last=last, updated=now, models_order=[m.name for m in MODELS])
    fw.pop("error", None)
