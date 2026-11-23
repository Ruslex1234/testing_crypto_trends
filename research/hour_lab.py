"""Hour Lab: can we bet for or against each coin over the next hour and beat fees?

Inputs (all free, all historical, no lookahead):
  * Binance USDT perpetual 1h candles WITH taker buy volume (aggressive buyers vs sellers)
  * Binance futures metrics every 5 min: open interest, top trader and crowd long/short ratios,
    taker buy/sell volume ratio
  * Binance funding rates
  * S&P 500 futures hourly (Yahoo) for risk-on / risk-off spillover
  * price structure: returns, volatility, range position, CRT sweeps of the previous 1h / 4h candle
Falls back to Coinbase hourly price history (data/history) when Binance is unreachable.

Method: one gradient boosting model across 8 coins predicts the next hour's volatility-scaled return.
Walk forward: retrained every week on past data only. Thresholds come from the previous 30 days
of predictions only. Every rule is also scored on simple no-ML baselines with the same costs.
Positions: enter at the close, exit one hour later, optional stop inside the hour (assumed hit first).

Writes docs/hourlab/{results.json, REPORT.md, live_config.json}; caches data in data/hourlab.
Run: python3 research/hour_lab.py [--offline]
"""
import concurrent.futures as cf
import csv
import gzip
import io
import json
import math
import os
import sys
import time
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "research"))
CACHE = os.path.join(ROOT, "data", "hourlab")
OUT = os.path.join(ROOT, "docs", "hourlab")
COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK"]
BV = "https://data.binance.vision/data/futures/um"
DAYS = 730
COSTS = {"0.04% (perp maker both sides)": 0.0004, "0.08% (maker in, taker out)": 0.0008,
         "0.12% (perp taker both sides)": 0.0012, "0.20% (taker + slippage)": 0.0020}
DECIDE_COST = 0.0008  # realistic target for a small account on a low fee perp venue
STOPS = {"no stop": None, "stop 2x hourly vol": 2.0, "stop 3x hourly vol": 3.0}
QUANTS = [0.0, 0.8, 0.9, 0.95, 0.98, 0.99]
SLOT_USD = 125  # $1,000 account split into 8 slots, 1x leverage


# ----------------------------------------------------------------------------- download
def _fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-bot/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            err = e
        except Exception as e:  # noqa: BLE001
            err = e
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


def _zip_rows(blob):
    if not blob:
        return []
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        txt = z.read(z.namelist()[0]).decode()
    rows = list(csv.reader(io.StringIO(txt)))
    return [r for r in rows if r and r[0][:1].isdigit()]  # drop header rows if present


def _months(start, end):
    y, m = start.year, start.month
    while (y, m) < (end.year, end.month):
        yield f"{y}-{m:02d}"
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def _load_gz(path):
    if not os.path.exists(path):
        return []
    with gzip.open(path, "rt") as f:
        return [[float(x) for x in r] for r in csv.reader(f)]


def _save_gz(path, rows):
    with gzip.open(path, "wt") as f:
        csv.writer(f).writerows(rows)


