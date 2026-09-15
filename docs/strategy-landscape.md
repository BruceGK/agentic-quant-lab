# Agentic Quant Lab: long-only strategy landscape

**Research date: 2026-09-15. Classification: EXPLORATORY. No strategy is production-ready.**

## Decision

Build a **paper-only, deterministic liquid-ETF trend experiment first**, with
12-month absolute momentum and 10-month moving-average timing as separate frozen
rules. Its plausible value is reducing prolonged drawdowns, **not reliably beating
buy-and-hold**. Keep a static ETF/cash benchmark capable of winning the comparison.

Build a **simple quality-oriented ETF diversifier comparison second**, not a custom
stock-fundamentals engine or a momentum-quality mega-factor. This is a conditional
research priority: the available quality evidence is an academic long-portfolio
proxy, not validated ETF alpha.

Do not deploy the attractive survivor-panel stock momentum result: the central
strategy lost to equal weighting the same conveniently selected stocks. Do not
implement PEAD or a stock-level quality filter without clean timestamped data.

Phase 0 is frozen. No Azure changes, credentials, broker connection, trades,
scheduler activation, live execution or SEC infrastructure expansion occurred.
Both activation flags remain false. The newer research is intentionally outside
the Phase 0 package; its policy files were not loosened to run experiments.

## What was investigated

The [pre-result protocol](../research/protocol.md) fixes rules, costs, splits and kill
criteria. The [literature review](../research/notes/literature.md) distinguishes the
original evidence from replication, cost/crash/decay warnings and implementation claims.
The [data audit](../research/notes/data-audit.md) explains the limits.

| Family | Work actually done | What was not claimed |
| --- | --- | --- |
| A. Time-series trend | 6/9/10/12 absolute and SMA neighborhoods, dual SMA, capped volatility, cash/RF, next-session costs, long-period proxy, static exposure/placebo checks | Long-short futures evidence does not establish SPY/cash alpha |
| B. Equity momentum | 6-1/9-1/12-1/combined ranks; 10/20/30/50 stocks; monthly/10-session; three liquidity screens/costs; fixed rank buffer/sector cap; random/equal-weight controls; large-stock academic long leg | Survivor-selected 70-stock panel is not a historical liquid-universe backtest |
| C. Momentum + quality | Literature/data feasibility; net 50/50 long momentum/quality sleeve blend | Sleeve blending is **not** a stock-level quality filter or composite; neither was fabricated |
| D. Quality/value | Large robust-profitability and value long baskets; joint value/profitability neighborhoods; fixed trend/momentum/value and quality mixes | Monthly academic baskets do not reveal holdings, actual turnover, point-in-time revisions or ETF tracking |
| E. PEAD/earnings momentum | Original/cost/liquidity evidence; announcement/consensus/revision/price-confirmation feasibility audit | No clean free joined consensus/timestamp dataset; no invented surprise or LLM backtest |

Optional complex strategies were not needed to answer the decision. No HFT, short
stat-arb, options, crypto, reinforcement learning or free-form agent stock picking.

## Evidence quality and test design

**481 predeclared runs, not 481 independent discoveries.** All variants are retained
in [tournament.csv](../research/results/tournament.csv), including weak results.
Central representatives were chosen before results, not by best Sharpe.
Development 1964-1999, validation 2000-2009, comparison 2010-2019, and 2020-2026
holdout-like windows are retrospective: known rules and crises make them
**pseudo-out-of-sample**, not untouched discovery data.

Actual ETF snapshots cover SPY 2000-2015 and AGG 2006-2015, with warmup reducing
the evaluated windows. The complete survivor stock panel is evaluated 2004-2012.
French revised academic returns supply 1964-July 2026 cross-checks; a market proxy
is labeled as such, never called SPY. No actual ETF or stock test silently extends
into 2020. All numeric strategies are long-only and unlevered.

Daily decisions observe close t, trade at close t+1, and first earn t+1 to t+2.
Monthly-only proxy timing waits an extra month to avoid pretending a closing price
was known before trading at that same close. Costs use drifted pretrade weights and
a self-financing solve; every buy and sale incurs a fee.
Simulation starts before the evaluated slice to build lookback history. Existing
positions can be inherited at a slice boundary; pre-boundary fees are not charged
again, and a not-yet-eligible strategy remains cash until its first delayed rebalance.
This is not a new-account launch simulation at each displayed period start.

