# Agentic Quant Lab — editable slide source

**11 slides · 16:9 · 6 minutes 40 seconds, including the terminal demo.**
The `On-slide text` blocks feed [generate_slides.py](generate_slides.py).
Keep their line order when editing copy; the generator checks the expected
line counts. Layouts, diagrams, and chart bars are editable native PowerPoint
shapes. The trend chart reads committed research metrics, never demo scores.
The [presenter script](presentation-script.md) is embedded in all eleven notes.

## Design and regeneration

Midnight navy, white headings, mint deterministic code, violet agent reasoning,
amber research qualifications, and muted future work. Arial typography,
20–28 pt body text, 34 pt titles, generous margins. Only metadata, sources, chart
ticks, and footers are smaller. No stock photography, external fonts, or linked media.

From the repository root, with Python/uv already available:

```bash
uv run --no-project --with-requirements demo/requirements.txt python demo/generate_slides.py
```

Authoring dependencies are isolated from the production project. Their initial
installation may require internet; viewing the finished presentation does not.
The generator writes the PPTX and a structural validation report. To refresh the
PDF and contact sheet as well, use already-installed LibreOffice and Poppler:

```bash
uv run --no-project --with-requirements demo/requirements.txt python demo/generate_slides.py --render
```

Rendering is local, not a cloud upload. A missing renderer must not block delivery
of the structurally valid PPTX. Open the deck on the actual presenting machine
before the talk; the PDF is the font-stable fallback.

## Slide 1 — Agentic Quant Lab

