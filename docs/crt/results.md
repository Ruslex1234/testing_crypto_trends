# CRT research results (auto-generated)

Generated 2026-11-20 00:11 UTC. All figures are **R multiples after costs** (1R = the risk to the stop). Chosen config = max of min(train, validation) expectancy (n train >= 20, n val >= 10); TEST data never influences the choice.

## NQ futures, 5m data (MNQ costs)
2026-09-11 to 2026-11-19, 13675 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 15M | CRT 30M | CRT 1H |
|---|---|---|---|
| Chosen config (train) | aggr atr 5R | eq ob 3R | aggr sweep partial |
| Train n / exp | 146 / 0.11 | 22 / 0.24 | 52 / -0.02 |
| Val n / exp | 58 / 0.12 | 11 / 0.80 | 25 / 0.05 |
| TEST n / exp | 72 / -0.12 | 13 / 0.10 | 26 / 0.43 |
| Test win rate / PF | 25% / 0.84 | 38% / 1.16 | 50% / 1.84 |
| Win rate (all) | 29% | 37% | 40% |
| Profit factor (all) | 1.08 | 1.52 | 1.18 |
| Expectancy R (all) | 0.05 | 0.33 | 0.11 |
| Avg winner R | 2.63 | 2.65 | 1.84 |
| Max DD R (all) | 18.57 | 6.55 | 14.26 |
| Max losing streak | 10 | 6 | 7 |
| Trades/day | 3.97 | 0.71 | 1.54 |
| Avg stop (pts) | 86.99 | 81.90 | 56.14 |
| Best session (n≥3) | NY pre-open (0.33) | NY midday (1.48) | NY midday (0.34) |
| Long exp / Short exp | 0.00 / 0.11 | -0.02 / 0.84 | -0.02 / 0.26 |

**Robustness across all configs** (positive in train AND val, then checked on test):

- 15M: 42/68 configs positive in test; 3 passed train+val, 0 of those positive in test. Naive train-best `ob ob 3R` test exp -0.22 (n 20)
- 30M: 36/53 configs positive in test; 26 passed train+val, 20 of those positive in test. Naive train-best `eq atr 5R` test exp 0.36 (n 14)
- 60M: 21/24 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `ob atr 4R` test exp -1.13 (n 3)

**Aggressive vs confirmed (best of each on train → val / test expectancy):**

- 15M: aggressive `aggr atr 5R` train 0.11 (n 146), val 0.12 (n 58), test -0.12 (n 72); confirmed `ob ob 3R` train 0.53 (n 33), val 0.05 (n 26), test -0.22 (n 20)
- 30M: aggressive `aggr sweep 5R` train 0.26 (n 119), val -0.30 (n 61), test 0.20 (n 81); confirmed `eq atr 5R` train 0.30 (n 18), val 0.83 (n 11), test 0.36 (n 14)
- 60M: aggressive `aggr sweep 5R` train 0.27 (n 77), val -0.94 (n 37), test 0.75 (n 29); confirmed `ob atr 4R` train 0.71 (n 10), val -0.93 (n 6), test -1.13 (n 3)

**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**

- `15m|aggr|atr|5R|pd_level|bias0`: 145 / -0.04, test 0.05 (n 32)
- `15m|aggr|atr|5R|session_level|bias0`: 246 / -0.10, test 0.07 (n 59)
- `15m|aggr|atr|5R|vwap|bias0`: 195 / 0.03, test -0.24 (n 53)
- `15m|aggr|atr|5R|daily_open|bias0`: 255 / -0.06, test 0.05 (n 65)
- `15m|aggr|atr|5R|killzone|bias0`: 138 / -0.15, test -0.12 (n 32)
- `15m|aggr|atr|5R|high_vol|bias0`: 166 / 0.14, test 0.11 (n 43)
- `15m|aggr|atr|5R|low_vol|bias0`: 165 / -0.09, test -0.29 (n 45)
- `30m|eq|ob|3R|pd_level|bias0`: 16 / 0.77, test 1.21 (n 4)
- `30m|eq|ob|3R|session_level|bias0`: 35 / 0.30, test 0.04 (n 10)
- `30m|eq|ob|3R|vwap|bias0`: 30 / 0.36, test -0.21 (n 7)
- `30m|eq|ob|3R|daily_open|bias0`: 27 / 0.40, test 0.48 (n 7)
- `30m|eq|ob|3R|killzone|bias0`: 15 / 0.05, test -1.01 (n 3)
- `30m|eq|ob|3R|high_vol|bias0`: 25 / 0.83, test 1.40 (n 6)
- `30m|eq|ob|3R|low_vol|bias0`: 21 / -0.26, test -1.01 (n 7)
- `30m|eq|ob|3R|pd_level+high_vol|bias0`: 12 / 0.70, test 1.21 (n 4)
- `60m|aggr|sweep|partial|pd_level|bias0`: 46 / 0.03, test 0.45 (n 9)
- `60m|aggr|sweep|partial|session_level|bias0`: 85 / 0.07, test 0.44 (n 23)
- `60m|aggr|sweep|partial|vwap|bias0`: 17 / 0.03, test -0.41 (n 5)
- `60m|aggr|sweep|partial|daily_open|bias0`: 79 / 0.06, test 0.31 (n 22)
- `60m|aggr|sweep|partial|killzone|bias0`: 22 / -0.35, test -1.02 (n 4)
- `60m|aggr|sweep|partial|high_vol|bias0`: 55 / 0.13, test 0.53 (n 14)
- `60m|aggr|sweep|partial|low_vol|bias0`: 48 / 0.09, test 0.31 (n 12)

