# AI predictor: walk-forward results (auto-generated)

2024-11-21 to 2026-11-28, 8 coins, hourly. Model retrained monthly on past data only; threshold chosen from earlier months only. Costs 0.9% round trip. Trade = TP 8xATR / SL 4xATR / 24h.

**Model quality (out of sample):** AUC 0.642 (0.5 = coin flip), Brier 0.0570, base win rate 5.9%, typical win probability needed to beat fees 41%.

| Approach | Trades | Win rate | Avg R/trade | Net R | Max DD | $100 @ 2% risk |
|---|---|---|---|---|---|---|
| **Cost-aware AI (the strategy)** | 40 | 2% | -0.158R | -6.3R | 11.4R | $87.36 |
| …first half of the period | 19 | 5% | +0.267R | +5.1R | 3.4R | $110.27 |
| …second half of the period | 21 | 0% | -0.542R | -11.4R | 10.1R | $79.22 |
| AI, trade whenever p > 50% | 65 | 12% | -0.382R | -24.9R | 29.0R | $59.81 |
| No AI: take every hour | 1997 | 5% | -0.338R | -674.4R | 675.8R | $0.00 |

**Calibration (does a predicted 40% win rate really win 40%?):**

| Predicted | Samples | Avg predicted | Actual win rate | Avg net R |
|---|---|---|---|---|
| 0.0-0.1 | 92240 | 3.4% | 4.9% | -0.288 |
| 0.1-0.2 | 12815 | 13.7% | 9.1% | -0.332 |
| 0.2-0.3 | 3285 | 24.1% | 11.8% | -0.373 |
| 0.3-0.4 | 1168 | 34.2% | 19.0% | -0.230 |
| 0.4-0.5 | 457 | 44.2% | 22.3% | -0.189 |
| 0.5-0.6 | 221 | 55.0% | 21.7% | -0.490 |
| 0.6-0.7 | 84 | 64.1% | 23.8% | -0.566 |
| 0.7-0.8 | 46 | 74.5% | 4.3% | +0.012 |
| 0.8-0.9 | 39 | 84.8% | 0.0% | +0.015 |

Live margin (EV must exceed, in R): None
