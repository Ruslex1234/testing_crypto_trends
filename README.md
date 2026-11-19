# Strategy Arena: crypto paper trading

Nine automated crypto strategies, each with **$100 of paper money**, trading every hour against
live market prices. A GitHub Action runs the bot, commits the balances, and a GitHub Pages
dashboard shows who is winning. After ~30 days the dashboard prints a verdict.

**No real money, no API keys, no exchange accounts.** Prices come from Coinbase's public
market data API (Kraken as fallback).

## The strategies and why they made the cut

Picked for having real evidence behind them in crypto or across asset classes, being
mechanical (no discretion), and being runnable with $100 (no leverage, no shorting).

| # | Strategy | Asset(s) | Rules | Evidence / rationale |
|---|----------|----------|-------|----------------------|
| 1 | **Buy & Hold BTC** | BTC | Buy once, never sell | The benchmark. Most active strategies fail to beat it after costs. |
| 2 | **Trend: 50 day SMA** | BTC | Hold BTC while daily close > 50 day average, else cash | Time series momentum (Moskowitz, Ooi, Pedersen 2012). Moving average rules on bitcoin show predictive power (Detzel et al. 2021). Main payoff: dodging large crashes. |
| 3 | **EMA 9/21 crossover** | ETH, 6h candles | Long when fast EMA > slow EMA | Faster momentum signal (MACD family). Catches moves earlier, pays more in whipsaw fees. |
| 4 | **Turtle breakout 20/10** | BTC + ETH, daily | Buy a 20 day high, sell a 10 day low, 50% per coin | Donchian channel breakout, the core of the Turtle system and most CTA trend funds. |
| 5 | **RSI dip buyer** | BTC, 1h | Buy RSI(14) < 30 only above 200h SMA; exit RSI > 55 or 6% stop | Short horizon mean reversion inside an uptrend (Connors style). |
| 6 | **Bollinger reversion** | SOL, 1h | Buy close below lower band (20, 2σ), sell at middle band, 8% stop | Mean reversion on a high volatility coin. Higher risk entry. |
| 7 | **Dual momentum rotation** | top 3 of BTC, ETH, SOL, XRP, DOGE, ADA, AVAX, LINK | Weekly: hold top 3 by 14 day return, only if positive, else cash | Cross sectional crypto momentum (Liu & Tsyvinski 2021; Liu, Tsyvinski, Wu 2022) plus an absolute momentum filter (Antonacci). |
| 8 | **Grid trader** | ETH | 10 levels across ±10%: buy each level down, sell each level up; re-centres if price escapes | Classic exchange bot. Wins in sideways chop, lags in strong trends. |
| 9 | **Volatility targeted trend** | BTC + ETH | Long a coin only if 30 day return > 0, sized to 50% annual vol target | Volatility scaling improves risk adjusted returns (Moreira & Muir 2017; Harvey et al. 2018). |

## How realistic is it

* **Fees:** 0.40% per fill (Kraken Pro entry tier taker). Coinbase Advanced charges ~0.60% at this size, so real costs may be higher.
* **Slippage:** 0.05% on BTC/ETH, 0.15% on other coins, always against you.
* **Execution:** signals on completed candles only (no lookahead), filled at the latest trade price. Fractional coins, $1 minimum order.
* **Churn control:** rebalances only when a position is >10% of equity off target.
* **Not modelled:** taxes, withdrawal fees, exchange downtime, partial fills.

## Setup (one time, about 2 minutes)

1. **Make this branch the default** (Settings → Branches) or merge it into `main`.
   GitHub only runs scheduled workflows on the default branch.
2. **Allow the bot to commit:** Settings → Actions → General → Workflow permissions → *Read and write*.
3. **Turn on Pages:** Settings → Pages → Source *Deploy from a branch* → pick the default branch, folder `/docs`.
4. **Kick off the first run:** Actions → *paper-trade* → *Run workflow*. After that it runs hourly.

Dashboard: `https://<your-username>.github.io/testing_crypto_trends/`

## Files

* `bot/market.py` fetches candles (Coinbase, Kraken fallback)
* `bot/strategies.py` the nine strategies, each returns target weights
* `bot/engine.py` paper broker: fees, slippage, rebalancing, state
* `docs/index.html` dashboard; `docs/data/state.json` all balances and trades
* `tests/test_sim.py` 45 day synthetic simulation (`python tests/test_sim.py`)

## Reading the verdict honestly

One month is ~720 hourly bars and maybe 5 to 30 trades per strategy. That is a small sample:
a strategy can win a month on luck. The dashboard ranks by return per unit of max drawdown and
only crowns a winner that also beat plain BTC. If nothing does, that's the answer: buy and hold
(or DCA) is the default. Not financial advice.
