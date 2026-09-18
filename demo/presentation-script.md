# Agentic Quant Lab — presentation script

**11 slides · 6 minutes 40 seconds · includes a 90-second terminal demo.**
Read **Script** and **Transition** aloud; everything else is a presenter cue.
Slide 7 is a scroll-through of completed output, not an interactive CLI.
“Live demo” means a local **synthetic dry run**, never live trading.

**Exact opening:** “Most AI trading demos start by asking an LLM what stock to buy; I wanted to build the opposite.”

**Exact closing:** “It's an AI that knows when not to trade.”

| Slide | Seconds | Presentation clock |
| --- | ---: | --- |
| 1 | 25 | 0:00–0:25 |
| 2 | 30 | 0:25–0:55 |
| 3 | 35 | 0:55–1:30 |
| 4 | 35 | 1:30–2:05 |
| 5 | 40 | 2:05–2:45 |
| 6 | 45 | 2:45–3:30 |
| 7 | 90 | 3:30–5:00 |
| 8 | 30 | 5:00–5:30 |
| 9 | 30 | 5:30–6:00 |
| 10 | 25 | 6:00–6:25 |
| 11 | 15 | 6:25–6:40 |

## Slide 1 — Agentic Quant Lab

**Timing:** 25 seconds · 0:00–0:25

### Goal
Introduce agents as researchers, not stock-picking oracles.

### Script
Most AI trading demos start by asking an LLM what stock to buy; I wanted to build the opposite.

Agentic Quant Lab asks which ideas deserve to survive. Agents behave like
researchers: they propose hypotheses. Evidence and deterministic controls decide
what happens next.

### Transition
Because generating a trading idea is the easy part.

### Presenter cues — not spoken
Pause after “the opposite.” Point to Research → Evidence → Risk → Execution.
Autonomous research is the destination; today's agent is a scripted stand-in.

## Slide 2 — AI can generate trades. Can we trust them?

**Timing:** 30 seconds · 0:25–0:55

### Goal
Make rejecting bad ideas the product's central problem.

### Script
A model can produce a convincing reason to buy almost anything.

But did the backtest use tomorrow's information? Did costs erase the edge?
Did we quietly leave out companies that disappeared?

A fluent explanation doesn't answer those questions. Neither does a beautiful
equity curve. The hard problem isn't generating strategies. It's rejecting bad ones.

### Transition
That requires a different architecture.

### Presenter cues — not spoken
Contrast the red shortcut with the evidence pipeline. “Trade” is future-only;
the implemented path ends at a dry run.

## Slide 3 — An autonomous research loop

**Timing:** 35 seconds · 0:55–1:30

### Goal
Separate agent reasoning from numerical and execution authority.

### Script
There are two lanes here. Agents research and reason. Deterministic code owns
the data checks, calculations, backtests, portfolio, and risk limits.

Every hypothesis becomes an experiment. Results face falsification, then a
tournament. Only a surviving proposal reaches the RiskGate. Evidence travels
alongside the process.

Today's demo agent is scripted, not an LLM. Robinhood is future work.

Agents propose. Evidence decides. RiskGate authorizes.

### Transition
And the first test is whether the idea can prove itself wrong.

### Presenter cues — not spoken
Trace both lanes and the evidence sidecar. The demo receipt is separate from
the unchanged Phase 0 production ledger.

## Slide 4 — The agent has to prove itself wrong

**Timing:** 35 seconds · 1:30–2:05

### Goal
Explain three scientific controls without implying they establish alpha.

### Script
First, a null control: a signal with no edge should not magically make money.
The broader research uses random controls; this demo uses flat, no-edge fixtures.

Second, a planted signal: can the machinery recover a pattern we deliberately
put into synthetic data?

Third, a leakage trap: future information must be rejected.

These checks validate mechanics, not market alpha. Costs and frozen
specifications matter too.

### Transition
The useful result is often “no,” and our real research shows that.

### Presenter cues — not spoken
Do not claim the demo performs real-market out-of-sample or regime validation.
It also checks deterministic reproduction.

## Slide 5 — The system already says “no”

**Timing:** 40 seconds · 2:05–2:45

