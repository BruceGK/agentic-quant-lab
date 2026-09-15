# ETF trend: fixed-rule modern validation

## Decision: RESEARCH MORE

**Do not promote ETF Trend to paper/shadow on this evidence.** The modern
fixed-rule results are substantially less attractive than the earlier crisis-heavy
ETF snapshot. Permanent 80/20 or 70/30 de-risking is the stronger comparator.

Why not claim a definitive executable rejection? We obtained auditable official
ETF NAV/distribution history through July 2026, but **not full-period exchange
closing transactions**. Next-session NAV is a valuation proxy, not a fill.
The frozen protocol requires clean executable-price verification before promotion.
The remaining work is that data check only; **no lookback, date, threshold or
Sharpe optimization is warranted to rescue these rules**. If actual-close
verification preserves the results below, reject the fixed trend implementation.

Only this ETF trend hypothesis was investigated. No new strategy family,
infrastructure, broker connection, paid data or trading/scheduling change.

## Frozen rules, assets and data

Protocol commit `a39b639` preceded modern strategy results.

- **Absolute12:** month-end SPY total-return level / level 12 calendar months
  earlier > 1; otherwise defensive.
- **SMA10:** month-end SPY total-return level > arithmetic mean of the last
  10 month-end levels, including the decision month; otherwise defensive.
- Equality means defensive. Monthly decisions, next-session execution, no same-close
  look-ahead. This is not a 252-/210-trading-day parameter approximation.
- Risky asset: SPY. Defensive asset: **BIL, 1-3-month US Treasury bills**, inception
  2007. No proxy splicing or leverage.
- Evaluation: January 4, 2016-July 31, 2026, 2,659 sessions; 2014-2015 warmup.
  July is the frozen common endpoint with the independent French daily RF series.
- Six fixed portfolios x 0/10/20 bps x BIL/zero-yield cash = **36 scenarios**.
  Static 80/20 and 70/30 rebalance monthly; buy-and-hold enters once.
  Initial account entry and both sides of each subsequent security rotation are charged.
- All portfolio returns are net of simulated trading costs; fund expenses are
  already present in issuer NAV. Taxes, actual fills and settlement constraints
  are not represented by these returns.

### Data quality is checked, not assumed

Official SSGA daily NAV and historical distribution workbooks provide the whole
sample. BIL's 2017-11-30 reverse split is treated as 0.5 new shares per old share;
NAV doubling is not a gain. It is corroborated by issuer share counts/assets and
an independent split-history source.

We accrue distributions at ex-date but reinvest at **payment**, preserving the
receivable meanwhile. All 12 published issuer NAV return checkpoints match within
2 bps; largest difference about 1.005 bps. An initial ex-date-reinvestment version
missed some SPY checkpoints by more than 5 bps/year and was corrected before
strategy evaluation. One NAV-only exchange-holiday observation is excluded
explicitly; no missing exchange session is forward-filled.

**Important remaining limitations:** full-history NAV rather than exchange closes;
premium/discount coverage only from 2025; current revised source vintage;
strategy units do not enforce unpaid-dividend cash constraints at switches
(maximum audited receivable fraction 0.65% SPY, 0.46% BIL). These results are
**EXPLORATORY NAV PROXIES**, not verified executable-close backtests.
The [data audit and source hashes](../research/etf_trend/README.md) disclose these
limitations and preserve original bytes outside Git.

## Results at the required 20 bps one-way stress cost

Percent values below are annualized except drawdown and exposure. Sharpe is
RF-excess, using the same independent daily rate and dates. Turnover charges
buys plus sells; the raw table also reports half-notional turnover.

| Portfolio | CAGR | Volatility | Sharpe | Max drawdown | Calmar | Worst full year |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SPY hold | 15.03% | 17.85% | 0.75 | -33.68% | 0.45 | -18.14% (2022) |
| BIL hold | 2.11% | 0.18% | -1.38 | -0.21% | 9.96 | -0.10% (2021) |
| Static 80% SPY / 20% BIL | 12.53% | 14.15% | 0.74 | -27.33% | 0.46 | -14.30% (2022) |
| Static 70% SPY / 30% BIL | 11.26% | 12.33% | 0.74 | -24.08% | 0.47 | -12.37% (2022) |
| Absolute12 / BIL | 11.26% | 16.14% | 0.60 | -33.68% | 0.33 | -12.60% (2022) |
| SMA10 / BIL | 7.85% | 12.56% | 0.48 | -28.19% | 0.28 | -22.28% (2022) |

BIL's negative excess Sharpe reflects its return versus the RF opportunity rate
and very small volatility; it does not mean a negative nominal return.
Riskless zero-yield cash has an undefined zero-RF Sharpe; the raw table also
reports its negative, variable-RF opportunity-cost statistic. Neither should
be compared to equity Sharpe as an alpha ranking.

