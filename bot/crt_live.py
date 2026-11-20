"""Live CRT paper account on BTC (long only: spot, $100, no shorting).

Uses the exact rules in crt.py. Each hourly run replays the 5 minute candles completed since the
previous run, in order, as if resting orders were sitting at the exchange:
  pending limit entry -> fills when price trades through it (at the better of limit/open)
  open position       -> stop (market on touch, fills at stop or worse on a gap),
                         target(s) (limit), or time exit after MAX_HOLD CRT candles.
Position size: risk RISK_PCT of equity to the stop, capped at 100% of equity (no leverage).
The configuration is the one selected by research/crt_research.py on train data (see
docs/crt/REPORT.md); change LIVE_CFG to switch.
"""
import crt

LIVE_CFG = crt.Config(tf=60, entry="aggr", stop="sweep", target="2R", longs=True, shorts=False,
                      name="CRT 1H, aggressive entry, stop beyond sweep, 2R target")
RISK_PCT = 0.02


def _new_setups(md, now):
    """CRT setups from CLOSED candles of the CRT timeframe only."""
    tf_sec = LIVE_CFG.tf * 60
    src = md["BTC"]["1h"] if LIVE_CFG.tf >= 60 else (md["BTC"].get("5m") or md["BTC"]["1h"])
    bars = [b for b in crt.resample(src, LIVE_CFG.tf) if b["t"] + tf_sec <= now]
    return list(crt.find_setups(bars, LIVE_CFG, crt.atr_series(bars)))


