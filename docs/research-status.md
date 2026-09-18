# Research status and provenance

This is a reading guide to the integrated research, **not a new experiment or
promotion decision**. Canonical structured status lives in the packaged
[`src/agentic_quant_lab/resources/research_status.json`](../src/agentic_quant_lab/resources/research_status.json).
The source reports below remain authoritative for methods, findings and limits.
The demo may display their status, but its synthetic tournament never scores or
promotes these real candidates.

## Integration provenance

The assigned integration branch is **`copilot/make-repository-demo-ready`**.
It was fast-forwarded onto the stable research/trend lineage, not developed on
stale `main`. Independent additions were restored without broad branch merges
or rewriting their conclusions.

| Contribution | Exact source head | Integration treatment |
| --- | --- | --- |
| Completed Phase 0 lineage | `04dda08b216a9b76e5d49b2c4c8e618c0d5c2362` | Historical recorder/acceptance foundation retained. |
| General research harness | `e6d620568de409655f7cfe4dd4a6538a282e8046` (`e6d6205`) | Inherited through stable lineage. |
| Stable research + fixed ETF Trend | `3e8273472ad24508463916c11b44bd4b754abe6d` | Fast-forward integration base. |
| Stock-data audit | `63a9b668b29499889f134c7eda0f3d333a33c528` | Original stock report, source matrix and audit JSON restored unchanged. |
| PEAD-data audit | `82cdf944f42015043ae4493541839bf13bbb2c4f` | Original PEAD report, source matrix and audit JSON restored unchanged. |
| Sector-relative momentum | `544b55e5c2a5110d483024e193055871c085c1a7` | Report, artifacts and additive landscape update copied byte-for-byte. |

Stock additions are `docs/stock-data-feasibility.md`,
`research/results/data_source_matrix.csv` and
`research/results/pit_data_audit.json`. PEAD additions are
`docs/pead-data-feasibility.md`, `research/results/pead_data_source_matrix.csv`
and `research/results/pead_pit_audit.json`. Sector additions are
`docs/etf-relative-momentum-validation.md` and
`research/etf_relative_momentum/`, with its additive update to
`docs/strategy-landscape.md`. Earlier trend artifacts and frozen protocols are
retained, not replaced by sector acquisition failures.

The Phase 0 [SEC acceptance report](sec-acceptance-report.md) records historical
external acceptance **PASS**. That does not set an activation flag:
`phase0.external_acceptance_complete = false`,
`phase0.scheduled_recording_enabled = false` and
`live_execution.enabled = false` deliberately remain untouched in the constitution.
Historical reports describe their own sessions. No SEC/Azure/live acceptance,
production recording, deployment or trading was rerun for this documentation work.

## Verdicts at a glance

| Real candidate | Preserved verdict | Performance evidence available? |
| --- | --- | --- |
| Fixed ETF Trend: Absolute12 and SMA10 | **RESEARCH MORE**; execution-data verification only; **no paper/shadow promotion** | Yes, explicitly exploratory modern NAV proxies, not executable-close returns. |
| Stock momentum / momentum + quality | **C. RESEARCH-GRADE STOCK TEST CURRENTLY BLOCKED.** | No new stock alpha backtest; inherited survivor-panel results remain exploratory. |
| Price-based PEAD | **LOW-COST DATA REQUIRED** | No qualified event/price join; no performance. |
| Consensus-surprise PEAD | **BLOCKED** | No accepted pre-release consensus-vintage evidence. |
| Analyst revision momentum | **BLOCKED** | No accepted multiple-vintage archive for the same target period. |
| Guidance-text PEAD | **LOW-COST DATA REQUIRED** | Original text is plausible input, not a qualified broad timed event/price dataset. |
| PEAD overall | **DEFER PEAD** | Acquisition feasibility only, not an alpha test. |
| Sector-relative / dual momentum | **EXPLORATORY; RESEARCH MORE; DATA ACQUISITION STILL BLOCKED** | Zero of 18 scenarios run; metrics unavailable, not zero. |

None of these labels means a validated profitable strategy. A data-access
blocker is not an economic rejection; a favorable toy score is not evidence
that a blocker has been solved.

