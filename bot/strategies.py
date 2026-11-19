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


def done(rows):
    return rows[:-1]


# ---------- strategies ----------
def hodl_btc(md, memo):
    """Benchmark: buy BTC once, never sell."""
    return {"BTC": 1.0}


def trend_sma50(md, memo):
    """Time-series momentum: hold BTC while last daily close > 50-day SMA, else cash."""
    c = closes(done(md["BTC"]["1d"]))
    return {"BTC": 1.0} if c[-1] > sma(c, 50) else {}


def ema_cross_6h(md, memo):
    """ETH on 6h candles: long when EMA(9) > EMA(21) (MACD-style momentum), else cash."""
    c = closes(done(md["ETH"]["6h"]))
    fast, slow = ema_series(c, 9)[-1], ema_series(c, 21)[-1]
    return {"ETH": 1.0} if fast > slow else {}


def donchian_turtle(md, memo):
    """Turtle-style breakout on BTC and ETH daily: enter on 20-day high, exit on 10-day low.
    Half the account is allocated to each coin."""
    w = {}
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
        if inpos:
            w[a] = 0.5
    return w


def rsi_reversion(md, memo):
    """BTC hourly mean reversion: buy when RSI(14) < 30, exit when RSI > 55
    or a 6% stop loss from entry is hit. Only buys dips while price is above
    the 200-hour SMA (don't catch knives in a downtrend)."""
    c = closes(done(md["BTC"]["1h"]))
    r = rsi(c[-120:], 14)
    price = md["BTC"]["price"]
    inpos = memo.get("in", False)
    if not inpos and r < 30 and c[-1] > sma(c, 200):
        inpos, memo["entry"] = True, price
    elif inpos and (r > 55 or price < memo.get("entry", price) * 0.94):
        inpos = False
    memo["in"] = inpos
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
    return {"SOL": 1.0} if inpos else {}


def momentum_rotation(md, memo, now=None):
    """Cross-sectional + absolute ('dual') momentum across 8 large coins.
    Every 7 days: rank by 14-day return, hold the top 3 equally, but only those
    with a positive return. Otherwise cash."""
    last = memo.get("last_rebalance", 0)
    if now is not None and now - last < 7 * 86400 and "weights" in memo:
        return memo["weights"]
    scores = {}
    for a, d in md.items():
        c = closes(done(d["1d"]))
        if len(c) > 15:
            scores[a] = c[-1] / c[-15] - 1
    top = sorted(scores, key=scores.get, reverse=True)[:3]
    w = {a: 1 / 3 for a in top if scores[a] > 0}
    memo["weights"], memo["last_rebalance"], memo["scores"] = w, now or 0, {
        a: round(s, 4) for a, s in scores.items()}
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
    return {"ETH": cur / levels}


def vol_target(md, memo):
    """Volatility-targeted trend on BTC + ETH. Each coin gets up to half the account,
    only if its 30-day return is positive, scaled by 50% / realised 20-day annual vol."""
    w = {}
    for a in ("BTC", "ETH"):
        c = closes(done(md[a]["1d"]))
        if c[-1] / c[-31] - 1 <= 0:
            continue
        rets = [math.log(b / a_) for a_, b in zip(c[-21:-1], c[-20:])]
        vol = stdev(rets) * math.sqrt(365)
        w[a] = 0.5 * min(1.0, 0.50 / max(vol, 1e-9))
    return w


STRATEGIES = [
    # id, name, function, short thesis, assets used
    ("hodl_btc", "Buy & Hold BTC (benchmark)", hodl_btc,
     "The bar every active strategy must beat after fees.", ["BTC"]),
    ("trend_sma50", "Trend: BTC above 50 day SMA", trend_sma50,
     "Time series momentum. Rides bull runs, sits in cash during crashes.", ["BTC"]),
    ("ema_cross_6h", "EMA 9/21 crossover (ETH 6h)", ema_cross_6h,
     "Faster momentum signal, similar to MACD. More trades, reacts quicker.", ["ETH"]),
    ("donchian", "Turtle breakout 20/10 (BTC+ETH)", donchian_turtle,
     "Classic channel breakout. Buys new highs, cuts on new lows.", ["BTC", "ETH"]),
    ("rsi_reversion", "RSI dip buyer (BTC 1h)", rsi_reversion,
     "Short term mean reversion: buy oversold dips in an uptrend.", ["BTC"]),
    ("bollinger", "Bollinger band reversion (SOL 1h)", bollinger_reversion,
     "Buys statistically stretched drops on a volatile coin.", ["SOL"]),
    ("momentum_rotation", "Dual momentum rotation (top 3 of 8)", momentum_rotation,
     "Weekly rotation into the strongest coins; cash if nothing is rising.", None),
    ("grid_eth", "Grid trader (ETH ±10%)", grid_eth,
     "Profits from chop: buys every dip level, sells every rip level.", ["ETH"]),
    ("vol_target", "Volatility targeted trend (BTC+ETH)", vol_target,
     "Trend filter plus risk sizing: smaller positions when markets are wild.", ["BTC", "ETH"]),
]