def crt_btc(md, memo, now=None):
    base = md["BTC"].get("5m") or md["BTC"]["1h"]
    step = 300 if md["BTC"].get("5m") else 3600
    closed = [b for b in base if b["t"] + step <= (now or 0)]
    events = []
    if memo.get("last_t") is None:  # first run: start watching from now, no backfilled trades
        memo["last_t"] = closed[-1]["t"] + step if closed else now
        memo["why"] = "Started; watching for the first CRT setup"
        return events
    seen = set(memo.get("seen", []))
    setups = []
    for s in _new_setups(md, now or 0):
        sid = f"{s['i']}-{s['sweep_t']}"
        if s["ready_t"] >= memo["last_t"] and sid not in seen:
            lv = crt.levels_for(s, LIVE_CFG)
            fees = s["entry"] * (0.0045 + (0.0045 if s["market"] else 0.0025))
            if lv and fees <= crt.MAX_COST_R * lv[2]:
                setups.append((s["ready_t"], sid, s, lv))
    setups.sort(key=lambda x: x[0])
    tf_sec = LIVE_CFG.tf * 60
    for b in closed:
        if b["t"] < memo["last_t"]:
            continue
        pos, order = memo.get("pos"), memo.get("order")
        # activate setups that became known at this candle's open
        while setups and setups[0][0] <= b["t"]:
            _, sid, s, (stop, tgt, risk) = setups.pop(0)
            seen.add(sid)
            if pos or order:
                continue
            order = {"entry": s["entry"], "stop": stop, "target": tgt, "market": s["market"],
                     "expire": b["t"] + crt.LIMIT_LIFE * tf_sec, "range": [s["L"], s["H"]],
                     "set_t": b["t"]}
            memo["order"] = order
        if order and not pos:
            fill = None
            if order["market"]:
                fill = b["o"]
            elif b["t"] >= order["expire"] or b["h"] >= order["target"] and b["l"] > order["entry"]:
                memo["order"] = order = None
            elif b["l"] <= order["entry"]:
                fill = min(order["entry"], b["o"])
            if fill is not None:
                risk = fill - order["stop"]
                if risk <= 0:
                    memo["order"] = None
                    continue
                tgt = order["target"]
                if LIVE_CFG.target.endswith("R"):
                    tgt = fill + float(LIVE_CFG.target[:-1]) * risk
                frac = min(1.0, RISK_PCT / (risk / fill))
                events.append({"t": b["t"], "side": "buy", "price": fill, "frac": frac,
                               "reason": f"CRT entry ({'market' if order['market'] else 'limit'})"})
                memo["pos"] = pos = {"entry": fill, "stop": order["stop"], "target": tgt,
                                     "risk": risk, "t": b["t"], "hold_end": b["t"] + crt.MAX_HOLD * tf_sec,
                                     "half": False}
                memo["order"] = order = None
                if b["l"] <= pos["stop"]:  # same candle: assume the worst
                    events.append({"t": b["t"], "side": "sell", "price": pos["stop"], "frac": 1.0,
                                   "reason": "CRT stop (same candle as entry)"})
                    memo["pos"] = None
                continue
        if pos:
            if b["l"] <= pos["stop"]:
                events.append({"t": b["t"], "side": "sell", "price": min(pos["stop"], b["o"]),
                               "frac": 1.0, "reason": "CRT stop" if not pos["half"] else "CRT breakeven"})
                memo["pos"] = None
            elif LIVE_CFG.target == "partial" and not pos["half"] and b["h"] >= pos["entry"] + 2 * pos["risk"]:
                events.append({"t": b["t"], "side": "sell", "price": pos["entry"] + 2 * pos["risk"],
                               "frac": 0.5, "reason": "CRT TP1 (half at 2R)"})
                pos["half"], pos["stop"] = True, pos["entry"]
            elif b["h"] >= pos["target"]:
                events.append({"t": b["t"], "side": "sell", "price": pos["target"], "frac": 1.0,
                               "reason": "CRT target"})
                memo["pos"] = None
            elif b["t"] >= pos["hold_end"]:
                events.append({"t": b["t"], "side": "sell", "price": b["c"], "frac": 1.0,
                               "reason": "CRT time exit"})
                memo["pos"] = None
    memo["last_t"] = closed[-1]["t"] + step if closed else memo["last_t"]
    memo["seen"] = sorted(seen)[-200:]
    pos, order = memo.get("pos"), memo.get("order")
    if pos:
        memo["stops"] = {"BTC": pos["stop"]}
        memo["levels"] = [{"name": "CRT target", "asset": "BTC", "price": pos["target"], "dir": "above"}]
        memo["why"] = (f"In BTC from ${pos['entry']:,.0f}: stop ${pos['stop']:,.0f}, "
                       f"target ${pos['target']:,.0f} ({(pos['target'] - pos['entry']) / pos['risk']:.1f}R)")
    elif order:
        memo["stops"] = {}
        memo["levels"] = [{"name": "CRT limit entry", "asset": "BTC", "price": order["entry"], "dir": "below"}]
        memo["why"] = (f"Limit buy at ${order['entry']:,.0f}, stop ${order['stop']:,.0f}, "
                       f"target ${order['target']:,.0f}; expires in "
                       f"{max(0, order['expire'] - (now or 0)) / 3600:.0f}h")
    else:
        memo["stops"], memo["levels"] = {}, []
        bars = crt.resample(md["BTC"]["1h"], LIVE_CFG.tf) if LIVE_CFG.tf >= 60 else crt.resample(base, LIVE_CFG.tf)
        bars = [x for x in bars if x["t"] + tf_sec <= (now or 0)]
        if len(bars) >= 2:
            c0 = bars[-1]
            memo["levels"] = [{"name": "CRT sweep of range low", "asset": "BTC", "price": c0["l"], "dir": "below"}]
            memo["why"] = (f"Waiting: last {LIVE_CFG.tf // 60 if LIVE_CFG.tf >= 60 else LIVE_CFG.tf}"
                           f"{'H' if LIVE_CFG.tf >= 60 else 'M'} range ${c0['l']:,.0f} to ${c0['h']:,.0f}. "
                           f"Needs a sweep below ${c0['l']:,.0f} that closes back inside")
    return events


crt_btc.broker = True
