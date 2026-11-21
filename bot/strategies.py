"""Each strategy returns target portfolio weights {asset: fraction_of_equity}.
Weights not listed are 0 (cash). Signals use COMPLETED candles only ([:-1]) so a
forming candle can't flip a decision back and forth inside the hour/day.
`memo` is a per-account dict persisted between runs for stateful strategies.
"""
import math


# ---------- indicators ----------
def closes(rows):
    return [r["c"] for r in rows]


def sma(xs, n):
    return sum(xs[-n:]) / n


def ema_series(xs, n):
    k = 2 / (n + 1)
    out = [xs[0]]
    for x in xs[1:]:
        out.append(x * k + out[-1] * (1 - k))
    return out


def rsi(xs, n=14):
    gains, losses = [], []
    for a, b in zip(xs[:-1], xs[1:]):
        d = b - a
        gains.append(max(d, 0)); losses.append(max(-d, 0))
    ag, al = sum(gains[:n]) / n, sum(losses[:n]) / n
    for g, l in zip(gains[n:], losses[n:]):  # Wilder smoothing
        ag = (ag * (n - 1) + g) / n
        al = (al * (n - 1) + l) / n
    if al == 0:
        return 100.0
    return 100 - 100 / (1 + ag / al)


def stdev(xs):
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def pct(x):
    return f"{x * 100:+.1f}%"


def done(rows):
    return rows[:-1]


# ---------- strategies ----------
def hodl_btc(md, memo):
    """Benchmark: buy BTC once, never sell."""
    memo["why"] = "Always 100% BTC"
    return {"BTC": 1.0}


def trend_sma50(md, memo):
    """Time-series momentum: hold BTC while last daily close > 50-day SMA, else cash."""
    c = closes(done(md["BTC"]["1d"]))
    m = sma(c, 50)
    memo["why"] = (f"In BTC while daily close ${c[-1]:,.0f} stays above 50d avg ${m:,.0f}"
                   if c[-1] > m else
                   f"Waiting for a daily close above the 50d avg ${m:,.0f} (BTC needs {pct(m / c[-1] - 1)})")
    return {"BTC": 1.0} if c[-1] > m else {}


def ema_cross_6h(md, memo):
    """ETH on 6h candles: long when EMA(9) > EMA(21) (MACD-style momentum), else cash."""
    c = closes(done(md["ETH"]["6h"]))
    fast, slow = ema_series(c, 9)[-1], ema_series(c, 21)[-1]
    k9, k21 = 2 / 10, 2 / 22
    cross = (slow * (1 - k21) - fast * (1 - k9)) / (k9 - k21)  # 6h close that makes EMAs meet
    memo["levels"] = [{"name": "EMA sell trigger" if fast > slow else "EMA buy trigger",
                       "asset": "ETH", "price": cross, "dir": "below" if fast > slow else "above"}]
    memo["why"] = (f"Long ETH: fast EMA {pct(fast / slow - 1)} above slow" if fast > slow else
                   f"Buys if a 6h candle closes above ${cross:,.0f} "
                   f"({pct(cross / md['ETH']['price'] - 1)} from here)")
    return {"ETH": 1.0} if fast > slow else {}


def donchian_turtle(md, memo):
    """Turtle-style breakout on BTC and ETH daily: enter on 20-day high, exit on 10-day low.
    Half the account is allocated to each coin."""
    w, why = {}, []
    for a in ("BTC", "ETH"):
        d = done(md[a]["1d"])
        last = d[-1]["c"]
        hi20 = max(r["h"] for r in d[-21:-1])
        lo10 = min(r["l"] for r in d[-11:-1])
        inpos = memo.get(a, False)
        if not inpos and last > hi20:
            inpos = True
        elif inpos and last < lo10:
            inpos = False
        memo[a] = inpos
        why.append(f"{a} in, exits below ${lo10:,.2f}" if inpos else
                   f"{a} needs close > 20d high ${hi20:,.2f} ({pct(hi20 / last - 1)})")
        if inpos:
            w[a] = 0.5
    memo["why"] = "; ".join(why)
    return w


