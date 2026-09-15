# Frozen modern ETF trend experiment

Frozen on 2026-09-15 before fetching/evaluating modern strategy results.
Baseline repository: `e6d6205`; Phase 0 remains unchanged.

## Exact rules (no optimization)

1. **Absolute12:** at the final SPY trading close of each calendar month, invest
   100% in SPY if its total-return level is strictly above its level at the final
   close **12 calendar months earlier**; otherwise 100% defensive.
2. **SMA10:** at the same decision time, invest 100% in SPY if its total-return
   level is strictly above the arithmetic mean of **10 month-end total-return
   levels, including the current month**; otherwise 100% defensive.

These are exact calendar-month definitions, not the earlier exploratory
252-/210-session approximations. Equality means defensive. No cash-rate hurdle,
buffer, alternate threshold, volatility scaling, stop, date search or parameter grid.
Adjusted total-return levels are preferred to unadjusted dividend-jumping prices.
No future adjustment is allowed to alter historical signal ratios; cross-check
price/distribution reconstruction and source conventions.

## Assets and sample

SPY is the only risky asset. First-choice defensive ETF is **BIL**, the liquid
1-3-month Treasury-bill fund, whose 2007 inception precedes the sample. Do not
splice SGOV or incompatible instruments. If BIL cannot be obtained/audited,
document the failure before considering SHV (also pre-2016); do not select a
defensive fund based on strategy performance.

Target evaluation: first trading session of January 2016 through **2026-07-31**.
The fixed end is the latest month already available in the independently cached
French daily risk-free series. This avoids extending the sample with an invented
cash rate. Seek data from December 2014 (prefer earlier warmup) to cover 12-month
momentum at December 2015. Report actual available coverage and any shorter window;
do not replace modern ETF history with academic market proxies.

Use public/free or already available data, no paid registration, secret or broker
connection. Respect blocked/gated endpoints. Save source URLs, hashes and retrieval
times, audit duplicate/missing sessions, positive prices, splits/distributions,
total-return reconstruction, and independent issuer/source agreement.
No clean data means **RESEARCH MORE**, not a made-up backtest.

## Six primary portfolios and costs

SPY buy-and-hold; defensive buy-and-hold; static 80% SPY/20% defensive;
static 70% SPY/30% defensive; Absolute12; SMA10.
Static mixes rebalance at the same monthly decisions. Buy-and-hold enters once.
All start from the same initial cash on the first evaluation session.
December 2015 signals may execute only at that first January session's **close**.
Subsequent month-end signals execute at the following SPY trading session's close.
The prior allocation earns the intervening return. Initial entry and every buy
and sale incur the fee; portfolio wealth is self-financing. No execution-price
advantage is inferred from a month-end close already observed.

Only one-way 0, 10 and 20 bps scenarios. A full SPY-to-BIL rotation trades about
200% of portfolio notional and is charged on both legs. Turnover reports traded
notional/year and half that amount as one-way-equivalent turnover.
Monthly scheduling/entitlements/settlement are hypothetical; no actual orders.

Repeat the same six allocations and exact signals with the defensive leg replaced
by **literal 0%-yield cash**, charging costs only for securities actually traded.
Also construct a *matched-cost* zero-defensive-return attribution with original BIL
notional costs to separate defensive total-return contribution from trading costs.
Defensive ETF total return includes accrued yield, price moves, fees and reinvestment;
do not call all of it pure interest without distribution data.

## Metrics and decompositions

For every portfolio/scenario: CAGR; 252-session annualized volatility; Sharpe using
the independent daily French RF opportunity rate (also disclose zero-RF Sharpe);
daily max drawdown; Calmar; worst **complete** calendar year; turnover; equity-state
switch count (initial entry separately); proportion of days with equity exposure
and average equity weight; beta/correlation to SPY on identical dates.
No ranking of near-riskless ETF Sharpe as an equity-alpha result.
Partial-year 2026 is not a complete worst/best year.

Detect all SPY peak-to-trough drawdown episodes of at least **10%** in the evaluation
sample using total-return highs; report recovery date or right censoring. Within
each episode and each trend, report decision/actual exit/re-entry dates; SPY loss
after exit to subsequent trough while defensive; rebound from the defensive-spell
low to re-entry missed; total net relative wealth during each defensive spell;
time defensive; and matched-cost BIL-versus-zero contribution.
Do not double-count overlapping avoided losses and missed rebounds as independent P&L.

Enumerate **all** defensive spells. Label a completed spell a whipsaw when SPY's
total return from exit close to re-entry close is positive and the net timing
result underperforms staying in SPY. Also report lengths <=3 calendar months
separately, with no parameter search. A switch alone is not a closed trade.
Use exact wealth/log-return identities for attribution and costs, with tests.

Show fixed 2016-2019, 2020, 2021, 2022, 2023-2025 and 2026 YTD regimes, plus
crisis-exclusion/descriptive contribution tables. Do not cherry-pick one crisis
to promote the result. Compare Absolute12 and SMA10 signal agreement, defensive
overlap and whether conclusions survive 20 bps/zero-yield cash.

## Mandatory falsification and decision

Take each monthly signal from the **following** month and attempt to assign it to
the earlier decision month, retaining its true later `available_at`. The harness
must reject this intentionally advanced signal as look-ahead, before simulation.
The existing null/planted-positive/future-perturbation/cost tests remain in force.

Choose exactly **PROMOTE TO PAPER/SHADOW**, **RESEARCH MORE**, or **REJECT**.
Promotion requires clean-enough modern data, meaningful drawdown reduction that
is not solely a one-crisis artifact, and a defensible trade-off versus permanent
80/20 and 70/30 de-risking at 20 bps and zero cash. It need not beat SPY CAGR,
but opportunity cost and whipsaws must be acceptable and explicit. If promoted,
choose simplicity and consistent behavior, not maximum Sharpe.

No production-ready claim. No broker code, live trading, infrastructure, scheduler
or activation-policy change. `scheduled_recording_enabled=false` and
`live_execution_enabled=false` throughout.