**Multi-timeframe:**

- A: 1H bias + 15M exec `15m|aggr|atr|5R|-|bias60`: all 202 / -0.08, test -0.17 (n 48)
- B: 1H bias + 30M exec `30m|eq|ob|3R|-|bias60`: all 28 / 0.15, test -0.31 (n 7)
- C: 30M bias + 15M exec `15m|aggr|atr|5R|-|bias30`: all 206 / -0.00, test -0.08 (n 60)

**Focus: aggressive entry, stop beyond sweep (like-for-like across timeframes)**

- `15m|aggr|sweep|2R|-|bias0` train -0.06 (n 377), val -0.09 (n 178), test 0.11 (n 194)
  - sessions: Asia/overnight 0.02 (n 232), London -0.02 (n 181), NY afternoon -0.11 (n 75), NY midday -0.06 (n 100), NY open -0.14 (n 60), NY pre-open 0.04 (n 101)
  - filters (all exp / test exp): pd_level -0.21/-0.11 (n 248), session_level -0.19/-0.03 (n 483), vwap 0.07/0.07 (n 373), daily_open -0.14/0.06 (n 515), killzone -0.00/-0.00 (n 249), high_vol -0.06/-0.03 (n 370), low_vol -0.10/0.16 (n 417)
  - MTF: 60m bias -0.12/0.10 (n 359), 30m bias -0.02/0.14 (n 370)
- `15m|aggr|sweep|3R|-|bias0` train -0.06 (n 305), val 0.09 (n 153), test 0.12 (n 139)
  - sessions: Asia/overnight 0.11 (n 178), London -0.05 (n 148), NY afternoon 0.04 (n 60), NY midday 0.08 (n 84), NY open 0.08 (n 52), NY pre-open -0.18 (n 75)
  - filters (all exp / test exp): pd_level -0.17/-0.09 (n 239), session_level -0.17/-0.02 (n 439), vwap 0.04/-0.09 (n 330), daily_open -0.14/0.02 (n 465), killzone -0.08/-0.15 (n 222), high_vol 0.12/0.28 (n 319), low_vol -0.25/-0.21 (n 345)
  - MTF: 60m bias -0.12/0.01 (n 337), 30m bias 0.00/0.12 (n 337)
- `30m|aggr|sweep|2R|-|bias0` train 0.12 (n 178), val 0.14 (n 82), test 0.11 (n 119)
  - sessions: Asia/overnight -0.04 (n 105), London 0.10 (n 93), NY afternoon 0.29 (n 47), NY midday 0.31 (n 53), NY open 0.20 (n 34), NY pre-open 0.11 (n 47)
  - filters (all exp / test exp): pd_level 0.04/0.21 (n 146), session_level 0.08/0.20 (n 274), vwap 0.16/-0.00 (n 158), daily_open -0.02/0.04 (n 281), killzone 0.05/0.06 (n 133), high_vol 0.15/0.18 (n 184), low_vol 0.01/0.09 (n 230)
  - MTF: 60m bias -0.04/-0.10 (n 194)
- `30m|aggr|sweep|3R|-|bias0` train 0.22 (n 141), val 0.40 (n 72), test 0.08 (n 99)
  - sessions: Asia/overnight 0.11 (n 83), London 0.05 (n 74), NY afternoon 0.42 (n 38), NY midday 0.49 (n 50), NY open 0.23 (n 31), NY pre-open 0.19 (n 36)
  - filters (all exp / test exp): pd_level -0.02/0.08 (n 132), session_level 0.14/0.24 (n 238), vwap 0.15/-0.27 (n 147), daily_open 0.07/0.08 (n 234), killzone -0.03/0.06 (n 124), high_vol 0.31/0.15 (n 151), low_vol 0.01/0.06 (n 198)
  - MTF: 60m bias -0.06/-0.01 (n 174)
