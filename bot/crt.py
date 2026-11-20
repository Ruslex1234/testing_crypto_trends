"""Candle Range Theory (CRT) model: objective rules, shared by the backtest and the live account.

Definitions (on the CRT timeframe TF, completed candles only):
  Range candle   C0 with high H, low L, equilibrium EQ = (H+L)/2. Must be significant:
                 H-L >= RANGE_ATR x ATR14(TF).
  Sweep          one of the next SWEEP_WINDOW candles trades beyond H (or L) but CLOSES back inside
                 the range. That close is the rejection. A close beyond the level is a breakout,
                 not a sweep, and kills that side of the setup.
  Displacement   a later candle whose body >= DISP_ATR x ATR, closing in the trade direction.
  MSS / CHoCH    that displacement candle closes beyond the structure between C0 and the sweep
                 (long: above the highest high after C0 up to the sweep).
  Entry zones    aggressive: market at the rejection close.
                 fvg: limit at the midpoint of a fair value gap left by the displacement.
                 eq:  limit at the CRT 50% level.
                 ob:  limit at the open of the last opposite candle before displacement.
  Stops          sweep (beyond the sweep extreme), rejection (beyond the rejection candle),
                 atr (1.5 x ATR from entry), ob (beyond the order block candle).
                 Always padded by STOP_BUF x ATR so a stop isn't the exact extreme.
  Targets        range (opposite side of the CRT range), fixed 2R/3R/4R/5R,
                 partial (half at 2R, stop to breakeven, rest at the range opposite or 4R).
Fills are simulated on finer base candles. If stop and target fall in the same base candle the
stop is assumed first (conservative). Limit orders expire after LIMIT_LIFE TF candles and are
cancelled if price reaches the target or the invalidation level before filling.
"""
from dataclasses import dataclass, field

RANGE_ATR = 0.6
SWEEP_WINDOW = 3
DISP_ATR = 0.6
STOP_BUF = 0.1
CONFIRM_WINDOW = 6
LIMIT_LIFE = 8
MAX_HOLD = 32
MIN_RR_RANGE = 1.5
MAX_COST_R = 0.25   # skip trades whose round-trip costs exceed this fraction of the risk


@dataclass
class Config:
    tf: int = 60                 # CRT timeframe in minutes
    entry: str = "fvg"           # aggr | fvg | eq | ob
    stop: str = "sweep"          # sweep | rejection | atr | ob
    target: str = "range"        # range | 2R | 3R | 4R | 5R | partial
    longs: bool = True
    shorts: bool = True
    filters: tuple = ()          # pd_level, session_level, vwap, killzone, high_vol, daily_open
    bias_tf: int = 0             # 0 = none, else HTF CRT direction must agree
    name: str = ""


@dataclass
class Trade:
    side: int
    signal_t: int
    entry_t: int = 0
    entry: float = 0.0
    stop: float = 0.0
    target: float = 0.0
    exit_t: int = 0
    exit: float = 0.0
    r_gross: float = 0.0
    r_net: float = 0.0
    risk_pts: float = 0.0
    session: str = ""
    hit: dict = field(default_factory=dict)  # max favourable excursion in R, TP reach flags
    reason: str = ""


# ---------- helpers ----------
def resample(rows, minutes):
    step = minutes * 60
    out = []
    for r in rows:
        b = r["t"] - r["t"] % step
        if out and out[-1]["t"] == b:
            o = out[-1]
            o["h"] = max(o["h"], r["h"]); o["l"] = min(o["l"], r["l"])
            o["c"] = r["c"]; o["v"] = o.get("v", 0) + r.get("v", 0); o["n"] += 1
        else:
            out.append({"t": b, "o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"],
                        "v": r.get("v", 0), "n": 1})
    return out


def atr_series(bars, n=14):
    out, prev_c, a = [], None, None
    for b in bars:
        tr = b["h"] - b["l"] if prev_c is None else max(b["h"] - b["l"], abs(b["h"] - prev_c),
                                                          abs(b["l"] - prev_c))
        a = tr if a is None else (a * (n - 1) + tr) / n
        out.append(a)
        prev_c = b["c"]
    return out


