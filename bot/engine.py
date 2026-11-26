"""Paper trading engine. Run once per hour (GitHub Actions cron).

Realism model:
  * Taker fee 0.40% per fill (Kraken Pro entry tier; Coinbase Advanced is 0.60%, so this is
    on the cheap side of what a $100 retail account actually pays).
  * Slippage 0.05% on BTC/ETH, 0.15% on other coins, always against you.
  * Fractional coins allowed, $1 minimum order, no leverage, no shorting.
  * Signals on completed candles, fills at the latest traded price.
  * Rebalances only when the target differs from the current position by >10% of equity
    (or a full exit / full entry), so drift doesn't bleed fees.
"""
import inspect
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from strategies import STRATEGIES  # noqa: E402
import risk  # noqa: E402
import journal  # noqa: E402

START_CASH = 100.0
FEE = 0.004
SLIP = {"BTC": 0.0005, "ETH": 0.0005}
SLIP_DEFAULT = 0.0015
MIN_ORDER = 1.0
REBAL_BAND = 0.10
MAX_HISTORY = 24 * 400  # ~400 days of hourly points

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_PATH = os.path.join(ROOT, "docs", "data", "state.json")


def new_account(sid, name, thesis):
    return {"id": sid, "name": name, "thesis": thesis, "cash": START_CASH, "holdings": {},
            "memo": {}, "trades": [], "history": [], "fees_paid": 0.0, "error": None}


# Leveraged mirrors (perp style): each copies a base account's moves times L, pays funding on the
# borrowed part while the base is invested, and is liquidated if one run's move wipes out 90%.
# Leverage levels chosen by research/leverage_lab.py on 8 years of history (see docs/lab/leverage.json).
LEVERED = [
    ("lev_trend_2x", "Trend SMA50 at 2x leverage", "trend_sma50", 2,
     "Best 8 year growth of any setting: $100 -> $8,900 (vs $2,500 at 1x). Worst drop about 85%."),
    ("lev_vol_3x", "Vol target at 3x leverage", "vol_target", 3,
     "8 years: $100 -> $4,600 (vs $1,400 at 1x). Volatility sizing keeps 3x survivable."),
    ("lev_btc_10x", "LOTTERY: BTC at 10x leverage", "hodl_btc", 10,
     "Demonstration only. Doubles in 11% of weeks, but every 10x account was liquidated within 8 years."),
]
FUNDING_YR = 0.11


def step_levered(state, now):
    for sid, name, base_id, lev, thesis in LEVERED:
        base = state["accounts"].get(base_id)
        if not base or "equity" not in base:
            continue
        acct = state["accounts"].get(sid) or new_account(sid, name, thesis)
        acct["name"], acct["thesis"] = name, thesis
        m = acct["memo"]
        beq = base["equity"]
        if "base_prev" in m and not m.get("liquidated") and m["base_prev"] > 0:
            r = beq / m["base_prev"] - 1
            hours = max(0.0, (now - m.get("t_prev", now)) / 3600)
            fund = (lev - 1) * m.get("expo", 0.0) * FUNDING_YR * hours / 8760
            mult = 1 + lev * r - fund
            if mult <= 0.1:
                m["liquidated"] = now
                acct["trades"].append({"t": now, "side": "sell", "asset": "ALL", "qty": 0, "price": 0,
                                       "usd": round(acct["cash"], 4), "fee": 0, "reason": f"LIQUIDATED at {lev}x",
                                       "pnl": round(-acct["cash"], 4)})
                acct["cash"] = 0.0
            else:
                acct["fees_paid"] += acct["cash"] * fund
                acct["cash"] *= mult
        m["base_prev"], m["t_prev"] = beq, now
        m["expo"] = 1 - base["cash"] / beq if beq > 0 else 0.0
        m["lev"], m["base"] = lev, base_id
        acct["holdings"] = {}
        acct["target"] = {k: round(v * lev, 3) for k, v in (base.get("target") or {}).items()}
        acct["equity"] = round(acct["cash"], 4)
        acct["history"].append([now, acct["equity"]])
        acct["history"] = acct["history"][-MAX_HISTORY:]
        acct["error"] = "liquidated" if m.get("liquidated") else None
        state["accounts"][sid] = acct