def rsi_reversion(md, memo):
    """BTC hourly mean reversion: buy when RSI(14) < 30, exit when RSI > 55
    or a 6% stop loss from entry is hit. No trend filter: it buys dips in any market."""
    c = closes(done(md["BTC"]["1h"]))
    r = rsi(c[-120:], 14)
    price = md["BTC"]["price"]
    inpos = memo.get("in", False)
    if not inpos and r < 30:
        inpos, memo["entry"] = True, price
    elif inpos and (r > 55 or price < memo.get("entry", price) * 0.94):
        inpos = False
    memo["in"] = inpos
    memo["stops"] = {"BTC": memo["entry"] * 0.94} if inpos else {}
    memo["why"] = (f"Holding BTC, exits at RSI > 55 (now {r:.0f}) or stop "
                   f"${memo.get('entry', price) * 0.94:,.0f}" if inpos else
                   f"Waiting for hourly RSI below 30 (now {r:.0f})")
    return {"BTC": 1.0} if inpos else {}


def bollinger_reversion(md, memo):
    """SOL hourly: buy a close below the lower Bollinger band (20, 2σ), sell at the middle band.
    8% stop loss."""
    c = closes(done(md["SOL"]["1h"]))
    win = c[-20:]
    mid, sd = sum(win) / 20, stdev(win)
    price = md["SOL"]["price"]
    inpos = memo.get("in", False)
    if not inpos and c[-1] < mid - 2 * sd:
        inpos, memo["entry"] = True, price
    elif inpos and (c[-1] >= mid or price < memo.get("entry", price) * 0.92):
        inpos = False
    memo["in"] = inpos
    memo["stops"] = {"SOL": memo["entry"] * 0.92} if inpos else {}
    memo["levels"] = [{"name": "BB take profit (mid band)", "asset": "SOL", "price": mid,
                       "dir": "above"} if inpos else
                      {"name": "BB buy (lower band)", "asset": "SOL", "price": mid - 2 * sd,
                       "dir": "below"}]
    memo["why"] = (f"Holding SOL, exits at middle band ${mid:,.2f}" if inpos else
                   f"Waiting for an hourly close below ${mid - 2 * sd:,.2f} "
                   f"({pct((mid - 2 * sd) / c[-1] - 1)} from here)")
    return {"SOL": 1.0} if inpos else {}


def momentum_rotation(md, memo, now=None):
    """Cross-sectional + absolute ('dual') momentum across 8 large coins.
    Every 7 days: rank by 14-day return, hold the top 3 equally, but only those
    with a positive return. Otherwise cash."""
    last = memo.get("last_rebalance", 0)
    # hold picks for 7 days; while in cash, re-check daily so it can re-enter promptly
    hold = 7 * 86400 if memo.get("weights") else 86400
    if now is not None and now - last < hold and "weights" in memo:
        w, sc = memo["weights"], memo.get("scores", {})
        best = max(sc, key=sc.get) if sc else "?"
        memo["why"] = (f"Holding {', '.join(w)} until next weekly rebalance" if w else
                       f"All coins down over 14 days at last check (best: {best} "
                       f"{pct(sc.get(best, 0))}); next check in {(last + hold - now) / 3600:.0f}h")
        return w
    scores = {}
    for a, d in md.items():
        c = closes(done(d["1d"]))
        if len(c) > 15:
            scores[a] = c[-1] / c[-15] - 1
    top = sorted(scores, key=scores.get, reverse=True)[:3]
    w = {a: 1 / 3 for a in top if scores[a] > 0}
    memo["weights"], memo["last_rebalance"], memo["scores"] = w, now or 0, {
        a: round(s, 4) for a, s in scores.items()}
    best = top[0] if top else None
    memo["why"] = (f"Holding {', '.join(w)} until next weekly rebalance" if w else
                   f"All 8 coins down over 14 days (best: {best} {pct(scores[best])}); "
                   f"re-checks daily for any coin turning positive")
    return w


