"""Offline product walkthrough; synthetic fixtures are never research evidence."""

import argparse
import json
import random
from dataclasses import asdict
from datetime import datetime
from html import escape
from importlib.resources import files
from pathlib import Path
from typing import Any

import pandas as pd

from agentic_quant_lab.agents import DemoResearchAgent, ExperimentSpec, ResearchAgent
from agentic_quant_lab.execution import DryRunExecutionAdapter
from agentic_quant_lab.experiment import ExperimentResult, run_experiment
from agentic_quant_lab.ledger import digest
from agentic_quant_lab.portfolio import propose_portfolio
from agentic_quant_lab.risk import PortfolioSnapshot, RiskGate
from agentic_quant_lab.strategies import FixtureStrategy
from agentic_quant_lab.tournament import StrategyCandidate, rank_demo, research_candidates
from research.engine import AvailabilityError, Plan, simulate

BANNER = "MODE: DEMO | DATA: SYNTHETIC / FIXTURE | LIVE TRADING: DISABLED"


def load_fixture() -> tuple[dict[str, Any], pd.DataFrame]:
    resource = files("agentic_quant_lab").joinpath("resources/demo_fixture.json")
    fixture = json.loads(resource.read_text(encoding="utf-8"))
    rng = random.Random(fixture["seed"])
    values = [
        [
            round(value + rng.uniform(-0.05, 0.05), 6) if i < 2 else value
            for i, value in enumerate(r[1:])
        ]
        for r in fixture["prices"]
    ]
    prices = pd.DataFrame(
        values,
        index=pd.to_datetime([row[0] for row in fixture["prices"]], utc=True),
        columns=fixture["symbols"],
    )
    return fixture, prices


def demo_strategies(spec: ExperimentSpec) -> list[FixtureStrategy]:
    common = {"lookback": spec.lookback, "allocation": spec.allocation}
    return [
        FixtureStrategy(
            "demo-momentum",
            "Demo Relative Momentum",
            spec.hypothesis.rationale,
            "momentum",
            **common,
        ),
        FixtureStrategy(
            "demo-trend", "Demo Trend", "Positive trailing trend persists", "trend", **common
        ),
        FixtureStrategy(
            "demo-weak",
            "Demo Weak",
            "Deliberately losing fixture should be rejected",
            "weak",
            **common,
        ),
        FixtureStrategy(
            "demo-null", "Demo Null", "Flat fixture has no edge after costs", "null", **common
        ),
    ]


def scientific_controls(
    prices: pd.DataFrame,
    spec: ExperimentSpec,
    strategies: list[FixtureStrategy],
    results: dict[str, ExperimentResult],
) -> dict[str, bool]:
    strategy = strategies[0]
    original = results[strategy.id]
    future_plan = Plan(
        original.plan.weights,
        original.plan.available_at + pd.Timedelta(days=31),
    )
    future_rejected = False
    try:
        simulate(prices, future_plan, pd.Series(0.0, index=prices.index), fee_bps=spec.fee_bps)
    except AvailabilityError:
        future_rejected = True
    cut = len(prices) // 2
    changed = prices.copy()
    changed.iloc[cut:] *= 7
    unchanged_past = True
    repeatable = True
    for item in strategies:
        baseline = results[item.id]
        perturbed = run_experiment(item, changed, spec)
        repeat = run_experiment(item, prices, spec)
        unchanged_past &= baseline.plan.weights.iloc[:cut].equals(
            perturbed.plan.weights.iloc[:cut]
        ) and baseline.run.returns.iloc[:cut].equals(perturbed.run.returns.iloc[:cut])
        repeatable &= (
            baseline.run.returns.equals(repeat.run.returns)
            and baseline.plan.weights.equals(repeat.plan.weights)
            and baseline.metrics == repeat.metrics
        )
    flat = pd.DataFrame(100.0, index=prices.index, columns=prices.columns)
    flat_result = run_experiment(strategy, flat, spec)
    return {
        "no look-ahead: future availability rejected and future changes leave past unchanged": (
            future_rejected and unchanged_past
        ),
        "null control: flat data and no-edge candidate do not pass": (
            flat_result.metrics["total_return"] <= 0
            and results["demo-null"].metrics["total_return"] <= 0
        ),
        "planted positive signal recovered; deliberately weak candidate rejected": (
            original.metrics["total_return"] > 0.03
            and results["demo-weak"].metrics["total_return"] < 0
        ),
        "deterministic reproduction: identical plans, returns and metrics": repeatable,
    }


