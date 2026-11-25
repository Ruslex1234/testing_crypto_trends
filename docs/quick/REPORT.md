# Quick 1-hour long/short trades: walk-forward results (auto-generated)

2026-09-12 to 2026-11-25, 8 coins, decisions every hour. Stop 1.5x ATR(15m), take-profit 1.5x the stop, exit after 1h. Costs 0.12% round trip (perp-style). Retrained daily on past data only; margin chosen from earlier days only.

| Approach | Trades | Win rate | Avg per trade | Net | Max DD | Long/Short | $100 @ 1% risk |
|---|---|---|---|---|---|---|---|
| **Train on last 14 days** | 0 | – | – | – | – | – | – |
| …first half | 0 | – | – | – | – | – | – |
| …second half | 0 | – | – | – | – | – | – |
| …no filter, top 3 every hour | 4203 (72.1/day) | 10% | -0.199R | -836.3R | 839.5R | 2024L / 2179S | $0.02 |
| **Train on all history** | 26 (26.0/day) | 0% | -0.678R | -17.6R | 17.2R | 9L / 17S | $83.75 |
| …first half | 13 (13.0/day) | 0% | -0.658R | -8.6R | 8.0R | 0L / 13S | $91.75 |
| …second half | 13 (13.0/day) | 0% | -0.697R | -9.1R | 8.6R | 9L / 4S | $91.29 |
| …no filter, top 3 every hour | 4203 (72.1/day) | 10% | -0.180R | -754.9R | 755.2R | 2302L / 1901S | $0.05 |

Live: window = last_14_days, margin = None (NOT trading: no edge after costs)
