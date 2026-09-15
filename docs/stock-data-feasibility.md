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

Official SDK source was subsequently reachable through GitHub, and Norgate's
publisher-maintained Python documentation through the web reader. These yielded
useful **documentation evidence, not live market data**. Search-generated provider
summaries sometimes conflicted; their dollar prices are deliberately not presented
as verified current offers.

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

## Provider findings and free/low-cost comparison

The full requested comparison fields are in
`research/results/data_source_matrix.csv`. Unknown means unverified, not absent.
No subscription's actual entitlements were tested.

| Candidate | Best established role | Decisive limitation | Access/cost finding |
| --- | --- | --- | --- |
| Alpha Vantage | Historical `LISTING_STATUS` is a promising lead | Later-delisted cohort preservation and identity/price joins untested | No key configured; direct docs/API DNS failures; 25/day is an indexed-documentation lead |
| Massive / Polygon | Official SDK documents dated membership, FIGIs and ticker events | Overview's SEC report-date semantics can leak later filings; terminal proceeds unverified | Key required by SDK; no live entitlement test; current full-history price unverified |
| Nasdaq Trader | Current exchange-directory/classification cross-check | No historical directory archive established here | Public-file leads; access failed; no license or historical coverage certification |
| SEC | Original filings and accession-level quality observations | Facts/submissions inaccessible; not a price or listing master | Public no-key source candidate; current fair-access limits not re-read |
| Norgate | Documented permanent asset IDs, historical major-exchange status and constituent series | No numerical terminal-outcome validation; Windows updater required | Active subscription; Platinum/Diamond documented for historical series; minimum current price unverified |
| Sharadar SEP / TICKERS / ACTIONS | Paid active/dead price and reference-data candidate | Full historical metadata/terminal-event coverage untested | Nasdaq-channel and direct-channel prices/rights must be checked separately |
| Sharadar SF1 | Optional as-reported-fundamental candidate | Filing-date/vintage semantics and observations unverified | Paid minimum unknown; not necessary if SEC proof succeeds |
| Stooq | Potential free price cross-check only | Delisted universe, identity and action completeness unestablished | Current probe failed DNS; inherited audit also reports an earlier challenge |
| Tiingo / EODHD | Lower-cost price/action comparators | PIT universe and terminal-outcome chain unproved | Current plan, history, quotas and licensing unverified |
| OpenFIGI | Supplementary identifier mapping | Current mapping is not historical ticker-validity evidence | Official example supports no key; live rates and data rights unverified |

### Alpha Vantage: the explicit monthly-snapshot test