def run_scenario() -> dict[str, Any]:
    fixture, prices = load_fixture()
    agent: ResearchAgent = DemoResearchAgent()
    spec = agent.propose(tuple(prices.columns))
    strategies = demo_strategies(spec)
    results = {item.id: run_experiment(item, prices, spec) for item in strategies}
    controls = scientific_controls(prices, spec, strategies, results)
    if not all(controls.values()):
        raise ValueError("Scientific controls failed; no portfolio or execution is permitted")
    candidates = rank_demo(
        [
            StrategyCandidate(
                id=item.id,
                name=item.name,
                status=(
                    "SURVIVES (DEMO ONLY)"
                    if results[item.id].metrics["total_return"] > 0
                    else "REJECTED"
                ),
                metrics=results[item.id].metrics,
                evidence_quality="Planted fixture; not statistical or economic evidence",
                data_quality="SYNTHETIC / FIXTURE",
                known_limitations=(
                    "Toy in-sample demonstration; no out-of-sample inference or real promotion",
                    "Positive net fixture return is NOT a research approval gate",
                ),
                source="demo",
            )
            for item in strategies
        ]
    )
    survivor = next((c for c in candidates if c.status == "SURVIVES (DEMO ONLY)"), None)
    if survivor is None:
        raise ValueError("No surviving demo candidate; remain in cash")
    account = PortfolioSnapshot()
    target = results[survivor.id].plan.weights.iloc[-1]
    proposal = propose_portfolio(
        survivor,
        {str(k): float(v) for k, v in target.items()},
        {str(k): float(v) for k, v in prices.iloc[-1].items()},
        account,
        prices.index[-1].to_pydatetime(),
    )
    now = datetime.fromisoformat(fixture["timestamp"])
    gate = RiskGate()
    decision = gate.evaluate(proposal.intent, account, now=now)
    execution = DryRunExecutionAdapter(gate, account, now=now).submit(proposal.intent)
    intent = {
        **asdict(proposal.intent),
        "decision_at": proposal.intent.decision_at.isoformat(),
    }
    result = {
        "mode": "demo",
        "data": "SYNTHETIC / FIXTURE",
        "live_trading": "DISABLED",
        "experiment": asdict(spec),
        "controls": controls,
        "demo_candidates": [asdict(candidate) for candidate in candidates],
        "real_research": [asdict(candidate) for candidate in research_candidates()],
        "portfolio": {**asdict(proposal), "intent": intent},
        "risk": {"approved": decision.approved, "checks": decision.checks},
        "execution": asdict(execution),
        "equity_curve": [
            round(float(value), 10) for value in (1 + results[survivor.id].run.returns).cumprod()
        ],
    }
    config = {
        "experiment": asdict(spec),
        "strategies": [item.metadata for item in strategies],
        "risk_policy": asdict(gate.policy),
        "account": asdict(account),
    }
    input_hash = digest({"fixture": fixture, "realized_prices": prices.to_numpy().tolist()})
    config_hash = digest(config)
    receipt = {
        "experiment_id": "demo-" + digest([input_hash, config_hash])[:16],
        "input_hash": input_hash,
        "strategy_config_hash": config_hash,
        "result_hash": digest(result),
        "timestamp": fixture["timestamp"],
        "timestamp_kind": fixture["timestamp_kind"],
        "mode": "demo",
        "data": "SYNTHETIC / FIXTURE",
        "live_trading": "DISABLED",
        "execution": "dry_run",
    }
    return {**result, "configuration": config, "receipt": receipt}


