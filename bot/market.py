"""Public market data (no API keys). Coinbase Exchange first, Kraken as fallback."""
import json
import time
import urllib.request

UA = {"User-Agent": "paper-trader-bot/1.0", "Accept": "application/json"}

ASSETS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK"]
KRAKEN_PAIR = {"BTC": "XBTUSD", "DOGE": "XDGUSD"}


def _get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"GET failed {url}: {last}")


def _coinbase(asset, granularity):
    url = f"https://api.exchange.coinbase.com/products/{asset}-USD/candles?granularity={granularity}"
    rows = _get(url)
    # [time, low, high, open, close, volume], newest first
    out = [{"t": int(r[0]), "o": float(r[3]), "h": float(r[2]), "l": float(r[1]),
            "c": float(r[4]), "v": float(r[5])} for r in rows]
    return sorted(out, key=lambda x: x["t"])


def _kraken(asset, minutes):
    pair = KRAKEN_PAIR.get(asset, f"{asset}USD")
    data = _get(f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={minutes}")
    if data.get("error"):
        raise RuntimeError(str(data["error"]))
    key = next(k for k in data["result"] if k != "last")
    # [time, open, high, low, close, vwap, volume, count], oldest first
    return [{"t": int(r[0]), "o": float(r[1]), "h": float(r[2]), "l": float(r[3]),
             "c": float(r[4]), "v": float(r[6])} for r in data["result"][key]]


def candles(asset, interval):
    """interval: '1h' or '1d'. Returns oldest->newest; the last candle is still forming."""
    gran, mins = {"1m": (60, 1), "5m": (300, 5), "1h": (3600, 60), "1d": (86400, 1440)}[interval]
    try:
        rows = _coinbase(asset, gran)
        src = "coinbase"
    except Exception:  # noqa: BLE001
        rows = _kraken(asset, mins)
        src = "kraken"
    if len(rows) < 30:
        raise RuntimeError(f"too little data for {asset} {interval}")
    return rows, src


def resample(rows, hours):
    """Aggregate hourly candles into N-hour candles aligned to UTC."""
    step = hours * 3600
    out = []
    for r in rows:
        b = r["t"] - r["t"] % step
        if out and out[-1]["t"] == b:
            o = out[-1]
            o["h"] = max(o["h"], r["h"]); o["l"] = min(o["l"], r["l"])
            o["c"] = r["c"]; o["v"] += r["v"]
        else:
            out.append({**r, "t": b})
    return out


def load_all():
    data, errors, sources = {}, {}, set()
    for a in ASSETS:
        try:
            h, s1 = candles(a, "1h")
            d, s2 = candles(a, "1d")
            data[a] = {"1h": h, "1d": d, "6h": resample(h, 6), "price": h[-1]["c"]}
            try:
                data[a]["5m"], _ = candles(a, "5m")
                data[a]["price"] = data[a]["5m"][-1]["c"]
                data[a]["1m"], _ = candles(a, "1m")  # last 300 minutes: every minute since last run
                data[a]["price"] = data[a]["1m"][-1]["c"]
            except Exception:  # noqa: BLE001  (hourly fallback still works)
                pass
            sources |= {s1, s2}
        except Exception as e:  # noqa: BLE001
            errors[a] = str(e)
    return data, errors, sorted(sources)
