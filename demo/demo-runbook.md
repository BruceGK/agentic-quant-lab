# Agentic Quant Lab — demo runbook

**11 slides · 6:40 total · 90-second terminal demo on slide 7.**
Exact spoken words: [presentation-script.md](presentation-script.md).
All commands below run from **your local repository root**, not a CI runner path.

The demo is a scripted research agent plus deterministic synthetic fixtures.
It needs no API key, Azure, database, SEC, Robinhood, credentials, or runtime
internet. Initial Python/package installation can need internet; prepare first.
No real research or production acceptance needs to run tomorrow.

## Files to have open

| Purpose | Local file |
| --- | --- |
| Presentation | [Agentic-Quant-Lab-Demo.pptx](Agentic-Quant-Lab-Demo.pptx) |
| Slide-app fallback | [Agentic-Quant-Lab-Demo.pdf](Agentic-Quant-Lab-Demo.pdf) |
| Exact spoken words | [presentation-script.md](presentation-script.md) |
| Terminal fallback | [demo-output.txt](demo-output.txt) |
| Prerecorded local dashboard | [assets/offline-demo/index.html](assets/offline-demo/index.html) |
| Matching evidence | [receipt.json](assets/offline-demo/receipt.json), [result.json](assets/offline-demo/result.json) |
| Editable slide source | [slides.md](slides.md) |

Download the complete package before disconnecting. HTML is a local file, with
no server or external assets. Keep the prerecorded transcript, HTML, and JSON
together; do not pair a fresh result with an old receipt.

## Pre-demo

### 1. Select the published branch

Preserve any existing local changes before switching. Do not use reset, clean,
an automatic stash, force push, or a blind merge into `main`.

```bash
git status --short
git fetch origin demo/final-presentation
git checkout demo/final-presentation
git merge --ff-only origin/demo/final-presentation
git branch --show-current
git rev-parse --short HEAD
git status --short
```

Expected branch: **`demo/final-presentation`**, clean worktree.
If fast-forwarding is not possible, use an already downloaded verified package
instead of resolving history during rehearsal. The selected base was `80ac885`,
not the nearly empty `main`; do not check out the base and lose the final files.

### 2. Prepare and rehearse the exact quick-start

Prerequisites: Python 3.12+ and uv. Install packages before the talk.

```bash
uv sync
uv run aql demo --reset
uv run aql demo
```

`uv sync --frozen` is also supported when you want to insist on the committed
lockfile. Reset regenerates only the three owned output files; it does not
recursively delete the directory, user files, research, or the Phase 0 ledger.

For a prepared machine disconnected from the internet:

```bash
uv run --offline --no-sync aql demo
```

This bypasses uv dependency synchronization as well as network resolution.
If uv itself is unavailable but installation is intact:

```bash
.venv/bin/aql demo
```

Choose one stage command and rehearse it. Do not sync, fetch, or install during
the presentation. The deck's simple command is `uv run aql demo`; the explicit
offline variant is the safest choice after preparation.

### 3. Check the result

Confirm:

- Banner: **MODE: DEMO**, **DATA: SYNTHETIC FIXTURE**,
  **LIVE TRADING: DISABLED**, **EXECUTION: DRY RUN**.
- `[1/7] Research agent` is a deterministic stand-in, not a live LLM.
- The experiment and backtest use fictional inputs, delay, and **10 bps** costs.
- Four computed controls pass: null, planted signal, future-data rejection,
  deterministic reproduction.
- **Demo Weak** and **Demo Null** remain visibly rejected. Survivors are
  **DEMO ONLY**, not actual alpha.
- Portfolio: one whole-share BUY of fictional `DEMO_UP`, with most capital in cash.
- RiskGate checks pass for supplied demo state; live execution is disabled.
- Execution says **would submit BUY 10 DEMO_UP, estimated $1,919.92**,
  never “submitted.”
- The receipt binds the experiment, input, configuration, and result hashes;
  mode is demo and execution is dry run.
- Rerunning produces the same output and hashes. Fixed scenario time is not
  the actual invocation time or a production audit timestamp.

Fresh local files: `demo-output/index.html`, `demo-output/result.json`,
`demo-output/receipt.json`. Open the HTML directly in a browser if useful.
This receipt is separate from the Phase 0 append-only evidence ledger.

### 4. Stage the windows

1. Open the PPTX in PowerPoint or Keynote, then start the slideshow.
2. Open the PDF as the slide-app fallback. Verify fonts and projector legibility
   on the actual presentation machine; Linux rendering does not certify native
   PowerPoint/Keynote behavior.
3. Open `demo/demo-output.txt` and the prerecorded local dashboard in separate
   tabs. These are the fallback, not a fresh execution.
4. Set a large terminal font and enough scrollback. Stage `uv run aql demo`
   (or the rehearsed offline variant) without pressing Enter yet.
5. Rehearse Alt+Tab on Windows/Linux or Command+Tab on macOS from slide 7 to
   terminal and back. Show the audience the intended display, not private notes.
6. Disconnect networking and repeat the rehearsal. Internet failure changes
   nothing after the environment and artifacts are downloaded.

## During the presentation — slide 7

