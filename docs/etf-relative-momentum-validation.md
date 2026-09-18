# ETF cross-sectional / relative momentum

**Classification: EXPLORATORY. Decision: RESEARCH MORE.**
**Data-gate stop, not a completed backtest or an economic rejection.**

This is an independent research family, not a retuning of SPY Absolute12 or
SMA10. The isolated assigned branch incorporates
`research/long-only-strategy-tournament` at
`3e8273472ad24508463916c11b44bd4b754abe6d`. Work remains on the separate assigned
`copilot/researchetf-relative-momentum` branch; the base branch, published history
and earlier trend experiment are unchanged.

## Literature review before results

Reviewed September 15-16, 2026. Direct publisher/author full-text retrieval
failed DNS resolution in this environment. The review therefore uses
search-visible publisher/author/university metadata and abstracts, alongside the
base research's bibliographic review. It does **not** claim independently
verified full-text methods, reproduced paper results, or audited download links.

| Evidence | Relevance and limits |
| --- | --- |
| Jegadeesh & Titman (1993), *Returns to Buying Winners and Selling Losers*, [Journal of Finance](https://doi.org/10.1111/j.1540-6261.1993.tb04702.x) | Intermediate-horizon stock winner-minus-loser evidence; not a long-only ETF result. |
| Moskowitz & Grinblatt (1999), *Do Industries Explain Momentum?*, [Journal of Finance](https://doi.org/10.1111/0022-1082.00146) | Industry momentum motivates sector ranking, but constructed industry portfolios are not nine tradable SPDRs. |
| Andreu, Swinkels & Tjong-A-Tjoe (2013), *Can exchange traded funds be used to exploit country and industry momentum?*, [Financial Markets and Portfolio Management](https://doi.org/10.1007/s11408-013-0207-8), [author-university record](https://pure.eur.nl/en/publications/can-exchange-traded-funds-be-used-to-exploit-country-and-industry/) | Direct historical ETF evidence; the abstract reports country/industry momentum and bid-ask spreads below estimated break-even costs. This does not establish modern profitability, our exact rule, or all-in execution costs. |
| Faber (2010), *Relative Strength Strategies for Investing*, [author manuscript](https://mebfaber.com/wp-content/uploads/2018/12/SSRN-id1585517-Relative-Strength-Strategies-for-Investing.pdf) | Practitioner rotation precedent, using ten French industry portfolios rather than the nine traded SPDRs. Detailed filter claims were not verified and are not imported. |
| Antonacci (2012), *Risk Premia Harvesting Through Dual Momentum*, [SSRN 2042750](https://ssrn.com/abstract=2042750); (2013), *Absolute Momentum*, [SSRN 2244633](https://ssrn.com/abstract=2244633) | Practitioner relative-plus-absolute framework. Our same-window BIL hurdle is an explicit design choice, not a claimed exact replication of these papers. |
| Vanstone, Hahn & Earea (2021), *Industry momentum: an exchange-traded funds approach*, [Accounting & Finance](https://doi.org/10.1111/acfi.12724), [university record](https://research.bond.edu.au/en/publications/industry-momentum-an-exchangetraded-funds-approach/) | Direct ETF qualification: its abstract reports behavior different from stock momentum and an unexpected portfolio group surviving risk adjustment. It does not justify assuming top-ranked sectors win; detailed horizon/cost results are not verified here. |
| Hwang & Rubesam (2015), *The disappearance of momentum*, [European Journal of Finance](https://doi.org/10.1080/1351847X.2013.865654) | Negative stock evidence: the abstract reports disappearance after the late 1990s. Sample-dependent, not proof that every ETF momentum rule is dead. |
| McLean & Pontiff (2016), *Does Academic Research Destroy Stock Return Predictability?*, [Journal of Finance](https://doi.org/10.1111/jofi.12365) | Publication-decay evidence across stock predictors; not an ETF-specific decay estimate. Do not apply a literature-wide haircut as a measured sector effect. |
| Daniel & Moskowitz (2016), *Momentum Crashes*, [Journal of Financial Economics](https://doi.org/10.1016/j.jfineco.2015.12.002) | Rebound/crash risk matters, but the short-loser leg differs from a long-only sector book. Do not transplant long-short crash magnitudes. |
| Novy-Marx & Velikov (2016), *A Taxonomy of Anomalies and Their Trading Costs*, [Review of Financial Studies abstract](https://ideas.repec.org/a/oup/rfinst/v29y2016i1p104-147..html) | Trading costs can consume anomaly returns. This motivates fixed cost stresses and whipsaw disclosure, not adding a buffer after seeing results. |

**Specification inference, not performance selection:** academic cross-sectional
work commonly distinguishes intermediate momentum from the most recent month's
return; the [French prior-2-through-12 convention](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html)
is documented in the base review. Practitioner annual relative strength can
instead include the latest month. There is no verified evidence here establishing
which is better for this exact ETF universe. We choose **12-1** as an explicit
cross-sectional convention and reject the temptation to run both and keep the
winner. Stock short-horizon reversal need not transfer to sector ETFs; this is
a limitation of the choice, not a hidden claim of superiority. Top three is
a simple top-third portfolio, not the breadth with the highest reported Sharpe.

Taken together, the evidence supports a falsifiable experiment, **not promotion**.
ETF-specific qualifications, stock decay, switching costs and technology
concentration are serious alternatives to persistent rank-based alpha.

## Preregistration

The [frozen protocol](../research/etf_relative_momentum/protocol.json), committed
in **`79cb2aefe99bb1ab04443c3370c9e1b90de4cd26`**, defines the complete experiment
before sector results. No sector strategy performance has been calculated.
An unsuccessful source audit does not waive the pre-performance data requirements.

- Universe: XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY; SPY benchmark, BIL defense.
- One relative rule: monthly, equal-weight top three, **12-1** total returns.
  Precisely, at month-end `m`, rank `TR(m-1) / TR(m-12) - 1`.
  This is **eleven return intervals**, the conventional prior-2-through-12
  construction, not twelve returns shifted back one month.
- One dual variant: the same selected sectors must individually exceed BIL's
  return over that identical window; failed/equal slots go to BIL. No replacement
  from lower ranks. Exact ranking ties use alphabetical ticker order.
- Benchmarks: SPY hold, monthly equal-nine, monthly 80/20 SPY/BIL, monthly 70/30.
- Execute at the following verified exchange session close. No same-close fills.
- Only 0/10/20 bps one-way; charge buys and sells, initial entry, and BIL trades.
- Warmup 2014-2015; common evaluation January 2016-July 2026, matching the
  earlier modern ETF study's dates, not selected on sector results. This is
  deliberately **not inception-to-date evidence** and excludes the financial crisis.
- All requested regimes, rolling 36-month windows, rotations, holding spells,
  sector attribution, XLK exclusion and shuffled-rank diagnostics are frozen.
  No lookback grid, hurdle optimization, new strategy, or turnover buffer.

The including-current-month alternative would use `TR(m) / TR(m-12) - 1`.
It is plausible for ETFs, but is **not tested**. Choosing the familiar
cross-sectional convention is a prior specification choice, not a claim that
skipping a month empirically improves sector ETFs.

## Source gate: blocked before performance

On **2026-09-16 at 00:00:54 UTC**, 24 bounded GET attempts through the unchanged
`research.data.fetch` collector failed DNS resolution:

- Product-page and NAV-workbook candidates for each of the eleven ETFs: 22 attempts.
- The base's issuer-wide historical-distribution URL: one attempt.
- The base's independent French session-calendar/RF URL: one attempt.

The errors were `[Errno -5] No address associated with hostname` for
`www.ssga.com` and `mba.tuck.dartmouth.edu`. There were **no HTTP responses, no
market-data bodies, and no source-body hashes**. Web-fetch and shell checks
also failed. No raw research cache was present in the fresh clone.
This establishes an acquisition failure **in this environment**, not that the
issuer lacks these data or that a candidate URL is a valid/invalid endpoint.
No alternate DNS, unauthorized mirror, credentials or access workaround was used.

**URL patterns were not accepted as evidence.** Sector NAV/page paths are
explicitly marked *candidates* in the receipts, not verified issuer links.
Search summaries that asserted continuous coverage or no historical splits
without retrieved primary evidence were discarded. The existing SPY/BIL
manifest is useful provenance context but neither supplies its missing raw
bytes nor verifies any sector ETF.

| ETF | Issuer inception | Historical NAV / distributions | Continuous required coverage | Corporate actions / return reconciliation |
| --- | --- | --- | --- | --- |
| XLB | Unverified | Unverified / unverified | Unverified | Not run |
| XLE | Unverified | Unverified / unverified | Unverified | Not run |
| XLF | Unverified | Unverified / unverified | Unverified | Not run |
| XLI | Unverified | Unverified / unverified | Unverified | Not run |
| XLK | Unverified | Unverified / unverified | Unverified | Not run |
| XLP | Unverified | Unverified / unverified | Unverified | Not run |
| XLU | Unverified | Unverified / unverified | Unverified | Not run |
| XLV | Unverified | Unverified / unverified | Unverified | Not run |
| XLY | Unverified | Unverified / unverified | Unverified | Not run |
| SPY | Not reverified in this acquisition | Not reverified / not reverified | Not reverified | Not run |
| BIL | Not reverified in this acquisition | Not reverified / not reverified | Not reverified | Not run |

These are **unknowns, not assertions of missing trading days or invalid funds**.
Even the independent session count is null, not inferred from whichever ETFs
happen to be present. No forward filling, inferred split adjustment, fabricated
distribution, current-holdings backcast, or shortened-sample substitute was used.

The frozen audit specifically requires:

1. Primary evidence of inception, downloadable coverage and every required session
   for **all eleven** ETFs; hash and archive original bytes.
2. A single consistent historical share basis, checking whether fields are already
   split-adjusted. Audit candidate 2025 sector splits, the base-reported BIL
   reverse split, and **XLF's 2016 in-kind XLRE event**. A noncash entitlement is
   not an ordinary stock split or a cash dividend to guess from a NAV drop.
3. Ex-date accrual/payment-date reinvestment and 66 independent issuer return
   checkpoints (six per ETF), with the frozen 2 bps tolerance. No assertion that
   the SPY/BIL parser automatically handles sector noncash actions.
4. Disclosure of changed economic sector definitions, including the 2016 real-estate
   separation and 2018 communication-services restructuring. A fixed ticker
   universe is not a fixed constituent universe; XLK is not all technology risk.
5. A committed passed audit before running strategies. Complete issuer NAV would
   be sufficient to **run exploratory research**, but next-session NAV remains
   a valuation proxy, not a verified exchange fill. Neither NAV nor actual-close
   history was obtained here.

Because these requirements could not be satisfied, there was no defensible
performance calculation to continue with. This is not a decision to stop because
a strategy appeared attractive, nor permission to retune it.

## Results and falsification status

**Zero of the 18 preregistered primary scenarios ran.** All required metric
columns are present in [metrics_status.csv](../research/etf_relative_momentum/metrics_status.csv);
blank entries explicitly mean **unavailable**, never zero return or zero turnover.

| Model | 0 bps | 10 bps | 20 bps |
| --- | --- | --- | --- |
| SPY buy-and-hold | Not run | Not run | Not run |
| Monthly equal-weight nine sectors | Not run | Not run | Not run |
| Monthly static 80/20 SPY/BIL | Not run | Not run | Not run |
| Monthly static 70/30 SPY/BIL | Not run | Not run | Not run |
| Frozen pure sector-relative momentum | Not run | Not run | Not run |
| Frozen dual sector momentum | Not run | Not run | Not run |

No CAGR, volatility, Sharpe, drawdown, Calmar, worst complete year, turnover,
rotations, holdings count, beta, correlation, BIL exposure or sector concentration
is claimed for any model. The same applies to rolling three-year results.
Previously published SPY trend results are **not reused as results of this
unperformed matched experiment**.

| Required falsification | Answer on this evidence |
| --- | --- |
| 1. Outperform equal-weight sectors after costs | Not evaluable; no matched return paths. |
| 2. Outperform SPY risk-adjusted | Not evaluable; no Sharpe/beta comparison. |
| 3. Beat static de-risking | Not evaluable; both static controls remain mandatory. |
| 4. Depend on one sector or crisis | Not evaluable; no attribution or crisis exclusions computed. |
| 5. Dual filter adds value versus merely lowering exposure | Not evaluable; no pure/dual exposure and P&L decomposition. |
| 6. Performance lost to turnover | Not evaluable; no executions or fees simulated. |
| 7. Winners persist enough to offset switching | Not evaluable; no ranks, overlaps or completed holding spells. |
| 8. Collapse post-2020 | Not evaluable; the 2021-July 2026 slice remains frozen. |
| 9. Work separately in 2016-2019, 2020, 2021, 2022, 2023-2025 | All five not evaluated; no regime is silently omitted or labeled a pass. |
| 10. Apparent alpha is just tech concentration | Not evaluable; all-sector attribution, XLK contribution and descriptive eight-sector exclusion remain mandatory. |

There is **no monthly-rotation log to report**, not a finding of zero rotations.
Short spells, repeated exits/reentries, negative-value ranking changes and
shuffled-rank outcomes likewise remain uncomputed. Fabricating empty trade logs
or plausible-looking statistics would falsely suggest that the experiment ran.
The [diagnostic status artifact](../research/etf_relative_momentum/diagnostic_status.json)
records each of these explicitly.

## Controls and immutable evidence

The inherited research suite passed **44 tests**. The unchanged application and
Azure unit suites passed **156 tests**, with **79 prerequisite-dependent tests
skipped**. No database/live-service acceptance is claimed.

Secret scanning found no secrets. JSON/CSV consistency, all original artifact
hashes and the unchanged Phase 0 flags were checked. The automated review backend
was unavailable because its configured model was missing; a separate read-only
review of these changes found no significant issues. CodeQL classified these
documentation/metadata-only changes as trivial and skipped analysis; this is not
a claim of a completed security scan. The appended
[review receipt](../research/etf_relative_momentum/review_validation.json) records
these distinctions without changing the frozen evidence manifest.

Relevant inherited checks cover future availability, same-close rejection,
missing held returns, changed source hashes, drifted self-financing costs,
split-neutrality, distribution receivables, and synthetic cross-sectional
winners. These are **not substitutes** for the unimplemented sector-specific
adapter and its required tests: future-month ranking rejection, missing history
for *unheld* sectors, noncash/split source corruption, future-perturbation
invariance, and the 100-seed shuffled-rank experiment must still pass before
real sector results are permissible. No claim that shuffled ranks failed to
produce alpha is made without running them.

The files under `research/etf_relative_momentum/` are a frozen **negative
acquisition/evaluation-status vintage**, not raw market data or a completed
results package:

| Artifact | Contents |
| --- | --- |
| [protocol.json](../research/etf_relative_momentum/protocol.json) | One rule and dual variant; six models, costs, formulas, sample, diagnostics and decision gates, committed before performance. |
| [source_attempts.json](../research/etf_relative_momentum/source_attempts.json) | All 24 exact URLs, UTC request times, transport errors, and explicitly null source hashes. |
| [data_audit.json](../research/etf_relative_momentum/data_audit.json) | All eleven per-asset unresolved checks; `performance_permitted=false`; protocol/receipt hashes. |
| [metrics_status.csv](../research/etf_relative_momentum/metrics_status.csv) | All 18 scenario rows and required metric columns, explicitly unavailable. |
| [diagnostic_status.json](../research/etf_relative_momentum/diagnostic_status.json) | Every falsification, regime and sector-control status; no invented outcomes. |
| [outcome.json](../research/etf_relative_momentum/outcome.json) | Machine-readable classification, decision and the single unresolved question. |
| [validation.json](../research/etf_relative_momentum/validation.json) | Existing-test commands/counts and their scope limitations. |
| [artifact_manifest.json](../research/etf_relative_momentum/artifact_manifest.json) | SHA-256/length binding of protocol, receipts, audit and status artifacts to the frozen protocol commit. These are **artifact hashes**, not unavailable market-source hashes. |

The source receipts were collected with the existing `research.data.fetch`
(45-second timeout, 25 MB body limit, exact URLs listed per receipt); no downloader,
strategy engine, dependency or infrastructure was added. To continue, obtain
authorized original issuer archives or working authorized issuer access, discover
and verify real download links, and preserve the exact bodies and provenance in
the existing ignored research-cache convention. A later attempt must use a new
identified evidence vintage and retain this failed-attempt record unchanged.
Do not overwrite the frozen protocol or silently adopt a newly revised source.
The existing research test command is documented in `research/README.md`; the
exact commands used here are recorded in `validation.json`.

## Conclusion

**EXPLORATORY:** the evidence does not establish either profitability or failure
of sector-relative momentum. It establishes that the mandatory source gate could
not be passed here. No strategy is promoted; no economic rejection or parameter
rescue is justified. The optional cross-asset stage is not started.

**Exactly one unresolved question:** Can a complete, hash-verifiable issuer
dataset for the nine sectors, SPY and BIL, including corporate actions and an
independent session calendar, be retrieved and reconciled well enough to run
the frozen comparison?

## Research boundaries

Phase 0 remains frozen: `scheduled_recording_enabled = false` and
`live_execution.enabled = false` (the repository's live-execution flag).
There are no recorder, policy, dependency, infrastructure, scheduler or broker
changes. No trades, stock-level data acquisition, PEAD, or optional cross-asset
experiment are included.

RESEARCH MORE

## Acquisition-unblock retry — 2026-09-16 01:38:26 UTC

**DATA ACQUISITION STILL BLOCKED. Classification: EXPLORATORY.**

This is a new acquisition attempt, not a correction of the original DNS-failure
record above. The current runner was tested again rather than assuming the
previous runner's failure persisted. The frozen protocol at
`79cb2aefe99bb1ab04443c3370c9e1b90de4cd26` remains byte-for-byte identical
(SHA-256 `ae767c8fa68a2da9003e07bd0beb48131990b0a276a3725017ad89f277a6bffd`).
No strategy or parser code was changed.

### Normal network diagnosis

The new checks ran from `2026-09-16T01:38:26.159983+00:00` through
`2026-09-16T01:38:26.252387+00:00`, before any strategy-code changes or performance
calculations. All used ordinary system resolution and HTTPS clients:

| Check | Requests | Observed result |
| --- | ---: | --- |
| `getent ahosts`, separately for each required host | 2 | Exit 2, no addresses |
| Python `socket.getaddrinfo`, separately for each host | 2 | `gaierror`, errno -5: no address associated with hostname |
| Python urllib GET: eleven NAV URLs, eleven product-page URLs, distributions, French RF/calendar | 24 | DNS failures before an HTTP response |
| curl HEAD and GET: exact prior SPY NAV, BIL NAV, distribution and French RF URLs | 8 | Exit 6: could not resolve host |

The failing hosts are **`www.ssga.com`** and **`mba.tuck.dartmouth.edu`**.
There were **zero HTTP responses and zero downloaded market-data bodies**.
TLS, rate limits, challenges and URL validity were **not reached/evaluable**,
not diagnosed as failures. curl's `000` output is a local no-response sentinel,
not a server status. No alternate DNS, scraping proxy, challenge bypass,
network-setting change or repeated retry loop was used.

The [new network receipts](../research/etf_relative_momentum/acquisition_20260916T013826Z/network_diagnostics.json)
record every exact URL, client, method, UTC timing and error. Sector paths remain
unverified candidates from the original attempt, not newly verified issuer links.

### Prior successful sources and reusable behavior

The earlier Trend acquisition **did succeed**, according to its preserved
[source manifest](../research/etf_trend/results/data_manifest.json) and
[issuer checkpoints](../research/etf_trend/results/issuer_return_crosschecks.csv).
That manifest records retrieval at `2026-09-15T22:23:16.434200+00:00`;
all twelve SPY/BIL return checkpoints passed 2 bps, with maximum recorded
absolute difference approximately 1.005 bps. These are historical results,
not new reconciliations in this runner.

The exact previously successful URLs tested again were:

- SPY NAV: <https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-spy.xlsx>
- BIL NAV: <https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-bil.xlsx>
- Distributions: <https://www.ssga.com/library-content/products/fund-data/etfs/us/spdr-etf-historical-distributions.xlsx>
- Independent RF/session calendar: <https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip>

No source bodies listed in the Trend manifest were present in this clone's
research cache. Their historical hashes cannot replace missing raw bytes.
**Today's DNS failures do not establish that State Street's data are unavailable.**

The existing implementation was inspected, not reimplemented:

- `load_nav` reads `navhist`, header row 3, with strict dated/numeric NAV records.
- `load_distributions` filters the shared `dividend` sheet by ticker, validates
  ex/record/payment dates and sums cash income/capital-gain fields within 2014+.
- `payable_total_return` accrues on ex-date, retains receivables until payment,
  applies explicit share-unit ratios and reinvests at payment.
- The BIL audit verifies **2017-11-30, 0.5 new shares per old share**, using NAV,
  shares outstanding and independent evidence; a reverse split is not a gain.
- The independent French RF dates define exchange sessions. Missing required
  sessions fail; extra nonexchange NAV observations are identified separately.
- Issuer checkpoints use the frozen **2 bps** tolerance. The research downloader
  rejects mismatched expected source hashes rather than replacing a vintage.

The [new gate artifact](../research/etf_relative_momentum/acquisition_20260916T013826Z/data_gate.json)
records the inspected parser file hashes and functions. No market parser ran.
This SPY/BIL implementation is **not** evidence that the sectors have identical
corporate actions: XLF's 2016 XLRE in-kind entitlement and economic value, all
sector splits including candidate 2025 events, special/noncash distributions,
ticker continuity and unit changes still require actual source reconciliation.
None was guessed, silently treated as a cash dividend, or newly marked verified.

### Per-ETF gate result

Here **FAIL means required evidence could not be acquired**, not a failed
economic test or a measured issuer-return mismatch.

| ETF | Acquisition gate | Exact failing NAV source suffix | Corporate actions / issuer checkpoints |
| --- | --- | --- | --- |
| XLB | FAIL — DNS | `navhist-us-en-xlb.xlsx` | Not run |
| XLE | FAIL — DNS | `navhist-us-en-xle.xlsx` | Not run |
| XLF | FAIL — DNS | `navhist-us-en-xlf.xlsx` | Not run |
| XLI | FAIL — DNS | `navhist-us-en-xli.xlsx` | Not run |
| XLK | FAIL — DNS | `navhist-us-en-xlk.xlsx` | Not run |
| XLP | FAIL — DNS | `navhist-us-en-xlp.xlsx` | Not run |
| XLU | FAIL — DNS | `navhist-us-en-xlu.xlsx` | Not run |
| XLV | FAIL — DNS | `navhist-us-en-xlv.xlsx` | Not run |
| XLY | FAIL — DNS | `navhist-us-en-xly.xlsx` | Not run |
| SPY | FAIL — DNS | `navhist-us-en-spy.xlsx` | Not rerun; prior six passes preserved |
| BIL | FAIL — DNS | `navhist-us-en-bil.xlsx` | Not rerun; prior six passes preserved |

Each suffix above belongs to
`https://www.ssga.com/library-content/products/fund-data/etfs/us/`; every complete
URL is retained in the receipts. The shared distribution source and all
inception-page requests also failed DNS. Calendar acquisition failed at the
exact French URL above. Coverage, missing/duplicate sessions, non-session
observations and new checkpoint pass/fail counts remain **unknown**, not zero.
No ETF was dropped, no return was forward-filled and the January 2016-July 2026
evaluation window was not shortened.

### Gate decision and evidence preservation

**`performance_permitted = false`.** Zero of the eighteen model/cost scenarios
ran. All frozen falsification diagnostics remain unrun, including shuffled
ranks, future-ranking rejection, XLK exclusion, rolling windows, regimes,
rotation/spell analysis and turnover attribution. This retry is blocked by
**absence of raw inputs**, not solely by NAV-versus-market-close execution
quality: neither new economic evidence nor new execution evidence exists.

The new dated directory contains network receipts, the per-ETF gate, parser
hashes and an [artifact manifest](../research/etf_relative_momentum/acquisition_20260916T013826Z/artifact_manifest.json).
Its hashes bind our records, **not unseen vendor data**. Source-body hashes and
coverage are explicitly null because nothing was retrieved. The original
acquisition artifacts, earlier successful Trend artifacts and protocol are
unchanged; later attempts must use another identified vintage.

Validation for this retry checked JSON consistency, all original and new
artifact hashes, protocol equality to its frozen commit, and unchanged disabled
Phase 0 flags. No production code, dependencies or tests changed; the earlier
test counts above remain historical, not tests rerun during this documentation
and evidence-only retry. No broker, Robinhood, Azure, purchase or trading action
was performed.

Secret scanning was clean. The automated review backend was unavailable because
its configured model was missing; a separate read-only review found no
significant issues. CodeQL skipped these documentation/metadata-only changes as
trivial; no completed CodeQL analysis is claimed.

**One unresolved question:** Can normal authorized access to the two source
hosts, or authorized exact-byte source archives, supply the complete inputs
needed to pass the unchanged data gate?

The required unblock is normal runner DNS/HTTPS access to those hosts or supplied
authorized raw archives with verifiable provenance. No protocol alteration or
parameter optimization can resolve this environmental failure. No promotion
or economic rejection is justified.

RESEARCH MORE
