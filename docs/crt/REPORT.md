# CRT Professional Trading System: Research Report

**Instrument:** Nasdaq 100 futures (NQ / MNQ). **Timeframes:** 15M, 30M, 1H (plus 4H on BTC).
**Code:** rules in [`bot/crt.py`](../../bot/crt.py), backtester in [`research/crt_research.py`](../../research/crt_research.py),
raw output in [`results.md`](results.md) / [`results.json`](results.json), indicator in [`crt_indicator.pine`](crt_indicator.pine).
Run date: 2026-11-20. Re-run any time: Actions → *crt-research* → Run workflow.

---

## Bottom line

1. **30M CRT is the only timeframe that held up out of sample.** The model is: aggressive entry after the
   sweep candle closes, stop beyond the sweep extreme, fixed 2R target. Expectancy was positive and stable
   across all three data partitions: **+0.12R train (178 trades), +0.14R validation (82), +0.11R untouched
   test (119)**. That's 379 trades, profit factor 1.19, after MNQ commissions and slippage.
2. **The edge is small and not yet statistically conclusive** (t ≈ 1.7). It also comes mostly from
   **shorts** (+0.27R vs +0.01R for longs) in a 10 week sample. Treat it as a candidate under forward
   test, not a proven system. It is being forward-tested live on the dashboard from 2026-11-20.
3. **1H CRT does not work** as defined here. On 2 years of NQ data it lost **-0.18R per trade over 2,055
   trades**, in *every* session and under *every* filter. **15M CRT has no edge** (-0.02R over 749 trades,
   positive only in the test slice).
4. **None of the confirmation filters reliably helped**: VWAP, previous day levels, session levels, daily
   open, killzones, volatility regime and higher timeframe bias. Several *looked* good in one period and
   failed in another. That's the curve fitting your brief warned about.
5. **$100 cannot trade this.** The average 30M stop is 60 points: **$120 per MNQ contract, $1,200 per NQ**.
   At 1 to 2% risk per trade you need roughly **$6k to $12k for 1 MNQ**. The $100 arena account therefore
   runs CRT on BTC, where only the **4H** timeframe clears retail spot fees (about 1 trade a month).

---

## 1. Candle Range Theory: definitions used (objective, testable)

| Concept | Rule in this system |
|---|---|
| CRT range candle (C0) | Any closed candle on the CRT timeframe whose range ≥ **0.6 × ATR(14)** of that timeframe (filters out insignificant candles) |
| Range High / Low / 50% | C0 high, C0 low, (H+L)/2 |
| Liquidity sweep | One of the next **3** candles trades beyond C0's high (or low) **and closes back inside C0** |
| Breakout (not a sweep) | A candle **closes** beyond C0's high/low → that side is invalid. This is the key distinction from a breakout |
| Rejection | The sweep candle's close back inside the range |
| Displacement | A later candle with body ≥ **0.6 × ATR** in the trade direction |
| MSS / CHoCH | That displacement candle closes beyond the structure formed between C0 and the sweep (long: above the highest high since C0) |
| Entry zones tested | Aggressive (market after rejection), FVG midpoint, CRT 50%, order block (open of the last opposite candle before displacement) |
| Continuation target | Opposite side of the CRT range, or fixed R multiples |

No lookahead: every decision uses only closed candles. Orders are filled on 5 minute candles. If a stop
and a target are both touched inside the same 5 minute candle, **the stop is assumed first**. A limit
fill candle never gets credit for a target in that same candle.

The simulator was validated on synthetic random-walk data with realistic intrabar paths. Random entries
and all CRT variants came out at about 0R there, so it doesn't manufacture edge. (An earlier synthetic
test with unrealistic straight-line candles *did* fake an edge of +0.1R; that's why this check matters.)

## 2. Data, costs and method

| | |
|---|---|
| NQ intraday | Yahoo `NQ=F`, 5 minute candles, 2026-09-11 → 2026-11-19 (≈ 13.7k candles, the free maximum) |
| NQ long history | `NQ=F` hourly, 2024-06-30 → 2026-11-19 (≈ 13.7k candles), 1H CRT only |
| BTC | Coinbase BTC-USD 5 minute (60 days) and hourly (2 years) |
| MNQ costs | $1.24 commission round trip (0.62 pt) + 1 tick slippage on stops/market exits + 1 tick on market entries |
| NQ costs | $4.20 round trip (0.21 pt) + same slippage. NQ vs MNQ changed results by about 0.01R: costs are small next to a 60 pt stop |
| BTC costs | 0.40% taker / 0.25% maker + 0.05% slippage per side |
| Cost rule | Skip any trade whose round-trip cost exceeds 0.25R |
| Split | Chronological **50% train / 25% validation / 25% out-of-sample test** |
| Grid | 4 entries × 4 stops × 6 targets = 96 configs per timeframe, both directions, one position at a time |
| Selection | Pre-registered rule: maximise the **worse** of train and validation expectancy (n ≥ 20 / 10). Test data never influences selection |

