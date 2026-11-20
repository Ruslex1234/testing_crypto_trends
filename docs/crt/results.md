# CRT research results (auto-generated)

Generated 2026-11-20 00:03 UTC. All figures are **R multiples after costs** (1R = the risk to the stop). Selection uses the TRAIN period only; VAL and TEST are untouched.

## NQ futures, 5m data (MNQ costs)
2026-09-11 to 2026-11-19, 13673 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 15M | CRT 30M | CRT 1H |
|---|---|---|---|
| Chosen config (train) | ob ob 3R | aggr atr 5R | ob atr 4R |
| Train n / exp | 33 / 0.29 | 59 / 0.31 | 10 / 0.71 |
| Val n / exp | 26 / 0.05 | 34 / -0.56 | 5 / -0.91 |
| TEST n / exp | 20 / -0.22 | 38 / -0.02 | 3 / -1.00 |
| Win rate (all) | 29% | 28% | 22% |
| Profit factor (all) | 1.11 | 0.98 | 0.97 |
| Expectancy R (all) | 0.08 | -0.01 | -0.03 |
| Avg winner R | 2.82 | 2.40 | 3.28 |
| Max DD R (all) | 12.31 | 24.07 | 10.58 |
| Max losing streak | 11 | 13 | 11 |
| Trades/day | 1.14 | 1.89 | 0.27 |
| Avg stop (pts) | 46.65 | 125.76 | 163.48 |
| Best session (n≥3) | NY afternoon (0.56) | NY open (0.67) | NY pre-open (1.38) |
| Long exp / Short exp | -0.04 / 0.27 | -0.21 / 0.23 | 0.51 / -0.46 |

**Aggressive vs confirmed (best of each on train → val / test expectancy):**

- 15M: aggressive `aggr atr 5R` train 0.18 (n 143), val -0.01 (n 60), test -0.13 (n 74); confirmed `ob ob 3R` train 0.29 (n 33), val 0.05 (n 26), test -0.22 (n 20)
- 30M: aggressive `aggr atr 5R` train 0.31 (n 59), val -0.56 (n 34), test -0.02 (n 38); confirmed `eq atr 5R` train 0.30 (n 18), val 0.83 (n 11), test -0.01 (n 13)
- 60M: aggressive `aggr sweep 5R` train 0.27 (n 77), val -0.93 (n 37), test 0.63 (n 31); confirmed `ob atr 4R` train 0.71 (n 10), val -0.91 (n 5), test -1.00 (n 3)

**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**

- `15m|ob|ob|3R|pd_level|bias0`: 24 / 0.50, test -1.03 (n 4)
- `15m|ob|ob|3R|session_level|bias0`: 45 / -0.04, test -0.22 (n 10)
- `15m|ob|ob|3R|vwap|bias0`: 52 / 0.09, test -0.16 (n 14)
- `15m|ob|ob|3R|daily_open|bias0`: 37 / 0.29, test -0.14 (n 9)
- `15m|ob|ob|3R|killzone|bias0`: 34 / 0.12, test -0.58 (n 9)
- `15m|ob|ob|3R|high_vol|bias0`: 40 / 0.07, test -0.44 (n 7)
- `15m|ob|ob|3R|low_vol|bias0`: 39 / 0.10, test -0.10 (n 13)
- `30m|aggr|atr|5R|pd_level|bias0`: 86 / 0.02, test 0.61 (n 21)
- `30m|aggr|atr|5R|session_level|bias0`: 125 / -0.07, test 0.10 (n 36)
- `30m|aggr|atr|5R|vwap|bias0`: 93 / 0.00, test -0.23 (n 25)
- `30m|aggr|atr|5R|daily_open|bias0`: 122 / -0.01, test 0.23 (n 35)
- `30m|aggr|atr|5R|killzone|bias0`: 77 / 0.15, test -0.18 (n 19)
- `30m|aggr|atr|5R|high_vol|bias0`: 92 / -0.20, test -0.10 (n 29)
- `30m|aggr|atr|5R|low_vol|bias0`: 89 / 0.24, test 0.19 (n 28)
- `30m|aggr|atr|5R|killzone+low_vol|bias0`: 59 / 0.27, test -0.14 (n 17)
- `60m|ob|atr|4R|pd_level|bias0`: 7 / -0.29, test – (n 0)
- `60m|ob|atr|4R|session_level|bias0`: 16 / 0.10, test -1.00 (n 3)
- `60m|ob|atr|4R|vwap|bias0`: 16 / -0.22, test -1.00 (n 3)
- `60m|ob|atr|4R|daily_open|bias0`: 14 / 0.10, test -1.00 (n 2)
- `60m|ob|atr|4R|killzone|bias0`: 7 / 0.02, test -1.00 (n 2)
- `60m|ob|atr|4R|high_vol|bias0`: 10 / -0.74, test -1.00 (n 2)
- `60m|ob|atr|4R|low_vol|bias0`: 9 / 0.66, test -1.00 (n 1)

