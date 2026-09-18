# Agentic Quant Lab: five-minute demo

**Audience takeaway:** strategy agents propose experiments; deterministic code
calculates, challenges, compares and risk-checks them before dry-run execution.
The product vision is a disciplined research workflow, **not a claim of profitable
alpha**. Today the agent is deterministic, the data is synthetic and Robinhood
is not connected.

## Before presenting — outside the five minutes

Use the repository root with **Python 3.12 and uv**. Prepare the environment while
Python, build dependencies and packages are available:

```sh
uv sync
uv run aql demo
```

Installation can require a network. Do not promise a cold offline install with
missing packages. The demo runtime itself needs no network, SEC contact,
PostgreSQL, Azure credentials, market-data account or broker account.

Once installed, rehearse the guaranteed-offline invocation:

```sh
uv run --offline --no-sync aql demo
```

If uv's cache is unavailable but the installed `.venv` is intact, use the
preinstalled entry point directly, with no network:

```sh
.venv/bin/aql demo
```

Preinstallation is mandatory for both offline commands. Keep
`demo-output/index.html` ready in a local browser tab; it needs no web server.
Keep `demo-output/receipt.json` available for inspection. The detailed companion
is `demo-output/result.json`.

For a clean repeat, the normal command is:

```sh
uv run aql demo --reset
```

Offline, use `uv run --offline --no-sync aql demo --reset` or
`.venv/bin/aql demo --reset`. Normal reruns deterministically overwrite the owned
outputs; `--reset` regenerates those same files only. It does not remove unrelated
files or touch a research archive or the Phase 0 ledger. No cloud, real-data
acquisition or historical acceptance commands belong in this presentation.

## 0:00–0:30 — Product vision

Show the README's vertical flow.

> “Agentic Quant Lab turns strategy ideas into explicit experiments, tests the
> assumptions, compares candidates and passes a portfolio proposal through risk
> checks. Evidence travels with the result. We are demonstrating that workflow,
> not presenting a discovered profitable strategy.”

Say immediately: **“Deterministic agent today; LLM-backed research is future work.
Synthetic fixtures only; live trading is disabled.”**

## 0:30–1:30 — Run the seven-stage workflow

On the prepared presenter machine:

```sh
uv run --offline --no-sync aql demo
```

The ordinary Quick Demo command is `uv run aql demo`. If uv is unavailable or its
cache causes trouble, use `.venv/bin/aql demo`—do not try a network installation
during the offline presentation.

Point to the banner:

```text
MODE: DEMO | DATA: SYNTHETIC / FIXTURE | LIVE TRADING: DISABLED
```

Walk down the actual stages:

| Stage | Say |
| --- | --- |
| `[1/7]` Research agent | “A deterministic implementation proposes a hypothesis through a replaceable agent interface. No LLM or API was called.” |
| `[2/7]` Experiment | “The universe, signal, timing, costs and constraints are explicit.” |
| `[3/7]` Backtest | “The existing research engine runs on synthetic monthly valuations, with one-period delay and 10 bps one-way cost.” |
| `[4/7]` Falsification | “Null and planted-positive controls, future-availability rejection, future-perturbation invariance and deterministic reproduction challenge the mechanics.” |
| `[5/7]` Strategy tournament | “Relative Momentum, Trend, Weak and Null compete only on the fixture; a portfolio proposal follows.” |
| `[6/7]` RiskGate | “A single proposed BUY is checked against an explicitly supplied demo snapshot.” |
| `[7/7]` Execution + evidence | “This says ‘would submit,’ not ‘submitted.’ A dry-run result and local evidence files are produced.” |

## 1:30–2:30 — Dashboard, tournament and portfolio

Open **`demo-output/index.html`** locally. Show the hypothesis, experiment,
backtest, falsification, tournament and portfolio cards.

> “The instruments are fictional: DEMO_UP, DEMO_WEAK and DEMO_NULL. The committed
> fixture uses seed 20260918. Relative Momentum is compressed three-period
> momentum skipping the latest period—not the real sector study's 12-1 rule.
> The planted pattern makes the pipeline explainable; it is not market evidence.”

Point out **Demo Relative Momentum**, **Demo Trend**, **Demo Weak** and
**Demo Null**. Weak and Null are deliberate synthetic contrasts, not real quality
or PEAD models. Do not quote a generated return as an expected investment return
or treat “SURVIVES (DEMO ONLY)” as research approval.

Show the allocation and cash remainder. This is a single demo sleeve with
whole-share sizing from an initially all-cash snapshot, not account synchronization,
automatic diversification or a live multi-order rebalance.

## 2:30–3:30 — Risk and the evidence receipt

Show the RiskGate checks and the **SIMULATED / DRY RUN** execution card.

> “Allowed symbols and instruments, long-only whole-share BUY, no leverage,
> position/order/concentration limits and decision freshness are checked against
> supplied state. This is not continuous risk enforcement on a live account.
> Live execution is a hard-fail boundary, and the Robinhood stub is disabled.”

Open the receipt or display it:

```sh
cat demo-output/receipt.json
```

Point to `experiment_id`, `input_hash`, `strategy_config_hash`, `result_hash`,
the timestamp and the demo/dry-run labels.

> “The clock is fixed scenario time so repeated outputs are deterministic.
> It is not the actual time of an audit event or this command. Hashing reuses the
> existing ledger utility, but this receipt is separate from the Phase 0 ledger.
> A matching hash binds content; it does not prove profitable alpha.”

## 3:30–4:30 — Real research, kept separate

Show **Real research — separate, no synthetic metrics** and open
[research-status.md](research-status.md) for the precise report verdicts.
The packaged `src/agentic_quant_lab/resources/research_status.json` is the
canonical structured summary, not generated fixture performance.

> “Modern ETF Trend is RESEARCH MORE, narrowly for executable-close verification.
> NAV-proxy results are weak versus static de-risking; there is no paper/shadow
> promotion or parameter rescue. Research-grade stock testing is currently
> blocked by data qualification. Price-based and guidance-text PEAD require
> low-cost data qualification; consensus-surprise and revision momentum are
> blocked. Overall, defer PEAD. Sector-relative momentum is exploratory,
> research more, acquisition still blocked: zero of eighteen scenarios ran.”

No available data is not a zero return or an economic rejection. Historical
Phase 0 SEC acceptance passed as documented, but the constitutional acceptance
flag and scheduling flag remain false. That historical acceptance—and all
SEC/Azure/live activity—was **not rerun** for this demo.

## 4:30–5:00 — Close with the honest next step

> “We have an evidence-first research workflow, a reproducible synthetic demo
> and explicit reasons real candidates remain unqualified. Next comes the
> missing data verification, not optimizing away a failed comparison. LLM agents
> and a separately authorized Robinhood integration are future extensions.
> Today, no broker is connected and no live capital is used.”

Leave the dashboard's mode banner visible. Do not end with a fictional winner's
return, a claim of validated alpha or a suggestion that changing one flag would
make this production-ready.