- ETF one-way friction: 2/5/20 bps, base 5.
- Stock one-way friction: 5/15/50 bps, base 15.
- Academic internal trading is unobservable: assumed base annual drag 1.5% for
  momentum and 0.5% for quality/value, with gross/3%/6% sensitivities; not measured
  turnover or slippage. A 0.1% market-proxy annual drag represents an implementation
  allowance, not an observed ETF fee.
- Cash tests include realized French RF and literal zero-yield cash. RF is not a
  guarantee of Robinhood sweep yield or a tradable Treasury ETF return; fallback
  instrument spread/fees and settlement remain implementation work.
- Taxes are **not modeled**; high taxable turnover may make momentum less attractive.
  Zero commissions do not remove spreads, slippage, taxes or market impact.

## Central net results: do not compare unlike samples

### Long monthly proxy comparison, January 1964-July 2026

Monthly drawdowns understate possible intramonth losses. Large-stock baskets still
lack audited tradable constituent history.

| Predeclared model | CAGR | Sharpe | Max drawdown | Excess CAGR vs market |
| --- | ---: | ---: | ---: | ---: |
| Market proxy, net allowance | 10.69% | 0.45 | -50.38% | -- |
| SMA10 + RF | 9.59% | 0.46 | -29.91% | -1.10 pp |
| Absolute12 + RF | 10.14% | 0.48 | -29.87% | -0.55 pp |
| Large-stock high momentum, 1.5% annual drag | 11.66% | 0.48 | -49.04% | +0.96 pp |
| Large-stock robust profitability, 0.5% drag | 11.40% | 0.50 | -48.20% | +0.70 pp |
| Large-stock value, 0.5% drag | 12.50% | 0.51 | -62.10% | +1.81 pp |
| Joint value/profitability, 0.5% drag | 14.07% | 0.53 | -54.92% | +3.38 pp |
| Equal trend/momentum | 10.76% | 0.50 | -31.54% | +0.07 pp |
| Equal trend/momentum/quality | 11.02% | 0.51 | -34.63% | +0.33 pp |

The joint sort's high CAGR is **not the winner**: it suffers a major decade failure,
requires unavailable holdings/PIT verification, and its drawdown is not defensive.
Paired 12-month-block bootstrap mean-excess intervals include zero for simple
trend, large momentum, quality and the simple mixes. These intervals are not
multiple-testing-adjusted and do not establish alpha even when a bound is positive.

### Actual historical ETF snapshot

| Model and sample | CAGR | Sharpe | Daily max drawdown |
| --- | ---: | ---: | ---: |
| SPY hold, 2001-2015 | 5.11% | 0.28 | -55.19% |
| SPY SMA210 sessions + RF, 2001-2015 | 8.73% | 0.67 | -17.31% |
| SPY absolute252 sessions + RF, 2001-2015 | 8.06% | 0.58 | -18.61% |
| Equal SPY/AGG hold, late 2007-2015 | 5.60% | 0.53 | -29.23% |
| Equal SPY/AGG SMA210 + RF, same dates | 6.02% | 0.94 | -8.08% |

The ETF timing result is attractive **and crisis-heavy, stale, small-sample evidence**.
AGG is aggregate bonds with credit/rate risk, not cash or a pure Treasury substitute.
The 0.94 Sharpe must not outrank the lower long-history Sharpe by mixing sample dates.
The longer proxy history says trend usually gives up some geometric return.

### Survivor-selected stock implementation test, January 2004-August 2012

| Model | CAGR | Sharpe | Daily max drawdown | Traded notional/year |
| --- | ---: | ---: | ---: | ---: |
| Equal-weight 70-stock convenience panel | 10.43% | 0.49 | -48.75% | 0.55x |
| 12-1, 20 names, monthly, $50m screen, 15 bps | 8.43% | 0.41 | -48.04% | 5.51x |
| Same momentum, fixed 1.5x rank buffer | 8.56% | 0.41 | -48.90% | 3.11x |
| Same momentum, 30% target sector cap | 8.08% | 0.39 | -48.04% | 5.66x |