**Multi-timeframe:**

- A: 1H bias + 15M exec `15m|ob|ob|3R|-|bias60`: all 35 / -0.05, test -0.52 (n 8)
- B: 1H bias + 30M exec `30m|aggr|atr|5R|-|bias60`: all 106 / -0.19, test 0.17 (n 25)
- C: 30M bias + 15M exec `15m|ob|ob|3R|-|bias30`: all 38 / 0.04, test -0.22 (n 10)

## NQ futures, 5m data (NQ costs)
2026-09-11 to 2026-11-19, 13673 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 15M | CRT 30M | CRT 1H |
|---|---|---|---|
| Chosen config (train) | ob ob 3R | aggr atr 5R | ob atr 4R |
| Train n / exp | 33 / 0.31 | 59 / 0.31 | 10 / 0.71 |
| Val n / exp | 26 / 0.06 | 34 / -0.56 | 5 / -0.91 |
| TEST n / exp | 20 / -0.21 | 38 / -0.02 | 3 / -1.00 |
| Win rate (all) | 29% | 28% | 22% |
| Profit factor (all) | 1.13 | 0.99 | 0.97 |
| Expectancy R (all) | 0.10 | -0.01 | -0.02 |
| Avg winner R | 2.84 | 2.40 | 3.28 |
| Max DD R (all) | 11.90 | 23.92 | 10.55 |
| Max losing streak | 11 | 13 | 11 |
| Trades/day | 1.14 | 1.89 | 0.27 |
| Avg stop (pts) | 46.65 | 125.76 | 163.48 |
| Best session (n≥3) | NY afternoon (0.57) | NY open (0.68) | NY pre-open (1.38) |
| Long exp / Short exp | -0.02 / 0.28 | -0.20 / 0.23 | 0.52 / -0.46 |

**Aggressive vs confirmed (best of each on train → val / test expectancy):**

- 15M: aggressive `aggr atr 5R` train 0.19 (n 143), val -0.01 (n 60), test -0.13 (n 74); confirmed `ob ob 3R` train 0.31 (n 33), val 0.06 (n 26), test -0.21 (n 20)
- 30M: aggressive `aggr atr 5R` train 0.31 (n 59), val -0.56 (n 34), test -0.02 (n 38); confirmed `eq atr 5R` train 0.30 (n 18), val 0.83 (n 11), test -0.01 (n 13)
- 60M: aggressive `aggr sweep 5R` train 0.28 (n 77), val -0.93 (n 37), test 0.64 (n 31); confirmed `ob atr 4R` train 0.71 (n 10), val -0.91 (n 5), test -1.00 (n 3)

**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**

- `15m|ob|ob|3R|pd_level|bias0`: 24 / 0.51, test -1.01 (n 4)
- `15m|ob|ob|3R|session_level|bias0`: 45 / -0.02, test -0.21 (n 10)
- `15m|ob|ob|3R|vwap|bias0`: 52 / 0.10, test -0.15 (n 14)
- `15m|ob|ob|3R|daily_open|bias0`: 37 / 0.30, test -0.12 (n 9)
- `15m|ob|ob|3R|killzone|bias0`: 34 / 0.13, test -0.57 (n 9)
- `15m|ob|ob|3R|high_vol|bias0`: 40 / 0.08, test -0.43 (n 7)
- `15m|ob|ob|3R|low_vol|bias0`: 39 / 0.11, test -0.09 (n 13)
- `30m|aggr|atr|5R|pd_level|bias0`: 86 / 0.02, test 0.61 (n 21)
- `30m|aggr|atr|5R|session_level|bias0`: 125 / -0.06, test 0.10 (n 36)
- `30m|aggr|atr|5R|vwap|bias0`: 93 / 0.01, test -0.23 (n 25)
- `30m|aggr|atr|5R|daily_open|bias0`: 122 / -0.00, test 0.23 (n 35)
- `30m|aggr|atr|5R|killzone|bias0`: 77 / 0.16, test -0.18 (n 19)
- `30m|aggr|atr|5R|high_vol|bias0`: 92 / -0.20, test -0.10 (n 29)
- `30m|aggr|atr|5R|low_vol|bias0`: 89 / 0.24, test 0.19 (n 28)
- `30m|aggr|atr|5R|killzone+low_vol|bias0`: 59 / 0.28, test -0.14 (n 17)
- `60m|ob|atr|4R|pd_level|bias0`: 7 / -0.29, test – (n 0)
- `60m|ob|atr|4R|session_level|bias0`: 16 / 0.10, test -1.00 (n 3)
- `60m|ob|atr|4R|vwap|bias0`: 16 / -0.21, test -1.00 (n 3)
- `60m|ob|atr|4R|daily_open|bias0`: 14 / 0.10, test -1.00 (n 2)
- `60m|ob|atr|4R|killzone|bias0`: 7 / 0.02, test -1.00 (n 2)
- `60m|ob|atr|4R|high_vol|bias0`: 10 / -0.74, test -1.00 (n 2)
- `60m|ob|atr|4R|low_vol|bias0`: 9 / 0.66, test -1.00 (n 1)

