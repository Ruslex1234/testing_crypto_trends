# Hour Lab: betting for or against each coin over the next hour (auto-generated)

Data: binance, 2024-12-01 to 2026-11-22, 138,552 coin-hours across 8 coins. Walk forward, retrained weekly on past data only. Runtime 195s.

Prediction quality (information coefficient, correlation of prediction with the next hour): **-0.0036**. Anything under +0.02 is too weak to pay fees.

## Does a stronger signal mean a better bet? (gross, before fees)

| Signal strength bucket | Bets | Hit rate | Avg move captured |
|---|---|---|---|
| 0.000-0.097 | 57,788 | 49.5% | +0.2 bp |
| 0.097-0.209 | 34,673 | 49.4% | -0.2 bp |
| 0.209-0.292 | 11,558 | 49.4% | -0.1 bp |
| 0.292-0.372 | 5,779 | 50.4% | +0.2 bp |
| 0.372-0.554 | 4,623 | 50.7% | +0.6 bp |
| 0.554-1.138 | 1,156 | 47.1% | -5.5 bp |

1 bp = 0.01%. Round trip fees are 4 to 20 bp, so a bucket needs a gross edge above that.

## Best model settings at each fee level

| Fees | Take top | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 | Max DD $ |
|---|---|---|---|---|---|---|---|---|---|
| 0.04% (perp maker both sides) | 20% | stop 2x hourly vol | 37.3 | 46% | -3.7 bp | -2.6 | -4.6 | $-1.72 | $1264 |
| 0.04% (perp maker both sides) | 10% | stop 2x hourly vol | 18.7 | 46% | -3.8 bp | -3.1 | -4.4 | $-0.89 | $605 |
| 0.04% (perp maker both sides) | all | stop 2x hourly vol | 192.0 | 46% | -4.0 bp | -3.6 | -4.3 | $-9.56 | $5846 |
| 0.08% (maker in, taker out) | 20% | stop 2x hourly vol | 37.3 | 43% | -7.7 bp | -6.6 | -8.6 | $-3.58 | $2334 |
| 0.08% (maker in, taker out) | 10% | stop 2x hourly vol | 18.7 | 43% | -7.8 bp | -7.1 | -8.4 | $-1.83 | $1158 |
| 0.08% (maker in, taker out) | all | stop 2x hourly vol | 192.0 | 42% | -8.0 bp | -7.6 | -8.3 | $-19.16 | $11538 |
| 0.12% (perp taker both sides) | 20% | stop 2x hourly vol | 37.3 | 40% | -11.7 bp | -10.6 | -12.6 | $-5.45 | $3415 |
| 0.12% (perp taker both sides) | 10% | stop 2x hourly vol | 18.7 | 40% | -11.8 bp | -11.1 | -12.4 | $-2.76 | $1716 |
| 0.12% (perp taker both sides) | all | stop 2x hourly vol | 192.0 | 39% | -12.0 bp | -11.6 | -12.3 | $-28.76 | $17314 |
| 0.20% (taker + slippage) | 20% | stop 2x hourly vol | 37.3 | 34% | -19.7 bp | -18.6 | -20.6 | $-9.18 | $5630 |
| 0.20% (taker + slippage) | 10% | stop 2x hourly vol | 18.7 | 35% | -19.8 bp | -19.1 | -20.4 | $-4.64 | $2834 |
| 0.20% (taker + slippage) | all | stop 2x hourly vol | 192.0 | 33% | -20.0 bp | -19.6 | -20.3 | $-47.97 | $28871 |

## Simple rules (no machine learning), at 0.08% fees

| Rule | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 |
|---|---|---|---|---|---|---|---|
| Funding contrarian (|funding|>0.03%) | stop 3x hourly vol | 0.8 | 48% | -0.7 bp | -5.2 | +8.2 | $-0.01 |
| Follow strong last hour (|z|>2) | no stop | 12.3 | 43% | -3.0 bp | -0.2 | -5.8 | $-0.47 |
| OI up + price up: follow | stop 2x hourly vol | 9.6 | 42% | -5.8 bp | -4.1 | -7.9 | $-0.69 |
| Crowd contrarian (fade crowd long/short) | stop 2x hourly vol | 174.6 | 43% | -7.5 bp | -7.6 | -7.4 | $-16.33 |
| Taker flow: follow aggressive side | stop 2x hourly vol | 60.0 | 40% | -7.6 bp | -7.8 | -7.5 | $-5.72 |
| Momentum: follow last hour | stop 2x hourly vol | 190.6 | 41% | -7.7 bp | -7.6 | -7.8 | $-18.43 |
| CRT 1h sweep (trade the reclaim) | no stop | 72.2 | 43% | -8.1 bp | -8.6 | -7.6 | $-7.30 |
| Taker flow: fade aggressive side | stop 3x hourly vol | 60.0 | 44% | -8.1 bp | -7.8 | -8.4 | $-6.09 |
| BTC leads: alts follow BTC's last hour | stop 2x hourly vol | 19.5 | 43% | -8.2 bp | -7.3 | -8.9 | $-2.00 |
| Reversal: fade last hour | no stop | 190.6 | 44% | -8.3 bp | -8.3 | -8.2 | $-19.66 |
| Hour of day seasonality (past only) | stop 3x hourly vol | 65.9 | 43% | -8.3 bp | -7.8 | -9.2 | $-6.88 |
| CRT 4h sweep (trade the reclaim) | no stop | 17.7 | 41% | -9.0 bp | -9.7 | -8.3 | $-1.98 |
| Fade strong last hour (|z|>2) | stop 2x hourly vol | 12.3 | 45% | -12.1 bp | -14.1 | -10.1 | $-1.86 |

## Honest pick

Chosen on the FIRST half only (fees 0.08%): take top 20% of signals, stop 2x hourly vol. Second half (unseen when choosing): **-8.6 bp per bet**, 37.3 bets/day, $-3.58/day on $1,000 over the whole period.

| Coin | Bets | Win | Avg net | 2nd half |
|---|---|---|---|---|
| BTC | 2948 | 39% | -7.1 bp | -8.1 |
| ETH | 2812 | 42% | -6.5 bp | -8.0 |
| SOL | 2721 | 44% | -8.6 bp | -9.8 |
| XRP | 2919 | 44% | -8.2 bp | -9.3 |
| DOGE | 2785 | 43% | -8.8 bp | -9.5 |
| ADA | 2730 | 44% | -7.4 bp | -7.8 |
| AVAX | 2769 | 44% | -6.4 bp | -6.5 |
| LINK | 2791 | 43% | -8.4 bp | -10.1 |

**Live decision:** NO TRADE: no setting kept a positive edge after 0.08% fees on data it was not tuned on.