def equity(acct, prices):
    # "unrealized": open perp-style positions (long or short) tracked by a broker strategy
    return (acct["cash"] + sum(q * prices[a] for a, q in acct["holdings"].items())
            + acct.get("memo", {}).get("unrealized", 0.0))


def _fill(acct, asset, side, usd, price, now, reason):
    slip = SLIP.get(asset, SLIP_DEFAULT)
    if side == "buy":
        usd = min(usd, acct["cash"])
        if usd < MIN_ORDER:
            return
        px = price * (1 + slip)
        fee = usd * FEE
        qty = (usd - fee) / px
        acct["cash"] -= usd
        acct["holdings"][asset] = acct["holdings"].get(asset, 0.0) + qty
        value = usd
    else:
        held = acct["holdings"].get(asset, 0.0)
        qty = min(held, usd / price)
        if qty * price < MIN_ORDER:
            return
        px = price * (1 - slip)
        gross = qty * px
        fee = gross * FEE
        acct["cash"] += gross - fee
        acct["holdings"][asset] = held - qty
        if acct["holdings"][asset] * price < 0.01:
            del acct["holdings"][asset]
        value = gross
    acct["fees_paid"] += fee
    acct["trades"].append({"t": now, "side": side, "asset": asset, "qty": round(qty, 8),
                           "price": round(px, 6), "usd": round(value, 4),
                           "fee": round(fee, 4), "reason": reason})


def rebalance(acct, target, prices, now, reason="signal"):
    eq = equity(acct, prices)
    band = acct["memo"].get("band", REBAL_BAND)
    assets = set(target) | set(acct["holdings"])
    orders = []
    for a in assets:
        cur = acct["holdings"].get(a, 0.0) * prices[a]
        tgt = target.get(a, 0.0) * eq
        diff = tgt - cur
        full_exit = target.get(a, 0.0) == 0 and cur >= MIN_ORDER
        full_entry = cur < MIN_ORDER and tgt >= MIN_ORDER
        if full_exit or full_entry or abs(diff) > band * eq:
            orders.append((a, diff, full_exit))
    # sells first to free cash, then buys
    for a, diff, full_exit in sorted(orders, key=lambda o: o[1]):
        if diff < 0:
            usd = acct["holdings"].get(a, 0) * prices[a] if full_exit else -diff
            _fill(acct, a, "sell", usd, prices[a], now, reason)
    buys = [(a, d) for a, d, _ in orders if d > 0]
    total = sum(d for _, d in buys)
    for a, d in buys:
        # if cash is short (fees), scale buys proportionally
        usd = d if total <= acct["cash"] else acct["cash"] * d / total
        _fill(acct, a, "buy", usd, prices[a], now, reason)


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"started": None, "accounts": {}, "runs": 0, "config": {}}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, separators=(",", ":"))
    os.replace(tmp, STATE_PATH)