- `60m|aggr|sweep|2R|-|bias0` train -0.06 (n 101), val -0.22 (n 45), test 0.37 (n 42)
  - sessions: Asia/overnight 0.27 (n 51), London -0.11 (n 46), NY afternoon -0.35 (n 27), NY midday 0.24 (n 36), NY open -1.02 (n 7), NY pre-open -0.02 (n 21)
  - filters (all exp / test exp): pd_level 0.01/0.32 (n 87), session_level -0.01/0.27 (n 153), vwap -0.02/0.19 (n 70), daily_open 0.11/0.67 (n 142), killzone -0.31/-0.72 (n 59), high_vol 0.03/0.41 (n 103), low_vol 0.00/0.24 (n 93)
- `60m|aggr|sweep|3R|-|bias0` train 0.19 (n 89), val -0.36 (n 35), test 0.39 (n 33)
  - sessions: Asia/overnight 0.34 (n 46), London -0.25 (n 36), NY afternoon -0.21 (n 23), NY midday 0.70 (n 33), NY open -1.02 (n 5), NY pre-open -0.17 (n 14)
  - filters (all exp / test exp): pd_level 0.14/0.53 (n 82), session_level 0.13/0.61 (n 134), vwap -0.05/-0.15 (n 66), daily_open 0.14/0.78 (n 126), killzone -0.21/-1.02 (n 59), high_vol 0.13/0.24 (n 92), low_vol 0.14/0.58 (n 82)

## NQ futures, 5m data (NQ costs)
2026-09-11 to 2026-11-19, 13675 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 15M | CRT 30M | CRT 1H |
|---|---|---|---|
| Chosen config (train) | aggr atr 5R | eq ob 3R | aggr sweep partial |
| Train n / exp | 146 / 0.12 | 22 / 0.25 | 52 / -0.01 |
| Val n / exp | 58 / 0.12 | 11 / 0.81 | 25 / 0.06 |
| TEST n / exp | 72 / -0.11 | 13 / 0.11 | 26 / 0.43 |
| Test win rate / PF | 25% / 0.85 | 38% / 1.17 | 50% / 1.86 |
| Win rate (all) | 29% | 37% | 40% |
| Profit factor (all) | 1.08 | 1.53 | 1.20 |
| Expectancy R (all) | 0.06 | 0.34 | 0.12 |
| Avg winner R | 2.64 | 2.66 | 1.85 |
| Max DD R (all) | 18.44 | 6.41 | 13.87 |
| Max losing streak | 10 | 6 | 7 |
| Trades/day | 3.97 | 0.71 | 1.54 |
| Avg stop (pts) | 86.99 | 81.90 | 56.14 |
| Best session (n≥3) | NY pre-open (0.34) | NY midday (1.49) | NY midday (0.35) |
| Long exp / Short exp | 0.01 / 0.12 | -0.01 / 0.85 | -0.01 / 0.27 |

**Robustness across all configs** (positive in train AND val, then checked on test):

- 15M: 42/68 configs positive in test; 3 passed train+val, 0 of those positive in test. Naive train-best `ob ob 3R` test exp -0.21 (n 20)
- 30M: 36/53 configs positive in test; 26 passed train+val, 20 of those positive in test. Naive train-best `eq atr 5R` test exp 0.36 (n 14)
- 60M: 21/24 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `ob atr 4R` test exp -1.13 (n 3)

**Aggressive vs confirmed (best of each on train → val / test expectancy):**

- 15M: aggressive `aggr atr 5R` train 0.12 (n 146), val 0.12 (n 58), test -0.11 (n 72); confirmed `ob ob 3R` train 0.55 (n 33), val 0.06 (n 26), test -0.21 (n 20)
- 30M: aggressive `aggr sweep 5R` train 0.27 (n 119), val -0.29 (n 61), test 0.21 (n 81); confirmed `eq atr 5R` train 0.30 (n 18), val 0.83 (n 11), test 0.36 (n 14)
- 60M: aggressive `aggr sweep 5R` train 0.28 (n 77), val -0.93 (n 37), test 0.75 (n 29); confirmed `ob atr 4R` train 0.71 (n 10), val -0.92 (n 6), test -1.13 (n 3)

**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**

