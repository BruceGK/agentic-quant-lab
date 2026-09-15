# Long-only strategy tournament: protocol before measured results

Created 2026-09-15, on research branch based on frozen Phase 0 commit `04dda08`.
No portfolio performance was calculated before this protocol. This is not a
registered prospective study: the rules and historical crises are already known.
Any temporal holdout is **pseudo-out-of-sample**, never an untouched discovery set.

## Decision, not parameter competition

Compare simple long-only, unlevered strategies for modest personal capital:
time-series trend, cross-sectional equity momentum, momentum plus quality,
quality/value, and PEAD. No strategy is assumed to win. All numerical results
are **EXPLORATORY** for personal implementation unless security-level membership,
corporate actions, publication availability and actual cost coverage are established.
No trading, broker connection, Azure operations or Phase 0 changes are permitted.

Predeclare the central models: 10-month moving average, 12-month absolute momentum,
12-1 monthly stock momentum with 20 names, large-stock French high-momentum sleeve,
large-stock robust-profitability sleeve, and equal quality/value combination.
Report the entire neighborhood, not just its winner.

## Data hierarchy and known gates

1. French Data Library monthly value-weighted market, RF, 6 size/momentum,
   6 size/operating-profitability, 6 size/value, 25 value/profitability portfolios.
   Use the **long portfolios**, not long-short factor returns as equity investments.
   Large-size baskets mitigate but do not establish liquidity or replicable holdings.
   Their internal trading, constituent counts and PIT vintage information are not
   available in monthly return series; costs must be scenario haircuts, not measured.
2. Immutable public QSTrader adjusted daily SPY/AGG snapshots (historical, not current).
   These permit actual ETF rules with next-session close execution, but lack recent
   regimes and independent corporate-action verification. No raw price-only return
   is substituted for a total-return series.
3. Immutable QSTK Yahoo historical stock snapshot. A fixed list of recognizable
   liquid stocks is explicitly a **survivor-selected convenience panel**, not a
   historical index. It is used to quantify sensitivity to breadth, costs, turnover,
   timing and concentration, never to establish investable stock alpha.
4. Live Yahoo was 429, Stooq returned a browser challenge, a recent PWB dataset
   requires a paid subscription, and an educational book's EOD panel is simulated.
   No challenge bypass, paid registration, fabricated price history or simulated
   data is used as market evidence.
5. No clean joined stock-level PIT fundamentals/earnings consensus were obtained.
   Momentum-quality filtering/composites and PEAD cannot be certified from prices
   or factor sleeves. If no valid free data appears, reject implementing those
   candidates now and record the research gap, not an invented numeric proxy.

Raw source bytes are cached locally, hashes and download URLs retained. The frozen
manifest can detect revised data. Raw third-party datasets are not committed.

## Experiments

- ETF trend: absolute returns over 6/9/10/12 months (126/189/210/252 sessions);
  price/total-return-index versus 6/9/10/12-month SMA; monthly decisions.
  Also dual 3/10-month SMA and a capped 10% annual-volatility target.
  No leverage: volatility scaling is `min(1, target / past volatility)`.
  Fallback: RF/T-bill proxy and literal zero-yield cash. SPY and SPY/AGG
  equal-allocation trends compared with same-assets buy-and-hold.
- Long historical market timing: same monthly absolute/SMA rules on French
  market total-return proxy and RF, 1964 onward (earlier data supplementary).
  It is not a SPY backtest. Monthly close-only data use an extra entire month
  between a signal and its eligible return to avoid same-close execution fiction.
  Also disclose immediate-next-month optimistic and two-month lag stress.
- Stock momentum: 6-1/9-1/12-1 and equal-rank combination; 10/20/30/50 names
  (when available), monthly and 10-session ("biweekly approximation") rebalance.
  Skip 21 sessions, include 126/189/252-session history. Price >= $5, trailing
  63-session median dollar volume >= $10m/$50m/$100m. No sector cap initially;
  report sector/volatility concentration, then compare one 30% sector-cap variant
  and a 1.5x buy/hold rank buffer rather than continuously tuning thresholds.
  Benchmark SPY, fixed-universe equal weight, and seeded random selections.
- Academic long legs: large high-momentum versus large low-momentum/market;
  robust-profitability versus market; value versus market; high value AND high
  profitability cell(s) versus single sorts. A 50/50 momentum-quality *sleeve mix*
  is not a stock-level quality filter and must never be described as one.
- Complementarity: aligned net returns and simple equal-weight mixes only.
  No optimizer, leverage, capital allocator or selection based on the best Sharpe.

## Execution, costs, diagnostics

Daily signal at close t may first rebalance at close t+1; first earned return is
t+1 to t+2. Performance includes gaps, dividends through adjusted-close returns,
weight drift and initial entry costs. No missing held-security return is filled
with zero or dropped silently.

Trade notional is the sum of absolute asset-weight changes from **drifted**
pretrade weights; purchases and sales are both charged. Self-financing portfolio
cost calculation must account for fees reducing investable capital.
Daily ETF one-way costs: 2 / 5 / 20 bps; stock: 5 / 15 / 50 bps.
Academic unobservable internal turnover: show 0 / 1 / 3 / 6% annual drag; use
predeclared base 1.5% momentum, 0.5% quality/value and 0.1% market.
Gross is diagnostic, not the headline.

Metrics: CAGR, annualized vol, RF-excess Sharpe, downside Sortino, max drawdown,
Calmar, traded-notional and one-way-equivalent turnover, holdings, entry-to-exit
holding spells (open spells censored), best/worst complete calendar year, SPY
beta/correlation when actual SPY exists (market-proxy otherwise), excess CAGR.
Monthly maximum drawdown is explicitly a month-end underestimate of intramonth risk.
Daily monthly win rates are labeled descriptive, not independent trade probabilities.

## Falsification and temporal comparison

- Long sample: 1964-1999 development, 2000-2009 validation, 2010-2019 comparison,
  2020-last complete data month held-out-like test, all fixed before results.
- Actual ETF and convenience-stock samples use their real date ranges, with
  2000-2007/2008-2009/2010+ subsets as available. Never fabricate post-2020 coverage.
- Report 2000-02, 2008, 2009 rebound, 2020, 2022 and 2023-25 when data exists.
  Bull/bear = contemporaneous benchmark return sign for descriptive attribution
  only, not a signal. Volatility regime is defined from lagged realized volatility.
- Costs across all scenarios; one extra decision lag; full parameter neighborhoods;
  zero-yield cash; crisis-exclusion robustness; paired block-bootstrap uncertainty
  for annualized mean excess return, not a multiple-testing-adjusted alpha claim.
- Mandatory deterministic controls: randomized no-signal ensemble, planted persistent
  signal recovered by the pipeline, deliberate future-availability violation rejected.
  Also a future-price-perturbation prefix test and hand-calculated cost/drift tests.

## Promotion/kill gates

Reject "deployable alpha" when it depends on survivor selection, unobserved PIT
features/consensus, microcap short legs, or a single best parameter. Reject added
complexity if improvements are fragile across costs/nearby parameters/time splits.
Trend may survive as risk management even with lower CAGR, if drawdown reduction
is economically meaningful and stable; call that insurance/defensive exposure, not
alpha. Report dependence on major crises rather than discarding such evidence.
The final ranking weights data integrity, robustness, simplicity and execution
burden before Sharpe. There may be no demonstrated stock-selection alpha.