def et_hour(t):
    """Hour in New York time (handles DST)."""
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    d = datetime.fromtimestamp(t, timezone.utc).astimezone(ZoneInfo("America/New_York"))
    return d.hour + d.minute / 60, d.date()


def session_of(t):
    h, _ = et_hour(t)
    if 2 <= h < 7:
        return "London"
    if 7 <= h < 9.5:
        return "NY pre-open"
    if 9.5 <= h < 11:
        return "NY open"
    if 11 <= h < 14:
        return "NY midday"
    if 14 <= h < 17:
        return "NY afternoon"
    return "Asia/overnight"


# ---------- context: levels known at each time (no lookahead) ----------
class Context:
    """Previous-day high/low, Asia & London high/low, daily open and session VWAP, all computed
    only from base candles that have already closed."""

    def __init__(self, base):
        self.base = base
        self.by_t = {}
        day_hi, day_lo, cur_day = {}, {}, None
        asia, london = {}, {}
        vwap_pv = vwap_v = 0.0
        prev_hi = prev_lo = None
        d_open = None
        last_day = None
        for b in base:
            h, day = et_hour(b["t"])
            key = day.toordinal() + (1 if h >= 18 else 0)  # futures day starts 18:00 ET
            if key != last_day:
                if last_day is not None:
                    prev_hi, prev_lo = day_hi.get(last_day), day_lo.get(last_day)
                last_day = key
                d_open = b["o"]
                vwap_pv = vwap_v = 0.0
            # snapshot BEFORE this candle updates anything (what a trader knew at its open)
            a = asia.get(key); lo = london.get(key)
            self.by_t[b["t"]] = {
                "pdh": prev_hi, "pdl": prev_lo, "open": d_open,
                "vwap": vwap_pv / vwap_v if vwap_v else None,
                "asia": a, "london": lo,
            }
            day_hi[key] = max(day_hi.get(key, b["h"]), b["h"])
            day_lo[key] = min(day_lo.get(key, b["l"]), b["l"])
            if h >= 18 or h < 2:
                asia[key] = (max(a[0], b["h"]), min(a[1], b["l"])) if a else (b["h"], b["l"])
            elif 2 <= h < 7:
                london[key] = (max(lo[0], b["h"]), min(lo[1], b["l"])) if lo else (b["h"], b["l"])
            v = b.get("v", 0) or 1.0
            vwap_pv += (b["h"] + b["l"] + b["c"]) / 3 * v
            vwap_v += v

    def at(self, t):
        return self.by_t.get(t, {})


# ---------- setup detection on the CRT timeframe ----------
def htf_bias(bars, atr, i_last):
    """Direction of the most recent HTF CRT sweep (+1 bullish / -1 bearish / 0) using only
    candles up to i_last (completed)."""
    for j in range(i_last, max(i_last - 2, 1) - 1, -1):
        c0, c1 = bars[j - 1], bars[j]
        if c1["l"] < c0["l"] and c0["l"] < c1["c"] < c0["h"]:
            return 1
        if c1["h"] > c0["h"] and c0["l"] < c1["c"] < c0["h"]:
            return -1
    return 0