- `15m|aggr|atr|5R|pd_level|bias0`: 145 / -0.04, test 0.05 (n 32)
- `15m|aggr|atr|5R|session_level|bias0`: 246 / -0.09, test 0.07 (n 59)
- `15m|aggr|atr|5R|vwap|bias0`: 195 / 0.03, test -0.24 (n 53)
- `15m|aggr|atr|5R|daily_open|bias0`: 255 / -0.06, test 0.05 (n 65)
- `15m|aggr|atr|5R|killzone|bias0`: 138 / -0.15, test -0.12 (n 32)
- `15m|aggr|atr|5R|high_vol|bias0`: 166 / 0.15, test 0.11 (n 43)
- `15m|aggr|atr|5R|low_vol|bias0`: 165 / -0.08, test -0.28 (n 45)
- `30m|eq|ob|3R|pd_level|bias0`: 16 / 0.78, test 1.21 (n 4)
- `30m|eq|ob|3R|session_level|bias0`: 35 / 0.31, test 0.04 (n 10)
- `30m|eq|ob|3R|vwap|bias0`: 30 / 0.37, test -0.21 (n 7)
- `30m|eq|ob|3R|daily_open|bias0`: 27 / 0.40, test 0.49 (n 7)
- `30m|eq|ob|3R|killzone|bias0`: 15 / 0.06, test -1.00 (n 3)
- `30m|eq|ob|3R|high_vol|bias0`: 25 / 0.84, test 1.40 (n 6)
- `30m|eq|ob|3R|low_vol|bias0`: 21 / -0.25, test -1.01 (n 7)
- `30m|eq|ob|3R|pd_level+high_vol|bias0`: 12 / 0.71, test 1.21 (n 4)
- `60m|aggr|sweep|partial|pd_level|bias0`: 46 / 0.04, test 0.46 (n 9)
- `60m|aggr|sweep|partial|session_level|bias0`: 85 / 0.08, test 0.44 (n 23)
- `60m|aggr|sweep|partial|vwap|bias0`: 17 / 0.04, test -0.40 (n 5)
- `60m|aggr|sweep|partial|daily_open|bias0`: 79 / 0.07, test 0.32 (n 22)
- `60m|aggr|sweep|partial|killzone|bias0`: 22 / -0.33, test -1.02 (n 4)
- `60m|aggr|sweep|partial|high_vol|bias0`: 55 / 0.14, test 0.53 (n 14)
- `60m|aggr|sweep|partial|low_vol|bias0`: 48 / 0.10, test 0.32 (n 12)

**Multi-timeframe:**

- A: 1H bias + 15M exec `15m|aggr|atr|5R|-|bias60`: all 202 / -0.07, test -0.17 (n 48)
- B: 1H bias + 30M exec `30m|eq|ob|3R|-|bias60`: all 28 / 0.16, test -0.31 (n 7)
- C: 30M bias + 15M exec `15m|aggr|atr|5R|-|bias30`: all 206 / 0.00, test -0.08 (n 60)

**Focus: aggressive entry, stop beyond sweep (like-for-like across timeframes)**

- `15m|aggr|sweep|2R|-|bias0` train -0.04 (n 377), val -0.07 (n 178), test 0.12 (n 194)
  - sessions: Asia/overnight 0.04 (n 232), London -0.00 (n 181), NY afternoon -0.09 (n 75), NY midday -0.05 (n 100), NY open -0.13 (n 60), NY pre-open 0.05 (n 101)
  - filters (all exp / test exp): pd_level -0.20/-0.10 (n 248), session_level -0.17/-0.02 (n 484), vwap 0.08/0.08 (n 373), daily_open -0.13/0.07 (n 516), killzone 0.01/0.01 (n 249), high_vol -0.05/-0.02 (n 370), low_vol -0.08/0.17 (n 417)
  - MTF: 60m bias -0.11/0.12 (n 359), 30m bias -0.01/0.15 (n 370)
- `15m|aggr|sweep|3R|-|bias0` train -0.04 (n 305), val 0.11 (n 153), test 0.13 (n 139)
  - sessions: Asia/overnight 0.13 (n 178), London -0.03 (n 148), NY afternoon 0.05 (n 60), NY midday 0.09 (n 84), NY open 0.09 (n 52), NY pre-open -0.16 (n 75)
  - filters (all exp / test exp): pd_level -0.16/-0.08 (n 239), session_level -0.16/-0.01 (n 440), vwap 0.05/-0.08 (n 330), daily_open -0.13/0.03 (n 466), killzone -0.06/-0.14 (n 222), high_vol 0.13/0.29 (n 319), low_vol -0.23/-0.20 (n 345)
  - MTF: 60m bias -0.10/0.02 (n 337), 30m bias 0.02/0.13 (n 337)
