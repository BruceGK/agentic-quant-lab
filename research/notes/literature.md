# Evidence review before the tournament

Reviewed 2026-09-15. Original publisher/author metadata and RePEc abstracts were
cross-checked where publisher full text was unavailable. These are literature
summaries, not reproduced papers or claims that this repository replicated them.
Academic long-short, leveraged futures, large institutional capacity and an
unlevered personal long equity portfolio are different objects.

## A. Time-series trend / absolute momentum

**Rationale:** underreaction and gradual information diffusion; systematic exit
from persistently falling markets can lower loss exposure. Alternative explanation:
dynamic beta plus reduced exposure, not an unconditional excess-return anomaly.

- Moskowitz, Ooi and Pedersen (2012), *Time series momentum*, JFE 104, 228-250,
  [DOI/abstract](https://ideas.repec.org/a/eee/jfinec/v104y2012i2p228-250.html).
  Evidence spans 58 liquid futures and persistence over 1-12 months. This is
  cross-asset futures, typically volatility-scaled, with shorts: it does **not**
  establish that SPY/cash will beat SPY.
- Hurst, Ooi and Pedersen (2017), *A Century of Evidence on Trend-Following Investing*,
  [author page](https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing).
  Extends simulated history to 1880. Supports examining many crises/markets, but
  constructed early data, execution assumptions and author-manager affiliation
  limit how directly simulated long histories transfer to retail ETFs.
- Faber (2007), *A Quantitative Approach to Tactical Asset Allocation*,
  [SSRN 962461](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461).
  Well-known 10-month SMA practitioner baseline, not a reason to tune exactly 10.
  Full text retrieval was restricted here; treat it as a rule specification and
  bibliographic reference, not independently verified numerical performance.

**Failure regimes:** fast V-shaped rebounds, sideways whipsaw, sudden overnight
crashes before the next rebalance; positive cash yields make timing look better
than zero-yield cash. No guarantee of avoiding the next crash. Benefits concentrated
in rare crises can still matter as insurance, but cannot be sold as stable alpha.
Monthly ETF turnover/liquidity and fractional sizing are attractive for small capital.
No leverage, shorts or exotic order types are needed. Volatility caps may be mostly
de-risking; compare to equal-beta static exposure before promoting them.

**Agent fit:** research change detection, diagnosing whipsaw/regime failure and
proposing bounded robustness tests. Not calculation of moving averages or changing
risk limits from free-form commentary.

## B. Cross-sectional equity momentum: long leg only

- Jegadeesh and Titman (1993), *Returns to Buying Winners and Selling Losers*,
  [original abstract](https://ideas.repec.org/a/bla/jfinan/v48y1993i1p65-91.html).
  Winner-minus-loser returns over 3-12-month holding periods; some subsequent
  reversal. This is not proof that a 20-stock long book beats an ETF after costs.
- Jegadeesh and Titman (2001), *Profitability of Momentum Strategies*,
  [replication](https://ideas.repec.org/a/bla/jfinan/v56y2001i2p699-720.html).
  Persistence in the 1990s is useful post-original-sample evidence, not proof
  of persistence after publication to 2026.
- Daniel and Moskowitz (2016; NBER working paper 2014), *Momentum Crashes*,
  [NBER abstract](https://ideas.repec.org/p/nbr/nberwo/20439.html).
  Large losses cluster after market declines/high volatility during rebounds.
  The short-loser leg's option-like exposure matters; do not transplant its
  dramatic crash magnitudes to a long-only winner book.
- Novy-Marx and Velikov (2016), *A Taxonomy of Anomalies and Their Trading Costs*,
  [RFS abstract](https://ideas.repec.org/a/oup/rfinst/v29y2016i1p104-147..html).
  Buy/hold buffers are effective; high turnover can exhaust paper profits.
  This motivates one fixed rank buffer and explicit turnover costs, not an
  assumption that zero commissions mean zero friction.
- French [momentum construction](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html):
  monthly size/prior-2-12 intersections with NYSE breakpoints. We use large high
  prior-return portfolios, not the published long-short MOM factor as an investment.

**Rationale:** underreaction, herding/slow diffusion; **weaknesses:** rebound crashes,
sector crowding, changing beta and large turnover. Capital capacity is less of a
concern for a small account than bid/ask, taxes, share granularity and behavioral
discipline. Bigger portfolio breadth trades concentration for weaker top ranks;
biweekly turnover needs a real reason. A fixed current/surviving list cannot
establish stock alpha, even with correct lagged signals.

**Agent fit:** identify concentration/crowding, research signal decay, audit corporate
actions/universe changes and propose interpretable tests. Ranking math stays deterministic.

## C. Momentum plus quality

- Novy-Marx (2013; NBER 2010), *The Other Side of Value: The Gross Profitability
  Premium*, [abstract](https://ideas.repec.org/p/nbr/nberwo/15940.html).
  Gross profitability relates to average returns and improves value sorts in
  large/liquid stocks in the study. It does not prove an arbitrary quality filter
  improves every momentum portfolio.
- Asness, Frazzini and Pedersen (2019), *Quality minus junk*,
  [abstract/DOI](https://ideas.repec.org/a/spr/reaccs/v24y2019i1d10.1007_s11142-018-9470-2.html).
  Profitability/growth/safety quality-minus-junk evidence in the US and 24 other
  countries. A long-short composite is not the same as one profitable-company
  filter or a personal long-only momentum-quality implementation.

Economic hypothesis: avoid fragile, levered winners and improve tails. Counter:
quality is expensive and may remove precisely the recovering stocks driving returns,
reduce breadth, or simply tilt to large defensive sectors. A cash-flow/leverage
filter and a composite score must be tested separately against pure momentum.
No evidence-based reason to retain complexity without material, stable improvement.
French quality and momentum sleeve blending is only **allocation complementarity**,
not evidence for stock-level interaction. Without joined PIT security features,
do not create a fake filter using current fundamentals.

**Agent fit:** flag accounting comparability, restatements and hypothesis failures;
later examine bounded earnings-quality text with timestamped inputs. Do not
generate an unreviewable weighted mega-factor.

## D. Quality/value diversifier

The two quality sources above support a profitability/value relationship, not a
universal guarantee. French July-to-June fundamental portfolios use preceding-year
accounting values: [operating-profitability construction](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/six_portfolios_me_op.html).
We can compare long robust-profitability, long value, and joint value/profitability
return baskets; cannot recover original holdings/trades/filing-time vintage from them.

Value can underperform for a decade and concentrates in structurally challenged
sectors; cheap distressed firms are not automatically safer. Quality can become a
crowded duration/valuation bet. Annual/slow rebalances may improve tax/cost feasibility,
but a small account should compare an ETF implementation with its all-in fee and tracking.
Treat this as a possible diversifier, not the assumed primary strategy.
Agents can investigate accounting changes/valuation pitfalls and conflicting literature.

## E. Earnings momentum / PEAD

Bernard and Thomas (1989), *Post-Earnings-Announcement Drift: Delayed Price Response
or Risk Premium?*, [bibliographic DOI](https://doi.org/10.2307/2491062), motivates
underreaction to earnings information; it is not a liquid-stock post-cost result.

Chordia, Goyal, Sadka, Sadka and Shivakumar (2009), *Liquidity and the
Post-Earnings-Announcement Drift*,
[verified FAJ abstract](https://ideas.repec.org/a/taf/ufajxx/v65y2009i4p18-32.html).
Their sample's long-short drift is concentrated in illiquid stocks; reported
transaction costs consume 70-100% of paper profits. This challenges the proposed
liquid-only retail strategy. It does not imply all modern PEAD variants are dead.

Clean tests require announcement times, historically available earnings/revenue
surprises and forecast vintages, revisions/guidance definitions, and executable
post-announcement prices. Seasonal earnings change is not analyst surprise; filing
acceptance is not necessarily the first earnings press release. Current estimate
snapshots or retrospectively restated actuals are invalid substitutes.
Free comprehensive point-in-time consensus was not found. Refuse a PEAD backtest
rather than invent it. Post-event price confirmation alone would be momentum,
not evidence for incremental earnings information. Text/LLM features come only
after a defensible numeric baseline and correctly timestamped costs.

**Agent fit is potentially highest here**, for research synthesis and bounded
guidance interpretation, but the data/timing burden is also highest. No credentials
or agent order execution is necessary to explore that hypothesis later.

## Cross-family falsification

- Hou, Xue and Zhang (2020), *Replicating Anomalies*,
  [abstract](https://ideas.repec.org/a/oup/rfinst/v33y2020i5p2019-2133..html):
  mitigating microcaps/value-weighting eliminates many published anomalies and
  materially shrinks surviving effects. Their thresholds are not our significance
  tests; they motivate no-microcap, long-leg and cost discipline.
- McLean and Pontiff (2016), *Does Academic Research Destroy Stock Return
  Predictability?*, [DOI](https://doi.org/10.1111/jofi.12365):
  a relevant publication-decay warning. Full text was not retrieved here; no
  precise decay percentage is used as independently verified evidence.
- Do not turn a retrospective parameter grid into a "winner" p-value. Report
  neighborhood dispersion, all tested variants, withheld-like periods and paired
  bootstrap intervals, with explicit selection/revision limitations.

## Robinhood compatibility (public documents only)

[Official Agentic overview](https://robinhood.com/us/en/support/articles/agentic-trading-overview/)
confirms a dedicated account and Trading MCP, and warns of agent errors and loss.
[Trading with your agent](https://robinhood.com/us/en/support/articles/trading-with-your-agent/)
is the operational reference to verify order types and restrictions.
[Fractional shares](https://robinhood.com/us/en/support/articles/fractional-shares/)
notes Not Held order discretion. Availability, fractional support and settlement
in this specific product must not be inferred solely from the main retail app.
Public-doc review is not an account entitlement/order-routing test.

All proposed equities/ETFs are hypothetical long-only allocations, unlevered, with
cash/reduced exposure when defensive. Small-capacity suitability is not personal
investment advice; a $1k/$10k/$50k sizing sensitivity should expose fixed-share
rounding and taxable turnover. We do not connect to the MCP, read account data,
assume crypto permissions, or send any order. Future deterministic constraints and
human approval must sit outside an agent's discretionary research suggestions.
