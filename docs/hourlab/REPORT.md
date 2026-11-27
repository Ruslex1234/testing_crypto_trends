# Hour Lab: betting for or against each coin over the next hour (auto-generated)

Data: binance, 2024-12-05 to 2026-11-26, 138,552 coin-hours across 8 coins. Walk forward, retrained weekly on past data only. Runtime 135s.

Prediction quality (information coefficient, correlation of prediction with the next hour): **-0.0025**. Anything under +0.02 is too weak to pay fees.

## Does a stronger signal mean a better bet? (gross, before fees)

| Signal strength bucket | Bets | Hit rate | Avg move captured |
|---|---|---|---|
| 0.000-0.097 | 57,788 | 49.5% | -0.2 bp |
| 0.097-0.209 | 34,673 | 50.0% | +0.3 bp |
| 0.209-0.291 | 11,558 | 50.0% | +0.0 bp |
| 0.291-0.373 | 5,779 | 48.5% | -3.0 bp |
| 0.373-0.544 | 4,623 | 50.2% | +0.1 bp |
| 0.544-1.176 | 1,156 | 47.7% | -0.5 bp |

1 bp = 0.01%. Round trip fees are 4 to 20 bp, so a bucket needs a gross edge above that.

## Best model settings at each fee level

| Fees | Take top | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 | Max DD $ |
|---|---|---|---|---|---|---|---|---|---|
| 0.04% (perp maker both sides) | 1% | no stop | 2.0 | 48% | +0.9 bp | +2.7 | -0.7 | $+0.02 | $75 |
| 0.04% (perp maker both sides) | 2% | no stop | 3.9 | 47% | -0.4 bp | +4.0 | -4.4 | $-0.02 | $149 |
| 0.04% (perp maker both sides) | 2% | stop 3x hourly vol | 3.9 | 47% | -2.5 bp | +0.5 | -5.2 | $-0.12 | $151 |
| 0.08% (maker in, taker out) | 1% | no stop | 2.0 | 46% | -3.1 bp | -1.3 | -4.7 | $-0.08 | $111 |
| 0.08% (maker in, taker out) | 2% | no stop | 3.9 | 45% | -4.4 bp | +0.0 | -8.4 | $-0.22 | $219 |
| 0.08% (maker in, taker out) | 2% | stop 3x hourly vol | 3.9 | 44% | -6.5 bp | -3.5 | -9.2 | $-0.32 | $235 |
| 0.12% (perp taker both sides) | 1% | no stop | 2.0 | 43% | -7.1 bp | -5.3 | -8.7 | $-0.18 | $147 |
| 0.12% (perp taker both sides) | 2% | no stop | 3.9 | 42% | -8.4 bp | -4.0 | -12.4 | $-0.41 | $288 |
| 0.12% (perp taker both sides) | 2% | stop 3x hourly vol | 3.9 | 42% | -10.5 bp | -7.5 | -13.2 | $-0.51 | $349 |
| 0.20% (taker + slippage) | 1% | no stop | 2.0 | 38% | -15.1 bp | -13.3 | -16.7 | $-0.38 | $253 |
| 0.20% (taker + slippage) | 2% | no stop | 3.9 | 38% | -16.4 bp | -12.0 | -20.4 | $-0.80 | $516 |
| 0.20% (taker + slippage) | 2% | stop 3x hourly vol | 3.9 | 37% | -18.5 bp | -15.5 | -21.2 | $-0.91 | $578 |

## Simple rules (no machine learning), at 0.08% fees

| Rule | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 |
|---|---|---|---|---|---|---|---|
| Funding contrarian (|funding|>0.03%) | stop 3x hourly vol | 0.8 | 48% | -0.5 bp | -4.8 | +8.7 | $-0.00 |
| Follow strong last hour (|z|>2) | no stop | 12.3 | 43% | -3.1 bp | -0.7 | -5.4 | $-0.48 |
| OI up + price up: follow | stop 2x hourly vol | 9.5 | 43% | -5.5 bp | -3.3 | -8.3 | $-0.65 |
| Crowd contrarian (fade crowd long/short) | stop 2x hourly vol | 174.7 | 43% | -7.5 bp | -7.5 | -7.4 | $-16.28 |
| Taker flow: follow aggressive side | stop 2x hourly vol | 60.1 | 40% | -7.7 bp | -7.6 | -7.7 | $-5.75 |
| Momentum: follow last hour | stop 2x hourly vol | 190.6 | 41% | -7.7 bp | -7.5 | -7.9 | $-18.29 |
| Hour of day seasonality (past only) | stop 2x hourly vol | 68.2 | 43% | -7.9 bp | -7.0 | -9.3 | $-6.75 |
| CRT 1h sweep (trade the reclaim) | no stop | 72.2 | 43% | -8.0 bp | -8.5 | -7.4 | $-7.19 |
| Taker flow: fade aggressive side | stop 3x hourly vol | 60.1 | 44% | -8.1 bp | -7.9 | -8.2 | $-6.07 |
| Reversal: fade last hour | no stop | 190.6 | 44% | -8.3 bp | -8.4 | -8.1 | $-19.69 |
| BTC leads: alts follow BTC's last hour | stop 2x hourly vol | 19.5 | 42% | -8.4 bp | -7.5 | -9.1 | $-2.04 |
| CRT 4h sweep (trade the reclaim) | no stop | 17.7 | 41% | -8.8 bp | -9.3 | -8.4 | $-1.96 |
| Fade strong last hour (|z|>2) | stop 2x hourly vol | 12.3 | 45% | -12.3 bp | -13.5 | -11.1 | $-1.89 |

## Honest pick

Chosen on the FIRST half only (fees 0.08%): take top 2% of signals, no stop. Second half (unseen when choosing): **-8.4 bp per bet**, 3.9 bets/day, $-0.22/day on $1,000 over the whole period.

| Coin | Bets | Win | Avg net | 2nd half |
|---|---|---|---|---|
| BTC | 342 | 42% | -4.8 bp | -10.7 |
| ETH | 315 | 46% | -2.4 bp | +0.6 |
| SOL | 294 | 45% | -7.5 bp | -16.7 |
| XRP | 305 | 43% | -7.2 bp | -6.5 |
| DOGE | 297 | 44% | -5.9 bp | -13.1 |
| ADA | 238 | 47% | -2.6 bp | -13.2 |
| AVAX | 276 | 45% | -3.1 bp | -6.4 |
| LINK | 289 | 46% | -1.2 bp | -1.5 |

**Live decision:** NO TRADE: no setting kept a positive edge after 0.08% fees on data it was not tuned on.