- `30m|aggr|sweep|2R|-|bias0` train 0.14 (n 178), val 0.15 (n 82), test 0.12 (n 119)
  - sessions: Asia/overnight -0.03 (n 105), London 0.11 (n 93), NY afternoon 0.30 (n 47), NY midday 0.32 (n 53), NY open 0.21 (n 34), NY pre-open 0.12 (n 47)
  - filters (all exp / test exp): pd_level 0.05/0.22 (n 146), session_level 0.09/0.21 (n 274), vwap 0.17/0.00 (n 158), daily_open -0.01/0.05 (n 281), killzone 0.06/0.07 (n 133), high_vol 0.16/0.19 (n 184), low_vol 0.02/0.10 (n 230)
  - MTF: 60m bias -0.03/-0.10 (n 194)
- `30m|aggr|sweep|3R|-|bias0` train 0.23 (n 141), val 0.41 (n 72), test 0.09 (n 99)
  - sessions: Asia/overnight 0.12 (n 83), London 0.06 (n 74), NY afternoon 0.43 (n 38), NY midday 0.50 (n 50), NY open 0.24 (n 31), NY pre-open 0.20 (n 36)
  - filters (all exp / test exp): pd_level -0.01/0.08 (n 132), session_level 0.15/0.25 (n 238), vwap 0.16/-0.26 (n 147), daily_open 0.08/0.09 (n 234), killzone -0.01/0.06 (n 124), high_vol 0.32/0.16 (n 151), low_vol 0.03/0.07 (n 198)
  - MTF: 60m bias -0.05/0.00 (n 174)
- `60m|aggr|sweep|2R|-|bias0` train -0.05 (n 101), val -0.21 (n 45), test 0.37 (n 42)
  - sessions: Asia/overnight 0.28 (n 51), London -0.10 (n 46), NY afternoon -0.34 (n 27), NY midday 0.24 (n 36), NY open -1.01 (n 7), NY pre-open -0.01 (n 21)
  - filters (all exp / test exp): pd_level 0.01/0.33 (n 87), session_level -0.00/0.28 (n 153), vwap -0.01/0.19 (n 70), daily_open 0.12/0.68 (n 142), killzone -0.30/-0.71 (n 59), high_vol 0.04/0.41 (n 103), low_vol 0.01/0.25 (n 93)
- `60m|aggr|sweep|3R|-|bias0` train 0.20 (n 89), val -0.35 (n 35), test 0.39 (n 33)
  - sessions: Asia/overnight 0.35 (n 46), London -0.24 (n 36), NY afternoon -0.21 (n 23), NY midday 0.70 (n 33), NY open -1.01 (n 5), NY pre-open -0.16 (n 14)
  - filters (all exp / test exp): pd_level 0.14/0.53 (n 82), session_level 0.13/0.61 (n 134), vwap -0.05/-0.14 (n 66), daily_open 0.15/0.78 (n 126), killzone -0.20/-1.01 (n 59), high_vol 0.14/0.24 (n 92), low_vol 0.15/0.59 (n 82)

## NQ futures, 1H CRT on 2 years of hourly data (MNQ costs)
2024-06-30 to 2026-11-20, 13714 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 1H |
|---|---|
| Chosen config (train) | ob ob 2R |
| Train n / exp | 68 / 0.06 |
| Val n / exp | 25 / 0.14 |
| TEST n / exp | 39 / -0.26 |
| Test win rate / PF | 26% / 0.66 |
| Win rate (all) | 35% |
| Profit factor (all) | 0.97 |
| Expectancy R (all) | -0.02 |
| Avg winner R | 1.85 |
| Max DD R (all) | 13.36 |
| Max losing streak | 8 |
| Trades/day | 0.15 |
| Avg stop (pts) | 74.29 |
| Best session (n≥3) | NY open (0.26) |
| Long exp / Short exp | -0.07 / 0.06 |

**Robustness across all configs** (positive in train AND val, then checked on test):

- 60M: 6/74 configs positive in test; 5 passed train+val, 0 of those positive in test. Naive train-best `fvg sweep 5R` test exp -0.72 (n 14)

**Aggressive vs confirmed (best of each on train → val / test expectancy):**

- 60M: aggressive `aggr atr 5R` train 0.10 (n 420), val 0.03 (n 225), test -0.14 (n 241); confirmed `fvg sweep 5R` train 0.62 (n 15), val -0.30 (n 9), test -0.72 (n 14)

**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**

- `60m|ob|ob|2R|pd_level|bias0`: 46 / 0.08, test 0.08 (n 16)
- `60m|ob|ob|2R|session_level|bias0`: 112 / -0.03, test -0.26 (n 31)
- `60m|ob|ob|2R|vwap|bias0`: 115 / -0.01, test -0.21 (n 33)
- `60m|ob|ob|2R|daily_open|bias0`: 67 / 0.01, test -0.32 (n 21)
- `60m|ob|ob|2R|killzone|bias0`: 44 / -0.07, test -0.01 (n 15)
- `60m|ob|ob|2R|high_vol|bias0`: 70 / -0.01, test -0.18 (n 21)
- `60m|ob|ob|2R|low_vol|bias0`: 64 / -0.06, test -0.38 (n 19)

