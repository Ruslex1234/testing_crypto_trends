"""Long hourly history (since 2019, or the coin's Coinbase listing) for the Strategy Lab.
Stored gzipped in data/history/<COIN>_1h.csv.gz; re-runs only fetch what's new."""
import csv
import gzip
import io
import json
import os
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "history")
COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK"]
START = int(datetime(2019, 1, 1, tzinfo=timezone.utc).timestamp())


def path(c):
    return os.path.join(OUT, f"{c}_1h.csv.gz")


def load(c):
    if not os.path.exists(path(c)):
        return []
    with gzip.open(path(c), "rt") as f:
        return [{"t": int(r["t"]), "o": float(r["o"]), "h": float(r["h"]), "l": float(r["l"]),
                 "c": float(r["c"]), "v": float(r["v"])} for r in csv.DictReader(f)]


def get(url):
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper-trader-bot/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{url}: {err}")


def update(c):
    rows = {r["t"]: r for r in load(c)}
    now = int(time.time()) // 3600 * 3600
    t = max(rows) + 3600 if rows else START
    while t < now:
        t2 = min(t + 300 * 3600, now)
        iso = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for r in get(f"https://api.exchange.coinbase.com/products/{c}-USD/candles"
                     f"?granularity=3600&start={iso(t)}&end={iso(t2)}"):
            if int(r[0]) < now:
                rows[int(r[0])] = {"t": int(r[0]), "o": r[3], "h": r[2], "l": r[1], "c": r[4], "v": r[5]}
        t = t2
        time.sleep(0.25)
    os.makedirs(OUT, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["t", "o", "h", "l", "c", "v"])
    for k in sorted(rows):
        r = rows[k]
        w.writerow([r["t"], r["o"], r["h"], r["l"], r["c"], r["v"]])
    with gzip.open(path(c), "wt") as f:
        f.write(buf.getvalue())
    first = min(rows) if rows else None
    return len(rows), datetime.fromtimestamp(first, timezone.utc).strftime("%Y-%m-%d") if first else None


if __name__ == "__main__":
    for c in COINS:
        print(c, update(c), flush=True)
