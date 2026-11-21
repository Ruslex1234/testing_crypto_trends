"""AI predictor: gradient-boosted trees that estimate, every hour, the probability that a long trade
hits its take-profit before its stop-loss within the next HORIZON hours.

Design follows the evidence (e.g. Bysik & Slepaczuk 2026, hourly BTC, walk-forward): naive
"trade every prediction" strategies lose to fees; a cost-aware filter that only trades when the
expected value clears costs is what can survive. So:
  * label  = triple barrier: TP = K_TP x ATR, SL = K_SL x ATR, timeout after HORIZON hours.
             Same-candle TP and SL counts as a loss (conservative).
  * model  = HistGradientBoostingClassifier on ~20 chart features (only past data, no lookahead).
  * trade  = only if p x reward - (1 - p) x risk - costs > margin, all in R units.
Features use simple moving windows (no long EMA warm-ups) so training on years of history and
predicting from the last 300 hours produce identical numbers.
"""
import csv
import math
import os

import numpy as np

HORIZON = 24          # hours a prediction/trade lives
K_SL = 4.0            # stop = 4 x ATR(14h) below entry
K_TP = 8.0            # take-profit = 8 x ATR(14h) above entry (2:1)
FEE_RT = 0.009        # round trip retail spot: 0.4% x 2 + slippage
MIN_HIST = 210        # bars needed before features are valid
COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK"]
FEATURES = ["r1", "r3", "r6", "r12", "r24", "r72", "r168", "rsi14", "atr_pct", "vol_ratio",
            "d_sma20", "d_sma50", "d_sma200", "pos24", "pos168", "dd168", "vz24",
            "hour_sin", "hour_cos", "dow", "btc_r24", "btc_r168"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "ml")


# ---------------- data ----------------
def load_cache(coin):
    p = os.path.join(CACHE, f"{coin}_1h.csv")
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return [{"t": int(r["t"]), "o": float(r["o"]), "h": float(r["h"]), "l": float(r["l"]),
                 "c": float(r["c"]), "v": float(r["v"])} for r in csv.DictReader(f)]


def merge(*series):
    m = {}
    for s in series:
        for r in s:
            m[r["t"]] = r
    return [m[t] for t in sorted(m)]


def _roll(x, n, fn):
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    w = np.lib.stride_tricks.sliding_window_view(x, n)
    out[n - 1:] = fn(w, axis=1)
    return out