**Overfitting check (important).** Picking the config with the best *training* result failed out of sample
on every timeframe. Example: the best 15M training config scored +0.53R in train and -0.22R in test.
Requiring a config to be positive in **both** train and validation was far more reliable:

| Timeframe | Configs positive in test | Passed train + val | …and also positive in test |
|---|---|---|---|
| 15M | 42 / 68 | 3 | **0** |
| 30M | 36 / 53 | 26 | **20 (77%)** |
| 1H (60 days) | 21 / 24 | 0 | 0 |
| 1H (2 years) | 6 / 74 | 5 | **0** |

## 3. Comparison report (like-for-like model: aggressive entry, sweep stop, 2R)

| Metric | CRT 15M | CRT 30M | CRT 1H (60d) | CRT 1H (2 yrs) |
|---|---|---|---|---|
| Win rate | 35% | **39%** | 35% | 29% |
| Profit factor | 0.97 | **1.19** | 1.00 | 0.75 |
| Expectancy (R, after costs) | -0.02 | **+0.12** | 0.00 | -0.18 |
| Train / Val / **Test** expectancy | -0.06 / -0.09 / +0.11 | **+0.12 / +0.14 / +0.11** | -0.06 / -0.22 / +0.37 | -0.16 / -0.18 / -0.21 |
| Average winner (R) | 1.91 | 1.94 | 1.88 | 1.87 |
| Maximum drawdown (R) | 77.7 | **14.9** | 27.1 | 384 |
| Max consecutive losses | 9 | 9 | 8 | 20 |
| Number of trades | 749 | 379 | 188 | 2,055 |
| Trades per day (23h market) | 10.8 | 5.5 | 2.8 | 2.4 |
| Average stop | 39 pts | 60 pts | 85 pts | 65 pts |
| Best trading session | none positive in a meaningful way | **NY midday +0.31R (n 53), NY afternoon +0.29R (n 47)** | Asia +0.27R (n 51), not confirmed in 2-yr data | none (all negative) |
| Best entry model | none validated | **Aggressive** (validated); 50%-level limit promising but unvalidated | none validated | none |

The 2-year 1H test uses hourly candles for fills, so a stop and a target in the same hour count as a loss.
That makes it slightly pessimistic, but it was negative in every session and under every filter, which
no fill assumption explains away.

### Sessions (30M model, all data)

| Session (New York time) | Trades | Expectancy |
|---|---|---|
| Asia / overnight (17:00-02:00) | 105 | **-0.04R** |
| London (02:00-07:00) | 93 | +0.10R |
| NY pre-open (07:00-09:30) | 47 | +0.11R |
| NY open (09:30-11:00) | 34 | +0.20R |
| NY midday (11:00-14:00) | 53 | **+0.31R** |
| NY afternoon (14:00-17:00) | 47 | **+0.29R** |

Restricting to New York hours (07:00-17:00) gives about 2.6 trades a day at roughly +0.23R. Caution:
this was chosen after seeing all the data, so it's a hypothesis for the forward test, not a validated rule.

### Volatility regime
At 30M, high-volatility conditions (ATR above its 100 candle median) did better than low volatility:
+0.15R vs +0.01R overall, and +0.18R vs +0.09R in test. The direction is consistent, the sample is small.

## 4. Exact rules: the validated 30M model

**SHORT**
1. A 30M candle closes (C0) with range ≥ 0.6 × ATR(14, 30M). Mark its high, low and 50%.
2. Within the next 3 candles, a 30M candle trades **above** C0's high and **closes back below it** (and above C0's low).
   If any of those candles closes above C0's high first, there's no short: it's a breakout.
3. **Entry:** sell at the open of the next 30M candle.
4. **Stop:** highest high reached during the sweep + 0.1 × ATR. This is the true invalidation: price
   reclaiming the swept liquidity means the idea is wrong.