def update_binance(coin, pool):
    """Hourly klines [t,o,h,l,c,v,qv,n,tbv], hourly metrics, funding. Cached; only new days fetched."""
    sym = f"{coin}USDT"
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=DAYS)
    out = {}
    # klines: monthly archives for full months, daily for the current month
    kp = os.path.join(CACHE, f"{coin}_k.csv.gz")
    have = {int(r[0]): r for r in _load_gz(kp)}
    last = max(have) if have else 0
    jobs = []
    for mo in _months(start, today.replace(day=1)):
        y, m = map(int, mo.split("-"))
        if datetime(y, m, 28, tzinfo=timezone.utc).timestamp() > last:
            jobs.append(f"{BV}/monthly/klines/{sym}/1h/{sym}-1h-{mo}.zip")
    d = max(today.replace(day=1), start)
    while d < today:
        if datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() + 86400 > last:
            jobs.append(f"{BV}/daily/klines/{sym}/1h/{sym}-1h-{d.isoformat()}.zip")
        d += timedelta(days=1)
    for rows in pool.map(lambda u: _zip_rows(_fetch(u)), jobs):
        for r in rows:
            t = int(r[0]) // 1000
            have[t] = [t, float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5]),
                       float(r[7]), float(r[8]), float(r[9])]
    k = [have[t] for t in sorted(have) if t >= datetime(start.year, start.month, start.day,
                                                         tzinfo=timezone.utc).timestamp()]
    _save_gz(kp, k)
    out["k"] = k
    # metrics: daily files of 5 min rows, aggregated to the last value inside each hour
    mp_ = os.path.join(CACHE, f"{coin}_m.csv.gz")
    mh = {int(r[0]): r for r in _load_gz(mp_)}
    mlast = max(mh) if mh else 0
    days = []
    d = start
    while d < today:
        if datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() + 86400 > mlast + 3600:
            days.append(d)
        d += timedelta(days=1)
    urls = [f"{BV}/daily/metrics/{sym}/{sym}-metrics-{x.isoformat()}.zip" for x in days]
    for rows in pool.map(lambda u: _zip_rows(_fetch(u)), urls):
        for r in rows:
            try:
                ts = int(datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp())
                vals = [float(x) if x not in ("", None) else float("nan") for x in r[2:8]]
            except (ValueError, IndexError):
                continue
            h = ts - ts % 3600
            prev = mh.get(h)
            if prev is None or ts >= prev[1]:
                mh[h] = [h, ts] + vals  # oi, oi_value, top_acct_ls, top_pos_ls, crowd_ls, taker_ls
    m = [mh[h] for h in sorted(mh)]
    _save_gz(mp_, m)
    out["m"] = m
    # funding: monthly + nothing else needed (8h cadence, archive lags a month: kept as known-at)
    fp = os.path.join(CACHE, f"{coin}_f.csv.gz")
    fh = {int(r[0]): r for r in _load_gz(fp)}
    flast = max(fh) if fh else 0
    jobs = [f"{BV}/monthly/fundingRate/{sym}/{sym}-fundingRate-{mo}.zip"
            for mo in _months(start, today.replace(day=1))
            if datetime(*map(int, mo.split("-")), 28, tzinfo=timezone.utc).timestamp() > flast]
    for rows in pool.map(lambda u: _zip_rows(_fetch(u)), jobs):
        for r in rows:
            t = int(r[0]) // 1000
            fh[t] = [t, float(r[2])]
    f = [fh[t] for t in sorted(fh)]
    _save_gz(fp, f)
    out["f"] = f
    return out


def yahoo_es():
    try:
        blob = _fetch("https://query1.finance.yahoo.com/v8/finance/chart/ES=F?interval=1h&range=730d")
        r = json.loads(blob)["chart"]["result"][0]
        ts, cl = r["timestamp"], r["indicators"]["quote"][0]["close"]
        rows = [[t - t % 3600, c] for t, c in zip(ts, cl) if c]
        _save_gz(os.path.join(CACHE, "ES_1h.csv.gz"), rows)
        return rows
    except Exception as e:  # noqa: BLE001
        print("ES fetch failed:", e)
        return _load_gz(os.path.join(CACHE, "ES_1h.csv.gz"))


def load_data(offline):
    os.makedirs(CACHE, exist_ok=True)
    data, source = {}, "binance"
    if not offline:
        try:
            with cf.ThreadPoolExecutor(24) as pool:
                for c in COINS:
                    t0 = time.time()
                    data[c] = update_binance(c, pool)
                    print(f"{c}: {len(data[c]['k'])} candles, {len(data[c]['m'])} metric hours, "
                          f"{len(data[c]['f'])} funding  ({time.time() - t0:.0f}s)", flush=True)
        except Exception as e:  # noqa: BLE001
            print("Binance download failed, falling back:", e)
            data = {}
    if not data or not data.get("BTC", {}).get("k"):
        cached = {c: {"k": _load_gz(os.path.join(CACHE, f"{c}_k.csv.gz")),
                      "m": _load_gz(os.path.join(CACHE, f"{c}_m.csv.gz")),
                      "f": _load_gz(os.path.join(CACHE, f"{c}_f.csv.gz"))} for c in COINS}
        if cached["BTC"]["k"]:
            data = cached
        else:
            import history
            source = "coinbase price only"
            cut = time.time() - DAYS * 86400
            data = {c: {"k": [[r["t"], r["o"], r["h"], r["l"], r["c"], r["v"], float("nan"), float("nan"),
                               float("nan")] for r in history.load(c) if r["t"] >= cut], "m": [], "f": []}
                    for c in COINS}
    es = _load_gz(os.path.join(CACHE, "ES_1h.csv.gz")) if offline else yahoo_es()
    return data, es, source