def grid_eth(md, memo):
    """Grid trading on ETH: 10 levels across ±10% of the price when the grid was set.
    Each level the price falls → own 10% more ETH; each level it rises → sell 10%.
    If price leaves the range, the grid re-centres on the current price."""
    price = md["ETH"]["price"]
    lo, hi = memo.get("lo"), memo.get("hi")
    if lo is None or price < lo or price > hi:
        memo["lo"], memo["hi"] = lo, hi = price * 0.9, price * 1.1
        memo["recentres"] = memo.get("recentres", -1) + 1
        memo.pop("level", None)
    levels = 10
    step = (hi - lo) / levels
    x = (hi - price) / step  # how many grid lines price sits below the top
    cur = memo.get("level", math.floor(x))
    # Hysteresis like resting grid orders: buy a level when price falls through its line,
    # sell it only when price climbs back through the line one step above.
    if math.floor(x) > cur:
        cur = math.floor(x)
    elif math.ceil(x) < cur:
        cur = math.ceil(x)
    cur = max(0, min(levels, cur))
    memo["level"] = cur
    memo["levels"] = ([{"name": "grid buy", "asset": "ETH", "price": hi - (cur + 1) * step,
                        "dir": "below"}] if cur < levels else []) + (
        [{"name": "grid sell", "asset": "ETH", "price": hi - (cur - 1) * step, "dir": "above"}]
        if cur > 0 else [])
    memo["why"] = (f"Grid ${lo:,.0f} to ${hi:,.0f}, {cur}/{levels} levels filled; "
                   f"next buy ${hi - (cur + 1) * step:,.0f}, next sell ${hi - (cur - 1) * step:,.0f}")
    return {"ETH": cur / levels}


def dca_btc(md, memo, now=None):
    """Dollar cost averaging: spread the $100 into BTC evenly over 30 days instead of all at
    once. Answers the practical question: lump sum (benchmark) or drip it in?"""
    memo.setdefault("start", now or 0)
    days = ((now or 0) - memo["start"]) / 86400
    frac = min(1.0, (days + 1) / 30)
    memo["band"] = 0.02  # small band so it buys roughly $3 a day
    memo["why"] = (f"Day {days:.0f} of 30: target {frac * 100:.0f}% in BTC" if frac < 1 else
                   "Fully invested, now holding")
    return {"BTC": frac}


def crash_buyer(md, memo):
    """Contrarian: buy BTC in thirds as it falls 15% / 25% / 35% below its 60 day high.
    Sell everything once it recovers to within 5% of the high it fell from."""
    d = done(md["BTC"]["1d"])
    price = md["BTC"]["price"]
    hi60 = max(r["h"] for r in d[-60:])
    dd = 1 - price / hi60
    tier = memo.get("tier", 0)
    ref = memo.get("ref_high", hi60)
    if tier and price >= ref * 0.95:
        tier = 0  # recovered: take profit
    else:
        new = 3 if dd >= 0.35 else 2 if dd >= 0.25 else 1 if dd >= 0.15 else 0
        if new > tier:
            if tier == 0:
                ref = hi60
            tier = new
    memo["tier"], memo["ref_high"] = tier, ref
    nxt = {0: 0.15, 1: 0.25, 2: 0.35}.get(tier)
    memo["levels"] = ([{"name": f"crash buy tier {tier + 1}", "asset": "BTC",
                        "price": hi60 * (1 - nxt), "dir": "below"}] if nxt else []) + (
        [{"name": "crash take profit", "asset": "BTC", "price": ref * 0.95, "dir": "above"}]
        if tier else [])
    memo["why"] = (f"BTC {dd * 100:.0f}% below 60d high ${hi60:,.0f}; holding {tier}/3, "
                   + (f"next buy at {nxt * 100:.0f}% down (${hi60 * (1 - nxt):,.0f}), " if nxt else "")
                   + f"sells at ${ref * 0.95:,.0f}" if tier else
                   f"BTC {dd * 100:.0f}% below 60d high ${hi60:,.0f}; first buy at 15% down "
                   f"(${hi60 * 0.85:,.0f})")
    return {"BTC": tier / 3} if tier else {}