def find_setups(bars, cfg, atr):
    """Yield setup dicts in time order. Each has everything needed to place orders, and the
    time (`ready_t`) at which it became known (close of the confirming candle)."""
    tf_sec = cfg.tf * 60
    i = 15
    n = len(bars)
    while i < n - 2:
        c0, a0 = bars[i], atr[i]
        H, L = c0["h"], c0["l"]
        if H - L < RANGE_ATR * a0:
            i += 1
            continue
        found = None
        long_ok, short_ok = cfg.longs, cfg.shorts
        hi_since, lo_since = H, L
        for j in range(i + 1, min(i + 1 + SWEEP_WINDOW, n)):
            b = bars[j]
            if long_ok and b["l"] < L:
                if L < b["c"] < H:
                    found = (1, j)
                    break
                if b["c"] <= L:
                    long_ok = False
            if short_ok and b["h"] > H:
                if L < b["c"] < H:
                    found = (-1, j)
                    break
                if b["c"] >= H:
                    short_ok = False
            hi_since, lo_since = max(hi_since, b["h"]), min(lo_since, b["l"])
            if not (long_ok or short_ok):
                break
        if not found:
            i += 1
            continue
        side, j = found
        sw = bars[j]
        ext = min(b["l"] for b in bars[i + 1:j + 1]) if side == 1 else max(b["h"] for b in bars[i + 1:j + 1])
        struct = max(b["h"] for b in bars[i + 1:j + 1]) if side == 1 else min(b["l"] for b in bars[i + 1:j + 1])
        setup = {"side": side, "i": i, "j": j, "H": H, "L": L, "EQ": (H + L) / 2, "ext": ext,
                 "atr": atr[j], "rej": sw, "sweep_t": sw["t"]}
        if cfg.entry == "aggr":
            setup.update(ready_t=sw["t"] + tf_sec, entry=sw["c"], market=True, k=j)
            yield setup
            i = j + 1
            continue
        # confirmed: displacement + MSS within CONFIRM_WINDOW
        conf = None
        for k in range(j + 1, min(j + 1 + CONFIRM_WINDOW, n)):
            b = bars[k]
            body = (b["c"] - b["o"]) * side
            if (b["l"] < ext if side == 1 else b["h"] > ext):
                break  # sweep extreme taken out again: invalid
            if body >= DISP_ATR * atr[k] and (b["c"] > struct if side == 1 else b["c"] < struct):
                conf = k
                break
        if conf is None:
            i = j + 1
            continue
        k = conf
        entry = None
        if cfg.entry == "fvg":
            for m in range(k, max(j, k - 2), -1):  # FVG formed by the displacement leg
                if m - 2 < 0:
                    continue
                a, c = bars[m - 2], bars[m]
                if side == 1 and c["l"] > a["h"]:
                    entry = (c["l"] + a["h"]) / 2
                    break
                if side == -1 and c["h"] < a["l"]:
                    entry = (c["h"] + a["l"]) / 2
                    break
        elif cfg.entry == "eq":
            entry = setup["EQ"]
            if (side == 1 and entry >= bars[k]["c"]) or (side == -1 and entry <= bars[k]["c"]):
                entry = None
        ob = None
        for m in range(k - 1, i, -1):  # last opposite candle before displacement
            if (bars[m]["c"] - bars[m]["o"]) * side < 0:
                ob = bars[m]
                break
        if cfg.entry == "ob" and ob:
            entry = ob["o"]
            if (side == 1 and entry >= bars[k]["c"]) or (side == -1 and entry <= bars[k]["c"]):
                entry = None
        if entry is None:
            i = k + 1
            continue
        setup.update(ready_t=bars[k]["t"] + tf_sec, entry=entry, market=False, k=k, ob=ob)
        yield setup
        i = k + 1


def levels_for(setup, cfg):
    """Stop and target prices for a setup under cfg. Returns None if invalid."""
    side, e, a = setup["side"], setup["entry"], setup["atr"]
    buf = STOP_BUF * a
    if cfg.stop == "sweep":
        stop = setup["ext"] - side * buf
    elif cfg.stop == "rejection":
        r = setup["rej"]
        stop = (r["l"] if side == 1 else r["h"]) - side * buf
    elif cfg.stop == "atr":
        stop = e - side * 1.5 * a
    elif cfg.stop == "ob":
        ob = setup.get("ob") or setup["rej"]
        stop = (ob["l"] if side == 1 else ob["h"]) - side * buf
    else:
        raise ValueError(cfg.stop)
    risk = (e - stop) * side
    if risk <= 0:
        return None
    opp = setup["H"] if side == 1 else setup["L"]
    if cfg.target in ("range", "partial"):
        tgt = opp
        if (tgt - e) * side < MIN_RR_RANGE * risk:
            return None
    else:
        tgt = e + side * float(cfg.target[:-1]) * risk
    return stop, tgt, risk


