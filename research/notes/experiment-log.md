# Experiment log and adjudication

## Checkpoints and order

1. Frozen Phase 0 baseline: `04dda08`; all local/remote heads and reachable history
   inspected. Only scientific control fixtures existed, not a strategy engine.
2. `a0a8895`: literature, data gates, costs, neighborhoods and kill criteria committed
   **before** calculating market performance.
3. `00609a2`: strict adapters, audited source hashes, deterministic engine and 19
   controls committed before the first tournament output.
4. First run completed 481 comparisons. An independent implementation review found:
   - an empty post-warmup eligible universe incorrectly retained prior stocks;
   - sliced holding statistics counted inherited positions as completed short spells;
   - partial January/December could be labeled a complete calendar year.
   Each was reproduced and fixed with regression tests, then all results recomputed.
5. Cash-equivalent excess returns showed an invalid floating-point Sharpe in a few
   tiny-variance regimes. Near-zero denominators now produce missing Sharpe/Sortino.
   Source hashes are reverified before every experiment, not just at acquisition.
6. Final main run: **481 models/scenarios**, **3,396 metric rows**, 35 representative
   monthly curves; exposure/placebo follow-up: 56 comparisons; quality-neighborhood
   follow-up: three fixed intersections under two cost assumptions; nine candidate
   cards, including three deliberately unmeasured data-gated candidates.

The later exposure/placebo and quality-bin checks are falsification follow-ups,
not a second parameter-selection stage. No "best" result was promoted afterward.
The annual academic drag grid uses each family's specified base (1.5% momentum,
0.5% quality/value), zero diagnostic, 3% and 6%; it does not present a generic 1%
case as if it had been run. The exact registry is authoritative about each tested case.

## A. Trend: survivor for risk management, not return dominance

See `SPY_*`, `SPY_AGG_*`, and `market_*` in
[all results](../results/tournament.csv); [parameter neighborhoods](../results/parameter_neighborhoods.csv);
[static exposure/placebos](../results/exposure_falsification.json).

- Actual older ETF next-session tests show large crisis drawdown benefits.
- The 1964-2026 proxy reduces max drawdown consistently across simple lookbacks,
  but gives up CAGR, especially after 2010. No all-period return improvement.
- Zero-yield cash materially reduces long-horizon returns.
- Extra volatility targeting mostly reduces exposure/return. Reject it as
  demonstrated incremental alpha; keep only if a future risk budget demands it.
- Static training-exposure comparisons and circular shifts weaken a timing-alpha
  interpretation. Recent SMA10 is dominated by its static comparator on several metrics.
- Promotion: fixed simple paper experiment, with a static comparator allowed to win.

## B. Momentum: implementation result fails its own benchmark

See `stocks_mom*`, `stocks_equal_weight`, `stocks_buffer1.5`, `stocks_sector30`;
[random controls](../results/random_portfolios.csv);
[concentration/bootstrap](../results/robustness.json);
[capital rounding](../results/capital_sizing.json).

- All 6-1/9-1/12-1/combined, breadth, timing, liquidity and friction cells are retained.
- Central 20-stock 12-1 monthly result loses to equal weighting the same 70 stocks.
  Its positive SPY excess is not adequate evidence once survivor selection is admitted.
- Faster 10-session turnover degrades median net performance.
- Buffering reduces trading substantially but its small performance gain does not
  rescue stock alpha. Sector capping fails to improve this representative case.
- Large French momentum long legs offer longer evidence, but much less convincing
  post-2010 net excess and unavailable internal turnover.
- Promotion: clean-data research only. Reject deploying the current survivor-selected book.

## C. Momentum-quality: two tests that must not be conflated

1. **Stock quality filter:** not run; a joined, publication-time-correct profitability/
   leverage/etc. panel for the same historical universe is unavailable.
2. **Stock rank composite:** not run for the same reason. An untested complexity
   claim cannot survive merely because the economics sounds plausible.

The 50/50 momentum-quality **sleeve mixture** is an allocation diagnostic only.
Its correlation around 0.91 means less diversification than a long-short-factor
narrative suggests. It does not prove a filter or composite improves individual
winner selection. Those two candidate cards explicitly carry no return statistics.

## D. Quality/value: do not chase the highest full-sample CAGR

See `long_quality*`, `long_value*`, `joint_value_quality*`;
[joint-bin neighborhoods](../results/quality_neighborhoods.csv).

- Large robust-profitability is relatively stable, but behaves mostly as equity beta.
  A low-cost quality ETF comparison is a reasonable second research priority,
  not a mandate to build PIT fundamentals infrastructure now.
- Joint value/profitability looks attractive over the full sample but fails a decade.
  The single extreme intersection is much worse than broader intersections,
  reinforcing concentration/data-audit concerns. These bins are **not size controlled**.
- Without constituent histories, extreme joint-cell returns cannot be confidently
  attributed to economics versus concentration/vendor issues. Do not generalize
  them to all quality ETFs or optimize the number of cells.
- Promotion: quality ETF paper comparison; watch slow value diversification;
  reject the full-sample joint-factor winner as a deployment choice.

## E. PEAD: legitimate data gate, not a disguised price proxy

No earnings surprise/estimate-revision performance table was manufactured.
Seasonal EPS change, current consensus, filing time, price momentum and LLM tone
are not interchangeable information sets. The literature's liquid-stock cost
challenge makes clean event timestamps and post-event entry particularly important.

Promotion: watch/research when trustworthy free or already-available data exists.
Reject building a custom PEAD strategy from the inputs presently available.
No SEC infrastructure extension or LLM strategy was needed.

## Complementarity

The fixed equal sleeves improve some full-history drawdown/Sharpe measures, but
long-only momentum and quality remain strongly correlated and equity-exposed.
Recent results do not prove the mixtures beat the market. No mean-variance,
risk-parity or learned capital allocator was built.

## Final verification

- **24 research tests passed**, including null, positive, leak rejection, future
  perturbation, fee/drift hand calculations, empty-eligible liquidation, censoring,
  complete years, near-zero denominators and source-hash checks.
- Ten existing Phase 0 constitution/scientific tests also passed: **34 combined**.
- Existing Ruff check/format across the repository: passed (60 Python files).
- Default Pyright and explicit research Pyright: zero errors/warnings.
- Existing wheel/source build: passed. Wheel inspection confirmed no research
  code/data in the production recorder package.
- Verified protocol, source, code and output hashes in
  [experiment manifest](../results/experiment_manifest.json).
- Verified 3,396 metric rows have no infinite numbers, all classifications are
  exploratory, mean invested weights remain in [0,1], and the three data-gated
  candidate cards have no fabricated CAGR.
- Frozen-path diff against `04dda08` is empty for recorder source, migrations,
  infrastructure, existing workflows, Dockerfile and Docker context.

No Azure request, broker connection, credential access, paid data purchase or trade
was made. Results support a research-backed shortlist, not production readiness.
