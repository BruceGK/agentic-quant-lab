# Agentic Quant Lab — presenter runbook

**Format:** 11 slides, 6:20 target plus ten seconds of breathing room; slide 7
contains the entire 75-second live-demo interlude. Exact spoken text is in
[presentation-script.md](presentation-script.md).

**Boundary:** “live demo” means the local **synthetic DRY RUN**, not a real live
run, real market backtest, broker submission, or production end-to-end test.
Today's research agent is scripted and deterministic, not an LLM. Actual
research is separately committed. No network is needed after preparation and
download of the complete checkout.

## Files to have locally

All paths below are relative to the already downloaded repository:
`/home/runner/work/agentic-quant-lab/agentic-quant-lab`.

| Purpose | File |
| --- | --- |
| Native presentation | `demo/Agentic-Quant-Lab-Demo.pptx` |
| No-slide-app fallback | `demo/Agentic-Quant-Lab-Demo.pdf` |
| Overview preview, not a slideshow | `demo/assets/deck-preview.png` |
| Exact spoken words | `demo/presentation-script.md` |
| Generated local dashboard | `demo-output/index.html` |
| Generated evidence receipt / complete result | `demo-output/receipt.json`, `demo-output/result.json` |
| Prerecorded synthetic dashboard | `demo/assets/offline-demo/index.html` |
| Matching prerecorded evidence / complete result | `demo/assets/offline-demo/receipt.json`, `demo/assets/offline-demo/result.json` |
| Matching prerecorded terminal transcript | `demo/assets/offline-demo/terminal.txt` |

The prerecorded set is a pre-generated fallback, **not** a new run or a live
result. Keep its HTML, JSON, and transcript together; never mix its receipt
with a newly generated result. HTML and PDF need only an existing local
browser/PDF viewer—no package installation, Python, uv, web server, or internet.

## Preparation — before the audience arrives

### 1. Use the presentation branch and a clean working tree

These commands are for the supplied Linux checkout, not a request to clone.
Complete fetching and all downloads **before** the presentation.

```sh
cd /home/runner/work/agentic-quant-lab/agentic-quant-lab
git status --short
git branch --show-current
```

`git status --short` must be empty before proceeding. If it is not, preserve
existing work outside this preparation flow; do not use destructive reset,
clean, or automatic stash commands.

```sh
git fetch origin copilot/create-complete-presentation-package
```

If the current branch is different, switch to the presentation branch:

```sh
git switch copilot/create-complete-presentation-package
```

Update only by fast-forward, then verify the checkout:

```sh
git merge --ff-only FETCH_HEAD
git branch --show-current
git status --short
git rev-parse --short HEAD
```

Expected branch: **`copilot/create-complete-presentation-package`**. The tree
must still be clean. If fast-forward fails, do not reset or merge unrelated
history; use an already verified downloaded package instead. The integrated
demo/research source baseline is **`60c83a0`**; the package's current HEAD can
be newer. Do not switch back to the baseline and lose the presentation files.

### 2. Prepare the optional executable demo

Use an existing Python **3.12+** and uv installation. On a machine without
them, use the HTML/PDF fallback, or arrange installation before rehearsal.
Do not install tools during the talk.

```sh
cd /home/runner/work/agentic-quant-lab/agentic-quant-lab
uv sync --frozen
uv run aql demo --reset
```

`uv sync --frozen` restores the checked-in environment without updating the
lockfile. Setup can need network access, downloads, and available package
caches. **A cold offline setup is not guaranteed.**

`--reset` regenerates the same three owned files in `demo-output`; it does not
delete unrelated files, research artifacts, or the Phase 0 ledger. Ordinary
reruns also deterministically overwrite those owned outputs.

The ordinary one-command demo is:

```sh
uv run aql demo
```

For the presentation, rehearse and use the **guaranteed-offline runtime**
invocation, after successful installation:

```sh
cd /home/runner/work/agentic-quant-lab/agentic-quant-lab
uv run --offline --no-sync aql demo
```

If uv itself or its cache is a problem but the installed virtual environment
is intact, the direct entry point requires no resolver or network:

```sh
cd /home/runner/work/agentic-quant-lab/agentic-quant-lab
/home/runner/work/agentic-quant-lab/agentic-quant-lab/.venv/bin/aql demo
```

Both executable offline paths require prior installation. Choose and rehearse
**one** stage command; do not run all alternatives during the interlude.
The CLI is not interactive: calculation and file writing finish before the
whole seven-stage transcript prints. There are no stage-by-stage pauses.

### 3. Inspect the rehearsal output

Confirm the following on the actual presenter machine; this checklist is not
a claim that a native presentation or live acceptance was already validated.

