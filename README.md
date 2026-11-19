# Strategy Arena: crypto paper trading

Ten automated crypto strategies, each with **$100 of paper money**, trading every hour against
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
| 2 | **TRW style TPI trend** | BTC, daily | 8 trend signals (EMA21, SMA50, EMA9/21, MACD, RSI, 14d ROC, 20d range, SMA20 slope) vote ±1; long while average > 0 | Reconstruction of the "Trend Probability Indicator" approach taught in The Real World investing campus. Aggregating signals cuts single-indicator whipsaw. |
| 3 | **TRW style box breakout** | BTC, ETH, SOL, daily | Close above a 20 day consolidation box (<30% tall) while price > 50 SMA and EMA9 > EMA21; stop at box middle, sized to risk 3% of the account; exit on stop or close < EMA21 | Reconstruction of the "box system" from The Real World trading campus, with its risk-per-trade rule. |
| 4 | **EMA 9/21 crossover** | ETH, 6h candles | Long when fast EMA > slow EMA | Faster momentum signal (MACD family). Catches moves earlier, pays more in whipsaw fees. |
| 5 | **Daily DCA** | BTC | Spread the $100 into BTC over 30 days (~$3/day) | The realistic beginner approach. Head to head with #1 it answers: lump sum or drip it in? (Vanguard 2012: lump sum wins ~2/3 of the time, DCA lowers regret.) |
| 6 | **Crash buyer** | BTC | Buy 1/3 at 15%, 2/3 at 25%, all at 35% below the 60 day high; sell at 95% of that high | Contrarian counterweight to the trend strategies, so the arena has something that acts in falling markets. |
| 7 | **RSI dip buyer** | BTC, 1h | Buy RSI(14) < 30; exit RSI > 55 or 6% stop | Short horizon mean reversion (Connors style). No trend filter. |
| 8 | **Bollinger reversion** | SOL, 1h | Buy close below lower band (20, 2σ), sell at middle band, 8% stop | Mean reversion on a high volatility coin. Higher risk entry. |
| 9 | **Dual momentum rotation** | top 3 of BTC, ETH, SOL, XRP, DOGE, ADA, AVAX, LINK | Weekly: hold top 3 by 14 day return, only if positive, else cash | Cross sectional crypto momentum (Liu & Tsyvinski 2021; Liu, Tsyvinski, Wu 2022) plus an absolute momentum filter (Antonacci). |
| 10 | **Grid trader** | ETH | 10 levels across ±10%: buy each level down, sell each level up; re-centres if price escapes | Classic exchange bot. Wins in sideways chop, lags in strong trends. |

## Stops and how they're scored

Enforced every hourly run by `bot/risk.py`, before the strategy gets a say:

| Strategy | Stop |
|---|---|
| TRW TPI, EMA crossover | Trailing: highest price since entry minus 2.5 × ATR(14d). Only moves up. |
| Momentum rotation | Same, 3 × ATR (alts swing harder) |
| RSI dip buyer / Bollinger | 6% / 8% below entry |
| TRW box breakout | Middle of the box; position sized so a stop costs 3% of the account |
| Crash buyer | Disaster stop 45% below its reference high, then 7 day cooldown |
| Buy & hold, DCA, grid | None by design |

After any stop-out the coin is blocked for 24h so the strategy can't instantly rebuy. Every
stop is re-checked 24h and 72h later: if price kept falling, the stop **saved** money; if it
bounced, it **cost** money. The dashboard's stop scorecard shows the tally.

## Every hour is a scored decision

Each run, every strategy decides: get in, get out, or do nothing. The run then uses data the
previous run never saw (the 5 minute candles since then) to:

* **Enforce stops against real lows**, like a resting stop order (gaps fill at the worse open).
* **Score past decisions** after 1h and 24h: was being in/out right? *Follow* (obey the strategy)
  vs *Opposite* (do the reverse). A strategy with negative edge is worth betting against.
* **Log scenarios**: every level a strategy watches (entry trigger, take profit, grid line,
  breakout, crash tier) is checked against real highs/lows; crossings are logged and re-checked
  24h later.

## How realistic is it

* **Fees:** 0.40% per fill (Kraken Pro entry tier taker). Coinbase Advanced charges ~0.60% at this size, so real costs may be higher.
* **Slippage:** 0.05% on BTC/ETH, 0.15% on other coins, always against you.
* **Execution:** signals on completed candles only (no lookahead), filled at the latest trade price. Fractional coins, $1 minimum order.
* **Churn control:** rebalances only when a position is >10% of equity off target (2% for DCA).
* **Transparency:** every strategy prints what it is waiting for on the dashboard.

Changed on day 1 (2026-11-19): Turtle breakout and volatility targeted trend were retired
(they duplicated the 50 day trend signal and all sat in cash together); DCA and crash buyer
replaced them, and the RSI dip buyer lost its uptrend filter. Later the same day the plain 50 day
trend account was replaced by two strategies modelled on The Real World (Andrew Tate's course)
crypto campuses. Those are reconstructions from public student notes and community discussion,
not the paid course material itself.
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
* `bot/strategies.py` the strategies, each returns target weights
* `bot/engine.py` paper broker: fees, slippage, rebalancing, state
* `docs/index.html` dashboard; `docs/data/state.json` all balances and trades
* `tests/test_sim.py` 45 day synthetic simulation (`python tests/test_sim.py`)

## Reading the verdict honestly

One month is ~720 hourly bars and maybe 5 to 30 trades per strategy. That is a small sample:
a strategy can win a month on luck. The dashboard ranks by return per unit of max drawdown and
only crowns a winner that also beat plain BTC. If nothing does, that's the answer: buy and hold
(or DCA) is the default. Not financial advice.
