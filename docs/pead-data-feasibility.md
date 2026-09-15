# PEAD data feasibility

Research date: **2026-09-15 UTC**. This is a data-acquisition decision, not an
alpha test or a production-readiness assessment.

**Answer:** a low-cost **price-response** baseline has a plausible acquisition
route without analyst consensus. A clean 2010–2026 joined dataset was **not**
obtained or certified. Historical consensus surprise and revision momentum
remain gated by actual vintage evidence, not merely API price. Original
guidance text is recoverable, but a broad timed, versioned event/price join is
still unqualified. No strategy performance is reported.

## Scope and isolation

The assigned branch, `copilot/researchpead-data-feasibility`, was fast-forwarded
to `research/long-only-strategy-tournament` at
`3e8273472ad24508463916c11b44bd4b754abe6d` before this investigation. It is the
separate PEAD branch; no work was based on the initial main-only tree.

Only this report and PEAD-prefixed research evidence are deliverables. Phase 0,
Azure, migrations, execution code, ETF Trend artifacts and stock-audit artifacts
are not changed. No broker, Robinhood, trading, purchase, deployment, new
dependency, alpha backtest, parameter search or LLM strategy was used.
`scheduled_recording_enabled = false` and `live_execution_enabled = false`
remain unchanged.

The target is liquid U.S. common stocks, ideally 2010 through the research date,
not the whole future calendar year 2026. The previously identified
historical-universe/delisting/PIT-stock-data problems remain acquisition
dependencies; this investigation does not repeat that audit or use the
tournament's survivor-selected stock panel as a substitute.

## Evidence standard

- **DIRECT:** an HTTP response actually retrieved during this investigation.
  A successfully retrieved issuer page is not a successfully retrieved vendor
  consensus history.
- **DIRECT_SCHEMA:** provider-owned SDK/reference files retrieved through
  GitHub. This verifies what the inspected documentation says, not historical
  data population, current API behavior or a purchased entitlement.
- **INDEXED:** primary-source documentation surfaced by web search, not a
  downloaded historical observation. Search synthesis, sample JSON and
  marketing examples are not observations.
- **BLOCKED:** the attempted request did not yield usable data. DNS failure is
  an environment-access failure, not a provider's authentication response or
  proof that its free tier is empty.
- **UNVERIFIED:** entitlement, price, licensing permission or PIT guarantee
  could not be established. Unknown values are not zero.

A record containing an old fiscal date is not necessarily a historical
information vintage. A current `last_updated` field is not an archive of
earlier values. Two identical downloads today cannot establish what a row
contained before a historical announcement.

## Provider findings and source matrix

The complete matrix is
`/home/runner/work/agentic-quant-lab/agentic-quant-lab/research/results/pead_data_source_matrix.csv`.
It records **all requested dimensions for every provider**, including explicit
unknowns, source URLs, licensing, free/paid boundaries, and actual observations.
The companion audit is
`/home/runner/work/agentic-quant-lab/agentic-quant-lab/research/results/pead_pit_audit.json`.
Both are research evidence, not backtest-ready input data.

