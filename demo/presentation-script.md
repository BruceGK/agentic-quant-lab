# Agentic Quant Lab — presentation script

Read only the text under **Script** aloud. Goals, timings, tables, and presenter
cues are not spoken. The last sentence of each script supplies the transition.
Slide 7 contains seven short spoken beats separated by screen navigation; the
CLI itself does not pause between stages.

**Target:** 750 spoken words; 6:20, including a 1:15 live-demo interlude with about
0:35 of screen navigation. Allow ten seconds of breathing room for a roughly 6:30 delivery.
“Live demo” means running the local **synthetic DRY RUN**, never live trading.
If using the prerecorded fallback, disclose it as directed in the
[runbook](demo-runbook.md).

| Slide | Duration | Presentation clock |
| --- | ---: | --- |
| 1 | 0:25 | 0:00–0:25 |
| 2 | 0:30 | 0:25–0:55 |
| 3 | 0:40 | 0:55–1:35 |
| 4 | 0:35 | 1:35–2:10 |
| 5 | 0:35 | 2:10–2:45 |
| 6 | 0:45 | 2:45–3:30 |
| 7 | 1:15 | 3:30–4:45 |
| 8 | 0:30 | 4:45–5:15 |
| 9 | 0:25 | 5:15–5:40 |
| 10 | 0:25 | 5:40–6:05 |
| 11 | 0:15 | 6:05–6:20 |

## Slide 1 — Agentic Quant Lab

**Timing:** 0:25 · 0:00–0:25

### Goal

Establish the contrarian premise: restraint is a product capability.

### Script

Most AI trading demos ask a model what to buy. I wanted to build the opposite.

Agentic Quant Lab asks whether an idea deserves to survive at all. The vision
is autonomous research, with evidence at every step and firm limits around
capital. Before I show the system, here's the problem it's trying to solve.

### Presenter cues — not spoken

Pause after the opening. This is a product vision, not a profitable-strategy
claim. Keep the distinction between **VISION**, **DEMO**, and **REAL RESEARCH**
visible throughout.

## Slide 2 — AI can generate trades. Can we trust them?

**Timing:** 0:30 · 0:25–0:55

### Goal

Replace “Does the story sound convincing?” with “What evidence would disprove it?”

### Script

A convincing trading story is easy to generate. Knowing whether it works is
much harder.

Was tomorrow's information accidentally used today? Did costs erase the edge?
Did we quietly leave out companies that disappeared?

A smooth equity curve doesn't answer those questions. I want a system that makes
weak ideas fail visibly, instead of making every idea sound investable. That
requires a different architecture.

### Presenter cues — not spoken

Let the three questions land. Do not suggest that an LLM can certify data
availability, historical investability, or executable fills.

## Slide 3 — An autonomous research loop

**Timing:** 0:40 · 0:55–1:35

### Goal

Explain the intended reasoning loop and the implemented deterministic boundary.

### Script

Think of this as two lanes. In the vision, AI reasons about hypotheses and designs
experiments. Deterministic code handles backtesting, scientific controls, the
strategy tournament, portfolio sizing, the RiskGate, and execution. An evidence
and provenance sidecar preserves what went in and what came out.

Today, the research agent is a scripted, deterministic stand-in, not an LLM.
The actual research was committed separately; this demo doesn't recreate it.

The intended loop learns what to test next without bypassing those rules.
First, it must challenge itself.

### Presenter cues — not spoken

Trace reasoning → experiment → backtest/controls → tournament → portfolio →
RiskGate → **DRY RUN**. Trace the evidence/provenance sidecar separately:
inputs, configuration, results, hashes, and source reports. It supports
inspection; it is not an alpha validator or a new Phase 0 ledger.

## Slide 4 — The agent has to prove itself wrong

**Timing:** 0:35 · 1:35–2:10

### Goal

Make falsification concrete without presenting toy controls as market validation.

### Script

The first job is to challenge the idea.

A null control asks whether noise looks profitable. Broader research uses random
controls; this demo uses flat data and a no-edge candidate. A planted signal
checks that we recover a known pattern. Leakage checks reject future information
and keep earlier decisions unchanged when future inputs change.

These test mechanics, not alpha. Out-of-sample and regime testing are research
requirements, not completed demo proof. Sometimes the right answer comes before
a backtest.

### Presenter cues — not spoken

The demo also checks deterministic reproduction. Its positive signal is planted,
not discovered. Do not claim this demo ran random-market, out-of-sample, regime,
or real-sector shuffled-rank tests. Historical research has its own disclosed
methods and limitations; retrospective splits are not prospective validation.

## Slide 5 — The system is designed to say NO

**Timing:** 0:35 · 2:10–2:45

### Goal

Distinguish a negative economic result from an honest data-gate stop.

### Script

Here's what saying no looks like in the real research.

