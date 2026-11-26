# Hour Lab: betting for or against each coin over the next hour (auto-generated)

Data: binance, 2024-12-04 to 2026-11-25, 138,552 coin-hours across 8 coins. Walk forward, retrained weekly on past data only. Runtime 112s.

Prediction quality (information coefficient, correlation of prediction with the next hour): **+0.0006**. Anything under +0.02 is too weak to pay fees.

## Does a stronger signal mean a better bet? (gross, before fees)

| Signal strength bucket | Bets | Hit rate | Avg move captured |
|---|---|---|---|
| 0.000-0.098 | 57,788 | 49.4% | -0.1 bp |
| 0.098-0.211 | 34,673 | 50.0% | +1.1 bp |
| 0.211-0.292 | 11,558 | 50.8% | -0.1 bp |
| 0.292-0.373 | 5,779 | 49.3% | -1.8 bp |
| 0.373-0.545 | 4,623 | 48.7% | -1.9 bp |
| 0.545-1.201 | 1,156 | 50.3% | +1.7 bp |

1 bp = 0.01%. Round trip fees are 4 to 20 bp, so a bucket needs a gross edge above that.

## Best model settings at each fee level

| Fees | Take top | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 | Max DD $ |
|---|---|---|---|---|---|---|---|---|---|
| 0.04% (perp maker both sides) | 1% | no stop | 2.0 | 49% | +1.8 bp | +2.9 | +0.9 | $+0.04 | $57 |
| 0.04% (perp maker both sides) | 1% | stop 3x hourly vol | 2.0 | 49% | +1.6 bp | +3.2 | +0.2 | $+0.04 | $55 |
| 0.04% (perp maker both sides) | 1% | stop 2x hourly vol | 2.0 | 48% | +0.6 bp | +1.0 | +0.2 | $+0.01 | $53 |
| 0.08% (maker in, taker out) | 1% | no stop | 2.0 | 47% | -2.2 bp | -1.1 | -3.1 | $-0.05 | $86 |
| 0.08% (maker in, taker out) | 1% | stop 3x hourly vol | 2.0 | 46% | -2.4 bp | -0.8 | -3.8 | $-0.06 | $80 |
| 0.08% (maker in, taker out) | 1% | stop 2x hourly vol | 2.0 | 45% | -3.4 bp | -3.0 | -3.8 | $-0.08 | $75 |
| 0.12% (perp taker both sides) | 1% | no stop | 2.0 | 43% | -6.2 bp | -5.1 | -7.1 | $-0.15 | $120 |
| 0.12% (perp taker both sides) | 1% | stop 3x hourly vol | 2.0 | 43% | -6.4 bp | -4.8 | -7.8 | $-0.16 | $116 |
| 0.12% (perp taker both sides) | 1% | stop 2x hourly vol | 2.0 | 42% | -7.4 bp | -7.0 | -7.8 | $-0.18 | $116 |
| 0.20% (taker + slippage) | 1% | no stop | 2.0 | 40% | -14.2 bp | -13.1 | -15.1 | $-0.35 | $215 |
| 0.20% (taker + slippage) | 1% | stop 3x hourly vol | 2.0 | 40% | -14.4 bp | -12.8 | -15.8 | $-0.35 | $218 |
| 0.20% (taker + slippage) | 1% | stop 2x hourly vol | 2.0 | 39% | -15.4 bp | -15.0 | -15.8 | $-0.38 | $233 |

## Simple rules (no machine learning), at 0.08% fees

| Rule | Stop | Bets/day | Win | Avg net | 1st half | 2nd half | $/day on $1,000 |
|---|---|---|---|---|---|---|---|
| Funding contrarian (|funding|>0.03%) | stop 3x hourly vol | 0.8 | 48% | -0.7 bp | -5.2 | +8.2 | $-0.01 |
| Follow strong last hour (|z|>2) | no stop | 12.3 | 43% | -3.1 bp | -0.9 | -5.3 | $-0.48 |
| OI up + price up: follow | stop 2x hourly vol | 9.5 | 42% | -5.9 bp | -4.2 | -8.0 | $-0.70 |
| Crowd contrarian (fade crowd long/short) | stop 2x hourly vol | 174.7 | 43% | -7.4 bp | -7.6 | -7.2 | $-16.23 |
| Taker flow: follow aggressive side | stop 2x hourly vol | 60.0 | 40% | -7.7 bp | -7.8 | -7.6 | $-5.77 |
| Momentum: follow last hour | stop 2x hourly vol | 190.6 | 41% | -7.7 bp | -7.6 | -7.8 | $-18.42 |
| Taker flow: fade aggressive side | stop 3x hourly vol | 60.0 | 44% | -8.0 bp | -7.7 | -8.3 | $-6.03 |
| CRT 1h sweep (trade the reclaim) | no stop | 72.2 | 43% | -8.0 bp | -8.7 | -7.4 | $-7.25 |
| Hour of day seasonality (past only) | stop 3x hourly vol | 67.8 | 43% | -8.1 bp | -7.4 | -9.0 | $-6.83 |
| Reversal: fade last hour | no stop | 190.6 | 44% | -8.2 bp | -8.3 | -8.1 | $-19.56 |
| BTC leads: alts follow BTC's last hour | stop 2x hourly vol | 19.5 | 42% | -8.5 bp | -8.4 | -8.7 | $-2.08 |
| CRT 4h sweep (trade the reclaim) | no stop | 17.7 | 42% | -8.8 bp | -9.4 | -8.3 | $-1.95 |
| Fade strong last hour (|z|>2) | stop 2x hourly vol | 12.3 | 45% | -12.2 bp | -13.5 | -11.1 | $-1.88 |

## Honest pick

Chosen on the FIRST half only (fees 0.08%): take top 1% of signals, stop 3x hourly vol. Second half (unseen when choosing): **-3.8 bp per bet**, 2.0 bets/day, $-0.06/day on $1,000 over the whole period.

| Coin | Bets | Win | Avg net | 2nd half |
|---|---|---|---|---|
| BTC | 172 | 43% | -3.4 bp | -5.3 |
| ETH | 148 | 50% | +6.9 bp | +10.9 |
| SOL | 151 | 53% | +4.9 bp | +6.0 |
| XRP | 151 | 43% | -11.0 bp | -11.9 |
| DOGE | 137 | 48% | +3.8 bp | +4.1 |
| ADA | 122 | 48% | -5.6 bp | -19.8 |
| AVAX | 143 | 45% | -13.4 bp | -4.9 |
| LINK | 160 | 42% | -1.7 bp | -10.1 |

**Live decision:** NO TRADE: no setting kept a positive edge after 0.08% fees on data it was not tuned on.
