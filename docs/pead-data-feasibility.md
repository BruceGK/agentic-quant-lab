# PEAD data feasibility

Research date: **2026-09-15 UTC**. This is a data-acquisition decision, not an
alpha test or a production-readiness assessment.

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
(`src/agentic_quant_lab/recorder.py:129–145`;
`migrations/001_evidence.sql:30–38`). SEC acceptance/publication times do not
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
