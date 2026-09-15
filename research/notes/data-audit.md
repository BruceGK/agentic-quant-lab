# Data audit and deviations established before performance calculation

See [data manifest](../results/data_manifest.json) for 79 hashed source downloads
and [machine-readable audit](../results/data_audit.json) for coverage/quality checks.
Raw bytes are ignored local cache, not redistributed. Re-running acquisition with
the manifest refuses changed hashes instead of silently replacing the research vintage.

| Dataset | Verified coverage | Permitted use |
| --- | --- | --- |
| French market/RF | July 1926-July 2026 monthly; daily RF available | Long-horizon total-return market **proxy**, not SPY |
| French size/prior-return | January 1927-July 2026 | Value-weighted long portfolios; no measured constituent turnover |
| French size/profitability | July 1963-July 2026 | Annual fundamental-sort long basket |
| French size/value | July 1926-July 2026 | Annual value-sort long basket |
| French value/profitability | July 1963-July 2026 | Joint fundamental baskets; not a momentum-quality stock filter |
| QSTrader SPY adjusted snapshot | January 3, 2000-January 4, 2016 | Actual ETF timing to last complete year, 2015 |
| QSTrader AGG adjusted snapshot | November 1, 2006-October 13, 2016 | SPY/AGG tests to 2015; this snapshot does NOT start at fund inception |
| QSTK 70-stock adjusted snapshot | February 1, 2000-September 12, 2012 | Survivor-biased implementation sensitivity only |

### Material source issues (not fixed with interpolation)

1. The French momentum **equal-weight** section has six column names but seven/eight
   values on some rows in this downloaded vintage. The parser raised, investigation
   confirmed malformed raw rows, and that entire section is **excluded**. The
   separately selected six-column **value-weight** table passes schema/date/finite
   checks. Requesting the malformed section still fails; no truncation or relabeling.
2. The convenience stock panel has eight dates with gaps, all before 2003:
   2000-02-23, 2000-06-02, 2000-06-09, 2000-07-20, 2000-08-28, 2000-08-29,
   2002-02-01 and 2002-11-22. They are real SPY sessions, not holidays.
   Use the complete 2003-2012-August window and a 252-session warm-up; evaluate
   only from 2004 onward. **Do not drop a held security's return or fill it with zero.**
   This data-quality truncation was made before any performance result, not selected
   for favorable returns. It does not solve survivor selection or missing delistings.
3. ETF samples do not cover 2020 or later. The French market/portfolio cross-checks
   do; they cannot certify ETF routing, tracking, slippage or modern stock-level breadth.
4. Historical adjusted closes encode corporate actions retrospectively. Constant
   adjustment factors cancel in return/moving-average ratios, but source corrections,
   timing, distributions, delisting proceeds and vendor mistakes remain unaudited.
   Price x volume liquidity is an approximate historical dollar-volume screen;
   source volume adjustment conventions are not independently reconstructed.
5. French US returns switched from CRSP FIZ to CIZ in the January 2025 release;
   [official library notes](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
   describe daily compounding/ex-date dividend reinvestment versus legacy month-end
   reinvestment and warn that history can be revised. Archive hash is not a PIT vintage.
6. French OP uses prior-year annual accounts to form portfolios in June. This is
   a lag convention, not an audit of original statement publication timestamps or
   restatements. Constituents, exact stock counts and internal transactions are
   unavailable here: annual drag scenarios cannot be called measured slippage.

### Sources deliberately not used

- Live Yahoo chart access returned 429; Stooq required a browser verification
  challenge. No repeated scraping loop or challenge bypass.
- EOD demo access was 403; Alpha Vantage's demo did not provide requested SPY
  data; Nasdaq's historical endpoint failed. No API subscriptions/credentials created.
- Papers With Backtest's recent stock/ETF datasets are **subscription-gated** by
  their own cards. No paid download or alternate route around that gate.
- Chris Conlan's educational stock panel is explicitly **simulated**. Its attractive
  sample size is not reason to treat it as real market evidence.
- A generic public ETF forecasting dataset lacked sufficient adjustment/provenance
  metadata. It was not substituted for clean tradable history.

### Implications for ranking

Every reported backtest is **EXPLORATORY for an implementable personal account**.
The academic portfolio layer is methodologically stronger for broad long-leg
cross-checking than a survivor-only list, but not a security-level replication.
No RESEARCH-GRADE stock alpha, no PEAD alpha, and no quality-filter improvement
may be inferred from these substitutes. A modern clean ETF daily dataset is the
first missing input for a forward paper-only implementation, not an excuse to
purchase data or improve the frozen SEC infrastructure.