def trw_tpi(md, memo):
    """Trend Probability Indicator in the style taught by The Real World investing campus:
    8 independent trend signals on BTC daily each vote +1/-1; hold BTC while the average > 0."""
    d = done(md["BTC"]["1d"])
    c = closes(d)
    e12, e26 = ema_series(c, 12), ema_series(c, 26)
    macd = [a - b for a, b in zip(e12, e26)]
    sig = ema_series(macd, 9)
    hi20, lo20 = max(r["h"] for r in d[-20:]), min(r["l"] for r in d[-20:])
    votes = {
        "price>EMA21": c[-1] > ema_series(c, 21)[-1],
        "price>SMA50": c[-1] > sma(c, 50),
        "EMA9>EMA21": ema_series(c, 9)[-1] > ema_series(c, 21)[-1],
        "MACD>signal": macd[-1] > sig[-1],
        "RSI>50": rsi(c[-120:], 14) > 50,
        "14d ROC>0": c[-1] > c[-15],
        "upper half of 20d range": c[-1] > (hi20 + lo20) / 2,
        "SMA20 rising": sma(c, 20) > sma(c[:-5], 20),
    }
    tpi = sum(1 if v else -1 for v in votes.values()) / len(votes)
    memo["tpi"] = tpi
    bulls = [k for k, v in votes.items() if v]
    e21 = ema_series(c, 21)[-1]
    up = c[-1] > e21
    memo["levels"] = [{"name": "TPI: EMA21 " + ("lost" if up else "reclaimed"), "asset": "BTC",
                       "price": e21, "dir": "below" if up else "above"}]
    memo["why"] = (f"TPI {tpi:+.2f} (long while > 0). Bullish: "
                   f"{', '.join(bulls) if bulls else 'none'}. Key levels: EMA21 ${e21:,.0f}, "
                   f"20d midpoint ${(hi20 + lo20) / 2:,.0f}, SMA50 ${sma(c, 50):,.0f}")
    return {"BTC": 1.0} if tpi > 0 else {}


def trw_box(md, memo):
    """Box breakout in the style of The Real World trading campus: on daily charts, a box is the
    last 20 days of consolidation (range under 30%). Enter on a daily close above the box top,
    only in a trend (price > 50 SMA and EMA9 > EMA21). Stop at box middle; size the position so a
    stop-out costs 3% of the account. Exit at the stop or a daily close below EMA21.
    Runs on BTC, ETH, SOL independently."""
    w, why, levels = {}, [], []
    risk = 0.03
    for a in ("BTC", "ETH", "SOL"):
        d = done(md[a]["1d"])
        c = closes(d)
        price = md[a]["price"]
        e9, e21 = ema_series(c, 9)[-1], ema_series(c, 21)[-1]
        pos = memo.get(a)
        if pos:
            if price < pos["stop"] or c[-1] < e21:
                memo[a] = pos = None
            else:
                w[a] = pos["w"]
                why.append(f"{a} in {pos['w'] * 100:.0f}%, stop ${pos['stop']:,.2f}")
                continue
        box = d[-21:-1]
        top, bot = max(r["h"] for r in box), min(r["l"] for r in box)
        levels.append({"name": "box top breakout", "asset": a, "price": top, "dir": "above"})
        tight = top / bot - 1 < 0.30
        trend = c[-1] > sma(c, 50) and e9 > e21
        if c[-1] > top and tight and trend:
            stop = (top + bot) / 2
            size = min(1 / 3, risk / max(1 - stop / price, 0.01))  # 1/3 cap: three coins share
            memo[a] = {"stop": stop, "w": size, "entry": price}
            w[a] = size
            why.append(f"{a} broke out, {size * 100:.0f}% in, stop ${stop:,.2f}")
        else:
            need = [f"close > box top ${top:,.2f}"] if c[-1] <= top else []
            if not trend:
                need.append("uptrend (>50SMA, EMA9>21)")
            if not tight:
                need.append("tighter box")
            why.append(f"{a} needs {' + '.join(need)}")
    memo["why"] = "; ".join(why)
    memo["stops"] = {a: memo[a]["stop"] for a in w if memo.get(a)}
    memo["levels"] = levels
    return w