# ---------- execution simulation on base candles ----------
def simulate(base, base_idx, setup, cfg, levels, cost):
    """Simulate one setup. `cost(entry_price, risk_pts, market_entry)` returns cost in price
    points for the round trip. Returns Trade or None (never filled)."""
    side = setup["side"]
    stop, tgt, risk = levels
    e = setup["entry"]
    t0 = setup["ready_t"]
    import bisect
    i = bisect.bisect_left(base_idx, t0)  # first base candle at/after the signal (skips gaps)
    if i >= len(base) or base[i]["t"] - t0 > 3 * 86400:
        return None
    tf_sec = cfg.tf * 60
    tr = Trade(side=side, signal_t=t0, stop=stop, target=tgt, risk_pts=risk)
    # fill
    if setup["market"]:
        fill_i, fill = i, base[i]["o"]
        risk = (fill - stop) * side
        if risk <= 0:
            return None
        if cfg.target not in ("range", "partial"):
            tgt = fill + side * float(cfg.target[:-1]) * risk
        tr.risk_pts, tr.target = risk, tgt
    else:
        expire = t0 + LIMIT_LIFE * tf_sec
        fill_i = fill = None
        for m in range(i, len(base)):
            b = base[m]
            if b["t"] >= expire:
                return None
            if (side == 1 and b["h"] >= tgt) or (side == -1 and b["l"] <= tgt):
                if not ((side == 1 and b["l"] <= e) or (side == -1 and b["h"] >= e)):
                    return None  # ran to target without us
            if (side == 1 and b["l"] <= e) or (side == -1 and b["h"] >= e):
                fill_i = m
                fill = min(e, b["o"]) if side == 1 else max(e, b["o"])
                break
        if fill_i is None:
            return None
        if (fill - stop) * side <= 0:
            return None
        risk = (fill - stop) * side
    tr.entry_t, tr.entry = base[fill_i]["t"], fill
    tr.session = session_of(base[fill_i]["t"])
    # manage
    partial = cfg.target == "partial"
    tp1 = fill + side * 2 * risk
    tp_final = tgt if partial else tgt
    if partial and (tgt - fill) * side < 2 * risk:
        tp_final = fill + side * 4 * risk
    half_done = False
    realized = 0.0
    cur_stop = stop
    mfe = 0.0
    hold_end = tr.entry_t + MAX_HOLD * tf_sec
    exit_px, exit_t, why = None, None, ""
    for m in range(fill_i, len(base)):
        b = base[m]
        fav = (b["h"] - fill) if side == 1 else (fill - b["l"])
        mfe = max(mfe, fav / risk)
        adverse_hit = (b["l"] <= cur_stop) if side == 1 else (b["h"] >= cur_stop)
        if adverse_hit:
            px = (min(cur_stop, b["o"]) if side == 1 else max(cur_stop, b["o"])) if m > fill_i else cur_stop
            exit_px, exit_t, why = px, b["t"], "stop" if not half_done else "breakeven"
            break
        if m == fill_i:
            continue  # order of events inside the fill candle is unknown: no target credit
        if partial and not half_done and ((b["h"] >= tp1) if side == 1 else (b["l"] <= tp1)):
            half_done = True
            realized += 0.5 * 2.0
            cur_stop = fill
        if (b["h"] >= tp_final) if side == 1 else (b["l"] <= tp_final):
            exit_px, exit_t, why = tp_final, b["t"], "target"
            break
        if b["t"] >= hold_end:
            exit_px, exit_t, why = b["c"], b["t"], "time"
            break
    if exit_px is None:
        return None  # still open at end of data
    move_r = (exit_px - fill) * side / risk
    r_gross = realized + (0.5 if half_done else 1.0) * move_r
    tr.exit_t, tr.exit, tr.reason = exit_t, exit_px, why
    tr.r_gross = r_gross
    tr.r_net = r_gross - cost(fill, risk, setup["market"]) / risk
    tr.hit = {"mfe": round(mfe, 2), **{f"tp{n}": mfe >= n for n in (2, 3, 4, 5)}}
    tr.risk_pts = risk
    return tr


