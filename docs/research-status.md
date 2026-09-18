# Research status and provenance

**Presentation evidence review: 2026-09-18. EXPLORATORY / not production-ready.**
This is the canonical human-readable summary of committed real research, not a
new experiment or promotion decision. The [packaged status](../src/agentic_quant_lab/resources/research_status.json)
contains the corresponding machine-readable labels; the original reports remain
authoritative. Synthetic demo results never score or promote these real candidates.

## Current conclusions

| Workstream | Preserved status | What the evidence supports |
| --- | --- | --- |
| Phase 0 evidence/provenance foundation | **COMPLETE: historical manual acceptance** | Prospective PIT recording, reconciliation and recovery demonstrated; scheduling and live execution remain disabled. |
| Fixed ETF Trend: Absolute12 and SMA10 | **RESEARCH MORE; near rejection, not promoted** | Modern NAV-based validation is weak versus static 80/20 and 70/30; executable-price verification remains open. |
| Stock momentum | **DATA BLOCKED** | Historical universe, stable security IDs, delisting/terminal returns and PIT joins unqualified; no new stock alpha test. |
| Momentum + quality | **DATA BLOCKED** | Inherits stock-data blockers and additionally needs original PIT fundamental vintages and filing-availability evidence. |
| PEAD | **DEFER; NOT TESTED** | Price-based low-cost feasibility may be possible; no qualified event/price join or accepted consensus/revision vintages. |
| ETF relative / dual momentum | **EXPLORATORY; RESEARCH MORE; performance NOT RUN** | Frozen protocol; acquisition/DNS gates prevented all 18 scenarios. This is not an economic rejection. |

The [SEC acceptance report](sec-acceptance-report.md) records historical **PASS**,
not a new live check. Eligibility is prospective:
`decision_eligible_at = fetched_at`, never backdated to SEC acceptance.
The [constitution](../src/agentic_quant_lab/constitution.toml) still has
`phase0.external_acceptance_complete = false`,
`phase0.scheduled_recording_enabled = false` and `live_execution.enabled = false`.
Completed manual acceptance does not authorize recurring recording or trading.

## Fixed modern ETF Trend: actual research metrics

Authority: [validation report](etf-trend-validation.md), [frozen protocol](../research/etf_trend/protocol.md)
and [reproduction guide](../research/etf_trend/README.md).
The sample is **2016-01-04 to 2026-07-31, 2,659 sessions**, after 2014-2015 warmup.
Exact calendar-month Absolute12/SMA10 rules use monthly decisions and next-session
NAV valuation; initial entry and both legs of security rotations are charged.
Six fixed portfolios x three costs x BIL/zero-yield cash give **36 scenarios**,
not parameter optimization.

**NAV-based modern validation, not executable-close returns.** Official issuer
NAV/distributions, BIL's 2017 reverse split and payment-date reinvestment were
audited; all 12 issuer return checkpoints matched within 2 bps. Full-period
exchange closes remain unverified. Revised source vintages, limited
premium/discount history and unpaid-dividend cash constraints at switches are
additional limitations, not verified execution assumptions.

At **20 bps one-way**, with **BIL defense**, the committed results are:

| Portfolio | Net CAGR | RF-excess Sharpe | Maximum drawdown |
| --- | ---: | ---: | ---: |
| SPY hold | 15.03% | 0.75 | -33.68% |
| Static 80% SPY / 20% BIL | 12.53% | 0.74 | -27.33% |
| Static 70% SPY / 30% BIL | 11.26% | 0.74 | -24.08% |
| Absolute12 / BIL | 11.26% | 0.60 | -33.68% |
| SMA10 / BIL | 7.85% | 0.48 | -28.19% |

**Chart source:** [metrics.csv](../research/etf_trend/results/metrics.csv), filtered
to `defense == "BIL"`, `one_way_cost_bps == 20`, and
`model in {"SPY", "STATIC80", "STATIC70", "ABS12", "SMA10"}` (exactly five rows).
Use `cagr`, `max_drawdown` and RF-excess `sharpe`; multiply the first two by 100
for percentages. Keep the full CSV precision until display rounding.
Static70 and Absolute12 only **round** to the same CAGR: their stored fractions
are `0.1125811788` and `0.1126074007`, respectively.