**Budget: 90 seconds.** The CLI computes and prints the complete result; it does
not pause after each stage. Pause your narration and scroll to each heading.
The experiment/backtest and tournament/portfolio pairs are separate beats in
one seven-stage output. The terminal alone is sufficient; HTML is optional.

| Clock | Screen action | Say exactly |
| --- | --- | --- |
| 0:00–0:15 | Switch to terminal, run `uv run aql demo`, show the banner and `[1/7] Research agent`. | “This is a synthetic dry run, not real research. The agent starts with a research hypothesis, not an order.” |
| 0:15–0:25 | Pause on `[2/7] Experiment`; point to the fixed specification. | “The hypothesis is converted into a deterministic experiment.” |
| 0:25–0:33 | Show `[3/7] Backtest`; do not sell the fixture returns. | “The backtest uses fictional prices, delayed decisions, and costs.” |
| 0:33–0:48 | Show `[4/7] Falsification`; point to null, planted, leakage, and reproduction checks. | “This is the important part — the model doesn't get to grade its own homework. These controls verify mechanics, not market alpha.” |
| 0:48–1:02 | Show `[5/7] Strategy tournament` and `Portfolio proposal`; keep rejected candidates visible. | “Bad strategies remain visible as rejected evidence. The portfolio keeps most of its capital in cash.” |
| 1:02–1:13 | Show `[6/7] RiskGate`; point to disabled live execution. | “Even a strategy that survives research still cannot trade directly.” |
| 1:13–1:30 | Show `[7/7] Execution`, “would submit,” and the evidence hashes. Return to the deck and advance to slide 8. | “Execution deliberately stops here today. Robinhood is disconnected. The receipt ties inputs, configuration, and results together. Now let's look at that last safety boundary.” |

The real-research status list is separate from synthetic scores. Do not stop to
read every entry during the demo. The 12-1 sector protocol was **not** run by
this toy three-period momentum example.

## Failure fallback — five seconds, then move on

If the CLI fails or is not ready within five seconds:

1. Press Ctrl+C on that attempted command.
2. Say: **“I'm switching to the prerecorded synthetic dry run. This is not a
   live result.”**
3. Open the already-staged [demo-output.txt](demo-output.txt), or run:

   ```bash
   cat demo/demo-output.txt
   ```

4. Continue the same stage narration; keep the 90-second clock running.
   The [prerecorded HTML](assets/offline-demo/index.html) shows the matching
   evidence if terminal viewing is awkward.
5. If a fresh output was shown first, explicitly identify the switch. Use only
   the matching prerecorded receipt/result afterward.

Do not debug packages, DNS, provider access, or credentials on stage. Do not
pretend a failed command succeeded. If neither fallback opens, stay on slide 7,
say the demo view is unavailable, and proceed to the risk boundary on slide 8.

If the native slide app fails, use the already-open PDF. The
[contact sheet](assets/deck-preview.png) is an overview, not an 11-page slideshow.

## Full timing map

| Slide | Time | Purpose |
| --- | --- | --- |
| 1 | 0:00–0:25 | Exact contrarian opening |
| 2 | 0:25–0:55 | Rejection, not generated trade ideas |
| 3 | 0:55–1:30 | Agent reasoning versus deterministic authority |
| 4 | 1:30–2:05 | Three scientific controls |
| 5 | 2:05–2:45 | Real research statuses and honest data gates |
| 6 | 2:45–3:30 | Actual trend metrics; no parameter rescue |
| 7 | 3:30–5:00 | Complete synthetic terminal demo |
| 8 | 5:00–5:30 | RiskGate and dry-run-only execution |
| 9 | 5:30–6:00 | Where AI adds value |
| 10 | 6:00–6:25 | Conditional roadmap |
| 11 | 6:25–6:40 | Exact closing; hold the slide |

## Guardrails for questions

- **Real findings:** [research-status.md](../docs/research-status.md) is canonical.
  Trend remains **RESEARCH MORE / near rejection**, not promoted; only frozen
  executable-close verification remains. Stock momentum/quality are data
  blocked. PEAD is deferred and untested. Sector-relative momentum has **0/18**
  scenarios run; an acquisition failure is not an economic rejection.
- **Actual risk illustration:** one BUY intent, $10,000 supplied all-cash equity,
  $2,000 order cap, $2,500 position cap, 25% concentration, positive whole shares,
  approved instruments, no leverage, and a fixed **2025-01-01** scenario clock.
  The adapter rechecks the gate. No live broker reconciliation or multi-order
  portfolio execution is claimed.
- **No external activity:** live trading disabled; Robinhood disconnected;
  Azure untouched; no production E2E, real-data acquisition, or SEC request.
- **Phase 0 unchanged:** `phase0.scheduled_recording_enabled = false`,
  `phase0.external_acceptance_complete = false`, and
  `live_execution.enabled = false` remain unchanged. Historical acceptance is
  documented evidence, not permission to activate scheduling or execution.
- **No investment claim:** synthetic scores demonstrate mechanics, not actual
  alpha. Hashes prove content linkage, not source truth or profitable returns.

Final branch: **`demo/final-presentation`**, based on the complete integration
at **`80ac885`**, with original research conclusions preserved.