**Multi-timeframe:**


**Focus: aggressive entry, stop beyond sweep (like-for-like across timeframes)**

- `60m|aggr|sweep|2R|-|bias0` train -0.16 (n 971), val -0.18 (n 517), test -0.21 (n 567)
  - sessions: Asia/overnight -0.10 (n 481), London -0.26 (n 413), NY afternoon -0.11 (n 306), NY midday -0.12 (n 424), NY open -0.22 (n 127), NY pre-open -0.33 (n 304)
  - filters (all exp / test exp): pd_level -0.21/-0.23 (n 869), session_level -0.20/-0.23 (n 1680), vwap -0.12/-0.19 (n 822), daily_open -0.20/-0.21 (n 1470), killzone -0.21/-0.38 (n 611), high_vol -0.12/-0.10 (n 1068), low_vol -0.21/-0.30 (n 1197)
- `60m|aggr|sweep|3R|-|bias0` train -0.11 (n 848), val -0.07 (n 435), test -0.13 (n 490)
  - sessions: Asia/overnight -0.09 (n 412), London -0.18 (n 335), NY afternoon 0.02 (n 271), NY midday -0.08 (n 375), NY open -0.17 (n 118), NY pre-open -0.17 (n 262)
  - filters (all exp / test exp): pd_level -0.16/-0.12 (n 840), session_level -0.15/-0.17 (n 1502), vwap -0.08/-0.18 (n 766), daily_open -0.13/-0.09 (n 1335), killzone -0.15/-0.29 (n 598), high_vol -0.05/-0.09 (n 953), low_vol -0.15/-0.15 (n 1066)

## BTC-USD spot, 5m data, retail fees, both directions
2026-09-21 to 2026-11-20, 17280 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 15M | CRT 30M | CRT 1H | CRT 4H |
|---|---|---|---|---|
| Chosen config (train) | not enough trades | not enough trades | not enough trades | not enough trades |
| Train n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
| Val n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
| TEST n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
| Test win rate / PF | not enough trades | not enough trades | not enough trades | not enough trades |
| Win rate (all) | not enough trades | not enough trades | not enough trades | not enough trades |
| Profit factor (all) | not enough trades | not enough trades | not enough trades | not enough trades |
| Expectancy R (all) | not enough trades | not enough trades | not enough trades | not enough trades |
| Avg winner R | not enough trades | not enough trades | not enough trades | not enough trades |
| Max DD R (all) | not enough trades | not enough trades | not enough trades | not enough trades |
| Max losing streak | not enough trades | not enough trades | not enough trades | not enough trades |
| Trades/day | not enough trades | not enough trades | not enough trades | not enough trades |
| Avg stop (pts) | not enough trades | not enough trades | not enough trades | not enough trades |
| Best session (n≥3) | not enough trades | not enough trades | not enough trades | not enough trades |
| Long exp / Short exp | not enough trades | not enough trades | not enough trades | not enough trades |

**Robustness across all configs** (positive in train AND val, then checked on test):

- 15M: 0/0 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `-` test exp – (n 0)
- 30M: 0/0 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `-` test exp – (n 0)
- 60M: 0/0 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `-` test exp – (n 0)
- 240M: 0/0 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `-` test exp – (n 0)

**Aggressive vs confirmed (best of each on train → val / test expectancy):**

- 15M: aggressive: too few trades; confirmed: too few trades
- 30M: aggressive: too few trades; confirmed: too few trades
- 60M: aggressive: too few trades; confirmed: too few trades
- 240M: aggressive: too few trades; confirmed: too few trades

**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**


**Multi-timeframe:**


**Focus: aggressive entry, stop beyond sweep (like-for-like across timeframes)**

- `15m|aggr|sweep|2R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
  - MTF: 60m bias –/– (n 0), 30m bias –/– (n 0)
- `15m|aggr|sweep|3R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
  - MTF: 60m bias –/– (n 0), 30m bias –/– (n 0)
- `30m|aggr|sweep|2R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
  - MTF: 60m bias –/– (n 0)
- `30m|aggr|sweep|3R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
  - MTF: 60m bias –/– (n 0)
- `60m|aggr|sweep|2R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
- `60m|aggr|sweep|3R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
- `240m|aggr|sweep|2R|-|bias0` train – (n 0), val – (n 0), test -1.20 (n 1)
  - sessions: Asia/overnight -1.20 (n 1)
  - filters (all exp / test exp): pd_level -1.20/-1.20 (n 1), session_level -1.20/-1.20 (n 1), vwap -1.20/-1.20 (n 1), daily_open –/– (n 0), killzone –/– (n 0), high_vol -1.20/-1.20 (n 1), low_vol –/– (n 0)