### Goal
Distinguish adverse research findings from data-gated, unrun experiments.

### Script
These are real research statuses, not demo scores.

ETF Trend remains research more, close to rejection. Stock momentum is blocked
by historical-universe and delisting evidence. Adding quality also needs
point-in-time fundamentals.

Earnings drift is deferred. A price-based route may be feasible, but historical
consensus and revision vintages remain blocked. We haven't tested PEAD.

Sector-relative momentum has a frozen protocol, but data acquisition stopped
at a network and DNS gate. No performance experiment ran.

Missing evidence is not an economic rejection.

### Transition
Trend did run, and it's the clearest example of why this discipline matters.

### Presenter cues — not spoken
The lab preserves negative evidence. None of these candidates is promoted to
paper, shadow, or live trading. Sector-relative momentum completed **0/18**
scenarios; unavailable metrics are not zero returns.
Source: [canonical research status](../docs/research-status.md).

## Slide 6 — Trend looked promising — until we tested it properly

**Timing:** 45 seconds · 2:45–3:30

### Goal
Show the real return/drawdown trade-off without rescuing the failed rules.

### Script
The earlier exploratory work made trend look promising. Then we froze the rules
and compared them with simply holding less equity.

At twenty basis points one-way, Absolute Twelve returned about eleven-point-three
percent a year, just like static seventy-thirty. But it still suffered the full
thirty-three-point-seven percent drawdown. Static seventy-thirty lost about
twenty-four percent instead.

SMA Ten gave up more return. Four of four Absolute Twelve defensive cycles,
and nine of eleven SMA Ten cycles, lost relative wealth versus staying invested.

We didn't retune the failed rule. These are exploratory NAV results, not
production-ready execution.

### Transition
Now I'll show the workflow with synthetic data, not replay those research results.

### Presenter cues — not spoken
Point at the 70/30 versus Absolute12 rows; do not read every number aloud.
The source window is **2016-01-04–2026-07-31**, with **BIL defense** and
**20 bps one-way costs**. Static splits mean SPY/BIL, not stock/aggregate bonds.

| Portfolio | Net CAGR | Maximum drawdown |
| --- | ---: | ---: |
| SPY | 15.03% | -33.68% |
| Static 80/20 | 12.53% | -27.33% |
| Static 70/30 | 11.26% | -24.08% |
| Absolute12 | 11.26% | -33.68% |
| SMA10 | 7.85% | -28.19% |

Static 70/30 and Absolute12 both round to 11.26%; Absolute12's exact CAGR is
slightly higher. The comparison is the drawdown trade-off, not a claim that
static 70/30 has a higher CAGR.

The whipsaw counts are **completed defensive cycles losing relative wealth
against SPY, including switching costs**, not necessarily negative absolute
returns. SMA10 protected part of the COVID decline but missed a large rebound.
The classification remains **RESEARCH MORE / near rejection**; verify executable
closes under the same frozen rules, without parameter rescue or promotion.
Sources: [metrics](../research/etf_trend/results/metrics.csv),
[whipsaws](../research/etf_trend/results/whipsaw_summary.csv),
[original report](../docs/etf-trend-validation.md).

## Slide 7 — One command → research to dry-run execution

**Timing:** 90 seconds · 3:30–5:00 · roughly 45 seconds speaking + 45 seconds navigation

### Goal
Show the complete deterministic research-to-dry-run path, with visible limits.

### Script
This is a synthetic dry run, not real research.

The agent starts with a research hypothesis, not an order.

The hypothesis is converted into a deterministic experiment.

The backtest uses fictional prices, delayed decisions, and costs.

This is the important part — the model doesn't get to grade its own homework.
These controls verify mechanics, not market alpha.

Bad strategies remain visible as rejected evidence. The portfolio keeps most
of its capital in cash.

Even a strategy that survives research still cannot trade directly.

Execution deliberately stops here today. Robinhood is disconnected.
The receipt ties inputs, configuration, and results together.

### Transition
Now let's look at that last safety boundary.