SPY on this window is about 4.82% CAGR: momentum appears to beat it by 3.61 pp,
but equal weighting the biased universe beats it by 5.61 pp. **Benchmark choice
reverses the alpha story.** Forty random eligible 20-stock portfolios have median
7.56% CAGR; 22.5% meet/exceed the central momentum CAGR. Neither comparison removes
survivorship bias. Reject deploying this panel's apparent stock-selection alpha.

## Falsification and parameter stability

### Trend

- The eight base-case long-proxy absolute/SMA neighborhoods span roughly
  9.02-10.41% CAGR and -30.28% to -29.87% max drawdown, versus 10.69% and -50.38%
  market. Drawdown reduction is more stable than excess return.
- In 2010-2019 all eight trail the market in CAGR. In 2020-July 2026, central
  SMA10 returns 10.86% versus 14.90% market; absolute12 returns 13.63%.
  This is no all-weather return enhancer.
- At 20 bps per side, old SPY SMA remains 8.61% CAGR versus 8.73% at 5 bps;
  low turnover makes plausible friction less important than regime/timing.
- Zero-yield cash lowers long-proxy SMA10 from 9.59% to 8.32% and absolute12
  from 10.14% to 9.06%. **Cash yield is an economically material assumption.**
- A 10% volatility cap reduces drawdown to about 17.5% in the long proxy but
  cuts CAGR to roughly 7.8-8.3%; it is de-risking, not established extra alpha.
- Static exposures estimated only on 1964-1999 are 75.2% for SMA10 and 80.1%
  for absolute12. Full-sample trend has lower drawdown than those static comparators,
  but SMA10 is worse on CAGR, Sharpe and drawdown in 2020 onward. Absolute12's
  recent drawdown is essentially the same as its static comparator.
- Circular timing shifts retain allocation spell structure. Roughly 14-15% have
  Sharpe at least as high as the real rules; no extraordinary timing-alpha claim.
  These are deliberately invalid trading alternatives, used only for falsification.
- Removing 2000-02, 2008-09, 2020 and 2022 leaves SMA10 about -2.67 pp annualized
  mean excess versus the market. Much of its value is avoiding some big crises.
  That may still be useful personal-account insurance, but has an opportunity cost.

### Momentum and quality/value

- In the stock grid, monthly median net CAGR is 8.28% versus 7.19% for the
  10-session rebalance approximation. Median traded notional rises from 5.68x to
  8.58x/year. Faster is not automatically better.
- The central momentum strategy's cost rises from approximately 0.28%/year at
  5 bps per side to 0.83% at 15 and 2.75% at 50. CAGR falls from 9.03% to
  8.43% to 6.36%. These are pre-tax.
- Rank buffering cuts turnover materially but improves CAGR only about 0.13 pp
  here and slightly worsens drawdown. Keep it as a cost-control hypothesis, not
  new alpha. The sector cap did not improve this case; do not optimize a rescue cap.
- The central winner book averaged 19.8 stocks, completed holding spells about
  4.55 months, and reached 51.5% in one static sector classification through
  selection/drift. Sector labels are not historical GICS, and holding spells at
  sample boundaries are censored rather than made artificially short.
- Large-stock momentum's 11.66% full CAGR becomes 9.96% with 3% annual internal
  drag, below market. It trails the market in 2010-2019 and 2020 onward at base
  drag. Its historical long-short reputation does not settle the retail long leg.
- Quality's long basket is more consistent recently, but correlates 0.97 with
  the market. It is a modest equity tilt, not a crash hedge or proof of a momentum filter.
- Joint value/profitability falls to **5.40% CAGR in 2010-2019 versus 13.49%
  market**, with about 52% drawdown and a -34.5% worst calendar year (2015).
  Reject a full-sample-optimized joint-factor winner despite its 14.07% headline.

## Complementarity, not an allocator

Correlations on aligned monthly net proxies:

