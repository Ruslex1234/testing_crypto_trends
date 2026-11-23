# Strategy verdict (8 year replay, 2019 to Nov 2026)

Every strategy was replayed hour by hour through the live bot engine on real Coinbase history,
with 0.4% fees plus slippage per fill and no lookahead. 17 strategies, plus 45 parameter variants
for robustness.

## Results

| Strategy | CAGR | Max drawdown | Sharpe | Verdict |
|---|---|---|---|---|
| BTC above 50 day SMA | +52.2% | 63% | 1.17 | Best return, but deep drawdown |
| Volatility targeted trend (BTC+ETH) | +40.3% | **46%** | 1.12 | **Best risk adjusted. Pick for real money** |
| Turtle breakout 20/10 (BTC+ETH) | +36.8% | 47% | 0.95 | Solid backup |
| Buy and hold BTC (benchmark) | +42.4% | 77% | 0.87 | The bar to beat |
| BTC/ETH 50/50 | +44.5% | 78% | 0.88 | Same pain as holding |
| DCA BTC | +39.6% | 77% | 0.84 | Same pain as holding |
| Momentum rotation | +30.5% | 81% | 0.75 | Worse than holding |
| TRW TPI trend | +24.3% | 59% | 0.72 | Trails simpler trend rules |
| TRW box breakout | +8.5% | 31% | 0.53 | Too few wins |
| Crash buyer | +2.1% | 66% | 0.21 | No edge |
| CRT on BTC 4H | -1.7% | 22% | -0.31 | No edge on crypto (50 trades) |
| EMA 9/21 crossover | -6.7% | 88% | 0.15 | **Retired** |
| Grid trader | -20.9% | 90% | -0.32 | **Retired** |
| RSI dip buyer | -45.1% | 99% | -2.01 | **Retired** |
| Bollinger reversion | -45.1% | 99% | -1.94 | **Retired** |

## Robustness (is it luck?)

- Vol target: 36 of 36 parameter variants made money. 22 of 36 made money in both halves of the period.
- SMA trend: 9 of 9 variants made money. Median CAGR +25%.
- The edge is real but it is a *trend* edge: it comes from sitting out crashes, not from predicting hours.

## The honest caveats

1. The last 2 years (BTC -38%) were hard for every strategy. Vol target made +13%/yr there, and the SMA rule +6%/yr.
   Mean reversion and grid trading blew up.
2. Returns come in bursts. Only about 45% of 30 day windows are positive. You will have losing months.
3. The 8 year figures include the 2020 to 2021 mania. Plan on 15 to 20% a year, not 40%.
4. Hourly prediction (AI predictor, 1h long/short) showed **no edge after fees** in walk forward tests.

## Capital needed for $20/day ($7,300/yr)

| Assumed annual return | Capital needed |
|---|---|
| 40% (8 year history repeats) | $18,250 |
| 20% (realistic) | $36,500 |
| 13% (last 2 years) | $56,000 |

Expect a 45% drawdown at some point: $10,000 can become $5,500 before it recovers.

## Rules before real money

1. Paper run vol_target live through the month end review (it joined the arena on 2026-11-21).
2. Start real money with the amount you can watch fall by half without selling.
3. Spot only, no leverage. Exchange with low fees (maker fees under 0.2%) since every rebalance pays them.
4. Kill switch: if live results trail the lab by more than 15 points over 90 days, stop and reassess.

## Hourly for/against betting (Hour Lab, Nov 2026)

Tested on 138,552 coin-hours (8 coins, Dec 2024 to Nov 2026) with Binance taker flow, open interest,
top trader and crowd long/short ratios, funding and S&P futures, plus 13 simple rules and a walk forward
gradient boosting model. Result: **no edge**. The best signal correlates under 1.3% with the next hour.
Every setting loses after 0.08% fees on unseen data; the most active one loses about $19/day on $1,000.
Hourly betting stays off. Full report: [docs/hourlab/REPORT.md](../hourlab/REPORT.md). It reruns daily
and will flip `docs/hourlab/live_config.json` to enabled only if an edge appears on unseen data.