def render_terminal(result: dict[str, Any]) -> str:
    spec = result["experiment"]
    lines = [
        "-" * 64,
        "Agentic Quant Lab — Demo Mode",
        BANNER,
        "-" * 64,
        "",
        "[1/7] Research agent (deterministic stand-in, no LLM/API)",
        f"Hypothesis: {spec['hypothesis']['title']}",
        spec["hypothesis"]["rationale"],
        "",
        "[2/7] Experiment",
        "Universe: " + " ".join(spec["universe"]) + " (fictional instruments)",
        "Signal: " + spec["signal"],
        "Rebalance: " + spec["rebalance"],
        f"Cost: {spec['fee_bps']:g} bps one-way | allocation: {spec['allocation']:.0%}",
        *["Constraint: " + constraint for constraint in spec["constraints"]],
        "",
        "[3/7] Backtest",
        "Existing deterministic research.engine.simulate on committed synthetic fixture.",
        "Monthly valuation observations; NOT executable market prices or real 12-1 results.",
        "",
        "[4/7] Falsification",
        *[f"{'PASS' if passed else 'FAIL'} {name}" for name, passed in result["controls"].items()],
        "",
        "[5/7] Strategy tournament — SYNTHETIC PERFORMANCE ONLY",
    ]
    for position, candidate in enumerate(result["demo_candidates"], 1):
        lines.append(
            f"{position}. {candidate['name']}: "
            f"net fixture return {candidate['metrics']['total_return']:+.2%}"
            f" — {candidate['status']}"
        )
    lines += [
        "",
        "REAL RESEARCH — separate evidence, never ranked against synthetic metrics:",
    ]
    for candidate in result["real_research"]:
        lines += [
            f"  {candidate['name']}: {candidate['status']}",
            f"    {candidate['data_quality']}",
            *[f"    {limitation}" for limitation in candidate["known_limitations"]],
        ]
    portfolio = result["portfolio"]
    lines += [
        "",
        f"Portfolio proposal: {portfolio['strategy_id']}",
        *[f"  Target {symbol}: {weight:.0%}" for symbol, weight in portfolio["weights"].items()],
        f"  Target cash: {portfolio['cash_weight']:.0%}; whole-share rounding leaves extra cash.",
        "",
        "[6/7] RiskGate — deterministic demo snapshot checks",
        *[
            f"{'PASS' if passed else 'FAIL'} {name}"
            for name, passed in result["risk"]["checks"].items()
        ],
        "",
        "[7/7] Execution — SIMULATED / DRY RUN ONLY",
    ]
    execution = result["execution"]
    lines += [
        f"Would submit: BUY {execution['quantity']} shares {execution['symbol']}",
        f"Estimated notional: ${execution['estimated_notional']:,.2f} (fixture reference price)",
        execution["message"],
        "",
        "Evidence receipt (separate from the Phase 0 production ledger):",
        *[f"  {name}: {value}" for name, value in result["receipt"].items()],
        "",
        "Demo complete. No live capital was used. Robinhood is not connected.",
    ]
    return "\n".join(lines)


def render_html(result: dict[str, Any]) -> str:
    def card(title: str, value: Any) -> str:
        text = value if isinstance(value, str) else json.dumps(value, indent=2, sort_keys=True)
        return f"<section><h2>{escape(title)}</h2><pre>{escape(text)}</pre></section>"

    cards = [
        card("Hypothesis", result["experiment"]["hypothesis"]),
        card("Experiment", result["experiment"]),
        card(
            "Backtest — synthetic net fixture returns",
            [{"name": row["name"], "metrics": row["metrics"]} for row in result["demo_candidates"]],
        ),
        card("Falsification — actual computed checks", result["controls"]),
        card(
            "Tournament — DEMO ONLY",
            [{"name": row["name"], "status": row["status"]} for row in result["demo_candidates"]],
        ),
        card("Portfolio proposal", result["portfolio"]),
        card("RiskGate", result["risk"]),
        card("Execution — SIMULATED / DRY RUN", result["execution"]),
        card("Evidence receipt — fixed scenario clock", result["receipt"]),
        card("Real research — separate, no synthetic metrics", result["real_research"]),
    ]
    return (
        "<!doctype html><html lang='en'><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Agentic Quant Lab — Demo</title><style>"
        "body{font:16px system-ui;margin:2rem auto;max-width:1100px;padding:0 1rem;"
        "background:#101827;color:#edf3ff}h1{font-size:2.5rem}h2{font-size:1.1rem}"
        ".badge{background:#233e37;padding:1rem;border-left:4px solid #70ebae}"
        "main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1rem}"
        "section{background:#1d293e;border-radius:12px;padding:1rem;min-width:0}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.5 monospace}"
        "</style><h1>Agentic Quant Lab</h1>"
        f"<p class='badge'>{escape(BANNER)}</p>"
        "<p>Research → Experiment → Falsification → Tournament → Portfolio → Risk → Dry Run</p>"
        "<p>Agents research. Deterministic code calculates, controls risk, and executes.</p>"
        "<p>This demo agent is scripted. Fixture performance is planted, not investment evidence. "
        "No broker, external assets, telemetry or network calls.</p><main>"
        + "".join(cards)
        + "</main><footer><p>No live capital was used. Robinhood: future, not connected.</p>"
        "</footer></html>\n"
    )


def write_outputs(result: dict[str, Any], destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in (("receipt.json", result["receipt"]), ("result.json", result)):
        (destination / name).write_text(
            json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    (destination / "index.html").write_text(render_html(result), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic Quant Lab — offline synthetic demo")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Run locally; no network, credentials or live trading")
    demo.add_argument("--output-dir", type=Path, default=Path("demo-output"))
    demo.add_argument(
        "--reset",
        action="store_true",
        help="Regenerate the same three demo outputs; no state or unrelated files are deleted",
    )
    args = parser.parse_args()
    try:
        result = run_scenario()
        write_outputs(result, args.output_dir)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"{BANNER}\nDemo stopped: {exc}\n")
    print(render_terminal(result))
    print(f"\nLocal report: {args.output_dir / 'index.html'}")
    print(f"Receipt: {args.output_dir / 'receipt.json'}")


if __name__ == "__main__":
    main()
