# Hour Lab: betting for or against each coin over the next hour (auto-generated)

Data: binance, 2024-12-03 to 2026-11-24, 138,552 coin-hours across 8 coins. Walk forward, retrained weekly on past data only. Runtime 148s.

Prediction quality (information coefficient, correlation of prediction with the next hour): **+0.0049**. Anything under +0.02 is too weak to pay fees.

## Does a stronger signal mean a better bet? (gross, before fees)

| Signal strength bucket | Bets | Hit rate | Avg move captured |
|---|---|---|---|
| 0.000-0.097 | 57,788 | 49.7% | +0.3 bp |
| 0.097-0.208 | 34,673 | 50.3% | +0.8 bp |
| 0.208-0.291 | 11,558 | 50.1% | +0.7 bp |
| 0.291-0.374 | 5,779 | 49.5% | +1.7 bp |
| 0.374-0.553 | 4,623 | 50.8% | +0.3 bp |
| 0.553-1.207 | 1,156 | 48.5% | -3.6 bp |

1 bp = 0.01%. Round trip fees are 4 to 20 bp, so a bucket needs a gross edge above that.

## Best model settings at each fee level

| Fees | Take top | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 | Max DD $ |
|---|---|---|---|---|---|---|---|---|---|
| 0.04% (perp maker both sides) | 5% | no stop | 9.3 | 48% | -2.2 bp | -0.8 | -3.4 | $-0.25 | $274 |
| 0.04% (perp maker both sides) | 5% | stop 2x hourly vol | 9.3 | 47% | -2.7 bp | -1.7 | -3.7 | $-0.32 | $248 |
| 0.04% (perp maker both sides) | 10% | no stop | 18.7 | 47% | -2.8 bp | -2.2 | -3.4 | $-0.66 | $455 |
| 0.08% (maker in, taker out) | 5% | no stop | 9.3 | 45% | -6.2 bp | -4.8 | -7.4 | $-0.72 | $475 |
| 0.08% (maker in, taker out) | 5% | stop 2x hourly vol | 9.3 | 44% | -6.7 bp | -5.7 | -7.7 | $-0.78 | $517 |
| 0.08% (maker in, taker out) | 10% | no stop | 18.7 | 44% | -6.8 bp | -6.2 | -7.4 | $-1.60 | $1012 |
| 0.12% (perp taker both sides) | 5% | no stop | 9.3 | 42% | -10.2 bp | -8.8 | -11.4 | $-1.18 | $753 |
| 0.12% (perp taker both sides) | 5% | stop 2x hourly vol | 9.3 | 41% | -10.7 bp | -9.7 | -11.7 | $-1.25 | $794 |
| 0.12% (perp taker both sides) | 10% | no stop | 18.7 | 41% | -10.8 bp | -10.2 | -11.4 | $-2.53 | $1569 |
| 0.20% (taker + slippage) | 5% | no stop | 9.3 | 37% | -18.2 bp | -16.8 | -19.4 | $-2.12 | $1307 |
| 0.20% (taker + slippage) | 5% | stop 2x hourly vol | 9.3 | 36% | -18.7 bp | -17.7 | -19.7 | $-2.18 | $1349 |
| 0.20% (taker + slippage) | 10% | no stop | 18.7 | 36% | -18.8 bp | -18.2 | -19.4 | $-4.40 | $2683 |

## Simple rules (no machine learning), at 0.08% fees

| Rule | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 |
|---|---|---|---|---|---|---|---|
| Funding contrarian (|funding|>0.03%) | stop 3x hourly vol | 0.8 | 48% | -0.7 bp | -5.2 | +8.2 | $-0.01 |
| Follow strong last hour (|z|>2) | no stop | 12.3 | 43% | -2.9 bp | -0.6 | -5.2 | $-0.45 |
| OI up + price up: follow | stop 2x hourly vol | 9.5 | 43% | -5.5 bp | -3.6 | -7.9 | $-0.66 |
| Crowd contrarian (fade crowd long/short) | stop 2x hourly vol | 174.7 | 43% | -7.4 bp | -7.6 | -7.2 | $-16.20 |
| Taker flow: follow aggressive side | stop 2x hourly vol | 60.0 | 40% | -7.7 bp | -7.7 | -7.6 | $-5.75 |
| Momentum: follow last hour | stop 2x hourly vol | 190.6 | 41% | -7.7 bp | -7.5 | -7.9 | $-18.34 |
| CRT 1h sweep (trade the reclaim) | no stop | 72.1 | 43% | -8.1 bp | -8.7 | -7.4 | $-7.27 |
| BTC leads: alts follow BTC's last hour | stop 2x hourly vol | 19.5 | 43% | -8.1 bp | -7.4 | -8.6 | $-1.97 |
| Taker flow: fade aggressive side | stop 2x hourly vol | 60.0 | 44% | -8.1 bp | -7.7 | -8.4 | $-6.06 |
| Reversal: fade last hour | no stop | 190.6 | 44% | -8.2 bp | -8.4 | -8.1 | $-19.65 |
| Hour of day seasonality (past only) | stop 2x hourly vol | 66.0 | 43% | -8.4 bp | -7.7 | -9.4 | $-6.93 |
| CRT 4h sweep (trade the reclaim) | no stop | 17.7 | 42% | -8.8 bp | -9.3 | -8.3 | $-1.95 |
| Fade strong last hour (|z|>2) | stop 2x hourly vol | 12.3 | 45% | -12.3 bp | -13.6 | -10.9 | $-1.89 |

## Honest pick

Chosen on the FIRST half only (fees 0.08%): take top 5% of signals, no stop. Second half (unseen when choosing): **-7.4 bp per bet**, 9.3 bets/day, $-0.72/day on $1,000 over the whole period.

| Coin | Bets | Win | Avg net | 2nd half |
|---|---|---|---|---|
| BTC | 793 | 42% | -6.6 bp | -4.9 |
| ETH | 708 | 46% | -3.0 bp | -3.7 |
| SOL | 650 | 45% | -6.4 bp | -8.9 |
| XRP | 752 | 45% | -5.9 bp | -9.2 |
| DOGE | 645 | 43% | -6.8 bp | -7.0 |
| ADA | 669 | 47% | -5.9 bp | -14.9 |
| AVAX | 699 | 45% | -8.0 bp | -5.3 |
| LINK | 686 | 45% | -6.9 bp | -6.3 |

**Live decision:** NO TRADE: no setting kept a positive edge after 0.08% fees on data it was not tuned on.