Stock momentum is blocked by historical-universe and delisting evidence. Adding
quality also needs point-in-time fundamentals. Earnings drift is deferred:
the price-based route needs data qualification; historical consensus and
revision variants are blocked.

Sector-relative momentum has a frozen protocol, but a network and DNS gate stopped
acquisition. Zero of eighteen scenarios ran. That's missing evidence, not an
economic rejection.

Trend got further. Its results were a warning, not a promotion.

### Presenter cues — not spoken

These are **REAL RESEARCH** statuses, not scores from the synthetic tournament.

| Research family | Preserved status and reason |
| --- | --- |
| ETF Trend | **RESEARCH MORE**, near rejection; executable-price verification only; not promoted to paper/shadow. |
| Stock momentum | **RESEARCH-GRADE STOCK TEST CURRENTLY BLOCKED**: historical investable universe, security identity, delistings, and terminal returns remain unqualified. |
| Momentum + quality | Same stock-data blockers, plus original point-in-time filing/fundamental vintages. |
| PEAD / earnings drift | **DEFER PEAD** overall. Price-based and guidance-text routes: **LOW-COST DATA REQUIRED**, not qualified datasets. Consensus-surprise and analyst revisions: **BLOCKED** by historical-vintage requirements. Price-based PEAD does not require consensus. |
| ETF sector-relative / dual momentum | **EXPLORATORY; RESEARCH MORE; DATA ACQUISITION STILL BLOCKED**. Frozen protocol; **0/18 scenarios run** after network/DNS failure. Metrics unavailable, not zero. No economic rejection. |

Source: [research-status.md](../docs/research-status.md), with the original
stock, PEAD, and sector reports linked there.

## Slide 6 — Trend looked promising—until we tested it

**Timing:** 0:45 · 2:45–3:30

### Goal

Show a real adverse finding and preserve the precise research decision.

### Script

Trend initially looked promising as a way to step aside during trouble.
The follow-up froze the rules and compared them with simply holding less equity.

With Treasury-bill defense and twenty-basis-point one-way costs, Absolute Twelve
matched the static seventy-thirty portfolio's annual growth, but suffered the
full equity drawdown. The moving-average rule did worse. Missed rebounds and
repeated exits consumed the hoped-for protection.

The verdict is research more, close to rejection, not promoted. These are
exploratory NAV valuations, not executable closes. Verify the same rules on actual
closes; don't retune them to rescue the story.

Now, here's the workflow—not those research results.

### Presenter cues — not spoken

Point to the static 70/30 comparison; **do not read every number aloud**.
The following is the primary **BIL defensive-asset** comparison at **20 bps
one-way costs**, **2016-01-04–2026-07-31**. Percentages are net CAGR and maximum
drawdown, not synthetic demo returns.

| Portfolio | Net CAGR | Maximum drawdown |
| --- | ---: | ---: |
| SPY | 15.03% | -33.68% |
| STATIC80: 80% SPY / 20% BIL | 12.53% | -27.33% |
| STATIC70: 70% SPY / 30% BIL | 11.26% | -24.08% |
| ABS12: Absolute12 / BIL | 11.26% | -33.68% |
| SMA10 / BIL | 7.85% | -28.19% |

Absolute12 lost relative wealth versus staying in SPY in **4/4** completed
defensive cycles; SMA10 did so in **9/11**. Those are relative opportunity
losses, not necessarily negative absolute account returns. The result does
not justify retuning, promotion, or a universal rejection of trend investing.
If actual-close verification preserves the adverse result, reject these fixed
implementations. Source: [ETF trend validation](../docs/etf-trend-validation.md).

## Slide 7 — One command. Research to dry run.

**Timing:** 1:15 · 3:30–4:45 · about 0:40 speaking + 0:35 navigation

### Goal

Demonstrate the seven implemented stages while keeping synthetic output separate
from real research.

### Script

This is a live walkthrough of a synthetic dry run, not live trading. The agent
proposes a planted hypothesis.

The experiment fixes fictional instruments, timing, and costs before calculation.

The backtest uses synthetic monthly valuations, not market fills.

The controls challenge the mechanics; they don't validate alpha.

The tournament rejects Weak and Null. The survivor is demo-only; the portfolio
keeps most capital in cash.

The RiskGate checks one proposed buy against supplied demo state.

Execution says would submit, never submitted. The receipt binds the evidence.
Let's look at that capital boundary.

### Presenter cues — not spoken

