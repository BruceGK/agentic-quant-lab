# Agentic Quant Lab — editable deck source

11 slides · 16:9 · approximately 6½ minutes including the live interlude.
The numbered slides below are the editable text specification. The `On-slide text`
blocks feed `build_deck.py`; keep their line order when changing copy. Layout and
chart drawing are native PowerPoint shapes in that authoring file. The trend chart
reads the committed CSV, never demo output. Presenter scripts are embedded as notes.

## Design and regeneration

Midnight navy background; white headings; mint deterministic layer; violet agent
layer; amber qualification gates; muted blue-gray future work. Arial typography,
large titles, generous margins, no external fonts or linked media. Body text
generally 20–28 pt; only source/context labels and footers are smaller.

Authoring is optional, separate from the application environment:

```bash
cd /home/runner/work/agentic-quant-lab/agentic-quant-lab
python3 -m venv /tmp/aql-deck-authoring
/tmp/aql-deck-authoring/bin/pip install -r /home/runner/work/agentic-quant-lab/agentic-quant-lab/demo/requirements.txt
/tmp/aql-deck-authoring/bin/python /home/runner/work/agentic-quant-lab/agentic-quant-lab/demo/build_deck.py
```

To refresh the PDF on a machine with LibreOffice installed:

```bash
libreoffice -env:UserInstallation=file:///tmp/aql-deck-libreoffice --headless --convert-to pdf --outdir /home/runner/work/agentic-quant-lab/agentic-quant-lab/demo /home/runner/work/agentic-quant-lab/agentic-quant-lab/demo/Agentic-Quant-Lab-Demo.pptx
```

Open the deck on the actual presenting machine before the talk. The PDF is the
font-stable fallback. Rendering previews are derived from that PDF, not a separate
HTML approximation.

## Slide 1 — Agentic Quant Lab

### On-slide text
```text
From AI-generated hypotheses to
evidence-backed trading strategies
Agents research.
Deterministic systems decide.
RESEARCH
EVIDENCE
RISK GATE
DRY RUN
VISION → DISCIPLINED RESEARCH
```
### Visual instructions
Oversized two-line title left; four connected blocks right, violet to mint.
Make the research-to-risk progression more prominent than any market symbol.
### Speaker note summary
Open with the opposite of a stock-picking chatbot. Autonomy is the destination;
the existing scripted-agent demo illustrates the boundary, not LLM capability.

## Slide 2 — AI can generate trades. Can we trust them?

### On-slide text
```text
TYPICAL AI TRADING BOT
LLM
“Bullish”
BUY
AGENTIC QUANT LAB
Hypothesis
Evidence
Falsify
Risk gate
Trade*
Hallucinated reasoning
Backtest overfitting
Look-ahead / bad data
Uncontrolled execution
The hard problem is rejecting bad ideas.
*Future only. Today ends at dry run.
```
### Visual instructions
Red-tinted shortcut above a mint evidence pipeline. Four small risk labels under
the comparison. Dominant closing statement, no paragraph.
### Speaker note summary
Fluent reasoning is not evidence; rejection is the core product.

## Slide 3 — An autonomous research loop

### On-slide text
```text
AI / AGENTIC
DETERMINISTIC SYSTEMS
Research Agent
Hypothesis
Experiment
Backtest
Falsification
Tournament
Portfolio
RiskGate
Execution
Robinhood
FUTURE
EVIDENCE / PROVENANCE
Hypotheses · inputs · results · risk decisions
Target architecture. Scripted agent today; demo receipts ≠ Phase 0 ledger.
```
### Visual instructions
Violet agent column left. Mint deterministic nodes snake across two rows, with
arrows connecting every stage. Future Robinhood box muted and dashed. Evidence
sidecar joins agent, backtest and risk. Execution is downstream of the gate.
### Speaker note summary
Separate scientific reasoning from numerical authority; distinguish target
autonomy, current deterministic demonstration and future broker integration.

## Slide 4 — The agent has to prove itself wrong