- `240m|aggr|sweep|3R|-|bias0` train – (n 0), val – (n 0), test -1.20 (n 1)
  - sessions: Asia/overnight -1.20 (n 1)
  - filters (all exp / test exp): pd_level -1.20/-1.20 (n 1), session_level -1.20/-1.20 (n 1), vwap -1.20/-1.20 (n 1), daily_open –/– (n 0), killzone –/– (n 0), high_vol -1.20/-1.20 (n 1), low_vol –/– (n 0)

## BTC-USD spot, 5m data, retail fees, LONG ONLY (what the $100 account can do)
2026-09-21 to 2026-11-20, 17280 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 15M | CRT 30M | CRT 1H | CRT 4H |
|---|---|---|---|---|
| Chosen config (train) | not enough trades | not enough trades | not enough trades | not enough trades |
| Train n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
| Val n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
| TEST n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
| Test win rate / PF | not enough trades | not enough trades | not enough trades | not enough trades |
| Win rate (all) | not enough trades | not enough trades | not enough trades | not enough trades |
| Profit factor (all) | not enough trades | not enough trades | not enough trades | not enough trades |
| Expectancy R (all) | not enough trades | not enough trades | not enough trades | not enough trades |
| Avg winner R | not enough trades | not enough trades | not enough trades | not enough trades |
| Max DD R (all) | not enough trades | not enough trades | not enough trades | not enough trades |
| Max losing streak | not enough trades | not enough trades | not enough trades | not enough trades |
| Trades/day | not enough trades | not enough trades | not enough trades | not enough trades |
| Avg stop (pts) | not enough trades | not enough trades | not enough trades | not enough trades |
| Best session (n≥3) | not enough trades | not enough trades | not enough trades | not enough trades |
| Long exp / Short exp | not enough trades | not enough trades | not enough trades | not enough trades |

**Robustness across all configs** (positive in train AND val, then checked on test):

- 15M: 0/0 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `-` test exp – (n 0)
- 30M: 0/0 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `-` test exp – (n 0)
- 60M: 0/0 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `-` test exp – (n 0)
- 240M: 0/0 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `-` test exp – (n 0)

**Aggressive vs confirmed (best of each on train → val / test expectancy):**

- 15M: aggressive: too few trades; confirmed: too few trades
- 30M: aggressive: too few trades; confirmed: too few trades
- 60M: aggressive: too few trades; confirmed: too few trades
- 240M: aggressive: too few trades; confirmed: too few trades

**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**


**Multi-timeframe:**


**Focus: aggressive entry, stop beyond sweep (like-for-like across timeframes)**

- `15m|aggr|sweep|2R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
  - MTF: 60m bias –/– (n 0), 30m bias –/– (n 0)
- `15m|aggr|sweep|3R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
  - MTF: 60m bias –/– (n 0), 30m bias –/– (n 0)
- `30m|aggr|sweep|2R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
  - MTF: 60m bias –/– (n 0)
- `30m|aggr|sweep|3R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
  - MTF: 60m bias –/– (n 0)