def features(rows, btc_rows=None):
    """Feature matrix (len(rows) x len(FEATURES)); rows before MIN_HIST are NaN."""
    t = np.array([r["t"] for r in rows], dtype=np.int64)
    o, h, l, c, v = (np.array([r[k] for r in rows], dtype=float) for k in "ohlcv")
    prev = np.concatenate([[c[0]], c[:-1]])
    tr = np.maximum(h - l, np.maximum(abs(h - prev), abs(l - prev)))
    atr = _roll(tr, 14, np.mean)
    lr = np.diff(np.log(c), prepend=np.log(c[0]))

    def ret(n):
        out = np.full(len(c), np.nan)
        out[n:] = c[n:] / c[:-n] - 1
        return out

    up = np.maximum(np.diff(c, prepend=c[0]), 0)
    dn = np.maximum(-np.diff(c, prepend=c[0]), 0)
    ag, al = _roll(up, 14, np.mean), _roll(dn, 14, np.mean)
    rsi = 100 - 100 / (1 + ag / np.where(al == 0, 1e-12, al))
    vol24, vol168 = _roll(lr, 24, np.std), _roll(lr, 168, np.std)
    sma = {n: _roll(c, n, np.mean) for n in (20, 50, 200)}
    hi24, lo24 = _roll(h, 24, np.max), _roll(l, 24, np.min)
    hi168, lo168 = _roll(h, 168, np.max), _roll(l, 168, np.min)
    lv = np.log1p(v)
    vz = (lv - _roll(lv, 24, np.mean)) / (_roll(lv, 24, np.std) + 1e-9)
    hrs = (t // 3600) % 24
    dow = (t // 86400 + 4) % 7
    F = {
        "r1": ret(1), "r3": ret(3), "r6": ret(6), "r12": ret(12), "r24": ret(24),
        "r72": ret(72), "r168": ret(168), "rsi14": rsi, "atr_pct": atr / c,
        "vol_ratio": vol24 / (vol168 + 1e-12),
        "d_sma20": (c - sma[20]) / atr, "d_sma50": (c - sma[50]) / atr, "d_sma200": (c - sma[200]) / atr,
        "pos24": (c - lo24) / (hi24 - lo24 + 1e-12), "pos168": (c - lo168) / (hi168 - lo168 + 1e-12),
        "dd168": c / hi168 - 1, "vz24": vz,
        "hour_sin": np.sin(2 * math.pi * hrs / 24), "hour_cos": np.cos(2 * math.pi * hrs / 24),
        "dow": dow.astype(float),
    }
    if btc_rows is not None:
        bmap = {r["t"]: r["c"] for r in btc_rows}
        bc = np.array([bmap.get(x, np.nan) for x in t])
        b24, b168 = np.full(len(c), np.nan), np.full(len(c), np.nan)
        b24[24:] = bc[24:] / bc[:-24] - 1
        b168[168:] = bc[168:] / bc[:-168] - 1
        F["btc_r24"], F["btc_r168"] = b24, b168
    else:
        F["btc_r24"], F["btc_r168"] = ret(24), ret(168)
    X = np.column_stack([F[k] for k in FEATURES])
    X[:MIN_HIST] = np.nan
    return X, t, c, atr


def labels(rows, c, atr):
    """Triple-barrier outcome for a long entered at each candle's close.
    Returns (win 0/1 or -1 if unknown yet, realised R before costs, sl_pct, bars until exit)."""
    h = np.array([r["h"] for r in rows]); l = np.array([r["l"] for r in rows])
    n = len(c)
    win = np.full(n, -1)
    rr = np.full(n, np.nan)
    hold = np.full(n, HORIZON)
    sl_pct = K_SL * atr / c
    for i in range(n - HORIZON):
        if not np.isfinite(sl_pct[i]):
            continue
        e = c[i]
        sl, tp = e * (1 - sl_pct[i]), e * (1 + sl_pct[i] * K_TP / K_SL)
        hh, ll = h[i + 1:i + 1 + HORIZON], l[i + 1:i + 1 + HORIZON]
        hit_sl = np.flatnonzero(ll <= sl)
        hit_tp = np.flatnonzero(hh >= tp)
        fs = hit_sl[0] if len(hit_sl) else HORIZON
        ft = hit_tp[0] if len(hit_tp) else HORIZON
        if ft < fs:
            win[i], rr[i], hold[i] = 1, K_TP / K_SL, ft + 1
        elif fs < HORIZON:
            win[i], rr[i], hold[i] = 0, -1.0, fs + 1
        else:
            win[i] = 0
            rr[i] = (c[i + HORIZON] / e - 1) / sl_pct[i]
    return win, rr, sl_pct, hold


def dataset(series):
    """series: {coin: rows}. Returns stacked arrays incl. coin index and timestamps."""
    btc = series.get("BTC")
    Xs, ys, rs, ts, cs, sls, prices, holds = [], [], [], [], [], [], [], []
    for ci, (coin, rows) in enumerate(series.items()):
        if len(rows) < MIN_HIST + HORIZON + 10:
            continue
        X, t, c, atr = features(rows, btc)
        y, r, sl, hd = labels(rows, c, atr)
        Xs.append(X); ys.append(y); rs.append(r); ts.append(t); sls.append(sl); prices.append(c)
        holds.append(hd)
        cs.append(np.full(len(t), ci))
    return (np.vstack(Xs), np.concatenate(ys), np.concatenate(rs), np.concatenate(ts),
            np.concatenate(cs), np.concatenate(sls), np.concatenate(prices), np.concatenate(holds))


def make_model():
    from sklearn.ensemble import HistGradientBoostingClassifier
    return HistGradientBoostingClassifier(max_iter=250, learning_rate=0.04, max_leaf_nodes=15,
                                          min_samples_leaf=200, l2_regularization=1.0,
                                          random_state=7)


def ev_r(p, sl_pct):
    """Expected R of a trade given win probability p (TP = 2R, SL = -1R, costs in R)."""
    return p * (K_TP / K_SL) - (1 - p) * 1.0 - FEE_RT / sl_pct


def train(X, y, t, until):
    """Fit on samples whose outcome was fully known before `until` (purged: entry <= until - HORIZON)."""
    m = (y >= 0) & np.all(np.isfinite(X), axis=1) & (t <= until - HORIZON * 3600)
    model = make_model()
    model.fit(X[m], y[m])
    return model, int(m.sum())