5. **Target:** 2R from the fill.
6. **Time stop:** exit at market after 32 candles (16 hours) if neither level is hit.
7. **Skip** if costs exceed 0.25R, or if a trade is already open.

**LONG:** mirror image. Sweep **below** C0's low, close back above it, buy the next open, stop below the
sweep low, 2R target.

**Confirmed variant (fewer, slower trades, matches your "1 to 2 a day" preference):** after the sweep, wait
for a displacement candle (body ≥ 0.6 ATR) that closes beyond the sweep candle's opposite extreme (MSS).
Then rest a limit at the CRT 50% level with the stop beyond the order block, targeting 3R. In-sample it
made +0.34R per trade with a 6.5R max drawdown, but on only **46 trades (0.7/day)**. It passed train and
validation and was positive in test (+0.10R, 13 trades). Promising, unproven. It's in the forward test too.

### Position sizing
Risk per contract = stop distance × point value. At the 60 pt average stop: **MNQ $120, NQ $1,200**.
Contracts = floor(account × risk% ÷ risk per contract).
- $10,000 account, 1% risk → $100 → **0 MNQ** on a 60 pt stop. Trade only when the stop is ≤ 50 pts, or risk 1.2%.
- $25,000, 1% → $250 → 2 MNQ.
- $150,000, 1% → $1,500 → 1 NQ.

The indicator prints the stop in points, the dollar risk per contract and the contract count for your settings.

## 5. Stop-loss comparison (30M, aggressive, 2R)

| Stop | Expectancy | Trades | Verdict |
|---|---|---|---|
| Beyond the sweep extreme | **+0.12R** | 379 | Best: the real invalidation point |
| Beyond the rejection candle | +0.12R | 379 | Same as sweep for aggressive entries (the sweep candle *is* the rejection candle) |
| Beyond the order block | +0.12R | 379 | Same for aggressive entries; differs only for confirmed entries |
| 1.5 × ATR | +0.00R | 175 | Worse: wider, arbitrary, not tied to structure |

## 6. Take-profit comparison (30M, aggressive, sweep stop)

| Target | Expectancy (all) | Test | Max DD | Note |
|---|---|---|---|---|
| CRT range opposite | **-0.11R** | +0.01R | 45R | The "textbook" target performed worst: often too close to clear costs, or never reached |
| **2R** | **+0.12R** | **+0.11R** | **15R** | Most consistent across all partitions |
| 3R | +0.21R | +0.08R | 14R | Higher average, but validation was unusually strong and test weaker; 13-loss streak |
| 4R | +0.12R | +0.09R | 22R | |
| 5R | +0.11R | +0.20R | 31R | 30-loss streak: psychologically brutal |
| Partial (½ at 2R, stop to BE, rest at range or 4R) | -0.02R | -0.04R | 26R | Partials *reduced* expectancy |

How often price got to each target before the stop (5R config): **2R 38%, 3R 28%, 4R 21%, 5R 15%**.
A higher R:R did not improve profitability. 2R gives the best balance of expectancy, drawdown and streaks.
Untested: PDH/PDL, equal highs/lows and unfilled FVG targets (left for future work).

## 7. Confirmation filters (each tested alone on the 30M model; all-period / test expectancy)

| Filter | All | Test | Trades | Verdict |
|---|---|---|---|---|
| None (baseline) | +0.12 | +0.11 | 379 | |
| Sweep reaches previous day high/low | +0.04 | +0.21 | 146 | Inconsistent: worse in train, better in test |
| Sweep reaches Asia/London high/low | +0.08 | +0.20 | 274 | Inconsistent |
| VWAP side after MSS | +0.16 | -0.00 | 158 | Failed out of sample |
| Daily open (discount/premium) | -0.02 | +0.04 | 281 | Hurt |
| Killzones (London 02-05, NY 08:30-11) | +0.05 | +0.06 | 133 | Fewer trades, no improvement |
| High volatility | +0.15 | +0.18 | 184 | Mild, consistent improvement; the only candidate |
| Low volatility | +0.01 | +0.09 | 230 | Worse |
| 1H CRT bias (multi-timeframe) | -0.04 | -0.10 | 194 | **Hurt** |

