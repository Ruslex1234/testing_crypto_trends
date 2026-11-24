# Hour Lab: betting for or against each coin over the next hour (auto-generated)

Data: binance, 2024-12-02 to 2026-11-23, 138,552 coin-hours across 8 coins. Walk forward, retrained weekly on past data only. Runtime 140s.

Prediction quality (information coefficient, correlation of prediction with the next hour): **+0.0076**. Anything under +0.02 is too weak to pay fees.

## Does a stronger signal mean a better bet? (gross, before fees)

| Signal strength bucket | Bets | Hit rate | Avg move captured |
|---|---|---|---|
| 0.000-0.098 | 57,788 | 49.7% | +0.1 bp |
| 0.098-0.208 | 34,673 | 49.6% | +0.5 bp |
| 0.208-0.290 | 11,558 | 50.2% | +0.1 bp |
| 0.290-0.370 | 5,779 | 50.9% | +2.2 bp |
| 0.370-0.550 | 4,623 | 50.5% | +3.4 bp |
| 0.550-1.230 | 1,156 | 49.7% | -2.5 bp |

1 bp = 0.01%. Round trip fees are 4 to 20 bp, so a bucket needs a gross edge above that.

## Best model settings at each fee level

| Fees | Take top | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 | Max DD $ |
|---|---|---|---|---|---|---|---|---|---|
| 0.04% (perp maker both sides) | 5% | no stop | 9.5 | 47% | -1.7 bp | -1.1 | -2.1 | $-0.20 | $195 |
| 0.04% (perp maker both sides) | 10% | no stop | 18.9 | 47% | -2.1 bp | -3.0 | -1.3 | $-0.50 | $465 |
| 0.04% (perp maker both sides) | 10% | stop 3x hourly vol | 18.9 | 47% | -2.5 bp | -2.7 | -2.4 | $-0.60 | $510 |
| 0.08% (maker in, taker out) | 5% | no stop | 9.5 | 44% | -5.7 bp | -5.1 | -6.1 | $-0.68 | $452 |
| 0.08% (maker in, taker out) | 10% | no stop | 18.9 | 44% | -6.1 bp | -7.0 | -5.3 | $-1.45 | $951 |
| 0.08% (maker in, taker out) | 10% | stop 3x hourly vol | 18.9 | 44% | -6.5 bp | -6.7 | -6.4 | $-1.54 | $1016 |
| 0.12% (perp taker both sides) | 5% | no stop | 9.5 | 41% | -9.7 bp | -9.1 | -10.1 | $-1.15 | $735 |
| 0.12% (perp taker both sides) | 10% | no stop | 18.9 | 41% | -10.1 bp | -11.0 | -9.3 | $-2.39 | $1511 |
| 0.12% (perp taker both sides) | 10% | stop 3x hourly vol | 18.9 | 41% | -10.5 bp | -10.7 | -10.4 | $-2.48 | $1572 |
| 0.20% (taker + slippage) | 5% | no stop | 9.5 | 37% | -17.7 bp | -17.1 | -18.1 | $-2.10 | $1304 |
| 0.20% (taker + slippage) | 10% | no stop | 18.9 | 36% | -18.1 bp | -19.0 | -17.3 | $-4.28 | $2633 |
| 0.20% (taker + slippage) | 10% | stop 3x hourly vol | 18.9 | 36% | -18.5 bp | -18.7 | -18.4 | $-4.37 | $2693 |

## Simple rules (no machine learning), at 0.08% fees

| Rule | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 |
|---|---|---|---|---|---|---|---|
| Funding contrarian (|funding|>0.03%) | stop 3x hourly vol | 0.8 | 48% | -0.7 bp | -5.2 | +8.2 | $-0.01 |
| Follow strong last hour (|z|>2) | no stop | 12.3 | 43% | -2.9 bp | +0.0 | -5.8 | $-0.45 |
| OI up + price up: follow | stop 2x hourly vol | 9.5 | 43% | -5.5 bp | -3.6 | -7.9 | $-0.65 |
| Crowd contrarian (fade crowd long/short) | stop 2x hourly vol | 174.6 | 43% | -7.4 bp | -7.6 | -7.3 | $-16.26 |
| Taker flow: follow aggressive side | stop 2x hourly vol | 60.0 | 40% | -7.6 bp | -7.7 | -7.6 | $-5.73 |
| Momentum: follow last hour | stop 2x hourly vol | 190.6 | 41% | -7.7 bp | -7.6 | -7.9 | $-18.35 |
| BTC leads: alts follow BTC's last hour | stop 2x hourly vol | 19.5 | 43% | -7.8 bp | -6.9 | -8.5 | $-1.90 |
| CRT 1h sweep (trade the reclaim) | no stop | 72.2 | 43% | -8.1 bp | -8.6 | -7.5 | $-7.30 |
| Taker flow: fade aggressive side | stop 2x hourly vol | 60.0 | 44% | -8.1 bp | -7.8 | -8.4 | $-6.08 |
| Reversal: fade last hour | no stop | 190.6 | 44% | -8.3 bp | -8.4 | -8.1 | $-19.66 |
| Hour of day seasonality (past only) | stop 2x hourly vol | 66.6 | 43% | -8.4 bp | -7.6 | -9.5 | $-6.96 |
| CRT 4h sweep (trade the reclaim) | no stop | 17.7 | 41% | -9.0 bp | -9.8 | -8.3 | $-2.00 |
| Fade strong last hour (|z|>2) | stop 2x hourly vol | 12.3 | 45% | -12.3 bp | -14.3 | -10.3 | $-1.89 |

## Honest pick

Chosen on the FIRST half only (fees 0.08%): take top 5% of signals, no stop. Second half (unseen when choosing): **-6.1 bp per bet**, 9.5 bets/day, $-0.68/day on $1,000 over the whole period.

| Coin | Bets | Win | Avg net | 2nd half |
|---|---|---|---|---|
| BTC | 806 | 41% | -6.1 bp | -5.8 |
| ETH | 719 | 45% | -2.7 bp | -4.6 |
| SOL | 691 | 47% | -1.7 bp | -2.9 |
| XRP | 743 | 44% | -6.2 bp | -9.0 |
| DOGE | 701 | 45% | -3.3 bp | -6.4 |
| ADA | 681 | 45% | -4.2 bp | -5.3 |
| AVAX | 663 | 44% | -7.2 bp | -5.7 |
| LINK | 728 | 42% | -13.6 bp | -9.3 |

**Live decision:** NO TRADE: no setting kept a positive edge after 0.08% fees on data it was not tuned on.