| Portfolio | Traded notional/year | State switches* | Equity return-days | Mean equity weight | Beta to SPY | Correlation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SPY hold | 0.095x | 0 | 99.96% | 99.96% | 1.00 | 1.00 |
| BIL hold | 0.095x | 0 | 0% | 0% | ~0 | ~0 |
| Static 80/20 | 0.232x | 0 | 99.96% | 80.03% | 0.79 | ~1.00 |
| Static 70/30 | 0.275x | 0 | 99.96% | 70.06% | 0.69 | ~1.00 |
| Absolute12 | 1.608x | 8 | 87.48% | 87.48% | 0.82 | 0.90 |
| SMA10 | 4.256x | 22 | 82.63% | 82.63% | 0.49 | 0.70 |

*Initial entry excluded. Static portfolio rebalances are not binary state switches.
The initial January session earns no equity return before its entry close, explaining
99.96% rather than 100% for continuously invested comparisons.

### All required cost levels

| Portfolio | CAGR at 0 bps | CAGR at 10 bps | CAGR at 20 bps |
| --- | ---: | ---: | ---: |
| SPY hold | 15.05% | 15.04% | 15.03% |
| BIL hold | 2.13% | 2.12% | 2.11% |
| Static 80/20 | 12.58% | 12.55% | 12.53% |
| Static 70/30 | 11.32% | 11.29% | 11.26% |
| Absolute12 | 11.62% | 11.44% | 11.26% |
| SMA10 | 8.77% | 8.31% | 7.85% |

The result is weak even without transaction fees. At 20 bps, Absolute12 sacrifices
**3.77 percentage points/year** versus same-cost SPY without reducing its worst
drawdown. SMA10 sacrifices **7.18 points/year** for only 5.50 points of full-sample
drawdown reduction. Static 70/30 gives more drawdown reduction and higher Sharpe
than either, with approximately Absolute12's CAGR.

## Decomposing exits, avoided losses and missed rebounds

All >=10% SPY peak-to-trough episodes within the evaluation window are retained.
The 2016 correction began before this sample; its defensive trade is still present
in the all-spells table rather than silently dropped.

| Equity episode | SPY trough loss | Absolute12 behavior | SMA10 behavior |
| --- | ---: | --- | --- |
| 2018-01-26 to 2018-02-08 | -10.07% | No exit; bears the decline | No exit; bears the decline |
| 2018-09-20 to 2018-12-24 | -19.29% | Exits 2019-01-02, **after trough**, re-enters Mar 1; misses 12.03% while out | Exits Nov 1, re-enters Dec 3 before the final fall; exits again Jan 2, re-enters Mar 1 |
| 2020-02-19 to 2020-03-23 | -33.68% | Exits Apr 1, **after trough**, re-enters May 1; misses 14.61% while out | Exits Mar 2, re-enters Jun 1: avoids 27.39% further fall, but misses 36.85% rebound from trough |
| 2022-01-03 to 2022-10-12 | -24.47% | Exits Jun 1, re-enters 2023-05-01: avoids 12.24% further fall, misses 17.45% rebound | Exits Mar 1, re-enters Apr 1; exits May 2, re-enters Dec 1; further Jan/Nov 2023 whipsaws before market recovery |
| 2025-02-19 to 2025-04-08 | -18.71% | No exit | Exits Apr 1, re-enters Jun 2: avoids 11.49% further fall, misses 19.30% rebound |

Avoided decline and missed rebound are **not additive profits and losses**.
They use different starting levels and occur within a single trade spell.
For exits after the market trough, only the unowned post-exit rebound is counted
as missed; the rebound already held before exit is not incorrectly discarded.
Exact decision dates, execution dates, paths, fees and net relative outcomes are
in [drawdown_events.csv](../research/etf_trend/results/drawdown_events.csv) and
[defensive_spells.csv](../research/etf_trend/results/defensive_spells.csv).

### Why the crisis protection did not become a durable net advantage

- SMA10's 2020 exit greatly reduced temporary losses. But SPY returned approximately
  -0.64% from its Mar 2 exit close to Jun 1 re-entry; after two rotations at 20 bps,
  the defensive spell was also approximately -0.64%. Its completed-cycle wealth
  advantage was essentially zero. Protection mattered while the crash was unfolding,
  but the subsequent rebound consumed the terminal-return advantage.
- Absolute12 remained invested through the full COVID trough, then stepped out for
  the sharp April rebound. Lower overall average exposure did not lower its worst loss.
- The useful May-December 2022 SMA spell gained about **1.13% relative wealth**
  versus staying in SPY, net of 20 bps. Other 2022/2023 round trips outweighed that gain.
- SMA10's worst complete year was **-22.28% in 2022**, worse than SPY's -18.14%,
  even though it reduced part of the peak-to-trough loss within that year.

There is no positive whole-sample timing-return benefit to attribute to one crisis.
Temporary drawdown protection was most dramatic in COVID for SMA10, with some
protection in 2022/2025; it was not consistently converted into favorable net
performance versus static de-risking.

## Whipsaws and defensive time

At 20 bps:

- **Absolute12:** four completed defensive spells, all four negative relative to
  remaining in SPY under the predeclared whipsaw definition; three were <=3 months.
  Total defensive time: **332 sessions**, plus initial uninvested entry timing.
