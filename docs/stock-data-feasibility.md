# U.S. stock data feasibility and integrity audit

**Audit date:** 2026-09-15. **Decision: C. RESEARCH-GRADE STOCK TEST CURRENTLY BLOCKED.**

This is a data-access/integrity finding, **not** evidence that a clean free stack
cannot exist or that momentum fails. No stock alpha backtest was run. No purchase,
account creation, broker access, production recording, or cloud change was made.

## Scope and evidence standard

Work starts at tournament commit `e6d620568de409655f7cfe4dd4a6538a282e8046`,
on the separate assigned `copilot/researchpit-stock-data-audit` branch. No Trend
agent branch was fetched or merged. Existing files, including
`docs/strategy-landscape.md`, are not changed.

The preferred window is January 2010 through August 2026, the last complete month
at the audit date; September is partial. A clean shorter window is preferable to
invented completeness. A January 2010 momentum decision additionally needs its
pre-2010 lookback, or the first eligible decision must be delayed.

Evidence labels used throughout:

- **Observed:** repository inspection or an actual response in this session.
- **Blocked:** request failed or necessary access was not available.
- **Design requirement:** a rule a future dataset must satisfy, not a passed test.
- **Unverified lead:** a provider capability or source to investigate, not a
  verified entitlement, price, license, coverage claim, or recommendation to buy.

**Observed:** the conventional Alpha Vantage and Massive/Polygon API-key environment
variables are not configured. Only presence was checked; no value was displayed,
no credential files were searched, and no key was requested. This does not prove
that the owner has no subscription elsewhere.

**Blocked:** official SEC documentation, Apple/Microsoft CompanyFacts, and their
submissions endpoints failed DNS resolution before returning HTTP data. Neither
an HTTP denial nor a successful empty dataset was observed. No original filing,
fundamental value, acceptance timestamp, or SEC payload hash can be claimed from
these requests. Raw network failures are recorded in
`research/results/pit_data_audit.json`. Public-data requests were bounded; no
challenge bypass or repeated scraping was used.

The inherited `research/notes/data-audit.md` already labels its old 70-stock panel
survivor-selected and missing delistings. Its earlier access failures are historical
repository evidence, not fresh tests of today's providers.

## Answers to the six decisions

| Question | Finding |
| --- | --- |
| Can we cleanly test long-only stock momentum? | **Not with data acquired and verified here.** Historical membership, security identity, complete held-position returns, and terminal outcomes are still unproved. |
| Can we cleanly test momentum + quality? | **Not yet.** It inherits all price/universe gates plus filing-vintage and issuer-to-security mapping gates. |
| Can SEC filings provide PIT quality features? | **Plausible in principle, not demonstrated here.** Original accession-level facts and public-availability metadata are needed; present-day CompanyFacts alone is not certification. |
| Can we preserve delisted securities? | The offline representation can; **no candidate vendor has passed the historical/terminal-return audit in this session**. A delisted flag is insufficient. |
| What is the stable security identifier? | None has been acquired and certified. Require an internal immutable **security/share-class issue ID**, with dated vendor-ID, ticker, exchange and issuer-CIK links. Never ticker alone, nor CIK alone. |
| What remains EXPLORATORY? | All inherited stock results, any current-constituent panel, unverified vendor-adjusted histories, synthetic timing demonstrations, and any unresolved delisting or filing-vintage joins. |

## Historical universe and identifier contract

Monthly membership must be reconstructed from securities that existed **then**,
including those subsequently delisted. Start from historical listings and dead
issues, not today's S&P 500, Nasdaq directory, CompanyFacts company list, or
currently supported price symbols. Modern personal-account eligibility is not a
historical exchange-membership source; this task makes no broker-availability claim.

Require issue-level listing and exit intervals, common-equity classification,
dated exchange and symbol aliases, and evidence for each interval. Distinguish:

- issuer versus share class versus exchange listing;
- IPO, ticker rename, merger, spin-off, and newly issued post-bankruptcy equity;
- last trading session, trading suspension, exchange delisting, OTC continuation,
  legal cancellation, and final cash/securities distribution.

CIK identifies a reporting entity, not one tradable share class. Multiple securities
may share it; a successor/reorganization can require a new security identity.
FIGI or a vendor permanent ID is a useful external link only after its issue,
share-class, exchange, coverage and effective-date semantics are established.
Never collapse related FIGIs just because they share an issuer. Quarantine ambiguous
ticker/CIK matches rather than joining by normalized company name.

Keep mapping valid-time intervals separately from when evidence was acquired.
Historical event dates reconstructed today do not prove that a vendor published
the same record on that historical day. Freeze each acquisition vintage and
record corrections explicitly; a hash proves byte identity, not historical truth.

For microcap/liquidity exclusion use contemporaneous raw prices and trailing
unadjusted share volume in compatible units. Point-in-time market capitalization
also needs historical shares outstanding and share-class allocation; today's cap
or a retrospectively split-adjusted price floor is not acceptable.

## Price, corporate-action and terminal-value contract

Daily raw OHLCV plus dated splits, dividends and distributions are preferable to
an opaque adjusted close. A usable adjusted series still needs documented
split/dividend treatment, adjustment-vintage provenance and terminal-value coverage.
Split adjustment alone is not a dividend-inclusive total return.

For monthly 6-1/9-1/12-1 mechanics, fix actual exchange-session/month boundaries,
warm-up and next-session consumption before testing performance. Identify a missing
bar as holiday, suspension, no trade, provider gap, or terminal event; these are
not interchangeable. Do not forward-fill a held position's missing return to zero
or drop it and renormalize the survivors. A suspended security may be untradeable
for months: a valuation assumption is not an executable sale.

Back-adjustment is not automatically fatal to every momentum ratio: a uniform
multiplicative factor applied to both endpoints cancels. Nevertheless, future
splits can change historical absolute-price filters; inconsistent volume scaling
changes liquidity; dividends, nonuniform corrections, spin-offs and retroactively
repaired bars can change ranks. Persist raw/action/vintage inputs and fail on a
changed hash instead of silently rerunning an earlier decision. A current
corrected-vintage return study is not an original-vintage execution replay.

**Delisting is an economic cash-flow problem, not a missing-row problem.** Preserve
the last valid exchange quote, OTC transition if relevant, merger consideration,
cancellation and later distributions. Do not assume final close equals terminal
proceeds, or that delisting means a universal -100% return. Cash acquisitions,
stock acquisitions and worthless cancellations need different accounting. If a
held terminal outcome is unresolved, block certification; explicitly labeled
valuation bounds may diagnose sensitivity but cannot make the dataset clean.

## SEC historical quality: proposed integrity proof, not a factor implementation

Official source entry points (requests here were blocked):

