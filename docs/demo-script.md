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

## 0:30–1:30 — Research agent → hypothesis

Run the full workflow on the prepared presenter machine, then focus on its
first two stages:

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

Point to `[1/7] Research agent` and `[2/7] Experiment`, then open the hypothesis
and experiment cards in **`demo-output/index.html`**.

> “A deterministic agent proposes a hypothesis through a replaceable interface.
> No LLM or API was called. The experiment specifies its universe, signal,
> timing, costs and constraints before calculating results.”

The symbols `DEMO_UP`, `DEMO_WEAK` and `DEMO_NULL` are fictional. The committed
fixture uses seed **20260918**. Relative Momentum is compressed **three-period
momentum skipping the latest period**, not the real sector study's **12-1** rule.

## 1:30–2:30 — Backtest + falsification

Show `[3/7] Backtest` and `[4/7] Falsification`, or their dashboard cards.

> “The existing research engine calculates returns from synthetic monthly
> valuations, with a one-period delay and 10 bps one-way cost. These are not
> executable market prices. The planted pattern makes the pipeline explainable;
> its generated return is not investment evidence.”

Point to the computed controls: null data and the no-edge candidate do not pass;
the planted-positive pattern is recovered and the weak candidate loses.
Future-available information is rejected, changing future inputs leaves earlier
decisions unchanged, and repeated calculations reproduce the same results.

> “These checks challenge the mechanics. Passing them does not validate alpha
> on real, dependent market data.”

## 2:30–3:30 — Tournament and rejected/data-blocked research

Show `[5/7] Strategy tournament`: **Demo Relative Momentum**, **Demo Trend**,
**Demo Weak** and **Demo Null**. Point to the actual rejected Weak/Null candidates.
They are synthetic contrasts, not quality or PEAD models; “SURVIVES (DEMO ONLY)”
does not mean research approval.

Then show **Real research — separate, no synthetic metrics** and
[research-status.md](research-status.md). The packaged
`src/agentic_quant_lab/resources/research_status.json` is the canonical structured
summary; generated fixture scores do not enter it.

> “ETF Trend remains RESEARCH MORE: weak NAV-proxy results versus static
> de-risking; verify actual closes, without promotion or parameter rescue.
> Research-grade stock testing is currently blocked. Price-based and guidance-text
> PEAD require low-cost data qualification; consensus-surprise and revisions
> are blocked. Overall, DEFER PEAD. Sector-relative momentum remains EXPLORATORY,
> RESEARCH MORE, acquisition still blocked: zero of eighteen scenarios ran.”

Distinguish rejected **demo** candidates from real candidates blocked by data:
missing evidence is neither zero return nor an economic rejection.

## 3:30–4:15 — Portfolio + deterministic RiskGate

Show the portfolio proposal and `[6/7] RiskGate`. Point to the allocation, cash
remainder and whole-share sizing from an initially all-cash demo snapshot.

> “A single proposed BUY passes deterministic checks for allowed symbols and
> instruments, long-only whole shares, no leverage, order/position/concentration
> limits and decision freshness. They use supplied demo state, not a broker
> account. This is not continuous live-account enforcement or a multi-order
> rebalance. Live execution is a hard-fail boundary.”

## 4:15–5:00 — Dry-run receipt and future Robinhood

Show `[7/7] Execution` and **SIMULATED / DRY RUN**: “would submit,” not
“submitted.” Open the receipt:

```sh
cat demo-output/receipt.json
```

Point to the experiment ID, input/configuration/result hashes and demo labels.

> “The timestamp is fixed scenario time, not an actual audit-event time.
> Hashing reuses the ledger utility, but demo receipts remain separate from
> Phase 0 evidence. Hashes bind content, not profitable alpha. Robinhood is
> a disabled stub; a separately authorized integration is future work.
> No broker is connected and no live capital was used.”

Presenter boundary: historical Phase 0 acceptance passed as documented, while
its constitutional acceptance and scheduling flags remain false. SEC/Azure/live
acceptance was **not rerun** here. Leave the mode banner visible; the next step
is qualifying missing research data, not claiming a profitable toy winner.