### On-slide text
```text
NULL CONTROL
No edge?
No alpha.
PLANTED SIGNAL
Known edge?
Recover it.
LEAKAGE TRAP
Future data?
Reject it.
Costs
Out-of-sample
Regime tests
Data provenance
Kill the idea. Don’t prompt-engineer a rescue.
Research requirements, not a claim that the demo validates market alpha.
```
### Visual instructions
Three equal cards with large 0, +, and t+1 symbols; risk-oriented amber/red for
leakage. Four controls along the bottom. No unsupported green production badge.
### Speaker note summary
Null includes random controls in the research test suite; live demo uses flat and
no-edge fixtures. Recovering a synthetic edge verifies mechanics, not profitability.

## Slide 5 — The system is designed to say NO

### On-slide text
```text
REAL RESEARCH
ETF Trend
RESEARCH MORE
Weak versus static de-risking
Stock Momentum
DATA BLOCKED
Historical universe + delistings
Momentum + Quality
DATA BLOCKED
Stock history + PIT fundamentals
PEAD / Earnings
DEFER
Consensus blocked; price route gated
ETF Relative Momentum
NOT YET TESTED
Frozen protocol; runner DNS blocked
Missing evidence is not an economic rejection.
Phase 0: historical evidence acceptance recorded. No production strategy claimed.
```
### Visual instructions
Five horizontal candidate cards. Status chips amber/blue-gray, never a profitable
green strategy. Make missing evidence visibly different from weak observed results.
### Speaker note summary
Trend is not promoted. Do not call all five strategies economically rejected:
stock data is unqualified, PEAD deferred, sector performance not yet computed.

## Slide 6 — Trend looked promising—until we tested it

### On-slide text
```text
REAL RESEARCH · EXPLORATORY / NAV-BASED
2016-01-04 → 2026-07-31 · SPY / BIL · 20 bps one-way costs
CAGR ↑
MAX DRAWDOWN ↓ magnitude
Absolute12: no worst-drawdown benefit
SMA10: COVID protection, then missed rebound
Losing defensive cycles: Absolute12 4/4 · SMA10 9/11
Rules stayed frozen. No optimization around the failure.
NAV proxy ≠ executable closes. Not production-ready.
```
### Visual instructions
Two aligned horizontal bar panels, one for annualized return and one for drawdown
magnitude. Each begins at zero. Signed drawdown numbers remain negative. Model
labels and numbers are editable text. Display five rows from metrics.csv, selecting
defense=BIL and one_way_cost_bps=20, in this order:

| Model | CAGR | Max drawdown |
| --- | ---: | ---: |
| SPY | 15.03% | -33.68% |
| Static 80/20 | 12.53% | -27.33% |
| Static 70/30 | 11.26% | -24.08% |
| Absolute12 | 11.26% | -33.68% |
| SMA10 | 7.85% | -28.19% |

Static splits mean SPY/BIL, **not** stock/aggregate-bond portfolios. The 4/4 and 9/11
counts refer to completed defensive cycles losing relative wealth versus SPY,
including switching costs, not a generic count of losing calendar periods.
### Speaker note summary
Similar rounded CAGR can hide very different drawdowns. Trend is weak, not a
success story. Verification of actual closes remains a gate, not license to retune.
### Evidence
[Committed metrics](../research/etf_trend/results/metrics.csv),
[whipsaws](../research/etf_trend/results/whipsaw_summary.csv),
[validated report](../docs/etf-trend-validation.md).

## Slide 7 — One command. Research to dry run.

### On-slide text
```text
uv run aql demo
Hypothesis → Experiment → Backtest
✓ Controls → Tournament → Portfolio
✓ RiskGate → DRY RUN
LIVE TRADING: OFF
DATA: DEMO FIXTURE
EXECUTION: DRY RUN
Scripted agent. No LLM call. No market-data API.
Prepared offline: uv run --offline --no-sync aql demo
```
### Visual instructions
Command dominates the upper half. Large flow lines underneath with mint
checkmarks on computed controls, not real profitability. Persistent safety badges.
### Speaker note summary
Switch to terminal and local HTML. Explain the synthetic path and all seven
stages. Completed output can be scrolled; the CLI does not pause interactively.

## Slide 8 — Agents never get direct control of capital