## Fixed modern ETF Trend

Authority: [ETF trend validation](etf-trend-validation.md);
[protocol and reproduction](../research/etf_trend/README.md).

The modern follow-up fixes Absolute12 and SMA10 on SPY, with BIL or zero-yield
cash defense. It uses exact calendar-month rules, monthly decisions and
next-session valuation, with initial entry and both sides of rotations charged.
January 4, 2016–July 31, 2026 supplies 2,659 evaluation sessions after 2014–2015
warmup. Six fixed portfolios × three cost levels × two defenses gives **36
scenarios**, not a parameter search.

Official issuer NAV/distributions were acquired. The audit normalizes BIL's
one-for-two 2017 reverse split and accrues distributions on ex-date while
reinvesting at payment. All 12 issuer return checkpoints matched within 2 bps.
These are historical acquisition/audit findings, not checks rerun for this guide.

The required **20 bps one-way** stress comparison illustrates the adverse result:

| Portfolio | Net CAGR | RF-excess Sharpe | Maximum drawdown |
| --- | ---: | ---: | ---: |
| SPY hold | 15.03% | 0.75 | -33.68% |
| Static 80% SPY / 20% BIL | 12.53% | 0.74 | -27.33% |
| Static 70% SPY / 30% BIL | 11.26% | 0.74 | -24.08% |
| Absolute12 / BIL | 11.26% | 0.60 | -33.68% |
| SMA10 / BIL | 7.85% | 0.48 | -28.19% |

Absolute12 did not reduce the worst drawdown; SMA10's temporary crisis protection
was eroded by missed rebounds and whipsaws. Static de-risking is the stronger
comparator. This later evidence supersedes the old crisis-heavy ETF
build-priority recommendation in the general landscape.

**Exact decision: RESEARCH MORE.** Full-period exchange closes remain
unverified; next-session NAV is a valuation proxy, not a fill. Current revised
source vintages, limited premium/discount history and unpaid-dividend cash
constraints at switches further limit execution interpretation.
**Do not promote to paper/shadow.** Verify the same rules on actual closes;
reject the fixed implementation if the adverse results persist. Do not optimize
lookbacks, dates or thresholds to rescue it. This is not a universal rejection
of trend across all markets or samples.

## Stock momentum and momentum + quality

Authority: [stock-data feasibility](stock-data-feasibility.md);
[audit](../research/results/pit_data_audit.json);
[source matrix](../research/results/data_source_matrix.csv).

**Exact decision: C. RESEARCH-GRADE STOCK TEST CURRENTLY BLOCKED.**
No new stock alpha backtest ran, no paid stack was certified and no purchase
was made. The audit could not qualify historical membership, immutable
issue/share-class identity, ticker continuity, complete held-position returns
and terminal economics. A delisted flag is not a terminal-return observation.
Today's constituents and a ticker/CIK-only join cannot establish a historical
investable universe.

Quality additionally requires original accession-level fact/value/timestamp
traces, correct accounting contexts and eligible filing vintages. Current
CompanyFacts data alone is not point-in-time certification. The attempted real
SEC traces were blocked; none is fabricated. Historical reconstruction must
remain separate from Phase 0's observed `decision_eligible_at = fetched_at`.

Reopen with permitted historical samples including IPOs, multiple share classes,
renames, delistings and terminal consideration, plus real filing/restatement
traces. Pass the report's ten acceptance gates before scaling acquisition or
testing alpha. This finding does not prove that a clean free or paid stack
cannot exist, or that momentum/quality fails economically.

## PEAD and earnings-related candidates

Authority: [PEAD-data feasibility](pead-data-feasibility.md);
[audit](../research/results/pead_pit_audit.json);
[source matrix](../research/results/pead_data_source_matrix.csv).

Preserve the distinctions: **price-based PEAD: LOW-COST DATA REQUIRED**;
**consensus-surprise PEAD: BLOCKED**; **revision momentum: BLOCKED**;
**guidance-text PEAD: LOW-COST DATA REQUIRED**.
**Overall recommendation: DEFER PEAD.**

