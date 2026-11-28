# Hour Lab: betting for or against each coin over the next hour (auto-generated)

Data: binance, 2024-12-06 to 2026-11-27, 138,552 coin-hours across 8 coins. Walk forward, retrained weekly on past data only. Runtime 127s.

Prediction quality (information coefficient, correlation of prediction with the next hour): **+0.0028**. Anything under +0.02 is too weak to pay fees.

## Does a stronger signal mean a better bet? (gross, before fees)

| Signal strength bucket | Bets | Hit rate | Avg move captured |
|---|---|---|---|
| 0.000-0.097 | 57,788 | 49.8% | +0.1 bp |
| 0.097-0.209 | 34,673 | 50.0% | +1.1 bp |
| 0.209-0.291 | 11,558 | 49.3% | -0.5 bp |
| 0.291-0.372 | 5,779 | 50.6% | +1.0 bp |
| 0.372-0.552 | 4,623 | 49.1% | -1.2 bp |
| 0.552-1.150 | 1,156 | 51.0% | -0.3 bp |

1 bp = 0.01%. Round trip fees are 4 to 20 bp, so a bucket needs a gross edge above that.

## Best model settings at each fee level

| Fees | Take top | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 | Max DD $ |
|---|---|---|---|---|---|---|---|---|---|
| 0.04% (perp maker both sides) | 1% | no stop | 2.0 | 49% | +0.0 bp | -3.8 | +3.5 | $+0.00 | $69 |
| 0.04% (perp maker both sides) | 1% | stop 3x hourly vol | 2.0 | 48% | -2.6 bp | -7.8 | +2.1 | $-0.07 | $76 |
| 0.04% (perp maker both sides) | 1% | stop 2x hourly vol | 2.0 | 47% | -3.2 bp | -7.1 | +0.5 | $-0.08 | $81 |
| 0.08% (maker in, taker out) | 1% | no stop | 2.0 | 46% | -4.0 bp | -7.8 | -0.5 | $-0.10 | $88 |
| 0.08% (maker in, taker out) | 1% | stop 3x hourly vol | 2.0 | 45% | -6.6 bp | -11.8 | -1.9 | $-0.17 | $105 |
| 0.08% (maker in, taker out) | 1% | stop 2x hourly vol | 2.0 | 44% | -7.2 bp | -11.1 | -3.5 | $-0.18 | $110 |
| 0.12% (perp taker both sides) | 1% | no stop | 2.0 | 44% | -8.0 bp | -11.8 | -4.5 | $-0.20 | $123 |
| 0.12% (perp taker both sides) | 1% | stop 3x hourly vol | 2.0 | 43% | -10.6 bp | -15.8 | -5.9 | $-0.27 | $164 |
| 0.12% (perp taker both sides) | 1% | stop 2x hourly vol | 2.0 | 42% | -11.2 bp | -15.1 | -7.5 | $-0.29 | $172 |
| 0.20% (taker + slippage) | 1% | no stop | 2.0 | 39% | -16.0 bp | -19.8 | -12.5 | $-0.41 | $246 |
| 0.20% (taker + slippage) | 1% | stop 3x hourly vol | 2.0 | 39% | -18.6 bp | -23.8 | -13.9 | $-0.48 | $287 |
| 0.20% (taker + slippage) | 1% | stop 2x hourly vol | 2.0 | 38% | -19.2 bp | -23.1 | -15.5 | $-0.49 | $295 |

## Simple rules (no machine learning), at 0.08% fees

| Rule | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 |
|---|---|---|---|---|---|---|---|
| Funding contrarian (|funding|>0.03%) | stop 3x hourly vol | 0.8 | 48% | -0.8 bp | -5.3 | +8.7 | $-0.01 |
| Follow strong last hour (|z|>2) | no stop | 12.3 | 43% | -3.3 bp | -0.7 | -5.7 | $-0.50 |
| OI up + price up: follow | stop 2x hourly vol | 9.5 | 43% | -5.5 bp | -3.3 | -8.2 | $-0.65 |
| Crowd contrarian (fade crowd long/short) | stop 2x hourly vol | 174.7 | 43% | -7.4 bp | -7.4 | -7.4 | $-16.22 |
| Taker flow: follow aggressive side | stop 2x hourly vol | 60.1 | 40% | -7.6 bp | -7.5 | -7.7 | $-5.74 |
| Momentum: follow last hour | stop 2x hourly vol | 190.6 | 41% | -7.7 bp | -7.5 | -7.9 | $-18.23 |
| Hour of day seasonality (past only) | stop 3x hourly vol | 66.8 | 43% | -8.0 bp | -7.2 | -9.2 | $-6.68 |
| CRT 1h sweep (trade the reclaim) | no stop | 72.2 | 43% | -8.0 bp | -8.4 | -7.6 | $-7.24 |
| Taker flow: fade aggressive side | stop 3x hourly vol | 60.1 | 44% | -8.1 bp | -8.0 | -8.2 | $-6.08 |
| Reversal: fade last hour | no stop | 190.6 | 44% | -8.3 bp | -8.5 | -8.1 | $-19.73 |
| BTC leads: alts follow BTC's last hour | stop 2x hourly vol | 19.5 | 42% | -8.4 bp | -7.2 | -9.4 | $-2.05 |
| CRT 4h sweep (trade the reclaim) | no stop | 17.7 | 41% | -8.8 bp | -9.3 | -8.3 | $-1.95 |
| Fade strong last hour (|z|>2) | stop 2x hourly vol | 12.3 | 45% | -12.1 bp | -13.7 | -10.7 | $-1.87 |

## Honest pick

Chosen on the FIRST half only (fees 0.08%): take top all of signals, stop 2x hourly vol. Second half (unseen when choosing): **-8.3 bp per bet**, 192.0 bets/day, $-18.55/day on $1,000 over the whole period.

| Coin | Bets | Win | Avg net | 2nd half |
|---|---|---|---|---|
| BTC | 14447 | 38% | -7.6 bp | -7.8 |
| ETH | 14447 | 41% | -7.4 bp | -8.7 |
| SOL | 14447 | 43% | -7.6 bp | -8.0 |
| XRP | 14447 | 42% | -8.1 bp | -8.8 |
| DOGE | 14447 | 43% | -8.2 bp | -9.1 |
| ADA | 14447 | 44% | -7.5 bp | -7.6 |
| AVAX | 14447 | 44% | -7.6 bp | -7.7 |
| LINK | 14447 | 44% | -7.9 bp | -8.8 |

**Live decision:** NO TRADE: no setting kept a positive edge after 0.08% fees on data it was not tuned on.