### On-slide text
```text
ORDER INTENT
BUY 10
DEMO_UP
≈ $1,919.92
FIXTURE ONLY
RISK GATE
✓ Approved symbol / instrument
✓ Long-only · no leverage
✓ Order / position / concentration
✓ Fresh decision · valid snapshot
✓ Live execution disabled
EXECUTION
DRY RUN
Robinhood
DISCONNECTED
Agents propose. RiskGate authorizes a dry run.
One BUY / supplied demo state. No broker reconciliation.
Future design: broker credentials stay outside research agents.
```
### Visual instructions
Order card enters a large central risk gate and exits to dry-run adapter. Future
Robinhood is detached visually, never a green check. Avoid claiming full live
portfolio enforcement; single-order scope is legible.
### Speaker note summary
Actual fixture order, fixed scenario clock and supplied snapshot. Adapter
re-evaluates risk. A passing demo gate is not permission to place a live order.

## Slide 9 — Where AI actually adds value

### On-slide text
```text
AGENT / TARGET CAPABILITIES
Read research · form hypotheses
Interpret earnings / guidance
Investigate failure regimes
Propose the next experiment
DETERMINISTIC CODE
Returns · rankings · backtests
Costs · portfolio mathematics
Scientific controls · risk limits
Order validation · execution
Use AI for reasoning.
Use code for truth.
“Truth” means reproducible calculations—not certainty about markets.
```
### Visual instructions
Violet and mint columns. Parallel line spacing. Closing statement large and
centered. Capabilities explicitly labeled target; no claim of a running LLM.
### Speaker note summary
Keep model reasoning useful without allowing it to replace math or self-authorize.

## Slide 10 — From research lab to autonomous trading system

### On-slide text
```text
NOW
Research +
falsification
Offline demo
NEXT
Qualified data
Paper / shadow
trading
THEN
Agent-driven
strategy
discovery
FINALLY
Risk-controlled
Robinhood
execution
Live execution is intentionally disabled today.
Promotion requires evidence—not a better story.
```
### Visual instructions
Four sequential milestones. NOW mint, NEXT amber, remaining muted. Future
milestones unfilled; no dates, deployment claims or live-trading toggle.
### Speaker note summary
Data qualification and paper/shadow trading precede separately authorized execution.

## Slide 11 — An AI that knows when NOT to trade

### On-slide text
```text
The goal isn’t an AI that trades more.
It’s an AI that knows
when NOT to trade.
RESEARCH
EVIDENCE
FALSIFICATION
RISK
Agentic Quant Lab
github.com/BruceGK/agentic-quant-lab
```
### Visual instructions
Oversized statement; NOT mint. Four restrained evidence/risk labels. Clean ending,
no extra appendix and no finance disclaimer wall.
### Speaker note summary
Finish on disciplined abstention rather than trade frequency or promised returns.

## Source-of-truth and scope

All remote heads and `git log --all` were inspected on 2026-09-18. This presentation
branch integrates `copilot/make-repository-demo-ready` at
`60c83a0dfba92472454a99e7296a1fc7389b9cd1` without changing its application,
research, infrastructure, recorder or constitution.

| Source branch tip | Evidence used |
| --- | --- |
| `copilot/phase-0-sec-filing-recorder` · `04dda08` | Historical manual acceptance, not a new E2E claim |
| `research/long-only-strategy-tournament` · `3e82734` | Frozen trend report and BIL metrics |
| `copilot/researchpit-stock-data-audit` · `63a9b66` | Historical stock-universe/PIT gates |
| `copilot/researchpead-data-feasibility` · `82cdf94` | PEAD route-specific data gates |
| `copilot/researchetf-relative-momentum` · `544b55e` | Frozen protocol; acquisition blocked, 0/18 scenarios |
| `main`, both presentation branches before this work · `fb9b789` | Initial README only; not sufficient research context |

The integration includes [consolidated provenance](../docs/research-status.md)
and the original branch reports. Real research slides cite historical committed
artifacts. The demo's 10 bps, monthly fixture, compressed momentum and planted
returns are **not** the trend study's 20 bps, daily NAV panel or the frozen
relative-momentum 12-1 experiment. No research or real E2E was rerun.