**Multi-timeframe:**

- A: 1H bias + 15M exec `15m|ob|ob|3R|-|bias60`: all 35 / -0.04, test -0.51 (n 8)
- B: 1H bias + 30M exec `30m|aggr|atr|5R|-|bias60`: all 106 / -0.19, test 0.17 (n 25)
- C: 30M bias + 15M exec `15m|ob|ob|3R|-|bias30`: all 38 / 0.05, test -0.21 (n 10)

## NQ futures, 1H CRT on 2 years of hourly data (MNQ costs)
2024-06-30 to 2026-11-19, 13650 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 1H |
|---|---|
| Chosen config (train) | fvg sweep 5R |
| Train n / exp | 15 / 0.62 |
| Val n / exp | 9 / -0.30 |
| TEST n / exp | 13 / -0.69 |
| Win rate (all) | 19% |
| Profit factor (all) | 0.92 |
| Expectancy R (all) | -0.07 |
| Avg winner R | 3.81 |
| Max DD R (all) | 17.79 |
| Max losing streak | 10 |
| Trades/day | 0.05 |
| Avg stop (pts) | 94.08 |
| Best session (n≥3) | NY open (0.61) |
| Long exp / Short exp | -0.57 / 0.86 |

**Aggressive vs confirmed (best of each on train → val / test expectancy):**

- 60M: aggressive `aggr atr 5R` train 0.10 (n 420), val 0.03 (n 225), test -0.15 (n 241); confirmed `fvg sweep 5R` train 0.62 (n 15), val -0.30 (n 9), test -0.69 (n 13)

**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**

- `60m|fvg|sweep|5R|pd_level|bias0`: 10 / -1.01, test -1.01 (n 4)
- `60m|fvg|sweep|5R|session_level|bias0`: 34 / 0.02, test -0.64 (n 11)
- `60m|fvg|sweep|5R|vwap|bias0`: 36 / -0.04, test -0.67 (n 12)
- `60m|fvg|sweep|5R|daily_open|bias0`: 15 / -0.21, test -0.19 (n 4)
- `60m|fvg|sweep|5R|killzone|bias0`: 16 / 0.75, test -0.19 (n 4)
- `60m|fvg|sweep|5R|high_vol|bias0`: 15 / 0.46, test -0.84 (n 5)
- `60m|fvg|sweep|5R|low_vol|bias0`: 23 / -0.45, test -0.60 (n 8)

**Multi-timeframe:**


## BTC-USD spot, 5m data, retail fees, both directions
2026-09-21 to 2026-11-19, 17280 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 15M | CRT 30M | CRT 1H | CRT 4H |
|---|---|---|---|---|
| Chosen config (train) | not enough trades | not enough trades | not enough trades | not enough trades |
| Train n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
| Val n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
| TEST n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
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

**Aggressive vs confirmed (best of each on train → val / test expectancy):**

- 15M: aggressive: too few trades; confirmed: too few trades
- 30M: aggressive: too few trades; confirmed: too few trades
- 60M: aggressive: too few trades; confirmed: too few trades
- 240M: aggressive: too few trades; confirmed: too few trades

**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**


**Multi-timeframe:**


## BTC-USD spot, 5m data, retail fees, LONG ONLY (what the $100 account can do)
2026-09-21 to 2026-11-19, 17280 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 15M | CRT 30M | CRT 1H | CRT 4H |
|---|---|---|---|---|
| Chosen config (train) | not enough trades | not enough trades | not enough trades | not enough trades |
| Train n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
| Val n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
| TEST n / exp | not enough trades | not enough trades | not enough trades | not enough trades |
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

**Aggressive vs confirmed (best of each on train → val / test expectancy):**

- 15M: aggressive: too few trades; confirmed: too few trades
- 30M: aggressive: too few trades; confirmed: too few trades
- 60M: aggressive: too few trades; confirmed: too few trades
- 240M: aggressive: too few trades; confirmed: too few trades

**Filters (each alone on the chosen config; all-period n / expectancy, test expectancy):**


**Multi-timeframe:**


## BTC-USD spot, 2 years of hourly data, LONG ONLY, 1H and 4H CRT
2024-11-20 to 2026-11-19, 17510 base candles. Split 50/25/25 train/val/test.

| Metric | CRT 1H | CRT 4H |
|---|---|---|
| Chosen config (train) | not enough trades | aggr atr 2R |
| Train n / exp | not enough trades | 10 / 0.32 |
| Val n / exp | not enough trades | 5 / -0.00 |
| TEST n / exp | not enough trades | 1 / 0.78 |
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

