# Fixed modern ETF trend validation

**Decision: RESEARCH MORE. Do not promote either rule to paper/shadow yet.**

The fixed-rule NAV-proxy results are unfavorable versus permanent de-risking.
The remaining research is **data/execution verification, not parameter tuning**:
full-period exchange closing prices were unavailable, so the official issuer's
audited daily NAVs are used as an explicitly labeled valuation proxy.
This is not evidence that better entry prices would rescue the rules.

See [the full experiment report](../../../docs/etf-trend-validation.md) and
the immutable [protocol](protocol.md), committed before modern strategy results.
Phase 0, existing strategy-family research and all trading controls are unchanged.

## What was fixed

Exactly six models, each at 0/10/20 bps one-way costs, with BIL and literal zero-yield
cash as defensive alternatives: **36 scenarios**, not a parameter tournament.
Only the two specified calendar-month signals are generated; there are no alternate
lookbacks, thresholds, rebalance dates or volatility overlays.

- Absolute12: SPY total-return level strictly above the month-end level 12 months ago.
- SMA10: SPY level strictly above the average of the latest 10 month-end levels.
- Buy-and-hold SPY/BIL and monthly static 80/20 and 70/30 comparisons.
- Decisions at month-end; earliest trade at the following exchange session's close.
  Because executable close history is unavailable, that trade is approximated by
  the following session's NAV; the distinction is not hidden.
- Same new-account entry at the first January 2016 session close, with initial fees.
  No rebalance occurs before the initial December 2015 signal, despite earlier warmup.

## Official data and checks

Sources are [issuer SPY NAV](https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-spy.xlsx),
[issuer BIL NAV](https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-bil.xlsx)
and [cash distributions](https://www.ssga.com/library-content/products/fund-data/etfs/us/spdr-etf-historical-distributions.xlsx).
These are actual ETF observations, not an academic market-return replacement.
BIL's 2007 inception covers the whole sample; **no defensive proxy was spliced**.

- 3,163 matched exchange sessions from January 2014 through July 2026;
  2,659 evaluation sessions from January 4, 2016 through July 31, 2026.
- The independent French daily US-equity/RF calendar defines sessions. One issuer
  NAV-only observation on Good Friday 2014 was excluded explicitly, not interpolated.
- BIL's November 30, 2017 one-for-two reverse split is normalized on that date.
  Issuer NAV doubled while shares outstanding halved; an independent split-history
  source confirms the event. There is no spurious 100% gain.
- Cash distributions are accrued as receivables on ex-date and reinvested only on
  payable date. SPY's delay can be 47 calendar days; using instant ex-date
  reinvestment initially failed the issuer return cross-check.
- Fresh-period reconstructions match all 12 June 30, 2026 issuer NAV return
  checkpoints (QTD, YTD, 1/3/5/10 years for each ETF) within 2 bps; largest gap
  approximately 1.005 bps. Longer periods are annualized.
- NAVs already reflect fund expenses; no second fund-fee haircut is added.

**Limitations:** current revised issuer vintage, not a historical timestamp archive;
full-period market closes/NBBO unavailable; premium/discount history covers only
2025 onward and refers to indicative NAV/closing midpoint, not exact closing trades.
Trading total-return units ignores the small amount of unavailable dividend cash at
switches (maximum observed receivable fractions about 0.65% SPY / 0.46% BIL).
These prevent a claim of research-grade executable returns. The share/receivable
reconstruction itself is verified; the trade-fill model remains a proxy.

## Reproduce

Only optional research dependencies, no account or API credentials:

```sh
uv sync --locked --group research
uv run --frozen --group research pytest -q research/tests/test_etf_trend.py
uv run --frozen --group research pyright research/etf_trend research/tests/test_etf_trend.py
uv run --frozen ruff check research/etf_trend research/tests/test_etf_trend.py
uv run --frozen ruff format --check research/etf_trend research/tests/test_etf_trend.py

uv run --frozen --group research python -m research.etf_trend.data
uv run --frozen --group research python -m research.etf_trend.run
```

The earlier hashed French `ff_daily.zip` in `research/.cache/` supplies the independent
RF/calendar; obtain its matching vintage using the existing research data instructions.
All issuer downloads are cached under ignored `research/.cache/etf_trend/`; raw
third-party files are not committed. A source revision fails hash verification,
not silently updates the result. The acquisition command and runner preserve
the fixed July 31, 2026 endpoint even if current files contain later dates.

## Outputs

| Artifact | Evidence |
| --- | --- |
| [data_manifest.json](results/data_manifest.json) | URLs/hashes, frozen panel and explicit NAV-proxy classification |
| [data_audit.json](results/data_audit.json) | Coverage, corporate actions, distributions and remaining data limitations |
| [issuer_return_crosschecks.csv](results/issuer_return_crosschecks.csv) | All independent issuer-performance cross-checks |
| [metrics.csv](results/metrics.csv) | Every requested metric for all 36 fixed scenarios |
| [calendar_returns.csv](results/calendar_returns.csv) | Complete years and separately marked 2026 YTD |
| [decisions.csv](results/decisions.csv) | Exact decision, feature availability and delayed execution dates |
| [defensive_spells.csv](results/defensive_spells.csv) | Every exit/re-entry, losses avoided, rebound missed, whipsaw, duration and fees |
| [drawdown_events.csv](results/drawdown_events.csv) | All >=10% in-sample SPY drawdowns and overlapping trend events |
| [whipsaw_summary.csv](results/whipsaw_summary.csv) | Complete-spell accounting and opportunity losses, without double counting |
| [attribution.csv](results/attribution.csv) | Exact P&L reconciliation and matched-cost defensive total-return contribution |
| [crisis_contributions.csv](results/crisis_contributions.csv) | Fixed-period relative log-wealth contributions; not counterfactual live portfolios |
| [rule_agreement.csv](results/rule_agreement.csv) | Same/different exposure states |
| [lookahead_falsification.json](results/lookahead_falsification.json) | Both one-month-advanced signals rejected before returns were calculated |
| [experiment_manifest.json](results/experiment_manifest.json) | Protocol/source/code/result hashes |

### Interpretation

Turnover is total bought-plus-sold notional divided by years; the additional
one-way-equivalent field divides it by two. Rotating from SPY to BIL charges both
legs; rotating to uninvested cash charges only the equity sale. Thus zero-yield cash
can beat low-yield BIL after costs without implying that income is harmful.

Main Sharpe uses French daily RF excess returns. BIL can have a negative Sharpe
against a T-bill opportunity rate despite positive nominal returns. Zero-yield
cash's opportunity-cost Sharpe is also negative; neither is an equity-alpha ranking.
Zero-RF Sharpe is reported separately; Calmar is undefined when drawdown is zero.

An avoided fall and missed rebound are pieces of the **same** defensive spell,
not additive independent profits/losses. If exit occurs after the crisis trough,
the rebound already owned before exit is not reported as missed. Complete-spell
log-relative returns reconcile to whole-sample trend-versus-SPY log wealth.
A "whipsaw" here is a completed defensive spell with positive SPY return and
negative net relative outcome; short spells <=3 months are separately counted.

No orders, broker/MCP calls, Azure operations, scheduler changes or live execution.

Final verification: 20 dedicated ETF tests plus 24 existing research-engine/data
tests and 10 unchanged Phase 0 policy/scientific controls passed (**54 total**).
Ruff, default and explicit research Pyright, package builds and source/protocol/
code/result hash checks passed. The two deliberately advanced monthly signals
were rejected. Whole-sample relative log wealth reconciles to the sum over
nonoverlapping defensive spells to floating-point precision.
