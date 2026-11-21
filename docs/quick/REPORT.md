# Quick 1-hour long/short trades: walk-forward results (auto-generated)

2026-09-08 to 2026-11-21, 8 coins, decisions every hour. Stop 1.5x ATR(15m), take-profit 1.5x the stop, exit after 1h. Costs 0.12% round trip (perp-style). Retrained daily on past data only; margin chosen from earlier days only.

| Approach | Trades | Win rate | Avg per trade | Net | Max DD | Long/Short | $100 @ 1% risk |
|---|---|---|---|---|---|---|---|
| **Train on last 14 days** | 0 | – | – | – | – | – | – |
| …first half | 0 | – | – | – | – | – | – |
| …second half | 0 | – | – | – | – | – | – |
| …no filter, top 3 every hour | 4224 (72.1/day) | 11% | -0.180R | -758.4R | 775.0R | 2100L / 2124S | $0.04 |
| **Train on all history** | 27 (27.0/day) | 15% | -0.294R | -7.9R | 9.0R | 16L / 11S | $92.25 |
| …first half | 13 (13.0/day) | 15% | -0.153R | -2.0R | 5.9R | 8L / 5S | $97.96 |
| …second half | 14 (14.0/day) | 14% | -0.424R | -5.9R | 6.1R | 8L / 6S | $94.17 |
| …no filter, top 3 every hour | 4224 (72.1/day) | 11% | -0.181R | -764.5R | 775.2R | 2268L / 1956S | $0.04 |

Live: window = last_14_days, margin = None (NOT trading: no edge after costs)
