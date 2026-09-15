# Offline long-only research

This directory is separate from the frozen Phase 0 recorder. It cannot connect to
a broker, query production evidence, deploy resources, or place trades.
The [research protocol](protocol.md) was committed before market performance was
calculated. All investable-strategy conclusions are **EXPLORATORY**, not production-ready.

## Reproduce

From the repository root, with Python 3.12 and existing uv:

```sh
uv sync --locked --group research
uv run --frozen --group research pytest -q research/tests
uv run --frozen ruff check research
uv run --frozen ruff format --check research
uv run --frozen --group research pyright research

# Public unauthenticated downloads only. Raw third-party data stays in ignored .cache/.
uv run --frozen --group research python -m research.data acquire
uv run --frozen --group research python -m research.tournament
uv run --frozen --group research python -m research.falsify
uv run --frozen --group research python -m research.report
```

Acquisition and every experiment verify the committed source manifest. French
files are revised by their publisher; a later download with a different hash fails
rather than silently regenerating the historical report. Reproduction then needs
the matching local archival bytes or a deliberately new, separately labeled vintage.
No data subscription, API key, secret or broker package is required.

Research dependencies are an optional group. Production runtime dependencies,
recorder source, migrations, Azure templates, existing workflows and policy flags
are unchanged. The existing default test suite excludes this directory; explicitly
invoke the research tests as above. No third-party raw market data is committed.

## What the code does

- [data.py](data.py): bounded public downloads, hashes, selected French table parsing,
  adjusted daily price validation; rejects changed sources and malformed selected blocks.
- [engine.py](engine.py): delayed decisions, exact self-financing proportional costs,
  drifted weights, cash, long-only/no-leverage and availability guards, metrics.
- [tournament.py](tournament.py): predeclared 481 strategy/cost/parameter runs, regimes,
  central-model returns, random portfolios, simple sleeve mixes and sizing diagnostics.
- [falsify.py](falsify.py): pre-2000-calibrated static exposure comparators, timing
  placebos, paired block uncertainty and crisis attribution. Placebos are not investments.
- [tests/](tests/): null and planted-signal controls, deliberately leaked data rejection,
  no-future-perturbation test, drift/cost hand checks and data-integrity tests.

This is a small experiment harness, not a generalized research/feature-store platform.
The mean-return bootstrap is descriptive and not a selection-adjusted alpha test.
`annual_traded_notional` charges both buys and sells; divide by two for the reported
one-way-equivalent turnover. Approximate holding duration excludes left-censored
positions inherited at a report boundary and right-censored open positions.
Daily best/worst complete years are checked against the source calendar.
Near-zero excess-return variance yields no Sharpe rather than floating-point fiction.
Simulations run through the lookback warmup before report slices are taken. A slice
can inherit an already invested position, and fees paid before that slice are not
charged again. Strategies whose first eligible monthly decision falls after the
evaluation boundary remain in cash until execution; no position is backfilled.
Thus the results are continuous-strategy period returns, not a separately reset
new-account launch on every displayed start date.

## Evidence files

| Artifact | Meaning |
| --- | --- |
| [data_manifest.json](results/data_manifest.json) | Exact URLs, bytes, hashes and source-vintage boundaries |
| [data_audit.json](results/data_audit.json) | Date coverage, missing values, adjustment ratios and schema checks |
| [tournament.csv](results/tournament.csv) | All net scenarios/parameters/regimes and requested metrics |
| [monthly_returns.csv](results/monthly_returns.csv) | Representative models chosen by the protocol, not highest Sharpe |
| [robustness.json](results/robustness.json) | Bootstrap intervals, concentration, regime/exclusion diagnostics |
| [random_portfolios.csv](results/random_portfolios.csv) | Forty seeded random-stock controls in the same biased panel |
| [correlations.csv](results/correlations.csv) | Aligned long-only sleeve correlations, not long-short factor correlations |
| [capital_sizing.json](results/capital_sizing.json) | One-date whole-share rounding diagnostic; not an execution simulation |
| [exposure_falsification.json](results/exposure_falsification.json) | Static exposure and random-timing checks |
| [crisis_attribution.csv](results/crisis_attribution.csv) | Calendar-year log-wealth excess attribution |
| [experiment_manifest.json](results/experiment_manifest.json) | Protocol/data/code/output hash binding for the main tournament |
| [candidate_summary.csv](results/candidate_summary.csv) | Standardized candidate cards; untestable features carry NA, not proxy performance |
| [quality_neighborhoods.csv](results/quality_neighborhoods.csv) | Nearby joint-sort cells under two cost drags, used only to falsify the full-sample winner |

Read the [data audit](notes/data-audit.md) before using any number. The 70-stock
panel is survivor-selected and old; current-constituent or PIT-clean claims are false.
French long portfolios are not ETFs or a list of executable stock trades.
Momentum-quality filters/composites and PEAD remain data-gated, not "tested" by proxies.

The final synthesis is [the strategy landscape](../docs/strategy-landscape.md).