- Banner: `MODE: DEMO | DATA: SYNTHETIC / FIXTURE | LIVE TRADING: DISABLED`.
- `[1/7] Research agent` explicitly identifies a deterministic stand-in,
  with no LLM/API.
- Four computed scientific controls pass. Demo Weak and Demo Null are
  **REJECTED**; surviving synthetic candidates say **SURVIVES (DEMO ONLY)**.
- Real-research entries are separate, without synthetic performance metrics.
- Portfolio proposal uses fictional `DEMO_UP`, an initially all-cash snapshot,
  and one whole-share BUY intent. RiskGate passes the supplied scenario.
- `[7/7] Execution` is **SIMULATED / DRY RUN ONLY**:
  **would submit BUY 10 DEMO_UP, estimated $1,919.92**. No order is submitted.
- The local receipt contains `experiment_id`, `input_hash`,
  `strategy_config_hash`, `result_hash`, `execution: dry_run`, and a fixed
  scenario timestamp. Fixed scenario time is not wall-clock execution time.

For an optional pre-talk receipt check:

```sh
cat /home/runner/work/agentic-quant-lab/agentic-quant-lab/demo-output/receipt.json
```

### 4. Open and stage the windows

1. Open the browser. Press **Ctrl+L** (macOS **Command+L**), paste this exact
   address, and press **Enter**:
   `file:///home/runner/work/agentic-quant-lab/agentic-quant-lab/demo-output/index.html`.
   The dashboard is a local file; no server is needed. Refresh after each run.
2. Open a second tab the same way:
   `file:///home/runner/work/agentic-quant-lab/agentic-quant-lab/demo/assets/offline-demo/index.html`.
   This is the **prerecorded fallback**. Keep it visibly distinguishable from
   the fresh `demo-output` tab by checking the address.
3. Open the prerecorded `receipt.json`, `result.json`, and `terminal.txt`
   alongside it if you want evidence inspection available. Use the absolute
   folder `/home/runner/work/agentic-quant-lab/agentic-quant-lab/demo/assets/offline-demo/`.
   Do not regenerate or overwrite this packaged fallback during the talk.
4. In the terminal, set a legible font, keep enough scrollback, and leave this
   command typed but **not yet executed**:
   `uv run --offline --no-sync aql demo`.
   Its working directory must be
   `/home/runner/work/agentic-quant-lab/agentic-quant-lab`.
5. In PowerPoint, choose **File → Open → Browse**, open
   `/home/runner/work/agentic-quant-lab/agentic-quant-lab/demo/Agentic-Quant-Lab-Demo.pptx`,
   select slide 1, then **Slide Show → From Beginning**.
   In Keynote, choose **File → Open**, open that `.pptx`, select slide 1,
   then click **Play**. On a Mac, copy the downloaded package locally and
   choose that local file; the Linux runner path is not a macOS volume.
6. Without a native slide app, use the browser's **Ctrl+L** and open
   `file:///home/runner/work/agentic-quant-lab/agentic-quant-lab/demo/Agentic-Quant-Lab-Demo.pdf`.
   Set the PDF viewer to **Fit to page**, then use its next-page control to
   advance one slide at a time. Rehearse the actual viewer's presentation/full-
   screen controls rather than assuming they match PowerPoint.
7. Rehearse **Alt+Tab** on Windows/Linux or **Command+Tab** on macOS to move
   from slide 7 to the terminal, then the browser, then back to the slideshow.
   On returning, advance once to slide 8. Share the intended display so the
   audience sees the demo rather than private presenter notes.

**Native-viewer risk:** PowerPoint and Keynote native applications are not
available for sandbox checking. Their opening, font rendering, notes, display
selection, and app-switch behavior must be checked on the actual presenter
machine. Do not label those checks “passed” before doing them. Keep the PDF
ready regardless.

### 5. Final offline rehearsal

With setup and the complete checkout already downloaded, disconnect networking
and rehearse the selected command and every window switch. Keep the fallback
HTML and PDF open. Check legibility at audience viewing distance; set zoom
before starting. Do not fetch code, sync packages, acquire market data, or
attempt external acceptance during the presentation.

## Timing map

| Slide | Time | Action |
| --- | --- | --- |
| 1 | 0:00–0:25 | Exact opening; establish the vision. |
| 2 | 0:25–0:55 | Explain why generated trades are not evidence. |
| 3 | 0:55–1:35 | Reasoning versus deterministic computation and controls. |
| 4 | 1:35–2:10 | Null, planted, leakage; disclose demo limits. |
| 5 | 2:10–2:45 | Show real research's rejection/data-gate discipline. |
| 6 | 2:45–3:30 | Explain adverse Trend findings; do not read the whole table. |
| 7 | 3:30–4:45 | Run and narrate the 75-second synthetic DRY RUN below. |
| 8 | 4:45–5:15 | Actual fixture risk example and supplied-state limits. |
| 9 | 5:15–5:40 | State where AI could add value. |
| 10 | 5:40–6:05 | Conditional roadmap, no activated trading. |
| 11 | 6:05–6:20 | Exact closing; hold the slide. |