| Provider | Most important finding | Recommended role / limitation |
| --- | --- | --- |
| SEC | Original filings, reported accounting facts and guidance text; no analyst expectations. Direct SEC requests blocked here. | Original-document provenance; acceptance is not earliest earnings time. |
| Alpha Vantage | Official implementation now documents **EARNINGS_ESTIMATES**, including revenue/EPS estimates, counts and revisions. Reviewed query is symbol-only; historical vintages unproven. | Do not incorrectly say the endpoint does not exist; do not infer PIT from its name. Forward-looking earnings calendar is not historical event history. |
| Massive / Polygon | Indexed Benzinga Earnings documentation advertises event time/date, EPS/revenue actual/estimate and history from **2010-04-30**. Separate guidance feed starts **2011-09-12**. | Retail timestamp-feed candidate. `last_updated` is not an as-of archive; no data rows retrieved. Stock prices require their own history entitlement. |
| Nasdaq public website | Calendar/earnings display; upcoming dates can be algorithmic. | Spot discovery only; not the separately licensed Zacks historical product or a bulk-use licence. |
| Financial Modeling Prep | Indexed stable earnings/analyst-estimate schemas include actuals, estimates, counts and `lastUpdated`. | No accepted original-vintage or release-session evidence; stable versus legacy schemas must not be mixed. |
| Finnhub | Official calendar schema includes BMO/AMC/during-market category and fiscal year/quarter; estimate models include counts. | Useful session/period schema, but no consensus-effective timestamp in inspected models; estimates explicitly include Finnhub proprietary estimates. |
| EODHD | Official reference distinguishes announcement date, fiscal-period date and nullable session. FAQ says exact estimate-change timestamps are not recorded and two fundamental versions are not retained. | Inexpensive **calendar/price qualification candidate**, not an acceptable historical consensus-revision archive. |
| Tiingo | EOD raw/adjusted prices and actions are relevant documented leads; inactive completeness not observed. | Alternative price backbone, not an earnings-consensus source. Current eligible price not verified. |
| Sharadar | Price/fundamental/event products are distinct from Zacks consensus. Historical prices/inactive securities are relevant leads. | Alternative price/security backbone; accounting/report dates do not prove announcement session. Current full-history contract unverified. |
| Intrinio / Zacks | Official surprise schema explicitly calls EPS consensus **pre-earnings release**, with time/session and count. Ordinary estimate `date` explicitly means **period end**. | Strongest inspected event-consensus schema; still needs original-freeze/correction policy and entitled historical samples. |
| Nasdaq Data Link / Zacks | ZEEH historical consensus, ZET trends, ZES surprises; ZREV/ZAR also surfaced as leads. | Commercial historical-vintage acquisition shortlist. Exact table coverage, licence and price unverified; no inference from Nasdaq's free calendar. |
| IEX / legacy | Official legacy SDK is unmaintained; estimates code describes **latest next-period consensus**. | Not a new 2026 IEX Cloud acquisition route. Only already lawfully held archives merit inspection; IEX Exchange data is a different product. |
| Stooq | Public historical-price download identified, but direct sample failed. | Cross-check only until action methodology, inactive outcomes and rights are known. No earnings or expectations. |
| Kaggle/public uploads | Historical NASDAQ EPS and U.S. price dataset cards found; files and upstream provenance not established. | No accepted public PIT dataset. Upload date/card licence does not establish original collection time or upstream rights. |
| Company IR | Three MSFT quarters and two guidance calls directly read. | Spot verification only, never the bulk historical source. |

### Strongest directly inspected provider evidence