The task's advertised historical-date/post-2010 capability is consistent with
search-indexed [listing documentation](https://www.alphavantage.co/documentation/#listing-status).
That is not a returned historical CSV. Direct keyless probes for active January
2010, active/delisted December 2020, and delisted August 2026 all failed DNS.
This is neither an authentication response nor proof that the free tier lacks
the endpoint.

**Hypothesis remains unresolved:** `state=active&date=D` must include securities
active at D that are delisted today. Compare complete old active and old delisted
responses with later delisted responses for the event cohort below, including
historical aliases. A missing verified member is a counterexample only after
pagination, classification and alias coverage are resolved. Fetching both states
does not cure an incomplete source.

Also inspect whether an old response contains a future `delistingDate` or revised
classification: correct historical membership does not make every field eligible
at D. Do not filter an old universe using future exit information. CSV fields,
stable IDs, date boundary behavior, row counts, actual quota and price-history
entitlement were **not tested**.

The indexed [support page](https://www.alphavantage.co/support/) reports 25
requests/day; treat the 8-/16-day reconstruction arithmetic below as conditional
on that allowance and one complete response per snapshot. Monthly universe
acquisition appears manageable **if** those semantics pass. Full daily adjusted
history, splits, dividends and delisted prices are separate access/coverage gates,
not benefits implied by `LISTING_STATUS`.

### Massive / Polygon: stronger identity contract, an actual PIT warning

Directly inspected official SDK source, pinned below, establishes:

- All-ticker `date` selects securities available on that date, and `active` is
  described relative to the queried date; default is true. The maximum documented
  page size is 1,000. Omitted date plus active=true is **not** a historical universe.
- Models expose CIK, composite/share-class FIGI, exchange/type, `delisted_utc`,
  `last_updated_utc`, and detailed `list_date`. Optional field presence does not
  prove completeness or precise event-boundary semantics.
- Ticker-event lookup by string targets the entity **currently** represented by
  that string; a prior entity needs its historical identifier.
- **Critical:** the ticker-details date documentation explicitly allows a filing
  submitted **2019-07-31**, for report period **2019-06-29**, in a details query
  dated **2019-06-29**. This is direct documentary evidence against interpreting
  every dated overview field as filing-publication-time-safe. It is not a live
  API reproduction and does not disprove the separate membership contract.
- Aggregate `adjusted` is split adjustment, not total-return certification.
  `raw=True` in the Python SDK requests a raw HTTP response, whereas
  `adjusted=False` requests unadjusted prices. Grouped daily aggregates default
  to **excluding OTC**, material after an exchange delisting.

The SDK's current split/dividend models also include historical adjustment factors;
the dividend model includes a split-adjusted cash amount. These fields do not
establish announcement-time availability, full historical entitlement or terminal
recoveries. The aggregate schema is OHLCV/trade data, not a numerical delisting
return table.

Direct historical reference and IBM aggregate probes failed DNS, so **no current
account access** or subscription requirement was established empirically. Indexed
[pricing](https://massive.com/pricing) distinguishes short free/basic history from
longer paid history; the exact 2010-capable plan and price require direct
confirmation. Price-history restrictions must not be assumed to equal historical
reference restrictions. At 10,000 hypothetical rows/date and 1,000/page, 200
snapshots would need 2,000 requests, not 200. Inactive-state page counts are separate.

### Norgate: the strongest directly readable paid-data documentation

[Publisher Python documentation](https://pypi.org/project/norgatedata/) directly
documents an unchanging `assetid`, first/last quoted dates, security subtypes,
index membership series, and major-exchange-versus-OTC history from **2000**.
The latter two series require **Platinum or Diamond**. This supports a concrete
candidate for a historical master, not a claim that any subscription was accessed
or that every historical classification is publication-time safe.

Its updater is Windows-only and must be running; the Python documentation also
supports WSL2 with mirrored networking. A Linux-only runner without that component
is not the documented acquisition environment. Do not build cloud infrastructure
to work around this task's boundary.

Adjustment modes include NONE, CAPITAL, CAPITALSPECIAL and default TOTALRETURN.
Dividend-column contents depend on what the adjusted prices already include;
distribution entitlement is dated the day before the ex-date. Double-counting
dividends is an obvious integration risk. Use no padding for a missingness audit;
the optional padding modes repeat prior closes.

The publisher's [Zipline integration documentation](https://pypi.org/project/zipline-norgatedata/)
describes padded bars and stale ticker metadata after database updates. Its
documented DBD-to-DBDQQ example illustrates why a cached ticker string is unsafe.
Integration conventions are **not proof of realized terminal proceeds**. No
complete delisting-return product was established. Minimum subscription price,
full-period tier coverage, trial depth, raw-action export completeness and
post-expiry retention rights remain unverified because the relevant
[pricing](https://norgatedata.com/stockmarketpackages.php) and
[FAQ](https://norgatedata.com/data-package-faq.php) pages were inaccessible.

The web reader returned publisher documentation, but a separate raw HTTP
archival attempt returned **HTTP 200 Client Challenge HTML**, not the document.
Those 3,038-byte response hashes are labeled as challenge bodies in the audit;
they must not be cited as hashes of Norgate documentation or market data. No
challenge was executed or bypassed.

### Other credible alternatives, pricing and licensing boundary

- **Nasdaq Trader:** `nasdaqlisted.txt` and `otherlisted.txt` plus their field
  definitions are leads for current symbols, exchanges, ETF/test flags. A current
  directory cannot certify historical membership. No 2010–2026 public directory
  archive was established. Security-name heuristics alone cannot reliably exclude
  preferreds, warrants, funds and reorganized issues.
- **Sharadar:** investigate SEP for equity prices, TICKERS/ACTIONS for identity
  and events; **SFP is the fund-price candidate, not a substitute common-stock
  table**. SF1's advertised as-reported versus most-recent dimensions must be
  checked against original filings before use. `permaticker` is an identifier
  lead, not a verified join in this audit. First/last price or first-added dates
  must not be equated with IPO/delisting/publication dates. Prices, channel-specific
  entitlements and historical versions were not retrieved.
- **EODHD and Tiingo:** inexpensive comparator leads, but neither passed the
  historical-universe or terminal-cash-flow gates. In particular, investigate
  pre-2018 separate corporate-action coverage in EODHD's delisted documentation;
  an indexed coverage caveat is not evidence that adjusted bars are necessarily
  unadjusted or that the gap has been solved.
- **Stooq:** no verified permanent security ID, complete dead-stock universe,
  action ledger or terminal outcomes here. Do not repeat challenge-blocked scraping
  or substitute a live-symbol download list.
- **OpenFIGI:** its official example constructs mapping/search requests without
  a mandatory key. No mapping request was executed. Exchange-level, composite,
  and share-class identifiers must remain distinguishable; no historical
  equity-alias `as_of` contract was established. Code's Apache license is not the
  license for every returned identifier. CUSIP and other third-party identifiers
  can have separate restrictions.

**No current numerical paid minimum is sufficiently verified to authorize a
recommendation.** Paid candidates are Norgate's required historical-series tier
and Sharadar's full-history equity/reference/action offering; no purchase should
follow merely from this shortlist. Obtain current tier, price, history, terminal
treatment and personal-use/retention terms together. SEC may remain the free
fundamentals layer if its proof succeeds. A price-only purchase cannot be assumed
to fix historical membership or delisting realizations.

Public API or SDK access is not a redistribution license. Do not commit vendor
raw data, infer perpetual export rights, or assume personal/nonprofessional
pricing permits team, commercial or cloud redistribution. Current license texts
for all proposed data acquisitions remain a gate.

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

## Delisting and ticker-change case investigation

**Zero cases passed a vendor-history test.** The table deliberately separates
event leads from observed vendor data. No final traded price was acquired for any
case, and no historical inclusion/removal assertion is certified.

The BBBY/TWTR/ATVI/FB leads were recovered from directly read
[secondary event research](https://github.com/huthargrave-lang/MONAD-quant/blob/main/docs/research/CA01_sec_form25_state_machine.md)
and its [corporate-action companion](https://github.com/huthargrave-lang/MONAD-quant/blob/main/docs/research/CA00_corporate_action_outcome_lab.md).
Their primary SEC documents were **not** retrieved here. Dates/amounts below are
explicitly provisional locators, not imported market-data facts.

| Security / event | Event lead to verify against primary documents | Historical-source falsification | Final prices/returns here |
| --- | --- | --- | --- |
| Legacy BBBY → BBBYQ, issuer CIK 0000886158 | Reported suspension 2023-05-03; Form 25 scheduled removal 2023-07-20; reported cancellation without value 2023-09-29 | Old 2020 active snapshot must retain the legacy issue; distinguish exchange exit, intervening OTC and cancellation; do not join a later reused BBBY string to these shares | NOT ACQUIRED; do not infer zero merely from disappearance |
| TWTR, CIK 0001418091 | Reported 2022-10-27 merger: $54.20 cash per eligible common share; suspension before 2022-10-28 open | Retain 2020 history and distinguish last exchange bar, legal conversion and cash settlement; do not carry a traded TWTR position indefinitely | NOT ACQUIRED; $54.20 is reported consideration, **not** a measured final close |
| ATVI, CIK 0000718877 | Reported 2023-10-13 completion: $95 cash per eligible common share | Preserve pre-acquisition universe membership and verify actual halt/removal, not just a requested halt | NOT ACQUIRED; consideration is not assumed final-price execution |
| FRC → FRCB | FDIC bank-resolution lead; exchange/OTC/terminal chain unresolved | Separate sale of deposits/assets from common-shareholder recovery; investigate bank-regulator filings rather than treating absent CompanyFacts as no historical accounts | NOT ACQUIRED; no terminal value inferred |
| SIVB → SIVBQ, holding-company CIK 0000719739 | Exchange and holding-company plan/cancellation documents still needed | Bank receivership is not automatically the holding company's common-equity terminal event; preserve OTC interval if applicable | NOT ACQUIRED; no terminal value inferred |
| FB → META, continuity control | Issuer-event lead: rename before 2022-06-09 open, without a new economic security | Reconcile one security's aliases and uninterrupted returns; a rename must not reset IPO/warm-up | NOT ACQUIRED; SDK mock discrepancy below is not a live return test |

Primary locators for a resumed audit:

- BBBY: [April suspension disclosure](https://www.sec.gov/Archives/edgar/data/886158/000119312523115523/d89202d8k.htm),
  [Nasdaq removal exhibit](https://www.sec.gov/Archives/edgar/data/886158/000135445723000478/bbbydelistreason.txt),
  [plan-effective filing](https://www.sec.gov/Archives/edgar/data/886158/000119312523247428/d579010d8k.htm).
- TWTR: [completion 8-K](https://www.sec.gov/Archives/edgar/data/1418091/000119312522272772/d411753d8k.htm),
  [NYSE notice](https://www.sec.gov/Archives/edgar/data/876661/000087666122000890/ruleprovisionnotice.htm).
- ATVI: [completion 8-K](https://www.sec.gov/Archives/edgar/data/718877/000110465923108985/tm2328253d1_8k.htm),
  [Nasdaq Form 25](https://www.sec.gov/Archives/edgar/data/718877/000135445723000768/primary_doc.xml).
- FRC: [FDIC resolution release](https://www.fdic.gov/news/press-releases/2023/pr23034.html).
- SIVB: [holding-company filing lookup](https://www.sec.gov/edgar/browse/?CIK=0000719739&owner=exclude).
- FB/META: [issuer announcement](https://www.sec.gov/Archives/edgar/data/1326801/000132680122000070/may312022-exhibit991.htm).

An instructive **directly verified fixture warning**: Massive's pinned official
META ticker-event mock gives **2022-06-11**, differing from the June 9 issuer-event
lead. Its tests use mocked responses. This is a reason to compare real event
responses against original notices, **not evidence that the current API is wrong**
and not a validated rename date. A fixture's `"status": "OK"` is not a successful
live request. The mock provenance is included in the JSON artifact.

For each eventual case, require old active membership, post-exit classification,
the full last-trade/OTC/terminal chain, actual final price and consideration, and
stable-ID continuity or a justified new issue. IPO first-trading evidence is also
still missing; a first returned bar or SEC registration date cannot substitute.

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

## Acquisition size and rate-budget arithmetic

These are **planning assumptions**, not measured provider payloads or verified
current limits.

- January 2010–August 2026 contains **200** completed monthly snapshots.
- At a hypothetical 25 requests/day, 200 one-request active snapshots need at least
  **8 days**; fetching active and delisted states each month needs 400 calls and
  at least **16 days**. Pagination, other requests, failures and corrections add
  cost. A final cumulative dead-symbol file may save calls but cannot establish
  the historical membership semantics by itself.
- If daily prices need one full-history request for each of 20,000 lifetime
  issues, the same allowance requires **800 days**, before corporate actions.
  A practical universe endpoint does not make full price acquisition practical.
- With 5,000–8,000 concurrent listings and 252 sessions/year for 16 years and
  eight months, plan for approximately **21–33.6 million daily rows**. At an
  assumed 100 text bytes/row, prices alone are **2.1–3.36 GB uncompressed**.
  Provider JSON, identifier histories, actions, archives and SEC filings add to
  this; compression and actual breadth are unmeasured.
- A hypothetical 15,000-row, 100-byte listing snapshot is 1.5 MB; 200 copies
  would be 300 MB before compression. Do not turn this example into a claim
  about any vendor's number of historical listings.

A small sample should precede a bulk transfer. SEC bulk archives versus individual
company requests need fresh published size/rate confirmation; none was available
here. Do not download an entire all-company archive merely to test two accessions.

## Acceptance-test ledger

No provider adapter, historical backfill engine or synthetic stock-data harness
was added. These are explicit **unpassed gates**, not a passing test suite. The
existing research hash/leakage controls are useful conventions, but their prior
success does not validate new sources. The JSON artifact records every status.

| # | Required adversarial check | Decisive failure condition | This audit |
| --- | --- | --- | --- |
| 1 | Query a monthly universe before a sample IPO | Future issue appears, including through a reused symbol | NOT RUN: no historical payload |
| 2 | Query before and after a known delisting | Pre-exit history disappears when rerun today | NOT RUN: no historical payload |
| 3 | Follow a ticker rename by security ID | Two artificial assets or a discontinuous return | NOT RUN: no identity/price join |
| 4 | Add a future split/dividend/correction vintage | Earlier decision changes without an explicit vintage mismatch | NOT RUN: no action vintages |
| 5 | Remove a held security's next return | Zero fill, silent row drop, renormalization, or invented executable exit | NOT RUN: no return panel |
| 6 | Supply a current-only constituent list | Accepted as evidence of historical completeness | NOT RUN: no stock adapter |
| 7 | Query before a real filing and after eligibility | New fact visible early, or unavailable after its eligible time without explanation | BLOCKED: SEC DNS failure |
| 8 | Add a later amendment or ordinary comparative restatement | Earlier as-of result mutates | BLOCKED: no accession/value trace |
| 9 | Alter a cached byte after provenance capture | Reacquisition/replay silently accepts the revision | NOT RUN on new data: failures have provenance but no payload hash |
| 10 | Deliberately inject future membership/facts/actions | Leaked fixture reaches a decision without rejection | NOT RUN: no stock adapter |

The acquisition itself failed before bytes existed, so there is no SHA-256 to
record for a nonexistent SEC payload. Hashing an error string would not certify
market or filing data. A resumed acquisition must retain request parameters
(without keys), provider/version, UTC retrieval time, HTTP status, byte count,
exact payload SHA-256, and availability/vintage interpretation. Never replace a
prior manifest to make a changed download pass.

## Verified documentary anchors

These are the official sources actually read, distinct from inaccessible website
links and secondary event leads. SDK evidence is pinned to immutable commits.

| Anchor | Directly supported finding |
| --- | --- |
| [Massive Go ticker models, lines 35–52](https://github.com/massive-com/client-go/blob/d24412df7b80e8b1996f2a0c97587cd2e0214e0f/rest/models/tickers.go#L35-L52) | Date/active membership contract and pagination limit |
| [Same file, lines 141–151](https://github.com/massive-com/client-go/blob/d24412df7b80e8b1996f2a0c97587cd2e0214e0f/rest/models/tickers.go#L141-L151) | Report-period rather than filing-publication date in ticker details |
| [Same file, lines 383–392](https://github.com/massive-com/client-go/blob/d24412df7b80e8b1996f2a0c97587cd2e0214e0f/rest/models/tickers.go#L383-L392) | String ticker-event lookup resolves the current entity |
| [Massive Python ticker models](https://github.com/massive-com/client-python/blob/481e5c270ea85e8eae5e96f8b9fda34e5e2a674a/massive/rest/models/tickers.py#L59-L116) | Optional identifier/listing/delisting fields |
| [Massive aggregate client](https://github.com/massive-com/client-python/blob/481e5c270ea85e8eae5e96f8b9fda34e5e2a674a/massive/rest/aggs.py#L27-L132) | Split adjustment, raw-response distinction and OTC default |
| [Massive dividends](https://github.com/massive-com/client-python/blob/481e5c270ea85e8eae5e96f8b9fda34e5e2a674a/massive/rest/models/dividends.py#L24-L37) and [splits](https://github.com/massive-com/client-python/blob/481e5c270ea85e8eae5e96f8b9fda34e5e2a674a/massive/rest/models/splits.py#L19-L27) | Historical adjustment fields, not completeness guarantees |
| [Massive META mock](https://github.com/massive-com/client-python/blob/481e5c270ea85e8eae5e96f8b9fda34e5e2a674a/test_rest/mocks/vX/reference/tickers/META/events%26types%3Dticker_change.json) and [mock setup](https://github.com/massive-com/client-python/blob/481e5c270ea85e8eae5e96f8b9fda34e5e2a674a/test_rest/base.py#L8-L43) | Fixture date only; not a production API response |
| [OpenFIGI official example](https://github.com/OpenFIGI/api-examples/blob/f847dce9492a6bac685f9fdf1d9450e57280a9c4/python/example.py#L31-L92) | Optional-key mapping/search construction |
| [Norgate Python documentation](https://pypi.org/project/norgatedata/) | Asset IDs, historical series, adjustments, padding and updater requirements |
| [Norgate Zipline documentation](https://pypi.org/project/zipline-norgatedata/) | Padding and stale-symbol integration warnings |

The CSV provides remaining provider documentation, pricing and licensing URLs as
**follow-up locators**. Those pages are not upgraded to directly verified sources.

## Stop decision and narrowly scoped reopening gate

**C. RESEARCH-GRADE STOCK TEST CURRENTLY BLOCKED.** The immediate blockers are
unavailable historical sample access and the lack of verified terminal economics,
identity continuity and real accession-level quality observations. This is not a
claim that all paid or free providers are deficient; the evidence here cannot
choose a complete stack or the cheapest adequate purchase.

Stop before a broad download, a strategy implementation or an alpha backtest.
Reopen only with ordinary permitted access to:

1. Current official limits, pricing and retention/use terms; do not request or
   publish credentials in the report.
2. A small historical sample covering the event cohort, survivors, multiple share
   classes and IPO controls, with complete pagination and raw/action provenance.
3. Independently verified original event documents and terminal consideration,
   including unresolved OTC claims rather than silent exclusions.
4. Real SEC accession/value/timestamp traces and a restatement negative control.
5. Passing versions of all ten acceptance gates, with coverage/missingness broken
   out by year and security outcome, before scaling the longest defensible period.

A shorter clean period may be accepted explicitly; restricting to today's
survivors may not. Funding discussions can resume after samples identify precisely
what a purchase solves. **Nothing was purchased, no paid stack is certified, and
neither momentum efficacy nor quality improvement was tested.**

## Validation and unchanged boundaries

The only additions are this report, the source matrix and the audit JSON.
JSON/CSV structure and cross-artifact status consistency are checked locally;
`git diff --check` and a diff against the requested tournament base check scope.
No documentation-specific test suite exists, and no executable adapter or new
dependency was added. These checks validate the artifacts, not market data.
Secret scanning and automated review are run before finalizing.

Phase 0 source, migrations, infrastructure, production workflows, broker code,
the strategy landscape and existing research results are unchanged relative to
the tournament base. `live_execution.enabled = false` and
`phase0.scheduled_recording_enabled = false` remain unchanged in the constitution.