# ---------- filters ----------
def passes(setup, cfg, ctx, bars, atr, atr_median, htf):
    t = setup["ready_t"]
    side = setup["side"]
    c = ctx.at(t) if ctx else {}
    for f in cfg.filters:
        if f == "pd_level":
            lvl = c.get("pdl") if side == 1 else c.get("pdh")
            if lvl is None or (setup["ext"] - lvl) * side > 0.25 * setup["atr"]:
                return False  # sweep must reach previous day's low/high
        elif f == "session_level":
            ok = False
            for s in ("asia", "london"):
                rng = c.get(s)
                if rng:
                    lvl = rng[1] if side == 1 else rng[0]
                    if (setup["ext"] - lvl) * side <= 0.25 * setup["atr"]:
                        ok = True
            if not ok:
                return False
        elif f == "vwap":
            v = c.get("vwap")
            if v is None or (bars[setup["k"]]["c"] - v) * side < 0:
                return False
        elif f == "daily_open":
            o = c.get("open")
            if o is None or (setup["entry"] - o) * side > 0:
                return False  # longs only below the daily open (discount), shorts above
        elif f == "killzone":
            h, _ = et_hour(t)
            if not (2 <= h < 5 or 8.5 <= h < 11):
                return False
        elif f == "high_vol":
            if setup["atr"] < atr_median[setup["j"]]:
                return False
        elif f == "low_vol":
            if setup["atr"] >= atr_median[setup["j"]]:
                return False
    if htf is not None:
        if htf(t) != side:
            return False
    return True


def run(base, cfg, cost, ctx=None, t_from=None, t_to=None):
    """Backtest one configuration. One position at a time."""
    bars = [b for b in resample(base, cfg.tf)]
    atr = atr_series(bars)
    med = []
    window = []
    for a in atr:
        window.append(a)
        window = window[-100:]
        med.append(sorted(window)[len(window) // 2])
    base_idx = [b["t"] for b in base]
    htf = None
    if cfg.bias_tf:
        hb = resample(base, cfg.bias_tf)
        hatr = atr_series(hb)
        hsec = cfg.bias_tf * 60
        closes = [b["t"] + hsec for b in hb]
        import bisect

        def htf(t):
            k = bisect.bisect_right(closes, t) - 1  # last HTF candle closed by t
            return htf_bias(hb, hatr, k) if k >= 2 else 0
    trades = []
    busy_until = 0
    for s in find_setups(bars, cfg, atr):
        if s["ready_t"] < busy_until:
            continue
        if t_from and s["ready_t"] < t_from:
            continue
        if t_to and s["ready_t"] >= t_to:
            break
        if not passes(s, cfg, ctx, bars, atr, med, htf):
            continue
        lv = levels_for(s, cfg)
        if not lv or cost(s["entry"], lv[2], s["market"]) > MAX_COST_R * lv[2]:
            continue
        tr = simulate(base, base_idx, s, cfg, lv, cost)
        if tr:
            trades.append(tr)
            busy_until = tr.exit_t
    return trades


def stats(trades, point_value=None):
    n = len(trades)
    if not n:
        return {"n": 0}
    rs = [t.r_net for t in trades]
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    eq = peak = dd = 0.0
    streak = max_streak = 0
    for r in rs:
        eq += r
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
        streak = streak + 1 if r <= 0 else 0
        max_streak = max(max_streak, streak)
    gp, gl = sum(wins), -sum(losses)
    by_side = {s: [t.r_net for t in trades if t.side == s] for s in (1, -1)}
    by_sess = {}
    for t in trades:
        by_sess.setdefault(t.session, []).append(t.r_net)
    out = {
        "n": n, "win_rate": len(wins) / n, "expectancy_r": sum(rs) / n, "net_r": sum(rs),
        "gross_profit_r": gp, "gross_loss_r": gl, "profit_factor": gp / gl if gl else None,
        "max_dd_r": dd, "max_consec_losses": max_streak,
        "avg_rr_realized_win": sum(wins) / len(wins) if wins else 0,
        "avg_risk_pts": sum(t.risk_pts for t in trades) / n,
        "tp_reach": {k: sum(1 for t in trades if t.hit.get(k)) / n for k in ("tp2", "tp3", "tp4", "tp5")},
        "long": {"n": len(by_side[1]), "exp": sum(by_side[1]) / len(by_side[1]) if by_side[1] else None},
        "short": {"n": len(by_side[-1]), "exp": sum(by_side[-1]) / len(by_side[-1]) if by_side[-1] else None},
        "sessions": {k: {"n": len(v), "exp": sum(v) / len(v)} for k, v in by_sess.items()},
        "trades_per_day": None,
    }
    if trades:
        days = max(1, (trades[-1].exit_t - trades[0].entry_t) / 86400)
        out["trades_per_day"] = n / days
    return out
