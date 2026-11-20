"""Daily 1-minute candle archive. Builds our own intraday history beyond what free APIs keep
(Yahoo: 1m for 7 days, 5m for 60 days; Coinbase: paginated but rate limited).

Layout: data/candles/1m/<SYMBOL>/<YYYY-MM>/<YYYY-MM-DD>.csv.gz  (UTC days, complete days only)
Columns: t (unix seconds), o, h, l, c, v
Run: python3 research/archive.py   (backfills any missing complete days still available)
"""
import csv
import gzip
import io
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "candles", "1m")
sys.path.insert(0, os.path.join(ROOT, "bot"))
from crt_forward import MARKETS  # noqa: E402  (same 13 forward-test markets)
from market import ASSETS  # noqa: E402  (8 arena coins)

UA = {"User-Agent": "Mozilla/5.0 (candle-archive)"}


def _get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


def yahoo_1m(symbol):
    res = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=7d")["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    out = []
    for i, t in enumerate(res.get("timestamp") or []):
        o, h, l, c = (q[k][i] for k in ("open", "high", "low", "close"))
        if None not in (o, h, l, c):
            out.append((int(t), o, h, l, c, q["volume"][i] or 0))
    return out


def coinbase_1m(asset, start, end):
    rows = {}
    t = start
    while t < end:
        t2 = min(t + 300 * 60, end)
        iso = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for r in _get(f"https://api.exchange.coinbase.com/products/{asset}-USD/candles"
                      f"?granularity=60&start={iso(t)}&end={iso(t2)}"):
            rows[int(r[0])] = (int(r[0]), r[3], r[2], r[1], r[4], r[5])
        t = t2
        time.sleep(0.35)
    return [rows[k] for k in sorted(rows)]


def path(symbol, day):
    safe = symbol.replace("=", "_").replace("^", "")
    return os.path.join(OUT, safe, day[:7], f"{day}.csv.gz")


def write_days(symbol, rows, today):
    by_day = {}
    for r in rows:
        by_day.setdefault(datetime.fromtimestamp(r[0], timezone.utc).strftime("%Y-%m-%d"), []).append(r)
    written = 0
    for day, rs in by_day.items():
        if day >= today:  # only complete UTC days
            continue
        p = path(symbol, day)
        if os.path.exists(p):
            continue
        os.makedirs(os.path.dirname(p), exist_ok=True)
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["t", "o", "h", "l", "c", "v"])
        w.writerows(sorted(rs))
        with gzip.open(p, "wt") as f:
            f.write(buf.getvalue())
        written += 1
    return written


def main():
    now = int(time.time())
    today = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d")
    day0 = now - now % 86400
    report = {}
    for sym in MARKETS:
        try:
            report[sym] = write_days(sym, yahoo_1m(sym), today)
        except Exception as e:  # noqa: BLE001
            report[sym] = f"error: {e}"[:120]
        time.sleep(0.5)
    for a in ASSETS:  # Coinbase: exact exchange prints for the arena coins, last 3 days
        sym = f"{a}-USD-coinbase"
        try:
            missing = [d for d in range(1, 4) if not os.path.exists(path(
                sym, datetime.fromtimestamp(day0 - d * 86400, timezone.utc).strftime("%Y-%m-%d")))]
            if missing:
                rows = coinbase_1m(a, day0 - max(missing) * 86400, day0)
                report[sym] = write_days(sym, rows, today)
            else:
                report[sym] = 0
        except Exception as e:  # noqa: BLE001
            report[sym] = f"error: {e}"[:120]
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
