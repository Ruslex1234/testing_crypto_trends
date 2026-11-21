"""Quick trades: 1 hour long OR short, decided every hour from 15 minute candles.

For each coin and each hour, two 3-class models (one for LONG, one for SHORT) estimate
P(take-profit first), P(stop-loss first), P(neither within the hour). Expected value in R:
    EV = P(tp) x RR - P(sl) x 1 + P(timeout) x avg_timeout_R - costs
A trade is opened on the better side only if its EV beats the walk-forward margin.
Features include Candle Range Theory signals (sweep of the previous 1h / 4h candle's high or low
with a close back inside) plus momentum, volatility, range position and BTC context.
Costs: perpetual-futures style, ~0.12% round trip (maker entries/targets, taker stops + slippage).
"""
import json
import math
import time
import urllib.request
from datetime import datetime, timezone

import numpy as np

COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK"]
BAR = 900                 # 15 minute candles
HOLD = 4                  # bars = 1 hour
K_SL = 1.5                # stop = 1.5 x ATR(14 x 15m)
RR = 1.5                  # take-profit = 1.5 x stop distance
FEE_RT = 0.0012           # round trip, perp-style
TRAIN_DAYS = 14           # the "last 2 weeks" window
MIN_HIST = 100
FEATURES = ["r1", "r2", "r4", "r8", "r16", "r32", "r96", "rsi14", "atr_pct", "vol_ratio",
            "d_sma20", "d_sma50", "pos16", "pos96", "vz16", "hour_sin", "hour_cos",
            "btc_r4", "btc_r16", "crt1h", "crt1h_pos", "crt1h_dh", "crt1h_dl",
            "crt4h", "crt4h_pos"]


def fetch_15m(coin, days):
    """Completed 15m candles from Coinbase, oldest first."""
    end = int(time.time()) // BAR * BAR
    t = end - days * 86400
    rows = {}
    while t < end:
        t2 = min(t + 300 * BAR, end)
        iso = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        url = (f"https://api.exchange.coinbase.com/products/{coin}-USD/candles"
               f"?granularity={BAR}&start={iso(t)}&end={iso(t2)}")
        for i in range(4):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "paper-trader-bot/1.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = json.loads(r.read().decode())
                break
            except Exception:  # noqa: BLE001
                time.sleep(2 * (i + 1))
        else:
            raise RuntimeError(f"fetch failed {coin}")
        for r in data:
            if int(r[0]) + BAR <= end:
                rows[int(r[0])] = {"t": int(r[0]), "o": r[3], "h": r[2], "l": r[1], "c": r[4], "v": r[5]}
        t = t2
        time.sleep(0.2)
    return [rows[k] for k in sorted(rows)]


def _roll(x, n, fn):
    out = np.full(len(x), np.nan)
    if len(x) >= n:
        out[n - 1:] = fn(np.lib.stride_tricks.sliding_window_view(x, n), axis=1)
    return out


def _crt(h, l, c, t, span):
    """CRT on `span`-bar candles built from completed 15m bars: at each bar, compare the last
    completed big candle (C1) with the one before (C0). +1 = swept C0 low and closed back inside,
    -1 = swept C0 high and closed back inside. Also price position in C0 and distances."""
    n = len(c)
    sig, pos, dh, dl = (np.full(n, np.nan) for _ in range(4))
    sec = span * BAR
    grp = t // sec
    agg = {}
    for i in range(n):
        g = agg.setdefault(grp[i], [h[i], l[i], c[i], 0])
        g[0], g[1], g[2], g[3] = max(g[0], h[i]), min(g[1], l[i]), c[i], g[3] + 1
    for i in range(n):
        last_done = grp[i] if (t[i] + BAR) % sec == 0 else grp[i] - 1
        g1, g0 = agg.get(last_done), agg.get(last_done - 1)
        if not g1 or not g0 or g1[3] < span or g0[3] < span:
            continue
        H0, L0 = g0[0], g0[1]
        H1, L1, C1 = g1[0], g1[1], g1[2]
        sig[i] = 1.0 if (L1 < L0 and L0 < C1 < H0) else -1.0 if (H1 > H0 and L0 < C1 < H0) else 0.0
        pos[i] = (c[i] - L0) / (H0 - L0 + 1e-12)
        dh[i] = (H0 - c[i]) / c[i]
        dl[i] = (c[i] - L0) / c[i]
    return sig, pos, dh, dl