# ----------------------------------------------------------------------------- features
FEATS = ["r1", "r4", "r12", "r24", "r72", "z1", "z4", "vol24", "volratio", "rangepos", "dist_hi", "dist_lo",
         "taker1", "taker4", "taker24", "vz", "nz", "oi1", "oi4", "oi24", "oi_turn", "top_ls", "top_ls_d4",
         "crowd_ls", "crowd_ls_d4", "taker_ls", "fund", "fund_rel", "btc_r1", "btc_r4", "btc_taker1", "btc_oi1",
         "rel_btc4", "es_r1", "es_r4", "hour_sin", "hour_cos", "dow", "hour", "crt1", "crt4", "coin"]


def _roll_mean(x, w):
    c = np.cumsum(np.insert(np.nan_to_num(x), 0, 0.0))
    out = np.full_like(x, np.nan)
    out[w - 1:] = (c[w:] - c[:-w]) / w
    return out


def _roll_std(x, w):
    m = _roll_mean(x, w)
    m2 = _roll_mean(x * x, w)
    return np.sqrt(np.maximum(m2 - m * m, 0))


def _roll_max(x, w):
    from numpy.lib.stride_tricks import sliding_window_view
    out = np.full_like(x, np.nan)
    out[w - 1:] = sliding_window_view(x, w).max(axis=1)
    return out


def _roll_min(x, w):
    return -_roll_max(-x, w)


def _lag(x, k):
    out = np.full_like(x, np.nan)
    out[k:] = x[:-k]
    return out


