"""Optional phone alerts via ntfy (free, no account): install the ntfy app, subscribe to a topic
name only you know, and save that name as the repository secret NTFY_TOPIC. Without the secret
nothing is sent."""
import os
import urllib.request


def send_new_trades(state, since):
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        return
    lines = []
    for a in state["accounts"].values():
        for t in a["trades"]:
            if t["t"] >= since:
                lines.append(f"{a['name']}: {t['side'].upper()} {t['asset']} ${t['usd']:.2f} @ {t['price']:,.4g} ({t['reason']})")
    if not lines:
        return
    eq = sum(a.get("equity", 0) for a in state["accounts"].values())
    body = "\n".join(lines[:12]) + f"\n\nArena total: ${eq:,.2f}"
    req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=body.encode(),
                                 headers={"Title": f"Paper trades: {len(lines)} new", "Tags": "chart_with_upwards_trend"})
    urllib.request.urlopen(req, timeout=10).read()