“LOW-COST DATA REQUIRED” is a plausible retail acquisition route, not a verified
price, purchase recommendation or clean 2010–2026 dataset. Price-response drift
does **not** need analyst consensus, but it still needs actual release sessions,
original-event provenance, historical security identity and inactive-inclusive
prices/actions. No qualified event/price join was obtained. Recoverable guidance
text does not by itself qualify a broad timed, versioned event/price join.

Before a baseline implementation or backtest, qualify the report's bounded
event/price sample, original/corrected versions, timing semantics and missingness.
Only then consider a predeclared price-only daily-bar baseline with decision
after event-session close and entry at the next session's open. Surprise and
revision variants separately require licensed, retained pre-event consensus
vintages for matching fiscal periods and accounting bases. Current estimates,
undated historical surprise values and LLM text output cannot substitute.
No PEAD performance or quality improvement is claimed.

## Sector-relative and dual momentum

Authority: [ETF relative-momentum validation](etf-relative-momentum-validation.md);
[frozen protocol](../research/etf_relative_momentum/protocol.json);
[outcome](../research/etf_relative_momentum/outcome.json);
[acquisition retry](../research/etf_relative_momentum/acquisition_20260916T013826Z/data_gate.json).

**Classification: EXPLORATORY. Decision: RESEARCH MORE.
DATA ACQUISITION STILL BLOCKED.** This is independent of SPY Absolute12/SMA10,
not a retuning or a completed economic test.

Protocol commit `79cb2aefe99bb1ab04443c3370c9e1b90de4cd26` freezes monthly
equal-weight top-three selection among nine sector SPDRs, with SPY/BIL controls.
At month-end `m`, the real **12-1** score is `TR(m-1) / TR(m-12) - 1`:
**eleven return intervals**, not twelve shifted returns. Its one dual variant
uses BIL's identical-window return as a hurdle, with failed/equal slots left in
BIL and no lower-ranked replacements. This is not the demo's compressed rule.

The original 24 issuer/calendar GET attempts failed DNS resolution. The separately
preserved retry also failed before HTTP responses; no new raw market bodies or
source-body hashes were obtained. `performance_permitted = false`;
**zero of 18** primary scenarios ran. Blank metrics mean unavailable.
Future-rank, shuffled-rank, XLK-exclusion, regime, rolling-window and turnover
diagnostics remain unrun, not passed. The earlier successful SPY/BIL trend audit
does not supply its missing raw bytes or qualify sector corporate actions.

The single unresolved question is whether normal authorized source access or
authorized exact-byte archives can supply the complete panel, corporate actions
and independent calendar to pass the unchanged gate. This includes XLF's 2016
XLRE noncash entitlement and issuer-return reconciliation; neither may be guessed.
Complete issuer NAV could permit exploratory evaluation but still would not
verify market fills. No parameter rescue, promotion, economic rejection or
optional cross-asset experiment is justified.

## Methodology and reproduction boundaries

The [general harness](../research/README.md) retains frozen hypotheses and all
481 predeclared runs, with delayed availability, exact self-financing costs,
drifted weights and null/planted/leakage controls. Its
[landscape](strategy-landscape.md) and [data audit](../research/notes/data-audit.md)
must accompany the results: the old stock panel is survivor-selected, academic
long baskets are not executable portfolios, retrospective splits are
pseudo-out-of-sample, and descriptive bootstrap intervals are not
selection-adjusted alpha tests. Sleeve blends do not implement stock-level
quality filters or composite factors.

Use the existing [general](../research/README.md) and
[ETF trend](../research/etf_trend/README.md) reproduction instructions, not the
demo command, to reproduce research. Optional research dependencies and matching
authorized raw archives must already be available for offline reproduction.
Third-party raw data is not committed; changed hashes must stop a reproduction
rather than silently update the vintage. New acquisitions must preserve old
failure receipts and identify a new evidence vintage.

The four demo strategies—Relative Momentum, Trend, Weak and Null—use fictional
symbols, fixture seed 20260918, monthly valuations, one-period delay and 10 bps
one-way costs. They are **synthetic only**, not implementations of the real
quality or PEAD candidates. Their deterministic receipt uses fixed scenario
time rather than actual audit-event time and remains outside the Phase 0 ledger.
No generated demo metric is added to the research evidence above.