Use the [75-second runbook](demo-runbook.md#the-75-second-slide-7-walkthrough).
Alt+Tab / Command+Tab to the prepared terminal; run the prepared offline command.
**All seven stages finish and print at once.** Narrate the completed output by
scrolling or finding dashboard section titles; do not wait for nonexistent
interactive prompts.

Keep `MODE: DEMO | DATA: SYNTHETIC / FIXTURE | LIVE TRADING: DISABLED` visible
at the start. The fictional symbols are `DEMO_UP`, `DEMO_WEAK`, and `DEMO_NULL`;
the demo's compressed three-period, skip-latest signal is **not** the real
sector study's 12-1 rule. Demo costs are **10 bps**, not slide 6's 20 bps stress.

If the CLI is not ready within five seconds, switch to the prerecorded fallback
and explicitly replace the live claim with the runbook's failure disclosure.
Do not restart the 75-second clock.

## Slide 8 — Agents never get direct control of capital

**Timing:** 0:30 · 4:45–5:15

### Goal

Describe the actual RiskGate illustration and its limits.

### Script

Here, the proposal is ten fictional shares, about nineteen hundred and twenty
dollars. It fits below the two-thousand-dollar order cap, the
twenty-five-hundred-dollar position cap, and twenty-five-percent concentration.

Those checks use a supplied ten-thousand-dollar, all-cash snapshot and a fixed
scenario clock, not wall time. There's no broker reconciliation, and live
execution is disabled. Agents propose; deterministic controls decide.
So where does AI belong?

### Presenter cues — not spoken

- Actual fixture intent: **BUY 10 DEMO_UP**, estimated **$1,919.92** at the
  fixture reference price; not an executed order or market quote.
- Order cap **$2,000**; position cap **$2,500**; concentration limit **25%**.
  Supplied snapshot: **$10,000 equity, $10,000 cash, no positions**.
- Target allocation is 20%; whole-share rounding leaves roughly **$8,080.08**
  hypothetical cash before any actual execution. This is one BUY intent, not a
  reconciled account, multi-order rebalance, or continuously enforced live book.
- The gate also checks allowed symbols/instruments, positive whole-share
  long-only BUY, no leverage, snapshot consistency, dry-run mode, disabled live
  execution, and decision freshness. The execution adapter evaluates the gate
  again. A failed check blocks the dry run.
- Clock: **2025-01-01T00:00:00+00:00**, fixed scenario time; not wall-clock
  freshness or actual audit-event time. Hashes bind contents, not truth or alpha.
  Receipt/provenance remain separate from the unchanged Phase 0 ledger.

## Slide 9 — Where AI actually adds value

**Timing:** 0:25 · 5:15–5:40

### Goal

Position AI as a research collaborator, not an unconstrained execution engine.

### Script

AI's useful role is turning vague ideas into explicit tests, finding contradictory
evidence, and explaining why a candidate failed.

It should reduce the cost of disciplined research, not manufacture certainty
or trade around safeguards. The deterministic boundary makes that reasoning
inspectable. That's the value proposition—and it gives us a concrete roadmap.

### Presenter cues — not spoken

These are intended capabilities of a future evaluated reasoning agent. Do not
claim today's scripted stand-in performed a literature search, selected new
experiments autonomously, or generated the separately committed research.

## Slide 10 — From research lab to autonomous trading system

**Timing:** 0:25 · 5:40–6:05

### Goal

Make the roadmap conditional on evidence, authorization, and new acceptance.

### Script

Today's deliverable is a reproducible research workflow and a dry-run boundary.
Next comes qualifying missing data and testing frozen rules, then a separately
evaluated reasoning agent.

Paper or shadow operation would require new acceptance. Any broker integration
would need explicit authorization, reconciliation, and operational controls.
None is activated here. That brings me back to the point.

### Presenter cues — not spoken

This presentation performs no real live run, market-data acquisition, SEC
request, Azure deployment/acceptance, Robinhood connection, or infrastructure
change. Archived acceptance reports describe their original sessions, not a
new validation. Phase 0 and its activation flags remain unchanged; historical
acceptance is not permission to schedule recording or enable trading.

## Slide 11 — An AI that knows when NOT to trade

**Timing:** 0:15 · 6:05–6:20

### Goal

Leave the audience with disciplined restraint, not a claim of alpha.

### Script

This is a research lab, not a claim of profitable alpha.

The goal is not an AI that trades more. It is an AI that knows when not to trade.

### Presenter cues — not spoken

Hold the closing slide. The final sentence is the ending; do not add another
spoken summary.

## Source and scope notes — not spoken

The integrated demo/research source baseline is **`60c83a0`**; the presentation
package is on **`copilot/create-complete-presentation-package`**, not a new
research vintage. Sources are [the original walkthrough](../docs/demo-script.md),
[research status and provenance](../docs/research-status.md),
[ETF Trend](../docs/etf-trend-validation.md),
[stock-data feasibility](../docs/stock-data-feasibility.md),
[PEAD-data feasibility](../docs/pead-data-feasibility.md), and
[ETF relative momentum](../docs/etf-relative-momentum-validation.md).
Runtime labels, stages, and scope follow `src/agentic_quant_lab/demo.py`,
`agents.py`, `portfolio.py`, `risk.py`, and `execution.py`.