- `60m|aggr|sweep|2R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
- `60m|aggr|sweep|3R|-|bias0` train – (n 0), val – (n 0), test – (n 0)
  - sessions: 
  - filters (all exp / test exp): pd_level –/– (n 0), session_level –/– (n 0), vwap –/– (n 0), daily_open –/– (n 0), killzone –/– (n 0), high_vol –/– (n 0), low_vol –/– (n 0)
- `240m|aggr|sweep|2R|-|bias0` train – (n 0), val – (n 0), test -1.20 (n 1)
  - sessions: Asia/overnight -1.20 (n 1)
  - filters (all exp / test exp): pd_level -1.20/-1.20 (n 1), session_level -1.20/-1.20 (n 1), vwap -1.20/-1.20 (n 1), daily_open –/– (n 0), killzone –/– (n 0), high_vol -1.20/-1.20 (n 1), low_vol –/– (n 0)
- `240m|aggr|sweep|3R|-|bias0` train – (n 0), val – (n 0), test -1.20 (n 1)
  - sessions: Asia/overnight -1.20 (n 1)
  - filters (all exp / test exp): pd_level -1.20/-1.20 (n 1), session_level -1.20/-1.20 (n 1), vwap -1.20/-1.20 (n 1), daily_open –/– (n 0), killzone –/– (n 0), high_vol -1.20/-1.20 (n 1), low_vol –/– (n 0)

## BTC-USD spot, 2 years of hourly data, LONG ONLY, 1H and 4H CRT
2024-11-20 to 2026-11-19, 17510 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 1H | CRT 4H |
|---|---|---|
| Chosen config (train) | not enough trades | aggr atr 2R |
| Train n / exp | not enough trades | 10 / 0.32 |
| Val n / exp | not enough trades | 5 / -0.00 |
| TEST n / exp | not enough trades | 1 / 0.78 |
| Test win rate / PF | not enough trades | 100% / – |
| Win rate (all) | not enough trades | 56% |
| Profit factor (all) | not enough trades | 1.47 |
| Expectancy R (all) | not enough trades | 0.25 |
| Avg winner R | not enough trades | 1.38 |
| Max DD R (all) | not enough trades | 2.47 |
| Max losing streak | not enough trades | 2 |
| Trades/day | not enough trades | 0.03 |
| Avg stop (pts) | not enough trades | 3435.99 |
| Best session (n≥3) | not enough trades | NY midday (0.79) |
| Long exp / Short exp | not enough trades | 0.25 / – |

**Robustness across all configs** (positive in train AND val, then checked on test):

- 60M: 0/0 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `-` test exp – (n 0)
- 240M: 0/0 configs positive in test; 0 passed train+val, 0 of those positive in test. Naive train-best `aggr atr 2R` test exp 0.78 (n 1)

**Aggressive vs confirmed (best of each on train → val / test expectancy):**

- 60M: aggressive: too few trades; confirmed: too few trades
- 240M: aggressive `aggr atr 2R` train 0.32 (n 10), val -0.00 (n 5), test 0.78 (n 1); confirmed: too few trades

**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**

- `240m|aggr|atr|2R|pd_level|bias0`: 14 / 0.24, test 0.78 (n 1)
- `240m|aggr|atr|2R|session_level|bias0`: 16 / 0.25, test 0.78 (n 1)
- `240m|aggr|atr|2R|vwap|bias0`: 7 / -0.05, test 0.41 (n 1)
- `240m|aggr|atr|2R|daily_open|bias0`: 14 / 0.25, test 0.78 (n 1)
- `240m|aggr|atr|2R|killzone|bias0`: 3 / 0.76, test 0.41 (n 1)
- `240m|aggr|atr|2R|high_vol|bias0`: 16 / 0.25, test 0.78 (n 1)
- `240m|aggr|atr|2R|low_vol|bias0`: 1 / 0.10, test – (n 0)

**Multi-timeframe:**


**Focus: aggressive entry, stop beyond sweep (like-for-like across timeframes)**

- `60m|aggr|sweep|2R|-|bias0` train -0.45 (n 1), val 1.84 (n 1), test – (n 0)
  - sessions: Asia/overnight 0.70 (n 2)
  - filters (all exp / test exp): pd_level 0.70/– (n 2), session_level 1.84/– (n 1), vwap 1.84/– (n 1), daily_open 0.70/– (n 2), killzone –/– (n 0), high_vol 0.70/– (n 2), low_vol –/– (n 0)
- `60m|aggr|sweep|3R|-|bias0` train -0.45 (n 1), val 1.16 (n 1), test – (n 0)
  - sessions: Asia/overnight 0.36 (n 2)
  - filters (all exp / test exp): pd_level 0.36/– (n 2), session_level 1.16/– (n 1), vwap 1.16/– (n 1), daily_open 0.36/– (n 2), killzone –/– (n 0), high_vol 0.36/– (n 2), low_vol –/– (n 0)
- `240m|aggr|sweep|2R|-|bias0` train 0.52 (n 2), val -0.34 (n 2), test -1.19 (n 2)
  - sessions: Asia/overnight -0.25 (n 4), NY afternoon -1.25 (n 1), NY midday 0.23 (n 1)
  - filters (all exp / test exp): pd_level -0.34/-1.19 (n 6), session_level -0.34/-1.19 (n 6), vwap -0.34/-1.19 (n 6), daily_open -0.05/-1.19 (n 3), killzone –/– (n 0), high_vol -0.34/-1.19 (n 6), low_vol –/– (n 0)
- `240m|aggr|sweep|3R|-|bias0` train 0.52 (n 2), val -0.34 (n 2), test -1.19 (n 2)
  - sessions: Asia/overnight -0.25 (n 4), NY afternoon -1.25 (n 1), NY midday 0.23 (n 1)
  - filters (all exp / test exp): pd_level -0.34/-1.19 (n 6), session_level -0.34/-1.19 (n 6), vwap -0.34/-1.19 (n 6), daily_open -0.05/-1.19 (n 3), killzone –/– (n 0), high_vol -0.34/-1.19 (n 6), low_vol –/– (n 0)