Modern fixed-rule results are substantially weaker than the earlier long-history
research and crisis-heavy ETF snapshot in the [landscape](strategy-landscape.md).
The old 2001-2015 snapshot used different session-based rules and cash treatment;
it is not a like-for-like comparison. Its build-priority recommendation is
superseded. Absolute12 retains SPY's worst drawdown; SMA10 sacrifices substantial
growth despite temporary protection. Static 80/20 and 70/30 offer the stronger
observed growth/drawdown tradeoff.

**Whipsaws and crises, BIL / 20 bps:**

- [whipsaw_summary.csv](../research/etf_trend/results/whipsaw_summary.csv), filtered
  to `defense == "BIL"` and `cost_bps == 20`: Absolute12 **4/4** completed defensive
  spells are whipsaws (332 defensive sessions); SMA10 **9/11** (461 sessions).
  The frozen definition requires positive SPY return while out **and** net
  underperformance versus staying in SPY. These are relative opportunity losses.
- [drawdown_events.csv](../research/etf_trend/results/drawdown_events.csv), using
  the same defense/cost filter: Absolute12 exits after the late-2018 and COVID troughs.
  Its 2020-04-01 to 2020-05-01 absence misses a **14.61%** SPY rebound.
  SMA10 exits 2020-03-02 and returns 2020-06-01: **27.39%** further SPY decline
  avoided, but **36.85%** rebound missed. These differently based returns are
  **not additive P&L**.
- [defensive_spells.csv](../research/etf_trend/results/defensive_spells.csv), same
  filter: SMA10's completed COVID cycle has near-zero net relative advantage;
  its 2022-05-02 to 2022-12-01 spell gains about **1.13% relative wealth**, but
  other whipsaws outweigh it. Temporary crisis protection is not durable alpha.

**Formal decision: RESEARCH MORE**, not REJECT or PROMOTE. "Near rejection" is
presentation shorthand for the adverse NAV result. Only same-rule actual-close
verification remains; reject the fixed implementation if that confirms it.
**No parameter rescue, no paper/shadow promotion, no production readiness.**
This is not a universal economic rejection of trend.

## Data-blocked candidates: do not invent performance

- **Stocks and quality:** the [stock audit](stock-data-feasibility.md) concludes
  **C. RESEARCH-GRADE STOCK TEST CURRENTLY BLOCKED**. Today's constituents,
  ticker/CIK-only joins and delisted flags do not establish historical membership,
  immutable issue/share-class identity or terminal economics. Current CompanyFacts
  is not PIT certification. Original accession/fact/value/availability traces,
  including restatements, remain unqualified; no new stock alpha backtest ran.
- **PEAD:** the [feasibility report](pead-data-feasibility.md) says price-based and
  guidance-text PEAD **LOW-COST DATA REQUIRED**; consensus-surprise and revision
  momentum **BLOCKED**; overall **DEFER PEAD**. Price response does not require
  consensus, but still needs qualified release sessions, historical IDs and
  inactive/action-inclusive prices. Recoverable guidance text is not a certified
  event/price join. Consensus/revision variants need retained pre-release and
  multiple-vintage evidence; none was accepted. No PEAD performance was tested.
- **Sector relative momentum:** the [report](etf-relative-momentum-validation.md)
  and [protocol](../research/etf_relative_momentum/protocol.json), frozen at
  `79cb2aefe99bb1ab04443c3370c9e1b90de4cd26`, specify monthly equal-weight top three
  of nine sector SPDRs. Real 12-1 is `TR(m-1) / TR(m-12) - 1`, **eleven intervals**;
  the dual variant leaves failed/equal same-window BIL-hurdle slots in BIL.
  The [outcome](../research/etf_relative_momentum/outcome.json) is
  `NOT_RUN_DATA_GATE`, **0/18** scenarios. The [retry gate](../research/etf_relative_momentum/acquisition_20260916T013826Z/data_gate.json)
  records DNS failure, zero HTTP responses/raw market bodies and
  `performance_permitted = false`. Diagnostics also remain unrun. Missing metrics
  mean unavailable, not zero or a loss. A complete panel, corporate actions
  (including XLF/XLRE entitlement) and independent calendar are still required;
  the earlier SPY/BIL audit does not supply them. No economic rejection is justified.