def coin_frame(c, d, es_map):
    k = np.array(d["k"], dtype=float)
    k = k[np.argsort(k[:, 0])]
    t, o, h, l, cl, v, qv, n, tb = k.T
    # keep only hours with a contiguous previous hour (gaps make returns lie)
    lc = np.log(cl)
    F = {}
    for w in (1, 4, 12, 24, 72):
        F[f"r{w}"] = lc - _lag(lc, w)
    vol = _roll_std(F["r1"], 24)
    F["vol24"] = vol
    F["volratio"] = vol / _roll_std(F["r1"], 168)
    F["z1"] = F["r1"] / vol
    F["z4"] = F["r4"] / (vol * 2)
    hi24, lo24 = _roll_max(h, 24), _roll_min(l, 24)
    F["rangepos"] = (cl - lo24) / np.maximum(hi24 - lo24, 1e-12)
    F["dist_hi"] = np.log(hi24 / cl) / vol
    F["dist_lo"] = np.log(cl / lo24) / vol
    tr = tb / np.where(v > 0, v, np.nan)
    F["taker1"] = tr - 0.5
    F["taker4"] = _roll_mean(tr, 4) - 0.5
    F["taker24"] = _roll_mean(tr, 24) - 0.5
    lv = np.log(np.maximum(v, 1e-9))
    F["vz"] = (lv - _roll_mean(lv, 168)) / np.maximum(_roll_std(lv, 168), 1e-9)
    ln = np.log(np.maximum(n, 1))
    F["nz"] = (ln - _roll_mean(ln, 168)) / np.maximum(_roll_std(ln, 168), 1e-9)
    # metrics: the bucket for bar t (open) holds 5 min snapshots taken during that hour -> known at t+3600
    mm = {int(r[0]): r for r in d["m"]}
    M = np.array([mm.get(int(x), [x, 0] + [np.nan] * 6)[2:8] for x in t], dtype=float)
    oi = np.log(np.where(M[:, 0] > 0, M[:, 0], np.nan))
    F["oi1"], F["oi4"], F["oi24"] = oi - _lag(oi, 1), oi - _lag(oi, 4), oi - _lag(oi, 24)
    F["oi_turn"] = np.log(_roll_mean(qv, 24) / np.where(M[:, 1] > 0, M[:, 1], np.nan))
    F["top_ls"] = np.log(M[:, 3])
    F["top_ls_d4"] = F["top_ls"] - _lag(F["top_ls"], 4)
    F["crowd_ls"] = np.log(M[:, 4])
    F["crowd_ls_d4"] = F["crowd_ls"] - _lag(F["crowd_ls"], 4)
    F["taker_ls"] = np.log(M[:, 5])
    # funding known at decision time (t + 3600): latest settlement <= that
    fr = np.array(d["f"], dtype=float) if d["f"] else np.zeros((0, 2))
    if len(fr):
        idx = np.searchsorted(fr[:, 0], t + 3600, side="right") - 1
        F["fund"] = np.where(idx >= 0, fr[np.maximum(idx, 0), 1], np.nan)
    else:
        F["fund"] = np.full_like(t, np.nan)
    F["fund_rel"] = F["fund"] - _roll_mean(F["fund"], 720)
    # ES: last completed hourly close by decision time
    if es_map:
        es_t = np.array(sorted(es_map))
        es_c = np.log(np.array([es_map[x] for x in es_t]))
        j = np.searchsorted(es_t, t, side="right") - 1  # ES bar opened at <= t, closes by t+3600
        ok = (j >= 4) & (t - es_t[np.maximum(j, 0)] <= 3600)
        jj = np.maximum(j, 4)
        F["es_r1"] = np.where(ok, es_c[jj] - es_c[jj - 1], np.nan)
        F["es_r4"] = np.where(ok, es_c[jj] - es_c[jj - 4], np.nan)
    else:
        F["es_r1"] = F["es_r4"] = np.full_like(t, np.nan)
    hr = ((t + 3600) // 3600) % 24
    F["hour"] = hr
    F["hour_sin"], F["hour_cos"] = np.sin(2 * np.pi * hr / 24), np.cos(2 * np.pi * hr / 24)
    F["dow"] = ((t + 3600) // 86400 + 3) % 7
    # CRT: bar swept the previous bar's high (or low) and closed back inside its range
    ph, pl = _lag(h, 1), _lag(l, 1)
    F["crt1"] = np.where((l < pl) & (cl > pl) & (cl < ph), 1.0, np.where((h > ph) & (cl < ph) & (cl > pl), -1.0, 0.0))
    # 4h version on UTC aligned 4h blocks, only at the bar closing a block
    h4, l4 = _roll_max(h, 4), _roll_min(l, 4)
    c4 = cl
    ph4, pl4 = _lag(h4, 4), _lag(l4, 4)
    at_close = (((t + 3600) // 3600) % 4) == 0
    F["crt4"] = np.where(at_close & (l4 < pl4) & (c4 > pl4) & (c4 < ph4), 1.0,
                         np.where(at_close & (h4 > ph4) & (c4 < ph4) & (c4 > pl4), -1.0, 0.0))
    F["coin"] = np.full_like(t, COINS.index(c))
    # outcomes for the next hour
    nxt_c, nxt_h, nxt_l = np.append(cl[1:], np.nan), np.append(h[1:], np.nan), np.append(l[1:], np.nan)
    contiguous = np.append(t[1:] - t[:-1] == 3600, False)
    prev_ok = np.insert(t[1:] - t[:-1] == 3600, 0, False)
    return {"t": t, "c": cl, "F": F, "ret": nxt_c / cl - 1, "up": nxt_h / cl - 1, "dn": nxt_l / cl - 1,
            "ok": contiguous & prev_ok & np.isfinite(vol) & (vol > 0)}


def build(data, es):
    es_map = {int(r[0]): r[1] for r in es} if es else {}
    frames = {c: coin_frame(c, data[c], es_map) for c in COINS if data.get(c, {}).get("k")}
    b = frames["BTC"]
    bmap = {int(x): i for i, x in enumerate(b["t"])}
    rows = []
    for c, fr in frames.items():
        bi = np.array([bmap.get(int(x), -1) for x in fr["t"]])
        has = bi >= 0
        for name, src in (("btc_r1", "r1"), ("btc_r4", "r4"), ("btc_taker1", "taker1"), ("btc_oi1", "oi1")):
            fr["F"][name] = np.where(has, b["F"][src][np.maximum(bi, 0)], np.nan)
        fr["F"]["rel_btc4"] = fr["F"]["r4"] - fr["F"]["btc_r4"]
        X = np.column_stack([fr["F"][f] for f in FEATS])
        keep = fr["ok"] & np.isfinite(fr["ret"])
        idx = np.where(keep)[0]
        idx = idx[idx >= 200]
        rows.append((X[idx], fr["t"][idx], fr["ret"][idx], fr["up"][idx], fr["dn"][idx], fr["F"]["vol24"][idx],
                     np.full(len(idx), COINS.index(c))))
    X, t, ret, up, dn, vol, coin = (np.concatenate([r[i] for r in rows]) for i in range(7))
    o = np.argsort(t, kind="stable")
    return {"X": X[o], "t": t[o], "ret": ret[o], "up": up[o], "dn": dn[o], "vol": vol[o], "coin": coin[o]}


# ----------------------------------------------------------------------------- model
def walk_forward(D, warm_days=120, step_days=7):
    from sklearn.ensemble import HistGradientBoostingRegressor
    t, X = D["t"], D["X"]
    y = np.clip(D["ret"] / D["vol"], -6, 6)
    cols = usable_cols(X)
    X = X[:, cols]
    cat = [cols.index(FEATS.index("coin"))]
    pred = np.full(len(t), np.nan)
    start = t[0] + warm_days * 86400
    start -= start % 86400
    w = start
    nfit = 0
    while w <= t[-1]:
        tr = t + 7200 <= w  # outcome bar closed before the window starts
        tr &= t >= w - 365 * 86400  # last year only: market structure drifts
        te = (t >= w) & (t < w + step_days * 86400)
        if te.any() and tr.sum() > 5000:
            m = HistGradientBoostingRegressor(max_iter=250, learning_rate=0.04, max_leaf_nodes=24,
                                              min_samples_leaf=400, l2_regularization=1.0,
                                              categorical_features=cat, random_state=7)
            m.fit(X[tr], y[tr])
            pred[te] = m.predict(X[te])
            nfit += 1
        w += step_days * 86400
    print(f"walk forward: {nfit} weekly refits", flush=True)
    return pred


def usable_cols(X):
    """Columns with at least 2% filled values (offline runs have no Binance flow data)."""
    return [j for j in range(X.shape[1]) if np.isfinite(X[:, j]).mean() > 0.02
            and np.nanstd(X[:, j]) > 0]


# ----------------------------------------------------------------------------- evaluation
def rolling_threshold(t, score, q, look=30 * 86400):
    """For each sample, the q quantile of |score| over the previous 30 days (past only)."""
    if q <= 0:
        return np.zeros(len(t))
    days = (t // 86400).astype(int)
    thr = np.full(len(t), np.inf)
    ud = np.unique(days)
    a = np.abs(score)
    for d in ud:
        past = (days < d) & (days >= d - look // 86400) & np.isfinite(a)
        if past.sum() > 500:
            thr[days == d] = np.quantile(a[past], q)
    return thr


def pnl(D, side, cost, stop):
    r = side * D["ret"]
    if stop is not None:
        lvl = stop * D["vol"]  # vol is the std of hourly log returns, ~ fraction
        hit = np.where(side > 0, D["dn"] <= -lvl, D["up"] >= lvl)
        r = np.where(hit, -lvl, r)
    return r - cost


def summarize(D, take, side, cost, stop):
    sel = take & (side != 0) & np.isfinite(side)
    if sel.sum() == 0:
        return None
    r = pnl({k: v[sel] for k, v in D.items() if isinstance(v, np.ndarray) and v.ndim == 1}, side[sel], cost, stop)
    t = D["t"][sel]
    days = max((D["t"][-1] - D["t"][0]) / 86400, 1)
    half = D["t"][0] + (D["t"][-1] - D["t"][0]) / 2
    usd = r * SLOT_USD
    hours = {}
    for ti, u in zip(t, usd):
        hours[ti] = hours.get(ti, 0) + u
    eq = np.cumsum([hours[k] for k in sorted(hours)])
    dd = float(np.max(np.maximum.accumulate(np.insert(eq, 0, 0))[1:] - eq)) if len(eq) else 0
    daily = {}
    for ti, u in zip(t, usd):
        daily[int(ti // 86400)] = daily.get(int(ti // 86400), 0) + u
    dv = np.array(list(daily.values()))
    return {"trades": int(sel.sum()), "per_day": sel.sum() / days, "win": float((r > 0).mean()),
            "avg_bp": float(r.mean() * 1e4), "net_pct_sum": float(r.sum() * 100),
            "first_bp": float(r[t < half].mean() * 1e4) if (t < half).any() else None,
            "second_bp": float(r[t >= half].mean() * 1e4) if (t >= half).any() else None,
            "usd_day_1000": float(usd.sum() / days), "max_dd_usd_1000": dd,
            "pos_days": float((dv > 0).mean()) if len(dv) else None,
            "longs": int((side[sel] > 0).sum()), "shorts": int((side[sel] < 0).sum())}


def baselines(D):
    X = D["X"]
    f = {n: X[:, FEATS.index(n)] for n in FEATS}
    out = {
        "Momentum: follow last hour": np.sign(f["r1"]),
        "Reversal: fade last hour": -np.sign(f["r1"]),
        "Follow strong last hour (|z|>2)": np.where(np.abs(f["z1"]) > 2, np.sign(f["z1"]), 0),
        "Fade strong last hour (|z|>2)": np.where(np.abs(f["z1"]) > 2, -np.sign(f["z1"]), 0),
        "Taker flow: follow aggressive side": np.where(np.abs(f["taker1"]) > 0.05, np.sign(f["taker1"]), 0),
        "Taker flow: fade aggressive side": np.where(np.abs(f["taker1"]) > 0.05, -np.sign(f["taker1"]), 0),
        "Funding contrarian (|funding|>0.03%)": np.where(np.abs(f["fund"]) > 0.0003, -np.sign(f["fund"]), 0),
        "Crowd contrarian (fade crowd long/short)": np.where(np.abs(f["crowd_ls"]) > 0.4, -np.sign(f["crowd_ls"]), 0),
        "OI up + price up: follow": np.where((f["oi1"] > 0.005) & (np.abs(f["z1"]) > 1), np.sign(f["r1"]), 0),
        "CRT 1h sweep (trade the reclaim)": f["crt1"],
        "CRT 4h sweep (trade the reclaim)": f["crt4"],
        "BTC leads: alts follow BTC's last hour": np.where((D["coin"] != 0) & (np.abs(f["btc_r1"]) > 0.006),
                                                          np.sign(f["btc_r1"]), 0),
    }
    # hour of day seasonality learnt from past data only (expanding mean per coin and hour)
    seas = np.zeros(len(D["t"]))
    hr = f["hour"].astype(int)
    sums, cnts = {}, {}
    days = (D["t"] // 86400).astype(int)
    order = np.argsort(D["t"], kind="stable")
    cur, buf = None, []
    for i in order:
        if days[i] != cur:  # update stats with yesterday's outcomes only at the day boundary
            for j in buf:
                key = (int(D["coin"][j]), hr[j])
                sums[key] = sums.get(key, 0) + D["ret"][j]
                cnts[key] = cnts.get(key, 0) + 1
            buf, cur = [], days[i]
        key = (int(D["coin"][i]), hr[i])
        if cnts.get(key, 0) >= 60:
            mu = sums[key] / cnts[key]
            seas[i] = np.sign(mu) if abs(mu) > 0.0004 else 0
        buf.append(i)
    out["Hour of day seasonality (past only)"] = seas
    return {k: np.nan_to_num(v) for k, v in out.items()}


def evaluate(D, pred):
    res = {"model": [], "baselines": []}
    valid = np.isfinite(pred)
    E = {k: v[valid] for k, v in D.items() if isinstance(v, np.ndarray) and len(v) == len(valid)}
    p = pred[valid]
    side_m = np.sign(p)
    # calibration: does a bigger prediction mean a bigger, more reliable move?
    dec = []
    qs = np.quantile(np.abs(p), [0, 0.5, 0.8, 0.9, 0.95, 0.99, 1.0])
    for a, b in zip(qs[:-1], qs[1:]):
        s = (np.abs(p) >= a) & (np.abs(p) <= b)
        rr = side_m[s] * E["ret"][s]
        dec.append({"bucket": f"{a:.3f}-{b:.3f}", "n": int(s.sum()), "hit": float((rr > 0).mean()),
                    "gross_bp": float(rr.mean() * 1e4)})
    res["calibration"] = dec
    corr = np.corrcoef(p, E["ret"] / E["vol"])[0, 1]
    res["ic"] = float(corr)
    for q in QUANTS:
        thr = rolling_threshold(E["t"], p, q)
        take = np.abs(p) >= thr
        for cn, cv in COSTS.items():
            for sn, sv in STOPS.items():
                s = summarize(E, take, side_m, cv, sv)
                if s:
                    res["model"].append({"q": q, "cost": cn, "cost_v": cv, "stop": sn, **s})
    for bn, side in baselines(E).items():
        for cn, cv in COSTS.items():
            for sn, sv in STOPS.items():
                s = summarize(E, np.ones(len(side), bool), side, cv, sv)
                if s:
                    res["baselines"].append({"name": bn, "cost": cn, "cost_v": cv, "stop": sn, **s})
    # per coin at the decision cost, best model threshold picked on the FIRST half only
    mm = [m for m in res["model"] if m["cost_v"] == DECIDE_COST and m["trades"] >= 200 and m["first_bp"] is not None]
    pick = max(mm, key=lambda m: m["first_bp"]) if mm else None
    res["pick"] = pick
    if pick:
        thr = rolling_threshold(E["t"], p, pick["q"])
        take = np.abs(p) >= thr
        res["per_coin"] = {}
        for i, c in enumerate(COINS):
            s = summarize(E, take & (E["coin"] == i), side_m, DECIDE_COST, STOPS[pick["stop"]])
            if s:
                res["per_coin"][c] = s
    return res


# ----------------------------------------------------------------------------- report
def report(res, D, source, runtime):
    span = (time.strftime("%Y-%m-%d", time.gmtime(D["t"][0])), time.strftime("%Y-%m-%d", time.gmtime(D["t"][-1])))
    L = [f"# Hour Lab: betting for or against each coin over the next hour (auto-generated)", "",
         f"Data: {source}, {span[0]} to {span[1]}, {len(D['t']):,} coin-hours across {len(COINS)} coins. "
         f"Walk forward, retrained weekly on past data only. Runtime {runtime:.0f}s.", "",
         f"Prediction quality (information coefficient, correlation of prediction with the next hour): "
         f"**{res['ic']:+.4f}**. Anything under +0.02 is too weak to pay fees.", "",
         "## Does a stronger signal mean a better bet? (gross, before fees)", "",
         "| Signal strength bucket | Bets | Hit rate | Avg move captured |", "|---|---|---|---|"]
    for d in res["calibration"]:
        L.append(f"| {d['bucket']} | {d['n']:,} | {d['hit'] * 100:.1f}% | {d['gross_bp']:+.1f} bp |")
    L += ["", "1 bp = 0.01%. Round trip fees are 4 to 20 bp, so a bucket needs a gross edge above that.", ""]
    L += ["## Best model settings at each fee level", "",
          "| Fees | Take top | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 | Max DD $ |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for cn in COSTS:
        rows = [m for m in res["model"] if m["cost"] == cn and m["trades"] >= 200]
        for m in sorted(rows, key=lambda m: -m["avg_bp"])[:3]:
            L.append(f"| {cn} | {'all' if m['q'] == 0 else f'{(1 - m['q']) * 100:.0f}%'} | {m['stop']} | "
                     f"{m['per_day']:.1f} | {m['win'] * 100:.0f}% | {m['avg_bp']:+.1f} bp | {m['first_bp']:+.1f} | "
                     f"{m['second_bp']:+.1f} | ${m['usd_day_1000']:+.2f} | ${m['max_dd_usd_1000']:.0f} |")
    L += ["", "## Simple rules (no machine learning), at 0.08% fees", "",
          "| Rule | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 |", "|---|---|---|---|---|---|---|---|"]
    rows = [b for b in res["baselines"] if b["cost_v"] == DECIDE_COST]
    best = {}
    for b in rows:
        if b["name"] not in best or b["avg_bp"] > best[b["name"]]["avg_bp"]:
            best[b["name"]] = b
    for b in sorted(best.values(), key=lambda b: -b["avg_bp"]):
        L.append(f"| {b['name']} | {b['stop']} | {b['per_day']:.1f} | {b['win'] * 100:.0f}% | {b['avg_bp']:+.1f} bp | "
                 f"{b['first_bp']:+.1f} | {b['second_bp']:+.1f} | ${b['usd_day_1000']:+.2f} |")
    p = res.get("pick")
    L += ["", "## Honest pick", ""]
    if p:
        L.append(f"Chosen on the FIRST half only (fees 0.08%): take top "
                 f"{'all' if p['q'] == 0 else f'{(1 - p['q']) * 100:.0f}%'} of signals, {p['stop']}. "
                 f"Second half (unseen when choosing): **{p['second_bp']:+.1f} bp per bet**, "
                 f"{p['per_day']:.1f} bets/day, ${p['usd_day_1000']:+.2f}/day on $1,000 over the whole period.")
        if res.get("per_coin"):
            L += ["", "| Coin | Bets | Win | Avg net | 2nd half |", "|---|---|---|---|---|"]
            for c, s in res["per_coin"].items():
                L.append(f"| {c} | {s['trades']} | {s['win'] * 100:.0f}% | {s['avg_bp']:+.1f} bp | {s['second_bp']:+.1f} |")
    verdict = res.get("live", {}).get("reason", "")
    L += ["", f"**Live decision:** {verdict}", ""]
    return "\n".join(L)


def main():
    offline = "--offline" in sys.argv
    t0 = time.time()
    data, es, source = load_data(offline)
    D = build(data, es)
    print(f"dataset: {len(D['t']):,} rows, {len(FEATS)} features, source {source}", flush=True)
    pred = walk_forward(D)
    res = evaluate(D, pred)
    p = res.get("pick")
    live = {"generated": int(time.time()), "enabled": False, "cost": DECIDE_COST}
    if p and p["second_bp"] is not None and p["second_bp"] > 2 and p["first_bp"] > 2 and p["trades"] >= 300:
        live.update(enabled=True, q=p["q"], stop=STOPS[p["stop"]], stop_name=p["stop"],
                    reason=f"TRADE: picked on the first half, still {p['second_bp']:+.1f} bp per bet after 0.08% fees "
                           f"on the unseen second half.")
    else:
        live["reason"] = ("NO TRADE: no setting kept a positive edge after 0.08% fees on data it was not tuned on."
                          if p else "NO TRADE: not enough bets to judge.")
    res["live"] = live
    os.makedirs(OUT, exist_ok=True)
    res.update(source=source, rows=int(len(D["t"])), span=[int(D["t"][0]), int(D["t"][-1])], feats=FEATS)
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(res, f, indent=1, default=float)
    with open(os.path.join(OUT, "live_config.json"), "w") as f:
        json.dump(live, f, indent=1)
    rep = report(res, D, source, time.time() - t0)
    with open(os.path.join(OUT, "REPORT.md"), "w") as f:
        f.write(rep)
    print(rep)


if __name__ == "__main__":
    main()