## The 75-second slide 7 walkthrough

Start the interlude clock on arriving at slide 7. Budget about **40 seconds
of speech and 35 seconds of navigation**, included in—not added to—the 75
seconds. The seven rows are presenter beats over completed output, not seven
interactive CLI steps. Exact browser section titles below match the current
renderer. Use **Ctrl+F** / **Command+F**, enter the title, **Enter**, then **Esc**
to dismiss Find without losing the section. Terminal scrollback is an equally
valid alternative if switching to the dashboard is awkward.

| Interlude clock | Stage and exact screen action | Say exactly |
| --- | --- | --- |
| 0:00–0:15 | **1 — Research agent.** Alt+Tab / Command+Tab to the terminal; press Enter on the staged offline command. Scroll to the banner and `[1/7] Research agent`. If output is not ready within five seconds, use the fallback rule below. | “This is a live walkthrough of a synthetic dry run, not live trading. The agent proposes a planted hypothesis.” |
| 0:15–0:23 | **2 — Experiment.** Switch to the prepared generated-dashboard tab and refresh. Find `Experiment`; point to fictional universe, delayed timing, and 10 bps costs. Alternatively scroll to `[2/7] Experiment`. | “The experiment fixes fictional instruments, timing, and costs before calculation.” |
| 0:23–0:31 | **3 — Backtest.** Find `Backtest — synthetic net fixture returns`, or scroll to `[3/7] Backtest`. Do not read fixture returns as real performance. | “The backtest uses synthetic monthly valuations, not market fills.” |
| 0:31–0:40 | **4 — Falsification.** Find `Falsification — actual computed checks`, or scroll to `[4/7] Falsification`. Point to null, planted, and leakage checks. | “The controls challenge the mechanics; they don't validate alpha.” |
| 0:40–0:53 | **5 — Tournament and portfolio.** Find `Tournament — DEMO ONLY`, then `Portfolio proposal`; show rejected Weak/Null and the cash remainder. Terminal alternatives: `[5/7] Strategy tournament` and `Portfolio proposal`. Do not dwell on the long intervening real-research list. | “The tournament rejects Weak and Null. The survivor is demo-only; the portfolio keeps most capital in cash.” |
| 0:53–1:01 | **6 — RiskGate.** Find `RiskGate`, or scroll to `[6/7] RiskGate`. Show the checks, not a broker account. | “The RiskGate checks one proposed buy against supplied demo state.” |
| 1:01–1:15 | **7 — Execution and evidence.** Find `Execution — SIMULATED / DRY RUN`, then `Evidence receipt — fixed scenario clock`. Terminal alternatives: `[7/7] Execution` and `Evidence receipt`. Point to “would submit” and the hashes; return to the slideshow with Alt+Tab / Command+Tab and advance to slide 8. | “Execution says would submit, never submitted. The receipt binds the evidence. Let's look at that capital boundary.” |

Approximate navigation budget per row: **6 / 4 / 4 / 5 / 5 / 4 / 7 seconds**.
Do not claim the dashboard animates, pauses, streams stages, or asks for approval.
It is a static view of a completed deterministic scenario.

For post-talk questions only, find `Real research — separate, no synthetic metrics`.
That section carries committed research statuses, not backtests performed by
the demo. The demo's three-period, skip-latest momentum rule is not the real
sector protocol's 12-1 rule.

## Failure rule — five seconds, then prerecorded fallback

If the CLI errors or has not produced its completed output within five seconds:

1. Press **Ctrl+C** in that terminal to stop the attempted command. Do not spend
   the interlude installing, fixing caches, retrying DNS, or debugging.
2. Say: **“The command isn't ready within five seconds, so I'm switching to the
   prerecorded dry run. This is not a live result.”**
3. Switch to the already open
   `file:///home/runner/work/agentic-quant-lab/agentic-quant-lab/demo/assets/offline-demo/index.html`.
   If needed, open it via the browser address bar. Show its banner and
   `Hypothesis`, then continue the same section-title walkthrough. Do not
   restart the interlude clock; use the disclosure instead of the live opening.
4. If the fresh output was already shown before failure, clearly identify the
   switch; use only the matching fallback receipt/result afterward.