- [SEC APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [Apple CompanyFacts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json)
- [Apple submissions](https://data.sec.gov/submissions/CIK0000320193.json)
- [Microsoft CompanyFacts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json)
- [Microsoft submissions](https://data.sec.gov/submissions/CIK0000789019.json)
- [Financial statement datasets](https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets)

These links identify intended primary sources; they are **not successfully
retrieved citations**. No sample metric values or accession/timestamp triples are
invented to fill the missing proof.

### Distinguish the dates and vintages

| Field/concept | Required interpretation |
| --- | --- |
| Period `start` / `end` | Economic interval or balance-sheet instant, not availability. |
| `filed` | Filing date; insufficient by itself for intraday availability. |
| `form` / `accn` | Preserve form and accession for every observation; never discard these during pivoting. |
| Filing acceptance | Join the **same accession** to metadata/original submission; verify timestamp timezone and dissemination semantics. |
| Historical eligibility | Explicit reconstructed public-availability policy with conservative processing lag and real trading calendar. |
| Acquisition timestamp | When this research actually retrieved these bytes, not when a historical strategy knew their contents. |
| Revision | Another accession or a changed source vintage is another version, not an in-place replacement. |

A current CompanyFacts download may contain multiple facts for one economic
period, including comparatives reported in later filings. `fy`/`fp` and a calendar
frame must not be mistaken for unique economic-period identity. A year label alone
does not distinguish quarter, year-to-date and annual durations. Inspect contexts,
taxonomy, units, scale and consolidated versus dimensional facts in original XBRL.
Missing/custom tags and absent early XBRL coverage must be measured rather than
silently converted to zero. A frame-level cross-section cannot replace
accession-specific evidence.

Filtering `end <= decision_date` leaks. Filtering `filed <= decision_date` is
necessary but does not by itself establish acceptance time, original-value
preservation, complete historical filings, or an unambiguous accounting context.
Never keep only the last CompanyFacts row for a period.

Retrieve original 10-K/10-Q XBRL for an accession and compare it with the
CompanyFacts representation. Retain amendments, but recognize that a later
ordinary 10-K/10-Q can also restate a comparative without `/A`. The observation
key needs CIK, accession, taxonomy/concept, unit, economic interval/instant and
context identity. Select only eligible vintages at the decision time. A later
statement can supersede a value **for later decisions**, not mutate earlier ones.

Historical submissions may require additional archive files, not just `recent`.
Issuer discovery must include historical filers, not only today's ticker mapping.
SEC filings alone do not supply an exchange security master or security returns.

### Small interpretable feature candidates

| Candidate | Inputs and rejection conditions |
| --- | --- |
| Profitability | Net income / average assets; use eligible compatible statement vintages and reject unusable denominators. |
| Operating profitability | Operating income / average assets as a plainly labeled simple measure, not an exact academic-factor replication. |
| Gross profitability | Revenue minus cost of revenue, over assets; require consistent tags/accounting scope. Banks and missing cost tags need separate treatment or explicit exclusion. |
| Leverage | Debt / assets, with a declared current/noncurrent debt definition; liabilities / assets is a different measure. |
| Cash generation | Operating cash flow / average assets; preserve cash-flow duration and units. |
| Simple accruals | (Net income minus operating cash flow) / average assets on matched intervals. |

Quarterly cash flow is often presented year-to-date. Derive a quarter or TTM only
from compatible, already-eligible periods; do not confuse nine-month YTD with Q3
or combine restated prior-year YTD with an unavailable vintage. Negative/zero
assets, currencies, changes of fiscal year and sector-specific definitions need
explicit missing/rejection policies, not favorable imputations. Quality coverage
must be measured among the historical universe, especially eventual failures.

### Required manual trace

The attempted sample was Apple (CIK 0000320193) and Microsoft (CIK 0000789019).
Both facts and submission downloads failed. **Real-filing trace: NOT RUN / BLOCKED.**
Add an issuer with an actual comparative restatement and an eventual delisting
before declaring broad viability; these two large survivors would only prove
mechanics, not coverage.

For each future sample record, retain: economic period, original accession and
form, filed date, timezone-qualified accepted/public timestamp, taxonomy/context,
unit/value, original-document hash, and first eligible strategy decision. Use a
declared conservative research lag (for example, the first session decision
strictly after acceptance plus 24 hours); execution must occur later still.
This lag is an assumption, not evidence of historical collection.

The required queries are: one day before filing cannot see the new observation;
after filing **but before eligibility** still cannot; the first eligible decision
can. Append a real amendment/comparative restatement and verify that rerunning the
earlier as-of query returns the original value. Do not claim this passes on
synthetic dates alone.

This is entirely separate from Phase 0: the production recorder's
`decision_eligible_at = fetched_at` remains unchanged (verified in
`src/agentic_quant_lab/recorder.py:129-145` and
`migrations/001_evidence.sql:30-38`). Reconstructed historical availability must
never be inserted as prospectively observed evidence.