def step(state, md, now, errors=None, sources=None):
    prices = {a: d["price"] for a, d in md.items()}
    prev = state.get("last_run")
    state["started"] = state["started"] or now
    state["runs"] += 1
    state["last_run"] = now
    state["data_errors"] = errors or {}
    state["data_sources"] = sources or []
    state["prices"] = prices
    state["config"] = {"start_cash": START_CASH, "fee": FEE, "slippage_major": SLIP["BTC"],
                       "slippage_alt": SLIP_DEFAULT, "rebalance_band": REBAL_BAND,
                       "min_order": MIN_ORDER}
    live = {sid for sid, *_ in STRATEGIES} | {m[0] for m in LEVERED}
    state["retired"] = state.get("retired", {})
    for sid in [k for k in state["accounts"] if k not in live]:
        state["retired"][sid] = state["accounts"].pop(sid)
    for sid, name, fn, thesis, needs in STRATEGIES:
        acct = state["accounts"].get(sid) or new_account(sid, name, thesis)
        acct["name"], acct["thesis"] = name, thesis
        state["accounts"][sid] = acct
        required = needs or list(md)
        held = list(acct["holdings"])
        if any(a not in md for a in set(required) | set(held)):
            acct["error"] = "market data missing this run; skipped"
        else:
            try:
                memo = acct["memo"]
                ntrades = len(acct["trades"])
                journal.score_decisions(acct, prices, now)
                journal.check_scenarios(acct, md, prev, prices, now)
                hit = ([] if getattr(fn, "broker", False)  # broker strategies own their stops
                       else risk.check_stops(acct, md, prev, prices))
                for a, fill in hit:  # stop loss: exit fully before the strategy speaks
                    _fill(acct, a, "sell", acct["holdings"][a] * fill * 1.0001, fill, now,
                          "stop loss")
                    risk.record_stop(acct, sid, a, fill, now)
                    if "in" in memo:
                        memo["in"] = False
                    if isinstance(memo.get(a), dict):
                        memo[a] = None
                    if "tier" in memo:
                        memo["tier"] = 0
                kwargs = {"now": now} if "now" in inspect.signature(fn).parameters else {}
                if getattr(fn, "broker", False):
                    memo["equity_hint"] = equity(acct, prices)
                    # strategy runs its own resting orders: execute its fills at their prices
                    for ev in fn(md, memo, **kwargs):
                        a, px = ev.get("asset", "BTC"), ev["price"]
                        if ev.get("type") in ("open", "close"):
                            # perp-style position: no coins held, profit/loss settles in cash
                            fee = ev.get("fee", 0.0)
                            acct["cash"] += ev.get("pnl", 0.0) - fee
                            acct["fees_paid"] += fee
                            acct["trades"].append({"t": ev["t"], "side": ev["side"], "asset": a,
                                                   "qty": round(ev["notional"] / px, 8),
                                                   "price": round(px, 6), "usd": round(ev["notional"], 4),
                                                   "fee": round(fee, 4), "reason": ev["reason"],
                                                   **({"pnl": round(ev["pnl"], 4)} if "pnl" in ev else {})})
                        elif ev["side"] == "buy":
                            eq = acct["cash"] + sum(q * (px if k == a else prices[k])
                                                    for k, q in acct["holdings"].items())
                            _fill(acct, a, "buy", eq * ev["frac"], px, ev["t"], ev["reason"])
                        elif a in acct["holdings"]:
                            q = acct["holdings"][a] * ev["frac"]
                            _fill(acct, a, "sell", q * px * (1.0001 if ev["frac"] >= 1 else 1),
                                  px, ev["t"], ev["reason"])
                    target = {}
                    acct["stops"] = {k: {"stop": v, "type": memo.get("stop_type", "strategy stop"),
                                         "dist": round(v / prices[k] - 1, 4)}
                                     for k, v in memo.get("stops", {}).items()}
                else:
                    target = dict(fn(md, memo, **kwargs))
                    for a, _ in hit:
                        target.pop(a, None)
                    target = risk.apply_cooldown(acct, target, now)
                    rebalance(acct, target, prices, now)
                    risk.update_stops(acct, sid, md, prices)
                risk.evaluate_stop_events(acct, prices, now)
                journal.record_decision(acct, needs or list(md), prices, now,
                                        len(acct["trades"]) > ntrades)
                journal.set_watch(acct, prices)
                acct["target"] = target
                acct["error"] = None
            except Exception as e:  # noqa: BLE001
                acct["error"] = f"{type(e).__name__}: {e}"
        if all(a in prices for a in acct["holdings"]):
            acct["equity"] = round(equity(acct, prices), 4)
            acct["history"].append([now, acct["equity"]])
            acct["history"] = acct["history"][-MAX_HISTORY:]
    step_levered(state, now)
    state.setdefault("btc_history", []).append([now, prices.get("BTC")])
    state["btc_history"] = state["btc_history"][-MAX_HISTORY:]
    return state


def main():
    from market import load_all
    md, errors, sources = load_all()
    if "BTC" not in md:
        print("No BTC data, aborting without changes:", errors)
        sys.exit(1)
    st0 = load_state()
    prev_run = st0.get("last_run") or 0
    state = step(st0, md, int(time.time()), errors, sources)
    import crt_forward
    crt_forward.update(state, int(time.time()))
    save_state(state)
    try:
        import notify
        notify.send_new_trades(state, prev_run)
    except Exception as e:  # noqa: BLE001  (alerts must never break trading)
        print("notify failed:", e)
    for a in state["accounts"].values():
        print(f"{a['name']:<42} ${a.get('equity', 0):8.2f}  trades={len(a['trades'])}"
              f"{'  ERR ' + a['error'] if a['error'] else ''}")


if __name__ == "__main__":
    main()