| Pair | Correlation |
| --- | ---: |
| SMA trend / large momentum | 0.79 |
| SMA trend / quality | 0.76 |
| Momentum / quality | 0.91 |
| Momentum / value | 0.75 |
| Quality / market | 0.97 |

Long-only sleeves share equity beta. They are not the low-correlated long-short
factors often shown in institutional research. Equal trend/momentum reduces full
drawdown meaningfully with approximately market CAGR, but trails market after 2010.
Adding quality gives a small full-sample Sharpe lift, not a proven allocation edge.
Momentum/quality alone is about 14.79% CAGR / 0.71 Sharpe in 2020 onward versus
market 14.90% / 0.72. Do not build an optimized capital allocator.

Value may help across different decades, but it worsens some drawdowns; it is not
a defensive replacement for cash. PEAD correlations are **unknown**, not inferred
from a narrative about earnings being different.

## Small capital and Robinhood feasibility

Only public documentation was read. No account, MCP endpoint, credentials or orders
were accessed. Long-only equity/ETF orders are structurally compatible with the user's
constraint; actual symbol/fractional eligibility and entitlements remain untested.
The official Agentic docs distinguish limited margin using unsettled proceeds from
borrowing: **no leverage assumed**. Cash accounts need T+1 settlement, so simultaneous
sell-and-rebuy backtests can be optimistic unless supported settlement handling is verified.

The historical one-date sizing diagnostic makes the issue concrete: with $1,000 and
20 equal target stocks, whole-share rounding funds only 11 names and leaves 56% cash;
with $10,000, about 11% remains uninvested; with $50,000, about 2%. This is not a
modern execution simulation, but it favors fewer ETFs/fractional sizing over many stocks.
Fractional orders have Not Held handling discretion; cost stress remains necessary.
Do not assume uninvested Agentic cash earns the full academic T-bill return.

## Explicit final ranking

“BUILD” means the **next paper-only deterministic experiment**, not live capital.

| Rank | Candidate | Why / confidence | Complexity |
| --- | --- | --- | --- |
| **BUILD FIRST** | Simple liquid-ETF absolute12 and SMA10, cash/Treasury fallback | Medium confidence in defensive purpose; low confidence in excess return. Robust drawdown reduction, cheap/transparent, but stale actual ETF data and static exposure competition | Low |
| **BUILD SECOND** | Quality-oriented ETF diversifier versus market and trend, conditional on clean ETF data | Medium-low: long-quality evidence consistent enough to compare, low turnover plausible, high market correlation limits diversification | Low-medium |
| **RESEARCH MORE** | Large/liquid 12-1 stock momentum, monthly, modest breadth and fixed buffer | Strong literature, weak personal implementation evidence here. Need delisting-aware historical universe and realistic after-tax costs | Medium |
| **RESEARCH MORE** | Momentum + one quality filter **separately** from a composite | No legitimate interaction backtest without joined PIT features. Require incremental net benefit over pure momentum or discard | Medium-high |
| **WATCH** | Slow value/quality-value sleeve | Can diversify decades; joint sort fails a major decade and has severe drawdowns. ETF implementation and valuation/crowding evidence needed | Medium |
| **WATCH** | Structured PEAD/earnings/revisions | High potential agentic research value, but liquid-stock cost concerns and unavailable free timestamped consensus block promotion | High |
| **REJECT now** | Biweekly high-turnover momentum as the default; best-Sharpe joint factor; survivor-panel alpha; custom PEAD/quality model built from current/revised proxies | More trading/complexity is not justified, or the data cannot support the claim | Unjustified |
| **REJECT for this task** | Equity shorts, leveraged futures, HFT/options/RL/LLM stock picking and autonomous execution | Constraint mismatch; no need to answer the research question | Out of scope |

## Agentic upside: where deterministic math stops

- **Trend:** agents can synthesize new replication evidence and inspect whipsaw,
  lag and cash-regime failures. Signal, position sizing and costs remain deterministic.
- **Momentum:** agents can propose preregistered concentration/turnover tests, audit
  suspicious corporate actions and identify changes in research evidence. No
  discretionary “bullish” overrides or risk-limit changes.