## Base and source-branch provenance

Final integration is **`demo/final-presentation`**, created from
`origin/copilot/create-complete-presentation-package` at
`80ac8854c4cdfbcc13f58b50761b714221557249`, a verified descendant of
`research/long-only-strategy-tournament` at
`3e8273472ad24508463916c11b44bd4b754abe6d`.
The general harness ancestor is `e6d620568de409655f7cfe4dd4a6538a282e8046`.
The complete base already contains the [PowerPoint](../demo/Agentic-Quant-Lab-Demo.pptx),
[PDF](../demo/Agentic-Quant-Lab-Demo.pdf) and [synthetic offline demo](../demo/assets/offline-demo/);
it is not the initial scaffold. Presentation commits `05d40c1` and `f83a779`
were present at review start.

The available `main` ref (`origin/main`) and
`origin/copilot/create-demo-presentation-package` both remain at initial
`fb9b789a6be052c0cd421810825efd104acd5960`. Do not confuse that stale package
branch with the **complete** presentation base.

Verification used **local origin refs, not a network refresh**. The following
committed files/trees were compared byte-for-byte with the listed source heads:

| Source ref | Exact head | Evidence comparison |
| --- | --- | --- |
| `origin/copilot/phase-0-sec-filing-recorder` | `04dda08b216a9b76e5d49b2c4c8e618c0d5c2362` | [SEC acceptance](sec-acceptance-report.md), [session report](session-report.md), [deployment report](azure-deployment-report.md) and [constitution](../src/agentic_quant_lab/constitution.toml): **identical**. |
| `origin/research/long-only-strategy-tournament` | `3e8273472ad24508463916c11b44bd4b754abe6d` | [Trend report](etf-trend-validation.md) and entire [trend tree](../research/etf_trend/): **identical**. |
| `origin/copilot/researchpit-stock-data-audit` | `63a9b668b29499889f134c7eda0f3d333a33c528` | [Stock report](stock-data-feasibility.md), [matrix](../research/results/data_source_matrix.csv) and [audit JSON](../research/results/pit_data_audit.json): **identical**. |
| `origin/copilot/researchpead-data-feasibility` | `82cdf944f42015043ae4493541839bf13bbb2c4f` | [PEAD report](pead-data-feasibility.md), [matrix](../research/results/pead_data_source_matrix.csv) and [audit JSON](../research/results/pead_pit_audit.json): **identical**. |
| `origin/copilot/researchetf-relative-momentum` | `544b55e5c2a5110d483024e193055871c085c1a7` | [Sector report](etf-relative-momentum-validation.md), entire [sector evidence tree](../research/etf_relative_momentum/) including the retry, and [landscape](strategy-landscape.md): **identical**. |

**No divergences in the checked original evidence.** This equality does not
claim that independent branch code is identical or that historical acceptance,
provider access or test counts were rerun. Source-session wording and original
reports/results are preserved; only this summary is updated for the final demo.

## Reproduction and demo boundary

The [general research](../research/README.md) and [data audit](../research/notes/data-audit.md)
retain exploratory limits: survivor-selected stocks, revised academic baskets,
pseudo-out-of-sample splits and non-selection-adjusted inference. The older
481-run tournament is not a production qualification; sleeve blends are not
stock-level quality filters.

Real research reproduction uses its own frozen protocols and matching authorized
raw archives, not the demo command. Raw third-party data is not committed; changed
hashes must stop reproduction rather than silently replace the vintage.
The offline demo uses fictional fixtures and deterministic scenario-time receipts,
outside the Phase 0 evidence ledger. Its results are **synthetic only**, not
evidence of real profitability or resolved PIT/data gates.

This presentation review resumed **no research**: no data acquisition, provider
calls, SEC/Azure checks, deployment, scheduling or live trading.