- **SMA10:** eleven defensive spells, **nine whipsaws**, with 461 defensive sessions.
  The other two spells were COVID (near-zero completed-cycle net advantage) and
  May-December 2022 (positive relative advantage).
- Across nonoverlapping spells, the relative log-wealth accounting reconciles exactly
  to the whole strategy-versus-SPY wealth gap. These are opportunity losses, not
  a claim that the account lost that much money in absolute terms.
- The costly short re-entry cycles are visible in 2016, late 2018/early 2019,
  June 2019, March 2022, January/November 2023, spring 2025 and April 2026.

No buffers, alternate months or thresholds were tested to repair these failures.

## Defensive yield versus literal zero cash

| Model, 20 bps | BIL CAGR | Zero-cash CAGR | BIL max drawdown | Zero-cash max drawdown |
| --- | ---: | ---: | ---: | ---: |
| Static 80/20 | 12.53% | 12.08% | -27.33% | -27.37% |
| Static 70/30 | 11.26% | 10.59% | -24.08% | -24.14% |
| Absolute12 | 11.26% | 11.10% | -33.68% | -33.68% |
| SMA10 | 7.85% | 7.92% | -28.19% | -28.27% |

Why does zero cash slightly outperform BIL for SMA10? Cash rotations trade only
the equity leg, whereas BIL rotations also incur defensive ETF buys/sells.
Holding actual exposures and fees fixed, BIL total return contributes approximately
**0.328 percentage points/year** to Absolute12 and **0.379 points/year** to SMA10.
The cash experiment saves trading costs; it is not evidence that positive yield hurts.

Defensive total return includes Treasury discount accrual/price movement,
distributions, reinvestment and embedded fund fees. We do not relabel all of it
as a guaranteed interest rate. Exact component dollar P&L and matched-cost
counterfactuals are in [attribution.csv](../research/etf_trend/results/attribution.csv).

## Answers to the nine decision questions

1. **Material drawdown reduction?** Absolute12: no, its maximum loss equals SPY's.
   SMA10: yes versus 100% SPY, but less than simple 70/30, and at a much larger CAGR cost.
2. **CAGR sacrificed?** At 20 bps, about 3.77 points/year for Absolute12 and
   7.18 points/year for SMA10 versus same-cost SPY.
3. **Beat permanent 80/20 or 70/30?** No convincing case. At 20 bps, 80/20 has
   higher CAGR, lower volatility and lower drawdown than Absolute12. Static 70/30
   has higher CAGR, lower volatility, higher Sharpe and lower drawdown than SMA10.
4. **Useful at 20 bps?** Tactical protection exists, but the overall trade-off does
   not justify the additional switching versus permanent de-risking.
5. **Useful with zero-yield cash?** No rescue. Absolute12 still bears the full worst
   crash; SMA10 still trails static alternatives substantially.
6. **Only one crisis?** COVID dominates SMA10's most dramatic temporary protection,
   but there is no positive net timing benefit to claim. Multiple crises and
   rebound/whipsaw regimes are explicitly included.
7. **Whipsaw damage?** Material: four of four Absolute12 defensive cycles and
   nine of eleven SMA10 cycles lost relative wealth to SPY at 20 bps.
8. **Same story?** They agree on exposure about **88.98% of sessions**, but differ
   critically in crisis timing: SMA10 exits before the COVID trough; Absolute12
   exits afterward. Both fail the overall net trade-off versus static de-risking here.
9. **Robust enough for paper/shadow?** **Not yet.** Full-period executable-price
   data remains unverified, and even the NAV-proxy case is weak. Do not promote
   or search alternative parameters; verify the same fixed rules on actual closes,
   and reject if the adverse result persists.

## Validation, reproduction and limits

- Frozen rules before results; no parameter tournament.
- Both signals advanced by one month while retaining their true later availability
  were **rejected as look-ahead before simulation**.
- Exact fee tests, first-entry timing, source-date checks, split neutrality,
  payment-date receivables, P&L identities, open-spell censoring and missed-rebound
  boundaries are regression-tested.
- All 36 model/fee/defense scenarios and full daily paths are retained, not just a winner.
- **54 targeted tests passed**: 20 dedicated ETF tests, 24 existing research tests,
  and 10 unchanged Phase 0 policy/scientific controls. Ruff, default and research
  Pyright, wheel/source builds and all source/code/result hashes passed verification.
  The maximum defensive-spell accounting residual was below `2e-15` log-wealth units.
- A focused independent correctness review found no significant issue; the final
  explicit rebound-boundary and spell-accounting tests additionally guard attribution.
- This is one retrospective, predominantly strong equity-market decade, not universal
  evidence against trend across assets, longer crises or other independently specified objectives.

[Reproduction instructions and all artifacts](../research/etf_trend/README.md).
Classification is exactly **RESEARCH MORE**, limited to execution-data verification.
No exact rule is promoted to paper/shadow, and no Robinhood execution is built.

```text
scheduled_recording_enabled = false
live_execution_enabled = false
```