- **Quality/value:** agents can audit accounting comparability/restatements and
  propose one interpretable hypothesis at a time, with availability metadata.
- **PEAD:** later agents may classify guidance changes or explain contradictory
  surprise measures after a numeric baseline works. This is the best plausible
  text-research fit and the least acceptable place to skip timestamp/consensus controls.

No agent needs broker credentials to add research value. Never entrust agents with
basic return calculations, free-form stock selection, bypassing constraints, changing
risk limits or unapproved order execution.

## Surprising findings

1. **The benchmark erased the momentum story:** beating SPY was weaker evidence than
   lagging equal weighting the selected survivors.
2. **A high full-history quality/value CAGR concealed a lost decade and large tail risk.**
3. **Long-only factor diversification is much smaller than the long-short narrative:**
   momentum/quality correlation is about 0.91.
4. **Trend's best-looking ETF result did not generalize into an all-period CAGR advantage.**
   Defensive utility survives this falsification; a return-enhancement claim does not.
5. **Cash assumptions matter more than a few bps of ETF spread.**
6. **A public academic CSV can still be malformed.** We rejected the corrupt
   equal-weight momentum block rather than quietly trimming it.

## What should and should not be built

Build only a research/paper specification for the simple ETF rules and static comparator,
with explicit prices, corporate actions, cash treatment, next-session timing and costs.
Keep the present small harness; no dashboard, database, feature store, allocator,
agent orchestrator, broker connector or further cloud resources.

Do not call the shortlist production-ready; do not deploy the survivor-stock book,
invent historical consensus, use today's quality fundamentals in past rankings,
or preserve complexity because it sounds sophisticated. If simple static exposure
wins on the properly audited modern sample, accept it rather than rescue trend
through a parameter search.

## Single next experiment

**Independently audit modern SPY and a short-Treasury ETF total-return/corporate-action
data for 2016-2026, then run the already fixed absolute12 and SMA10 rules against
buy-and-hold and a static equity/Treasury exposure comparator, with next-session
execution, zero-yield-cash sensitivity and 20 bps one-way stress costs.**

No rule retuning after seeing the modern period. Judge drawdown reduction alongside
CAGR sacrifice and settlement/fractional feasibility; if the simple static comparator
dominates, stop promoting trend. This remains paper research, not broker integration.

## Reproduction, evidence and boundaries

[Research README](../research/README.md), [all numerical rows](../research/results/tournament.csv),
[source hashes](../research/results/data_manifest.json),
[exposure/placebo checks](../research/results/exposure_falsification.json),
[cost/random controls](../research/results/random_portfolios.csv),
[bootstrap and regimes](../research/results/robustness.json).

Known unresolved biases: revised academic vintage, unknown basket constituents/internal
turnover, survivor-selected stocks, old ETF histories, unaudited distribution/delisting
adjustments, static sector labels, pseudo-holdouts, many correlated hypotheses and
unmodeled taxes/real fills/cash yield. No result qualifies as RESEARCH-GRADE
security-level deployable alpha.

Mandatory null/positive/leakage controls passed. Independent implementation review
found and led to fixes for empty-universe liquidation, left-censored holding spells,
and partial-year best/worst metrics; all results were recomputed after correction.
Near-zero cash-excess volatility is now reported as undefined Sharpe, not a large
floating-point artifact. Validation and final artifact hashes accompany the results.

Final checks: **24 research tests plus 10 unchanged Phase 0 policy/scientific tests
passed**; Ruff, default and research Pyright, package build and artifact-hash checks
passed. [The experiment log](../research/notes/experiment-log.md) records the review
fixes, strategy-specific decisions and exact scope. The
[standardized candidate cards](../research/results/candidate_summary.csv) include
all required metrics/compatibility/confidence fields, with explicit NA for untestable
fundamental/event candidates.

The unchanged repository [CI passed on the published research branch](https://github.com/BruceGK/agentic-quant-lab/actions/runs/35007001939).
That CI validates Phase 0 and its production image; the optional research-specific
tests/types were run explicitly as documented, not misrepresented as part of that job.

`scheduled_recording_enabled = false`; `live_execution_enabled = false`.
