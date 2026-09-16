# ETF cross-sectional / relative momentum

**Classification: EXPLORATORY. No sector performance has been calculated.**

This is an independent research family, not a retuning of SPY Absolute12 or
SMA10. The isolated assigned branch incorporates
`research/long-only-strategy-tournament` at
`3e8273472ad24508463916c11b44bd4b754abe6d`. Published history and the earlier trend
experiment are unchanged.

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

The [frozen protocol](../research/etf_relative_momentum/protocol.json) defines
the complete experiment before sector results. Its commit precedes any permissible
sector performance calculation; an unsuccessful source audit does not waive that
requirement. Source retrieval is currently blocked, not evidence of a losing or
winning strategy.

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

## Research boundaries

Phase 0 remains frozen: `scheduled_recording_enabled = false` and
`live_execution.enabled = false` (the repository's live-execution flag).
There are no recorder, policy, dependency, infrastructure, scheduler or broker
changes. No trades, stock-level data acquisition, PEAD, or optional cross-asset
experiment are included.