**Not tested** (needs data or definitions this pipeline doesn't have yet): Volume Profile POC/VAH/VAL,
anchored VWAP, discretionary support/resistance.

## 8. Multi-timeframe

| Config | All | Test | Trades |
|---|---|---|---|
| A. 1H bias + 15M execution | -0.12 | +0.10 | 359 |
| B. 1H bias + 30M execution | -0.04 | -0.10 | 194 |
| C. 30M bias + 15M execution | -0.02 | +0.14 | 370 |
| **D. Independent 30M** | **+0.12** | **+0.11** | **379** |

No multi-timeframe combination beat the plain 30M model. The 1H bias consistently made things worse,
which fits 1H CRT having no edge of its own.

## 9. Answers

1. **Most profitable timeframe:** 30M, the only one with positive expectancy in train, validation *and* test (+0.12R, PF 1.19).
2. **Most consistent:** 30M (+0.12 / +0.14 / +0.11R across the three periods). 15M and 1H swung sign between periods.
3. **Lowest drawdown:** 30M (14.9R vs 27R for 1H and 78R for 15M on the same 10 weeks).
4. **Best entry opportunities:** 30M aggressive entries (about 5.5 a day on a 23h market; about 2.6 a day in NY hours).
   For 1 to 2 a day, the confirmed 50%-limit variant (0.7 a day) is the candidate, pending forward data.
5. **Necessary confirmations:** the **close back inside the range** (sweep, not breakout) and a **significant range candle**
   (≥ 0.6 ATR). Displacement/MSS confirmation cut trades by 85 to 90% without a validated improvement. No external filter proved necessary.
6. **Stop-loss:** beyond the sweep extreme plus a 0.1 ATR buffer. That's the structural invalidation. ATR stops were worse.
7. **Take-profit:** a single fixed 2R exit. The CRT range opposite, partial exits and 4 to 5R targets were all worse or less stable.
8. **Best multi-timeframe combination:** none. Independent 30M beat every combination, and 1H bias hurt.
9. **Avoid trading:** with 1H or 15M CRT; in the Asia session (30M was -0.04R there); when the range candle is under 0.6 ATR;
   when costs exceed 0.25R; in low volatility; and with a 1H bias filter. **Also stop trading** if the forward test falls below
   about -10R over its first 50 trades, which would be outside what the backtest supports.

## 10. Limitations (read before risking money)

- **Short history:** 10 weeks of 5 minute NQ data is all that's freely available. One market regime, and a short-side
  skew that may not repeat. The 2-year check exists only for 1H.
- **Statistical strength:** +0.12R over 379 trades is about 1.7 standard errors from zero. Encouraging, not proof.
- **Selection:** with 96 configs per timeframe, some survivors are expected by chance. 20 of 26 train+val survivors
  staying positive in test (versus a 68% base rate) is evidence of something real, but modest.
- **Fills:** 5 minute resolution with worst-case same-candle rules. Real fills on fast moves can be worse; limit orders may queue.
- **Futures roll** and holiday sessions aren't specially handled in Yahoo's continuous contract.

## 11. Forward test (live, on the dashboard)

From 2026-11-20, every hourly run pulls fresh NQ 5 minute data and records new trades for:
- **30M aggressive, sweep stop, 2R** (main model)
- **30M limit at 50%, order block stop, 3R** (confirmed variant)

Results are shown in R after MNQ costs and as a $100 account risking 2% per trade. **Decision rule:** after 50 or more
forward trades, keep the model only if forward expectancy is positive and inside the backtest's range.

## 12. TradingView indicator (Pine Script v6)

File: [`crt_indicator.pine`](crt_indicator.pine). Paste it into the TradingView Pine editor → *Add to chart*.

- Detects 15M / 30M / 1H CRT ranges, each switchable (30M on by default, since it's the validated model).
- Draws range high, low and 50%, liquidity sweeps, entries, stop and target. Shows R:R, stop in points,
  $ per contract and contract count.
- Aggressive or confirmed entries (displacement + MSS, then FVG or 50% limit); sweep, rejection or ATR stops; range or 2R to 5R targets.
- Non-repainting: CRT candles come from `request.security(..., [1], lookahead_on)` and all logic runs on closed bars only.
  One active setup per timeframe, so no duplicate signals.
- Alerts on every entry. A statistics table per timeframe (trades, win rate, expectancy, profit factor; gross R on the loaded history).
- Differences from the backtest: the sweep must be the candle immediately after C0 (classic 2-candle CRT), and the stats exclude costs.

It could not be compiled in this environment. If TradingView reports an error, send me the line number and message.