### Presenter cues — not spoken
Follow the [90-second walkthrough](demo-runbook.md#during-the-presentation--slide-7).
Switch to the terminal and run `uv run aql demo`. With dependencies already
prepared, the network-independent variant is `uv run --offline --no-sync aql demo`.
Scroll through the completed output, pausing your narration at each stage.
The CLI has no interactive pauses.

Keep the banner visible: **MODE: DEMO · DATA: SYNTHETIC FIXTURE ·
LIVE TRADING: DISABLED · EXECUTION: DRY RUN**.
The fictional symbols are `DEMO_UP`, `DEMO_WEAK`, and `DEMO_NULL`.
The demo uses **10 bps** and compressed three-period, skip-latest momentum;
it is neither slide 6's real 20 bps study nor the unrun sector 12-1 experiment.

If the CLI fails or is not ready within five seconds, disclose the switch to
[prerecorded output](demo-output.txt). Do not troubleshoot during the talk.

## Slide 8 — Agents never get direct control of capital

**Timing:** 30 seconds · 5:00–5:30

### Goal
Show that a research proposal cannot authorize its own execution.

### Script
The proposal is ten fictional shares, about nineteen hundred and twenty dollars.

The RiskGate checks the instrument, positive long-only quantity, leverage,
order size, concentration, and freshness. Those checks use supplied demo state,
not a connected account.

The execution adapter checks the gate again. Live execution stays disabled.
Passing this demonstration gate authorizes only a dry run, never a broker order.

### Transition
So where does AI actually add value?

### Presenter cues — not spoken
Actual fixture intent: **BUY 10 DEMO_UP**, estimated **$1,919.92**.
Supplied snapshot: **$10,000 equity and cash**, no positions.
Limits: **$2,000 order**, **$2,500 position**, **25% concentration**.
The 20% allocation is rounded to whole shares.

The scenario clock is fixed at **2025-01-01T00:00:00+00:00**, not wall time.
This is one intent against supplied state, not broker reconciliation,
multi-order rebalancing, or continuous live-account enforcement.
Hashes bind contents; they do not establish truthful data or profitable alpha.

## Slide 9 — Where AI actually adds value

**Timing:** 30 seconds · 5:30–6:00

### Goal
Position AI as a research collaborator, not a substitute for calculations.

### Script
AI can help read research, form hypotheses, interpret earnings, and investigate
why a strategy stops working. Its useful job is proposing the next test and
finding evidence that contradicts the story.

Code should calculate returns, rank assets, allocate capital, and enforce limits.
Use AI for reasoning. Use code for truth — meaning reproducible calculations,
not certainty about markets.

### Transition
That division gives us a practical roadmap.

### Presenter cues — not spoken
The agent column describes target capabilities. Today's scripted stand-in did
not autonomously conduct the separately committed research.

## Slide 10 — Roadmap

**Timing:** 25 seconds · 6:00–6:25

### Goal
Make each future capability conditional on evidence and separate authorization.

### Script
Today we have research, falsification, and an offline demonstration.

Next: qualify the missing data, then paper or shadow trading with its own
acceptance gates. After that, evaluate agent-driven experiment generation.

Risk-controlled Robinhood execution is the final step, not today's feature.
Live trading is disabled. Nothing here changes Azure or the Phase Zero recorder.

### Transition
The destination is disciplined restraint.

### Presenter cues — not spoken
No live data acquisition, SEC acceptance, Azure deployment, scheduler change,
or broker connection is part of this presentation.

## Slide 11 — The goal isn’t an AI that trades more.

**Timing:** 15 seconds · 6:25–6:40

### Goal
End on the ability to abstain, not a promise of returns.

### Script
We're not using AI to guess trades. We're using it to decide which ideas deserve
to survive.

The goal isn't an AI that trades more.
It's an AI that knows when not to trade.

### Transition
None — hold the final slide in silence. Do not read this cue aloud.

## Source and scope notes — not spoken

Final branch: **`demo/final-presentation`**. The selected integration base is
**`80ac8854c4cdfbcc13f58b50761b714221557249`** from
`copilot/create-complete-presentation-package`, a descendant of the full
research lineage, not the initial `main`.

[Research status](../docs/research-status.md) preserves the original reports
and branch provenance. The demo is synthetic and deterministic; no new strategy
research, real-data acquisition, external acceptance, or trading occurred.