def vol_target(md, memo):  # noqa: C901
    """Volatility-targeted trend on BTC + ETH. Each coin gets up to half the account,
    only if its 30-day return is positive, scaled by 50% / realised 20-day annual vol."""
    w, why = {}, []
    for a in ("BTC", "ETH"):
        c = closes(done(md[a]["1d"]))
        if c[-1] / c[-31] - 1 <= 0:
            why.append(f"{a} 30d return {pct(c[-1] / c[-31] - 1)} (needs > 0)")
            continue
        rets = [math.log(b / a_) for a_, b in zip(c[-21:-1], c[-20:])]
        vol = stdev(rets) * math.sqrt(365)
        w[a] = 0.5 * min(1.0, 0.50 / max(vol, 1e-9))
        why.append(f"{a} long {w[a] * 100:.0f}% (vol {vol * 100:.0f}%)")
    memo["why"] = "; ".join(why)
    return w


from crt_live import crt_btc, LIVE_CFG  # noqa: E402
from ml_live import ml_predictor  # noqa: E402
from quick_live import quick_trader  # noqa: E402

STRATEGIES = [
    # id, name, function, short thesis, assets used
    ("hodl_btc", "Buy & Hold BTC (benchmark)", hodl_btc,
     "The bar every active strategy must beat after fees.", ["BTC"]),
    ("trw_tpi", "TRW style TPI trend (BTC)", trw_tpi,
     "8 trend indicators vote; long BTC while the average is positive.", ["BTC"]),
    ("trw_box", "TRW style box breakout (BTC/ETH/SOL)", trw_box,
     "Buy consolidation breakouts in uptrends, 3% account risk per trade.", ["BTC", "ETH", "SOL"]),
    ("ema_cross_6h", "EMA 9/21 crossover (ETH 6h)", ema_cross_6h,
     "Faster momentum signal, similar to MACD. More trades, reacts quicker.", ["ETH"]),
    ("dca_btc", "Daily DCA into BTC (30 days)", dca_btc,
     "Drip the $100 in about $3 a day. Lump sum vs DCA, settled with data.", ["BTC"]),
    ("crash_buyer", "Crash buyer (BTC, buys in thirds)", crash_buyer,
     "Contrarian: buys 15/25/35% drawdowns, sells on recovery.", ["BTC"]),
    ("rsi_reversion", "RSI dip buyer (BTC 1h)", rsi_reversion,
     "Short term mean reversion: buys oversold hours in any market, 6% stop.", ["BTC"]),
    ("bollinger", "Bollinger band reversion (SOL 1h)", bollinger_reversion,
     "Buys statistically stretched drops on a volatile coin.", ["SOL"]),
    ("momentum_rotation", "Dual momentum rotation (top 3 of 8)", momentum_rotation,
     "Weekly rotation into the strongest coins; cash if nothing is rising.", None),
    ("grid_eth", "Grid trader (ETH ±10%)", grid_eth,
     "Profits from chop: buys every dip level, sells every rip level.", ["ETH"]),
    ("crt_btc", "CRT (Candle Range Theory) on BTC", crt_btc,
     "Sweep of a candle's range, rejection, then trade back through it. Resting orders.", ["BTC"]),
    ("ml_predictor", "AI predictor (8 coins, hourly)", ml_predictor,
     "ML model predicts win/loss odds every hour; trades only when the edge beats fees. TP/SL on every trade.",
     None),
    ("quick_trader", "Quick 1h long/short (AI + CRT, perp-style)", quick_trader,
     "Every hour bets for OR against each coin for the next hour when expected value beats fees. Stop-loss and take-profit on every trade.",
     None),
]