5. If HTML viewing fails, open the packaged `terminal.txt` in a text viewer or:

   ```sh
   cat /home/runner/work/agentic-quant-lab/agentic-quant-lab/demo/assets/offline-demo/terminal.txt
   ```

   Scroll the prerecorded transcript; still describe it as prerecorded.
   If neither view is usable, stay on slide 7's workflow, say the demo view is
   unavailable, and proceed to slide 8. Do not pretend a command succeeded.

For an intentionally fallback-only talk, replace slide 7's opening with:
**“This is a prerecorded synthetic dry run, not a live run. The agent proposes
a planted hypothesis.”** The remaining stage narration is unchanged.

If a native slide application fails, use the already open
`demo/Agentic-Quant-Lab-Demo.pdf`; no installation is needed. The overview
`demo/assets/deck-preview.png` is a last-resort visual reference, not an
11-page presentation substitute.

## Risk example — exact facts for slide 8 and questions

| Item | What the implementation actually uses |
| --- | --- |
| Intent | **BUY 10 DEMO_UP**, a fictional instrument |
| Estimated notional | **$1,919.92**, computed from the fixture reference price |
| Supplied account | **$10,000 equity, $10,000 cash, no positions** |
| Target | 20% in the selected sleeve; whole-share rounding leaves extra cash |
| Order limit | **$2,000** |
| Position limit | **$2,500** |
| Concentration limit | **25%** of supplied equity |
| Freshness | Maximum 172,800 seconds, evaluated against the **fixed 2025-01-01 scenario clock**, not today's wall time |
| Other checks | Allowed symbols/instruments, positive whole-share long-only BUY, no leverage, consistent snapshot, dry-run mode, disabled live execution |
| Execution | Adapter rechecks RiskGate, returns **SIMULATED / DRY RUN**; “would submit,” not “submitted” |
| Explicit limits | One intent against supplied state; **no broker reconciliation**, multi-order rebalance, or continuous live-account enforcement |

Risk approval here is not real research approval. Hashes connect inputs,
configuration, and results; they do not establish truthful source data, actual
execution, profitable alpha, or regulatory compliance.

## Research and operational guardrails

- **ETF Trend:** exact decision **RESEARCH MORE**, close to rejection, not
  promoted. At 20 bps one-way costs with BIL defense, 2016-01-04–2026-07-31:
  SPY **15.03% / -33.68%**; STATIC80 **12.53% / -27.33%**; STATIC70
  **11.26% / -24.08%**; ABS12 **11.26% / -33.68%**; SMA10
  **7.85% / -28.19%** (net CAGR / maximum drawdown). Losing relative-wealth
  defensive cycles: **4/4** ABS12, **9/11** SMA10. These are exploratory NAV
  proxies, not executable closes. Verify the frozen rules; no retuning.
- **Stock momentum:** historical universe, security identity, delisting and
  terminal-return evidence block research-grade testing. **Quality** additionally
  requires point-in-time fundamentals; current restated values are not enough.
- **PEAD:** **DEFER PEAD**. Price-based and guidance-text routes require low-cost
  data qualification. Historical consensus-surprise and revision variants are
  blocked; price-based PEAD does not require consensus. No PEAD alpha result.
- **ETF relative momentum:** frozen protocol, **0/18 scenarios run**, network/DNS
  data-gate stop. **EXPLORATORY; RESEARCH MORE; DATA ACQUISITION STILL BLOCKED**.
  Unknown metrics are not zero returns and not an economic rejection.
- **Scientific controls:** broader research includes random null controls;
  this demo's null is flat/no-edge. Planted and leakage checks test machinery,
  not real alpha. Out-of-sample, regime, and unrun sector diagnostics are
  requirements, not completed proof from this demo.
- **No external activity:** do not run real research, acquire market data,
  contact SEC, deploy Azure, connect Robinhood, change infrastructure, or attempt
  real live/end-to-end acceptance. This package leaves Phase 0 unchanged.
  `phase0.external_acceptance_complete = false`,
  `phase0.scheduled_recording_enabled = false`, and
  `live_execution.enabled = false` remain untouched.
- **Historical evidence is historical:** archived SEC/Azure/acceptance reports
  describe their own sessions, not new checks performed for this presentation.
  Demo receipts are separate from the Phase 0 production ledger. No live capital
  is used, and Robinhood is a disabled stub.

Authoritative reading, all available locally:
[research status and provenance](../docs/research-status.md),
[ETF Trend](../docs/etf-trend-validation.md),
[stock-data feasibility](../docs/stock-data-feasibility.md),
[PEAD-data feasibility](../docs/pead-data-feasibility.md),
[ETF relative momentum](../docs/etf-relative-momentum-validation.md), and
[the original demo walkthrough](../docs/demo-script.md).
Source integration baseline: **`60c83a0`**. This runbook specifies rehearsal
checks and presentation actions; it does not invent test, native-viewer, or
external-acceptance results.