1. **Alpha Vantage:** pinned official
   [earnings/estimates/calendar implementation](https://github.com/alphavantage/alpha_vantage_mcp/blob/18465ac2ecc05f125e5460e4e0909f32dcab92cf/api/src/av_api/tools/fundamental_data.py#L185-L282)
   and [transcript interface](https://github.com/alphavantage/alpha_vantage_mcp/blob/18465ac2ecc05f125e5460e4e0909f32dcab92cf/api/src/av_api/tools/alpha_intelligence.py#L45-L67).
   Transcript history is claimed since 2010Q1; that is not proof of original
   transcript publication time or structured guidance.
2. **Finnhub:** official
   [EPS model](https://github.com/Finnhub-Stock-API/finnhub-go/blob/8071bcd46ca5101adcef7a844c96b81a3eceb76e/model_earnings_estimates_info.go#L17-L33),
   [revenue model](https://github.com/Finnhub-Stock-API/finnhub-go/blob/8071bcd46ca5101adcef7a844c96b81a3eceb76e/model_revenue_estimates_info.go#L17-L33)
   and [calendar model](https://github.com/Finnhub-Stock-API/finnhub-go/blob/8071bcd46ca5101adcef7a844c96b81a3eceb76e/model_earning_release.go#L17-L37).
   A schema field can be nullable/unpopulated historically; no returned rows
   were observed.
3. **EODHD:** official
   [fundamentals FAQ](https://github.com/EodHistoricalData/EODHD-MCP-Server/blob/1b38b8ecd669dc93b04738d2f6f7458539edada6/app/resources/references/general/fundamentals-faq.md#L128-L158)
   and [version-retention statement](https://github.com/EodHistoricalData/EODHD-MCP-Server/blob/1b38b8ecd669dc93b04738d2f6f7458539edada6/app/resources/references/general/fundamentals-faq.md#L208-L210).
   [Calendar queries](https://github.com/EodHistoricalData/EODHD-MCP-Server/blob/1b38b8ecd669dc93b04738d2f6f7458539edada6/app/resources/references/endpoints/upcoming-earnings.md)
   with `symbols` ignore `from`/`to`: such a query cannot certify a requested
   2010 window. Rolling 7/30/60/90-day trend values are not dated revisions.
   [EOD fields](https://github.com/EodHistoricalData/EODHD-MCP-Server/blob/1b38b8ecd669dc93b04738d2f6f7458539edada6/app/resources/references/endpoints/historical-stock-prices.md#L57-L74)
   distinguish raw OHLC, adjusted close and **split-adjusted volume**; reconstruct
   contemporaneous raw volume before raw-dollar liquidity calculations.
4. **Intrinio:** official [EPS estimate schema](https://github.com/intrinio/python-sdk/blob/master/docs/ZacksEPSEstimate.md#L14-L30)
   versus [EPS surprise schema](https://github.com/intrinio/python-sdk/blob/master/docs/ZacksEPSSurprise.md#L19-L30)
   and [sales surprise schema](https://github.com/intrinio/python-sdk/blob/master/docs/ZacksSalesSurprise.md#L19-L30).
   `actual_reported_code` includes BTO/DTM/AMC; EPS actual is Zacks-interpreted
   **non-GAAP**. Timezone, original freeze and correction retention still need
   verification. Sales schema mentions a count in prose without separately
   listing that property. Endpoint prose mentioning guidance is not evidence
   that the inspected models deliver guidance ranges/versions. These SDK
   documents are older than the inquiry; current API samples must resolve
   discrepancies.
5. **IEX:** official [unmaintained SDK notice](https://github.com/iexcloud/iexjs/blob/main/README.md)
   and [latest-estimate semantics](https://github.com/iexcloud/iexjs/blob/main/src/js/stocks/estimates.js#L17-L45).
   The reported 2024-08-31 Cloud shutdown was not verified from its original
   notice; the inspected legacy code is not evidence of a current service.

Missing PIT fields in a reviewed SDK do not prove that a provider has no
separate custom product. Conversely, access to provider code grants no licence
to its data. No provider's general “20+ years” statement certifies populated
earnings timestamps, inactive issuers or consensus vintages for that interval.

## What a qualifying event must preserve

Keep separate: issuer/security identity; accession/document identity; target
fiscal-period start/end and fiscal year/quarter; source publication time and
timezone; SEC acceptance time; vendor observation/effective time; our retrieval
time; correction/version identity; source URL and content hash; units,
currency, GAAP/non-GAAP basis and per-share adjustment basis.

Consensus must identify its target fiscal period, contributing analyst count,
EPS/revenue definitions, snapshot/effective time and availability time. Its
availability must precede the decision; for an earnings-surprise signal the
expectation must also be frozen **before the announcement**, not merely before
a next-day trade. Preserve every later revision separately. A historical
observation date without an intraday cutoff must be lagged conservatively; a
daily snapshot published after earnings is not a pre-announcement consensus.

| Integrity question | Required evidence / rejection rule |
| --- | --- |
| What did the market know? | Original release and previously available disclosures, not today's restated fundamentals. |
| What was the immediately preceding consensus? | Last available pre-release vintage, with coverage/staleness measured; never today's estimate or unexplained precomputed surprise. |
| What was reported? | Original EPS/revenue, period, units and accounting basis matched to the estimate; adjusted EPS cannot be compared to GAAP EPS silently. |
| When was it public? | Verified release timestamp or confirmed BMO/AMC session; a scheduled/estimated calendar date is insufficient. SEC acceptance is a distinct event. |
| When could a strategy decide? | After all used inputs were available plus a declared processing delay; distinguish historical reconstruction from prospective observation. |
| What could it trade? | A subsequent eligible exchange session/price, with holidays, DST, halts, actions, spreads and liquidity accounted for. No retrospectively known opening fill. |

Fail closed on ambiguous fiscal periods, missing release-session classification,
missing inactive-security outcomes, or incompatible adjustment conventions.
Do not silently delete failed events and call the remaining sample
representative: publish failure rates by year, issuer status and event type.

## SEC's precise role

SEC submissions and filing archives can supply accession identities,
filing/acceptance metadata, original 8-K filings and attached releases
(often Item 2.02 / Exhibit 99.1), plus 10-Q/10-K accounting disclosures.
Guidance can also occur under Items 7.01/8.01 or outside an earnings release;
not every Item 2.02 filing contains guidance and not every guidance change
appears in one.

An earnings release can precede its 8-K by days. The general four-business-day
8-K deadline makes **acceptance time an unsafe substitute for first public
earnings time**. A conference-call start time is likewise not the release time.
A delayed, filing-conditioned strategy is possible in principle, but is not
the same test as announcement-gap PEAD.

XBRL was phased in from 2009; coverage/tag consistency is not uniform in 2010.
Companyfacts is a present-day aggregation of facts from multiple filings, not
an automatically PIT-clean feature table. Bind every selected fact to its
accession and that filing's availability; preserve the original release when
the later 10-Q contains more information. Do not use a latest/calendar-frame
view as the vintage selector. Handle custom tags, quarter versus YTD duration,
53-week years, units, amendments and restatements. Derive Q4 from annual minus
YTD only when both operands were available and compatible; otherwise reject.
Do not assume an earnings exhibit is tagged or contains standardized adjusted
EPS.

**SEC does not provide analyst expectations, analyst counts or a consensus
revision archive.** Its free archive can support reported results, textual
guidance evidence and original-document provenance. SEC plus suitable market
prices can support an independently timestamp-verified price-response
baseline, a deliberately delayed filing-response baseline, or comparison to
the company's own previously published guidance. None is analyst-consensus
surprise or analyst revision momentum.

Historical reconstruction is explicitly counterfactual source availability.
It must not overwrite the recorder's prospective invariant:
`decision_eligible_at = fetched_at`, including catch-up
(`/home/runner/work/agentic-quant-lab/agentic-quant-lab/src/agentic_quant_lab/recorder.py:129–145`;
`/home/runner/work/agentic-quant-lab/agentic-quant-lab/migrations/001_evidence.sql:30–38`).
SEC acceptance/publication times do not
backdate something the prospective recorder only fetched today.

## Price and timing contract for a future baseline

Let **E** be the first regular session after a verified release: same session
for BMO; next exchange session for AMC/weekend/holiday. Intraday releases need
intraday pre/post-event prices; exclude them from the first daily-bar baseline.
Unknown sessions are explicit exclusions, not default BMO.

- Pre-announcement close: last regular close strictly before publication.
  An AMC event's close that day is a reference price, **not a legal entry**.
- Opening gap: E's open relative to that close, adjusted consistently for
  splits and ex-distributions. Observing the opening gap does not entitle the
  strategy to that same opening price.
- Simplest daily implementation: observe E's completed close-to-close abnormal
  return against a predeclared broad-market benchmark; make the decision only
  after E closes and execute no earlier than **E+1 open**. A gap feature, if
  retained, is also already known by that decision.
- Liquidity: preceding 20 completed sessions' raw price times raw volume, using
  only data available before the decision. Never use future index membership.
- Measure event-window 1/5/20/60-session returns separately from executable
  entry-to-exit returns. These are session counts, not calendar-day offsets.
  Events near the study cutoff have censored horizons, not invented outcomes.
- Store raw OHLCV, split factors, cash dividends, permanent identity and
  corporate-action dates. Back-adjusted prices are useful for returns, not
  actual dollar fills or historical dollar-liquidity thresholds.
- Follow mergers, ticker changes, suspensions and delistings through the
  holding period; do not drop unpriced terminal observations. A buyout price
  cannot be assumed to be a pre-close executable fill.

Before any performance calculation, acceptance tests must demonstrate:

| Deliberate contamination | Required result |
| --- | --- |
| AMC event entered at that day's close | Reject: close precedes release. |
| Signal using E's closing reaction filled at E close | Reject: signal not known before that fill. |
| Opening-gap signal filled at the open used to compute it | Reject absent a separately justified executable intraday model. |
| Future consensus revision changes a past decision | Past decision unchanged; otherwise reject the dataset/join. |
| Estimate for a different fiscal quarter or accounting basis | Reject, not nearest-date join. |
| Date-only announcement / missing session | Explicit unknown and excluded from gap baseline. |
| Restated actual replaces original release or future action changes eligibility | Historical decision unchanged. |
| Acquired/delisted security lacks exit/action evidence | Unresolved coverage failure, not zero return or sample deletion. |

These are acceptance requirements, **not executed PEAD tests**. No PEAD
implementation or smoke-test results are claimed in this report.

## Historical spot checks

### Directly retrieved issuer facts

The following are **actual readable issuer responses**, not vendor examples.
USD amounts below retain the release's accounting basis and precision.

| Issuer / fiscal period | Period end; announcement date | Reported revenue | Diluted EPS | Timing and acceptance result |
| --- | --- | --- | --- | --- |
| MSFT FY2010 Q2 | 2009-12-31; 2010-01-28 | $19.02bn | $0.74 GAAP | Exact release time/session unverified; not admitted. |
| MSFT FY2023 Q2 | 2022-12-31; 2023-01-24 | $52.747bn | $2.20 GAAP; $2.32 non-GAAP | Exact release time/session unverified; not admitted. |
| MSFT FY2023 Q3 | 2023-03-31; 2023-04-25 | $52.857bn | $2.45 GAAP | Exact release time/session unverified; not admitted. |

Sources: [FY2010 Q2](https://www.microsoft.com/en-us/Investor/earnings/FY-2010-Q2/press-release-webcast),
[FY2023 Q2](https://www.microsoft.com/en-us/Investor/earnings/FY-2023-Q2/press-release-webcast),
[FY2023 Q3](https://www.microsoft.com/en-us/Investor/earnings/FY-2023-Q3/press-release-webcast).

The 2010 release also gives $17.31bn revenue / $0.60 EPS **excluding Windows 7
deferred-revenue recognition**. Comparing $0.74 with an estimate on the
alternative basis would manufacture a surprise. Its FY2010 operating-expense
guidance is $26.2–26.5bn, not revenue guidance.

Directly retrieved [FY2023 Q2 call text](https://www.microsoft.com/en-us/investor/events/fy-2023/earnings-fy-2023-q2)
gives next-quarter segment revenue ranges of $16.9–17.2bn, $21.7–22.0bn and
$11.9–12.3bn. The [Q3 call text](https://www.microsoft.com/en-us/investor/events/fy-2023/earnings-fy-2023-q3)
gives next-quarter ranges of $17.9–18.2bn, $23.6–23.9bn and $13.35–13.75bn.
These refer to **different target quarters**: their difference is not a
same-period guidance revision. The calls were scheduled for 17:30 Eastern;
that is not a verified earnings-release timestamp or transcript publication
timestamp. Do not backdate call guidance to the earlier release.

The FY2023 Q2 page was fetched twice with curl at **23:21:29Z and 23:21:30Z on
2026-09-15**: HTTP 200, 626,094 bytes each, identical SHA-256
`2b8647f009e9eb2dfd30ce7c501cdc8903a853adde5c01025ae8638ab2e92542`.
An independent readable-body repeat also agreed on selected facts. This
demonstrates same-session stability of an issuer page only—not original 2023
bytes, a historical consensus vintage, or protection against later revisions.
Raw HTML remains outside the repository.

### Other requested cases: investigated, not certified

| Case / purpose | Primary source located | Observation and unresolved requirements |
| --- | --- | --- |
| AAPL FY2019 Q1 warning and results | [January 2 letter](https://www.apple.com/newsroom/2019/01/letter-from-tim-cook-to-apple-investors/); [January 29 results](https://www.apple.com/newsroom/2019/01/apple-reports-first-quarter-results/) | Direct requests failed DNS. Indexed warning says revenue outlook about $84bn versus prior issuer guidance $89–93bn; not analyst consensus. Warning and earnings are separate events. |
| AAPL FY2023 Q1, reported miss stress case | [February 2, 2023 results](https://www.apple.com/newsroom/2023/02/apple-reports-first-quarter-results/) | Direct request failed DNS. Indexed results indicate $117.2bn revenue / $1.88 EPS. No accepted pre-release consensus, release clock time, price or quantified miss. |
| META/then-FB FY2021 Q4, major-miss stress case | [February 2, 2022 results](https://investor.atmeta.com/investor-news/press-release-details/2022/Meta-Reports-Fourth-Quarter-and-Full-Year-2021-Results/default.aspx) | Direct request failed DNS. Indexed results indicate $33.671bn revenue / $3.67 GAAP EPS and next-quarter revenue guidance $27–29bn. Fiscal period is **2021 Q4**, not 2022 Q1; historical ticker was FB. No surprise magnitude certified. |
| ATVI FY2023 Q2, subsequently acquired | [Original SEC exhibit](https://www.sec.gov/Archives/edgar/data/718877/000162828023025102/atvi63023ex991prtables.htm) | Direct request failed DNS. Indexed results distinguish $2.21bn GAAP revenue from $2.46bn bookings and $0.74 GAAP / $0.91 non-GAAP EPS. A current earnings page's $1.08 actual / $0.88 estimate was rejected: vintage and EPS reconciliation unresolved. |

ATVI's acquisition completion on **2023-10-13** is independently stated in the
directly retrieved [Microsoft FY2024 Q2 release](https://www.microsoft.com/en-us/Investor/earnings/FY-2024-Q2/press-release-webcast).
That verifies eventual acquisition, not its historical executable exit prices.

Search-linked wire times suggested AMC for the Apple/Meta events and BMO for
ATVI. Those source bodies were inaccessible, so **none was promoted to a
verified timestamp**. Conditional first regular sessions would be January 3
and 30, 2019; February 3, 2022; February 3, 2023; and July 19, 2023 respectively,
if those release classifications are confirmed. MSFT's candidate sessions
would be January 29, 2010; January 25 and April 26, 2023 **if AMC is confirmed**.
These are calendar candidates, not exchange-calendar/halts validation, and the
opening prices were not obtained. They cannot be used as executable observations.

Contemporary preview searches did not yield a directly verified,
before-announcement consensus for any case. Post-event articles, current
earnings databases and search-generated figures were not substituted.
**No historical consensus API row was obtained; the consensus revision
re-query test is NOT RUN.** All pre-close/gap/1d/5d/20d/60d price observations
remain missing, not zero. No event passed the complete join.

### Access limitations and reproducibility

Direct submissions requests for AAPL, MSFT, META and ATVI failed DNS at
2026-09-15T23:04:41Z. Massive's AAPL historical earnings request and Nasdaq's
AAPL surprise request failed the same way. Earlier Alpha Vantage IBM public
demo and Nasdaq calendar requests also failed DNS. No HTTP 401/403, free-tier
limit, premium-entitlement response or returned consensus is inferred from
those failures.

The JSON audit records exact parent-request timestamps, URLs, outcomes,
repeat hashes and accepted versus discovery-only facts. Research-agent
readable-body observations without exact request timestamps are dated only;
no synthetic timestamp or hash was supplied. Documentation claims are
separate from these live results. Search results occasionally equated
`last_updated` with PIT or supplied sample/future earnings values; neither
was accepted.

## Cost answer: free, retail, or institutional?

### A. Free data

**Not enough was verified for a credible broad 2010–2026 backtest.** SEC offers
free reported facts and original-document evidence; issuer pages can corroborate
individual events. Free price downloads or a small survivor cohort do not
automatically solve historical identities, corporate actions, terminal outcomes,
release timing or licensing. A manually verified event example is feasible,
but is not a research-grade market-wide test. This is not a proof that every
possible free archive is unusable.

Free prospective snapshots could eventually build a new history if the chosen
API's licence permits retention. They cannot recreate unrecorded 2010–2026
consensus revisions. Hashing a download today freezes today's vintage, not
the historical one.

### B. Low-cost retail data

The cheapest **endpoint-supported qualification candidate substantiated here**
is **EODHD Calendar Feed + EOD All World**, advertised in provider-owned
reference files at **$19.99 + $19.99 = $39.98/month** for personal use.
This is **not a qualified PIT dataset, a checkout quote, or a claim of global
cheapest price**. The source explicitly allows prices to vary.

| Candidate | Price evidence / entitlement | What it would solve; what it would not |
| --- | --- | --- |
| EODHD Calendar Feed | Provider-source published **$19.99/month**; earnings **and trends** endpoints listed | Candidate event/fiscal dates, nullable session, EPS fields. Does not supply immutable consensus revisions, guaranteed original timing or revenue actuals. |
| EODHD EOD All World | Provider-source published **$19.99/month**, separate from calendar | Candidate OHLC, adjusted close, splits/dividends and volume. Inactive identities/terminal outcomes and raw-volume reconstruction still need audit. |
| EODHD Fundamentals + EOD | Published **$59.99 + $19.99 = $79.98/month**; fundamentals excludes EOD | Adds accounting statements/revenue; **does not fix restatement/vintage loss**. Unnecessary for the first price-only signal. |
| EODHD All-In-One | Published **$99.99/month** | Broader endpoint bundle, not a PIT guarantee. |
| Massive Benzinga Earnings | **Indexed-only $99/month**; event history from April 30, 2010 | Alternative event-session source if cheaper calendar fails. No certified original consensus freeze; no complete January–April 2010 history. |
| Massive Corporate Guidance | **Indexed-only separate $99/month**; history from September 12, 2011 | Structured ranges candidate, not proof of textual/original-version history; does not cover 2010. |
| Massive stock history | **Indexed-only** Starter $29/5 years; Developer $79/10 years; Advanced $199/20+ years | A 10-year entitlement in 2026 cannot cover 2010. Event add-on is separate; no full-stack acceptance was performed. |
| Finnhub dedicated estimates | **Indexed-only** Estimate-1 $75/month/market, 10 years; Estimate-2 $200, 20+ years | History-depth lead only. Billing commitment, current checkout and dated consensus archive not verified. |
| FMP plans | **Indexed-only** Starter $22/month equivalent billed annually; Premium $59; Ultimate $149 | Generic plan prices do not identify the minimum tier for the exact historical fields or establish PIT. |
| Alpha Vantage; Tiingo; Sharadar | Exact current eligible paid price **unverified** | Do not quote remembered prices or equate generic market-data plans with consensus history. |

Price sources: EODHD pinned
[Calendar Feed](https://github.com/EodHistoricalData/EODHD-MCP-Server/blob/1b38b8ecd669dc93b04738d2f6f7458539edada6/app/resources/references/subscriptions/calendar-feed.md),
[EOD](https://github.com/EodHistoricalData/EODHD-MCP-Server/blob/1b38b8ecd669dc93b04738d2f6f7458539edada6/app/resources/references/subscriptions/eod-historical-data-all-world.md),
[Fundamentals](https://github.com/EodHistoricalData/EODHD-MCP-Server/blob/1b38b8ecd669dc93b04738d2f6f7458539edada6/app/resources/references/subscriptions/fundamentals-data-feed.md),
[All-In-One](https://github.com/EodHistoricalData/EODHD-MCP-Server/blob/1b38b8ecd669dc93b04738d2f6f7458539edada6/app/resources/references/subscriptions/all-in-one.md)
and [plan/licensing distinctions](https://github.com/EodHistoricalData/EODHD-MCP-Server/blob/1b38b8ecd669dc93b04738d2f6f7458539edada6/app/resources/references/general/pricing-and-plans.md).
Indexed leads: [Massive earnings](https://massive.com/docs/rest/partners/benzinga/earnings),
[guidance](https://massive.com/docs/rest/partners/benzinga/corporate-guidance),
[stocks](https://massive.com/pricing),
[Finnhub estimates](https://finnhub.io/pricing-stock-estimates),
[FMP](https://site.financialmodelingprep.com/developer/docs/pricing).

No paid endpoint was exercised; no checkout was completed. No minimum paid
tier **with demonstrated historical PIT behavior** was verified. For business
internal research, do not assume personal-plan prices apply. Confirm
archival retention, derived outputs, publication and redistribution separately.
Only source references and selected factual findings—not raw vendor datasets—
are committed here.

### C. Institutional-grade/commercial consensus

Historical analyst consensus is **a commercial-data acquisition problem in this
investigation**, rather than something SEC can reconstruct. It is **not proven
to be institution-only**: commercial Zacks/Intrinio/Nasdaq products are relevant
leads, and login-gated pricing does not establish either institutional exclusivity
or unaffordability. No cheapest credible full-PIT consensus offering or current
price can honestly be named from the available evidence.

Prioritize [Nasdaq ZEEH](https://data.nasdaq.com/databases/ZEEH/documentation?anchor=column-definitions)
and [Zacks directly](https://zacksdata.com/datasets/consensus-data/) for historical
consensus snapshots; independently assess
[ZREV](https://data.nasdaq.com/databases/ZREV/documentation) for dated estimate
revisions and Intrinio's Zacks surprise product for frozen pre-release
consensus/actual pairs. **ZAR recommendations are not EPS/revenue revisions.**
The indexed ZEEH EPS-history-since-1979 claim is unverified; do not extend it to
revenue history, intraday availability or all delivery partners. A daily archive
can work with conservative lagging only after its publication cutoff and
correction semantics are known.

If an institution already has an appropriate historical-consensus licence,
incremental cost might differ, but no such entitlement was available or assumed.
Paying more does not waive any integrity gate.

## Variant decisions and the exact unblocking acquisition

| Variant | Feasibility finding |
| --- | --- |
| A. Pure price-based earnings drift | Does **not** require consensus. Credible if historical event sessions, original-source checks and an active/inactive price/action join qualify. Cheapest candidate stack is retail-sized, but not yet demonstrated. |
| B. Fundamental surprise | Needs original same-basis actual versus **pre-release frozen consensus**. Current estimates and unexplained historical surprise percentages are rejected. |
| C. Analyst revision momentum | Needs multiple dated observations for the same target period, not today's rolling change statistics or analyst recommendations. No accepted archive obtained. |
| D. Guidance revision/text | Original SEC releases/exhibits can provide free text and ranges; compare the **same target period** with its previously available guidance, including withdrawal/no-guidance. Transcript publication lags, incomplete capture and corporate-action/price joins still need qualification. No LLM strategy is justified yet. |
| E. Combined structured PEAD | Price confirmation and liquidity are feasible components, but adding them cannot repair a contaminated surprise input. Inherits the unmet B/C gates. |

**Before any baseline implementation/backtest, acquire and accept this bounded
qualification bundle, without an automatic purchase:**

1. Restore permitted public SEC/archive access and obtain provider-authorized
   historical event samples for AAPL, MSFT, FB/META and ATVI, plus a sample
   selected without knowing its subsequent returns across early, middle and
   recent years. Include BMO, AMC, intraday, unknown-session and inactive cases.
   Require actual—not projected—release session/time, timezone, fiscal-period
   identifiers and original-release provenance. If EODHD cannot establish
   historical actual sessions, evaluate Massive's earnings sample or a
   publisher-licensed timestamp archive; do not infer them from prices.
2. Obtain matching 2010-to-cutoff OHLCV/action/security-identity samples from the
   candidate EOD package, or a full-history Tiingo/Sharadar entitlement if its
   inactive/action coverage is better. Use the existing stock audit's
   acquisition requirements instead of reopening its momentum research.
   Include acquisition/delisting outcomes through each requested horizon.
   Require an exchange calendar, missingness report and permission to retain
   original responses. No present-day constituents or unpriced terminal exits.
3. Require paired original/corrected examples, documented timestamp semantics
   and unchanged historical decisions under the contamination tests above.
   Downloading twice today only checks short-interval stability; reconstruct
   historical revisions from retained source vintages or a documented provider
   archive. Audit missingness across years/issuer status before generalizing.
4. Only for surprise/revision variants, obtain an explicitly licensed ZEEH,
   Zacks or Intrinio historical extract containing **multiple pre-event
   availability dates for the same fiscal period**, analyst counts and
   original/corrected versions, plus EPS/revenue accounting-basis mappings.
   Verify the exact archive SKU, current price, retention rights and inactive
   coverage. If the provider cannot deliver those fields, remain blocked.
5. For guidance, pair original SEC documents for the **same forecast period**
   and retain metric/range, issue/raise/lower/withdraw status and earliest
   defensible availability. A delayed SEC-filing overlay must be labeled as
   such, not passed off as a trade at the earlier press-release time.

If steps 1–3 pass, the first experiment should be **price-only, long-only and
daily-bar**: a predeclared positive event-session abnormal-return signal,
trailing liquidity filter, decision after E close, entry at E+1 open and a
single predeclared multiweek holding period (for example 20 sessions), with
costs and corporate actions. Report continuous signal/return diagnostics before
any tuning; no surprise proxy, LLM or parameter search. This is the simplest
conditional next baseline, not authorization to build/run it now.

The reason to defer today is **no qualified event/price join**, not the absence
of analyst consensus alone. Access failures also prevent certification of the
otherwise plausible low-cost route. This report resolves the acquisition
decision and records those limits; it does not pretend the inaccessible
historical observations were verified.

## Final verdicts

Here, “LOW-COST DATA REQUIRED” identifies a plausible retail acquisition route,
**not** a passed dataset or guaranteed full coverage. “BLOCKED” means the
required historical PIT evidence is absent; it does not mean commercial data
cannot solve it.

Price-based PEAD: **LOW-COST DATA REQUIRED**

Consensus-surprise PEAD: **BLOCKED**

Revision momentum: **BLOCKED**

Guidance-text PEAD: **LOW-COST DATA REQUIRED**

Overall recommendation: **DEFER PEAD**

Unblock the price-only baseline with the authorized historical event-session
and inactive-inclusive price/action qualification bundle in steps 1–3.
Acquire dated, retained consensus vintages separately before enabling surprise
or revision research. Do not purchase anything or declare production readiness
on this report alone.