### On-slide text
```text
From AI-generated hypotheses to
evidence-backed trading strategies
Agents research.
Deterministic systems decide.
RESEARCH
EVIDENCE
RISK
EXECUTION / DRY RUN
VISION → DISCIPLINED RESEARCH
```
### Visual layout
Oversized two-line title left; four connected blocks right. Violet research
flows into mint evidence, risk, and dry-run execution.
### Data source
Product vision and current boundaries in the [README](../README.md); no metrics.
### Speaker-note summary
Build the opposite of an LLM stock-picker. Agents behave like researchers.

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
Falsification
RiskGate
Trade*
Hallucinated reasoning
Backtest overfitting
Look-ahead / bad data
Uncontrolled execution
The hard problem isn't generating strategies.
It's rejecting bad ones.
*Future only. Today ends at dry run.
```
### Visual layout
Red shortcut above a full-width mint evidence pipeline. Wide labels must not
split a word. Four risk labels; two-line closing statement.
### Data source
Architecture and scientific boundaries in the [README](../README.md).
### Speaker-note summary
Fluent reasoning is not evidence. Rejecting weak ideas is the difficult part.

## Slide 3 — An autonomous research loop

### On-slide text
```text
AGENTIC LAYER
DETERMINISTIC CODE
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
### Visual layout
Violet reasoning lane left. Mint deterministic nodes snake across two rows.
Evidence sidecar below; future Robinhood muted with a dashed outline.
### Data source
[Agent interface](../src/agentic_quant_lab/agents.py),
[demo orchestration](../src/agentic_quant_lab/demo.py), and
[execution boundary](../src/agentic_quant_lab/execution.py).
### Speaker-note summary
Agents propose. Evidence decides. RiskGate authorizes.

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
Frozen specifications
Regime tests
Data provenance
Reject a failing rule. Don't optimize a rescue.
Research requirements, not a claim that the demo validates market alpha.
```
### Visual layout
Three equal cards with 0, +, and t+1 symbols. Secondary scientific controls
along the bottom. No unsupported production-success badge.
### Data source
[Demo tests](../tests/test_demo.py) and
[research scientific controls](../tests/test_scientific_controls.py).
### Speaker-note summary
Broader research uses random nulls; the demo uses flat/no-edge fixtures.
Recovering a planted synthetic signal verifies mechanics, not profitability.

## Slide 5 — The system already says “no”

### On-slide text
```text
REAL RESEARCH
ETF Trend
RESEARCH MORE
Weak vs static de-risking
Stock Momentum
DATA BLOCKED
Universe / identity / delistings
Momentum + Quality
DATA BLOCKED
Stock history + PIT fundamentals
PEAD / Earnings
DEFER
Consensus vintages unavailable
ETF Relative Momentum
NOT YET TESTED
Frozen protocol; acquisition blocked
THIS IS THE POINT.
The lab preserves negative evidence.
Trend: near rejection. Missing data is not an economic rejection.
```
### Visual layout
Five clear horizontal cards. Amber adverse/deferred statuses and blue data
gates, never a green profitable-strategy claim. Large concluding phrase.
### Data source
[Canonical research status and original reports](../docs/research-status.md).
### Speaker-note summary
Trend is not promoted; stocks/quality lack qualified data; PEAD is untested;
relative momentum has zero completed performance scenarios.

## Slide 6 — Trend looked promising — until we tested it properly

### On-slide text
```text
REAL RESEARCH · EXPLORATORY / NAV-BASED
2016-01-04 → 2026-07-31 · SPY / BIL · 20 bps one-way costs
CAGR ↑
MAX DRAWDOWN ↓ magnitude
Absolute12: no worst-drawdown benefit
SMA10: COVID protection, then missed rebound
Losing defensive cycles: Absolute12 4/4 · SMA10 9/11
We didn't retune the failed rule.
NOT PRODUCTION-READY · NAV proxy, not executable closes.
```
### Visual layout
Two aligned horizontal bar panels with zero origins, comparing return against
drawdown magnitude. Keep drawdown labels signed negative and the
NOT PRODUCTION-READY qualification prominent at 20 pt. No fabricated series.
Select `defense=BIL`, `one_way_cost_bps=20` from the CSV:

| Model | Net CAGR | Max drawdown |
| --- | ---: | ---: |
| SPY | 15.03% | -33.68% |
| Static 80/20 | 12.53% | -27.33% |
| Static 70/30 | 11.26% | -24.08% |
| Absolute12 | 11.26% | -33.68% |
| SMA10 | 7.85% | -28.19% |

Static splits mean SPY/BIL, not stock/aggregate bonds. The 4/4 and 9/11
counts refer to completed defensive cycles losing relative wealth versus SPY,
including switching costs, not calendar periods or necessarily absolute losses.
### Data source
[Committed metrics](../research/etf_trend/results/metrics.csv),
[whipsaws](../research/etf_trend/results/whipsaw_summary.csv),
[validated report](../docs/etf-trend-validation.md).
### Speaker-note summary
Similar rounded CAGR masks very different drawdowns. Verify executable closes
under frozen rules; do not retune or promote the weak implementations.

## Slide 7 — One command → research to dry-run execution

### On-slide text
```text
uv run aql demo
Agent → Experiment → Backtest
Falsification → Tournament → Portfolio
RiskGate → DRY RUN
DATA: DEMO FIXTURE
LIVE TRADING: OFF
EXECUTION: DRY RUN
INTERNET: NOT REQUIRED
Scripted agent. Synthetic results. No LLM or broker call.
Prepared offline: uv run --offline --no-sync aql demo
```
### Visual layout
Large command above three workflow lines. Four two-line safety badges.
No dense screenshot; the presenter switches to the real terminal here.
### Data source
[Demo implementation](../src/agentic_quant_lab/demo.py),
[synthetic fixture](../src/agentic_quant_lab/resources/demo_fixture.json),
and [committed successful output](demo-output.txt).
### Speaker-note summary
Run the command and scroll through completed stages. No internet after setup.
Demonstrate machinery, not a discovered investment edge.

## Slide 8 — Agents never get direct control of capital

### On-slide text
```text
ORDER INTENT
BUY 10
DEMO_UP
≈ $1,919.92
FIXTURE ONLY
RiskGate
✓ Approved instrument
✓ Long-only · positive quantity
✓ No leverage
✓ Order / position limits
✓ Concentration limit
✓ Decision freshness
✓ live_execution_enabled = false
EXECUTION
DRY RUN ADAPTER
Robinhood
DISCONNECTED
Agents propose. RiskGate authorizes.
One BUY / supplied demo state. No broker reconciliation.
Future design: credentials stay outside research agents.
```
### Visual layout
Order intent enters a seven-check gate, then the DryRunExecutionAdapter.
Robinhood is detached and muted. Checks are legible, not decorative tiny text.
### Data source
[RiskGate](../src/agentic_quant_lab/risk.py),
[execution adapters](../src/agentic_quant_lab/execution.py),
[matching demo receipt](assets/offline-demo/receipt.json).
### Speaker-note summary
Actual fixture order, $2,000 order cap, $2,500 position cap, 25% concentration.
Fixed scenario time and supplied state; the adapter checks the gate again.

## Slide 9 — Where AI actually adds value

### On-slide text
```text
AGENT / TARGET CAPABILITIES
Read research
Generate hypotheses
Find failure regimes
Interpret earnings / guidance
Propose experiments
Investigate degradation
DETERMINISTIC CODE
Calculate returns
Rank assets
Run backtests + model costs
Allocate capital
Enforce risk limits
Submit orders (future only)
Use AI for reasoning.
Use code for truth.
“Truth” means reproducible calculations, not certainty about markets.
```
### Visual layout
Violet agent column and mint code column, six lines each, large closing line.
Target reasoning capabilities must not imply today's scripted agent is an LLM.
### Data source
[Current architecture and boundaries](../README.md); target capabilities, not
claims that a live agent performed the research.
### Speaker-note summary
Use models for reasoning and contradictions; do not delegate math or authority.

## Slide 10 — Roadmap

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
experiment
generation
FINALLY
Risk-controlled
Robinhood
execution
LIVE TRADING DISABLED TODAY
Promotion requires evidence, not a better story.
```
### Visual layout
Four milestones; NOW mint, NEXT amber, remaining muted. No deployment dates,
live toggle, or implied permission to execute.
### Data source
[Research reopening gates](../docs/research-status.md) and
[unchanged constitution](../src/agentic_quant_lab/constitution.toml).
### Speaker-note summary
Qualified data and separately accepted paper/shadow trading come before
agent-driven experiment generation and authorized broker execution.

## Slide 11 — The goal isn’t an AI that trades more.

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
### Visual layout
Oversized two-line statement, NOT mint. Four restrained labels. Clean ending.
### Data source
Product thesis, not a performance or investment claim.
### Speaker-note summary
Close with disciplined abstention. Hold the slide without another summary.

## Source-of-truth and scope

Final branch: **`demo/final-presentation`**. Selected base:
**`80ac8854c4cdfbcc13f58b50761b714221557249`**, the complete presentation
descendant of the full research lineage. The initial `main` was not used.
[Canonical provenance](../docs/research-status.md) records all inspected branch
tips and preserves the real conclusions.

Slides 5–6 are **REAL RESEARCH**. Slides 7–8 are **SYNTHETIC DEMO FIXTURE**.
The 10 bps monthly demo is not the 20 bps daily NAV study or the unrun 12-1
sector experiment. No research, provider acquisition, Azure acceptance,
Phase 0 recording, or broker connection is part of this delivery.