def features(rows, btc_rows=None):
    t = np.array([r["t"] for r in rows], dtype=np.int64)
    o, h, l, c, v = (np.array([float(r[k]) for r in rows]) for k in "ohlcv")
    prev = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(abs(h - prev), abs(l - prev)))
    atr = _roll(tr, 14, np.mean)
    lr = np.diff(np.log(c), prepend=np.log(c[0]))

    def ret(n):
        out = np.full(len(c), np.nan)
        out[n:] = c[n:] / c[:-n] - 1
        return out
    d = np.diff(c, prepend=c[0])
    ag, al = _roll(np.maximum(d, 0), 14, np.mean), _roll(np.maximum(-d, 0), 14, np.mean)
    rsi = 100 - 100 / (1 + ag / np.where(al == 0, 1e-12, al))
    hi16, lo16 = _roll(h, 16, np.max), _roll(l, 16, np.min)
    hi96, lo96 = _roll(h, 96, np.max), _roll(l, 96, np.min)
    lv = np.log1p(v)
    hrs = ((t + BAR) // 3600) % 24
    c1, p1, dh1, dl1 = _crt(h, l, c, t, 4)
    c4, p4, _, _ = _crt(h, l, c, t, 16)
    F = {"r1": ret(1), "r2": ret(2), "r4": ret(4), "r8": ret(8), "r16": ret(16), "r32": ret(32),
         "r96": ret(96), "rsi14": rsi, "atr_pct": atr / c,
         "vol_ratio": _roll(lr, 16, np.std) / (_roll(lr, 96, np.std) + 1e-12),
         "d_sma20": (c - _roll(c, 20, np.mean)) / atr, "d_sma50": (c - _roll(c, 50, np.mean)) / atr,
         "pos16": (c - lo16) / (hi16 - lo16 + 1e-12), "pos96": (c - lo96) / (hi96 - lo96 + 1e-12),
         "vz16": (lv - _roll(lv, 16, np.mean)) / (_roll(lv, 16, np.std) + 1e-9),
         "hour_sin": np.sin(2 * math.pi * hrs / 24), "hour_cos": np.cos(2 * math.pi * hrs / 24),
         "crt1h": c1, "crt1h_pos": p1, "crt1h_dh": dh1, "crt1h_dl": dl1, "crt4h": c4, "crt4h_pos": p4}
    if btc_rows is not None:
        bm = {r["t"]: float(r["c"]) for r in btc_rows}
        bc = np.array([bm.get(x, np.nan) for x in t])
        F["btc_r4"], F["btc_r16"] = np.full(len(c), np.nan), np.full(len(c), np.nan)
        F["btc_r4"][4:] = bc[4:] / bc[:-4] - 1
        F["btc_r16"][16:] = bc[16:] / bc[:-16] - 1
    else:
        F["btc_r4"], F["btc_r16"] = ret(4), ret(16)
    X = np.column_stack([F[k] for k in FEATURES])
    X[:MIN_HIST] = np.nan
    return X, t, c, atr, h, l


def outcome(side, i, c, atr, h, l):
    """Triple barrier for a trade entered at close of bar i. Returns (class, R before costs,
    sl_pct): class 0 = take-profit, 1 = stop, 2 = timeout. Same-bar TP and SL = stop."""
    sl_pct = K_SL * atr[i] / c[i]
    e = c[i]
    sl = e * (1 - side * sl_pct)
    tp = e * (1 + side * sl_pct * RR)
    for j in range(i + 1, i + 1 + HOLD):
        hit_sl = l[j] <= sl if side == 1 else h[j] >= sl
        hit_tp = h[j] >= tp if side == 1 else l[j] <= tp
        if hit_sl:
            return 1, -1.0, sl_pct
        if hit_tp:
            return 0, RR, sl_pct
    return 2, side * (c[i + HOLD] / e - 1) / sl_pct, sl_pct


def dataset(series):
    """Hourly decision points (bars whose close lands on :15) for all coins."""
    btc = series.get("BTC")
    out = {k: [] for k in ("X", "t", "coin", "yl", "rl", "ys", "rs", "slp", "price")}
    for ci, (cn, rows) in enumerate(series.items()):
        X, t, c, atr, h, l = features(rows, btc)
        for i in range(len(c)):
            if (t[i] + BAR) % 3600 != BAR or not np.all(np.isfinite(X[i])):
                continue  # decide once an hour, at the close of the hh:00-hh:15 bar
            if i + HOLD < len(c):
                yl, rl, sp = outcome(1, i, c, atr, h, l)
                ys, rs, _ = outcome(-1, i, c, atr, h, l)
            else:
                yl = ys = -1
                rl = rs = np.nan
                sp = K_SL * atr[i] / c[i]
            for k, val in (("X", X[i]), ("t", t[i] + BAR), ("coin", ci), ("yl", yl), ("rl", rl),
                           ("ys", ys), ("rs", rs), ("slp", sp), ("price", c[i])):
                out[k].append(val)
    return {k: np.array(v) for k, v in out.items()}


def fit(D, until, days=TRAIN_DAYS):
    """Two 3-class models trained on decisions whose 1h outcome was known before `until`.
    days=None means use all history."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    m = (D["yl"] >= 0) & (D["t"] + HOLD * BAR <= until)
    if days:
        m &= D["t"] >= until - days * 86400
    models = {}
    for side, y, r in ((1, "yl", "rl"), (-1, "ys", "rs")):
        mdl = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.05, max_leaf_nodes=15,
                                             min_samples_leaf=40, l2_regularization=1.0, random_state=7)
        mdl.fit(D["X"][m], D[y][m].astype(int))
        to = D[r][m][D[y][m] == 2]
        models[side] = (mdl, float(to.mean()) if len(to) else 0.0)
    return models, int(m.sum())


def predict_ev(models, X, slp):
    """EV in R (after costs) for long and short, plus class probabilities."""
    out = {}
    for side, (mdl, to_r) in models.items():
        pr = np.zeros((len(X), 3))
        pr[:, mdl.classes_.astype(int)] = mdl.predict_proba(X)
        ev = pr[:, 0] * RR - pr[:, 1] + pr[:, 2] * to_r - FEE_RT / slp
        out[side] = (ev, pr)
    return out
