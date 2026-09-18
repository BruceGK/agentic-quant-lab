import json
import re
import socket
import subprocess
import sys
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from agentic_quant_lab.agents import DemoResearchAgent
from agentic_quant_lab.demo import (
    BANNER,
    demo_strategies,
    load_fixture,
    main,
    render_html,
    render_terminal,
    run_scenario,
)
from agentic_quant_lab.execution import (
    DisabledExecutionError,
    DryRunExecutionAdapter,
    RobinhoodExecutionAdapter,
)
from agentic_quant_lab.experiment import run_experiment
from agentic_quant_lab.ledger import digest
from agentic_quant_lab.portfolio import propose_portfolio
from agentic_quant_lab.risk import OrderIntent, PortfolioSnapshot, RiskGate, RiskPolicy
from agentic_quant_lab.tournament import rank_demo, research_candidates
from research.engine import AvailabilityError, Plan, simulate

NOW = datetime(2025, 1, 1, tzinfo=UTC)
INTENT = OrderIntent("DEMO_UP", 10, 192, NOW - timedelta(days=1), "demo-momentum")


@pytest.fixture
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("The demo must never use network or DNS")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    for name in ("DATABASE_URL", "SEC_USER_AGENT", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"):
        monkeypatch.delenv(name, raising=False)


def test_scenario_offline_and_receipt_hashes(offline: None) -> None:
    result = run_scenario()
    assert result == run_scenario()
    assert all(result["controls"].values())
    assert result["risk"]["approved"]
    assert result["receipt"]["timestamp_kind"] == "fixed scenario clock, not wall-clock execution"
    assert result["receipt"]["experiment_hash"] == digest(result["experiment"])
    assert result["receipt"]["strategy_config_hash"] == digest(result["configuration"])
    payload = {
        key: value for key, value in result.items() if key not in ("receipt", "configuration")
    }
    assert result["receipt"]["result_hash"] == digest(payload)
    fixture, prices = load_fixture()
    assert result["receipt"]["input_hash"] == digest(
        {"fixture": fixture, "realized_prices": prices.to_numpy().tolist()}
    )
    assert (
        result["receipt"]["experiment_id"]
        == "demo-"
        + digest([result["receipt"]["input_hash"], result["receipt"]["strategy_config_hash"]])[:16]
    )
    assert result["receipt"]["mode"] == "demo"
    assert result["receipt"]["execution"] == "dry_run"
    assert result["receipt"]["live_trading"] == "DISABLED"
    assert result["execution"]["quantity"] == 10
    assert result["execution"]["estimated_notional"] == 1919.92
    assert {c["id"] for c in result["demo_candidates"] if c["status"] == "REJECTED"} == {
        "demo-weak",
        "demo-null",
    }
    assert BANNER in render_terminal(result)
    assert BANNER in render_html(result)
    assert all(c["source"] == "real_research" and not c["metrics"] for c in result["real_research"])
    assert "input_hash" in render_terminal(result)
    assert "result_hash" in render_html(result)


def test_seven_stages_and_explicit_safety_labels(offline: None) -> None:
    result = run_scenario()
    terminal, html = render_terminal(result), render_html(result)
    for label in (
        "MODE: DEMO",
        "DATA: SYNTHETIC FIXTURE",
        "LIVE TRADING: DISABLED",
        "EXECUTION: DRY RUN",
    ):
        assert label in terminal and label in html
    expected = (
        "Research agent",
        "Experiment",
        "Backtest",
        "Falsification",
        "Strategy tournament",
        "RiskGate",
        "Execution",
    )
    headings = re.findall(r"^\[(\d)/7\] (.+)$", terminal, re.MULTILINE)
    assert [number for number, _ in headings] == [str(number) for number in range(1, 8)]
    for number, ((_, heading), title) in enumerate(zip(headings, expected, strict=True), 1):
        assert heading.startswith(title)
        assert f"<h2>{number}. {title}" in html
    assert terminal.index("[5/7]") < terminal.index("Portfolio proposal:") < terminal.index("[6/7]")
    assert html.index("<h2>5.") < html.index("<h2>Portfolio proposal") < html.index("<h2>6.")
    assert "scripted" in terminal and "no live LLM/API" in terminal
    assert "scripted" in html and "not a live LLM" in html


def test_cli_reset_is_repeatable_and_preserves_unrelated_files(
    offline: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["aql", "demo", "--output-dir", str(tmp_path)])
    main()
    first = capsys.readouterr().out
    outputs = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    marker = tmp_path / "unrelated.txt"
    marker.write_text("keep me")
    nested = tmp_path / "unrelated"
    nested.mkdir()
    nested_marker = nested / "notes.txt"
    nested_marker.write_text("keep this too")
    for reset in (False, True, True):
        flags = ["--reset"] if reset else []
        monkeypatch.setattr(sys, "argv", ["aql", "demo", *flags, "--output-dir", str(tmp_path)])
        main()
        assert capsys.readouterr().out == first
        assert outputs == {name: (tmp_path / name).read_bytes() for name in outputs}
        assert marker.read_text() == "keep me"
        assert nested_marker.read_text() == "keep this too"
    assert set(outputs) == {"index.html", "receipt.json", "result.json"}
    assert json.loads(outputs["receipt.json"])["execution"] == "dry_run"


@pytest.mark.parametrize("output_dir", [None, "reports/offline-demo"])
def test_cli_preserves_relative_output_paths_across_working_directories(
    offline: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    output_dir: str | None,
) -> None:
    destination = Path("demo-output" if output_dir is None else output_dir)
    flags = [] if output_dir is None else ["--output-dir", output_dir]
    runs: list[tuple[str, dict[str, bytes]]] = []
    for name in ("first-checkout", "different-checkout"):
        directory = tmp_path / name
        directory.mkdir()
        monkeypatch.chdir(directory)
        monkeypatch.setattr(sys, "argv", ["aql", "demo", *flags])
        main()
        output = capsys.readouterr()
        assert not output.err
        assert output.out.endswith(
            f"\nLocal report: {destination / 'index.html'}\n"
            f"Receipt: {destination / 'receipt.json'}\n"
        )
        assert str(directory) not in output.out
        artifacts = {
            name: (destination / name).read_bytes()
            for name in ("index.html", "receipt.json", "result.json")
        }
        runs.append((output.out, artifacts))
    assert runs[0] == runs[1]


def test_installed_entrypoint_twice_in_network_blocked_process(
    offline: None, tmp_path: Path
) -> None:
    code = """
import sys
def no_network(event, args):
    if event.startswith("socket."):
        raise RuntimeError("Network disabled for demo test")
sys.addaudithook(no_network)
from importlib.metadata import entry_points
sys.argv[0] = "aql"
next(iter(entry_points(group="console_scripts", name="aql"))).load()()
"""
    command = [sys.executable, "-c", code, "demo"]
    first = subprocess.run(command, check=True, capture_output=True, text=True, cwd=tmp_path)
    destination = tmp_path / "demo-output"
    outputs = {path.name: path.read_bytes() for path in destination.iterdir()}
    for flags in ([], ["--reset"]):
        repeat = subprocess.run(
            command + flags, check=True, capture_output=True, text=True, cwd=tmp_path
        )
        assert first.stdout == repeat.stdout
        assert not first.stderr and not repeat.stderr
        assert outputs == {name: (destination / name).read_bytes() for name in outputs}
    assert "Demo complete. No live capital was used." in first.stdout
    assert set(outputs) == {"index.html", "receipt.json", "result.json"}
    assert (
        next(iter(entry_points(group="console_scripts", name="aql"))).value
        == "agentic_quant_lab.demo:main"
    )


def test_future_information_rejected() -> None:
    _, prices = load_fixture()
    spec = DemoResearchAgent().propose(tuple(prices.columns))
    strategy = demo_strategies(spec)[0]
    plan = strategy.build_target(prices)
    late = Plan(plan.weights, plan.available_at + pd.Timedelta(days=1))
    with pytest.raises(AvailabilityError, match="unavailable"):
        simulate(prices, late, pd.Series(0.0, index=prices.index), fee_bps=10)
    with pytest.raises(AvailabilityError, match="same close"):
        simulate(prices, plan, pd.Series(0.0, index=prices.index), fee_bps=10, delay=0)


def test_controls_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentic_quant_lab.demo.scientific_controls", lambda *args: {"null": False})
    with pytest.raises(ValueError, match="Scientific controls failed"):
        run_scenario()


def test_cli_reports_risk_rejection_without_writing_outputs(
    offline: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    destination = tmp_path / "denied-demo"
    monkeypatch.setattr(sys, "argv", ["aql", "demo", "--output-dir", str(destination)])
    monkeypatch.setattr(
        "agentic_quant_lab.risk.constitution", lambda: {"live_execution": {"enabled": True}}
    )
    with pytest.raises(SystemExit) as stopped:
        main()
    assert stopped.value.code == 1
    output = capsys.readouterr()
    assert not output.out
    assert BANNER in output.err
    assert "Demo stopped: Intent rejected: live execution disabled" in output.err
    assert not destination.exists()


def test_costs_are_real_and_bad_candidates_are_not_portfolios() -> None:
    _, prices = load_fixture()
    spec = DemoResearchAgent().propose(tuple(prices.columns))
    strategy = demo_strategies(spec)[0]
    gross = run_experiment(strategy, prices, replace(spec, fee_bps=0))
    net = run_experiment(strategy, prices, spec)
    assert net.metrics["total_return"] < gross.metrics["total_return"]
    assert net.metrics["sum_period_costs"] > 0
    candidate = research_candidates()[1]
    with pytest.raises(ValueError, match="never rank real"):
        rank_demo([candidate])
    with pytest.raises(ValueError, match="surviving demo"):
        propose_portfolio(candidate, {"DEMO_UP": 0.2}, {"DEMO_UP": 192}, PortfolioSnapshot(), NOW)


@pytest.mark.parametrize(
    ("change", "failed_check"),
    [
        ({"mode": "live"}, "dry_run mode"),
        ({"mode": "paper"}, "dry_run mode"),
        ({"symbol": "UNKNOWN"}, "allowed symbol"),
        ({"instrument_type": "option"}, "allowed instrument"),
        ({"quantity": -1}, "positive whole-share long-only BUY"),
        ({"quantity": 0}, "positive whole-share long-only BUY"),
        ({"quantity": 1.5}, "positive whole-share long-only BUY"),
        ({"quantity": True}, "positive whole-share long-only BUY"),
        ({"side": "SELL"}, "positive whole-share long-only BUY"),
        ({"reference_price": 0}, "positive whole-share long-only BUY"),
        ({"reference_price": -1}, "positive whole-share long-only BUY"),
        ({"reference_price": float("nan")}, "positive whole-share long-only BUY"),
        ({"reference_price": float("inf")}, "positive whole-share long-only BUY"),
        ({"quantity": 11}, "maximum order notional"),
        ({"decision_at": NOW - timedelta(days=3)}, "fresh strategy decision"),
        ({"decision_at": NOW + timedelta(seconds=1)}, "fresh strategy decision"),
        ({"decision_at": NOW.replace(tzinfo=None)}, "fresh strategy decision"),
    ],
)
def test_gate_and_adapter_reject_unsafe_intent(change: dict[str, Any], failed_check: str) -> None:
    intent = replace(INTENT, **change)
    gate = RiskGate()
    decision = gate.evaluate(intent, PortfolioSnapshot(), now=NOW)
    assert not decision.approved
    assert not decision.checks[failed_check]
    with pytest.raises(DisabledExecutionError):
        DryRunExecutionAdapter(gate, PortfolioSnapshot(), now=NOW).submit(intent)


@pytest.mark.parametrize(
    "account",
    [
        PortfolioSnapshot(equity=0),
        PortfolioSnapshot(cash=float("nan")),
        PortfolioSnapshot(cash=9_000),
        PortfolioSnapshot(cash=1_000, position_notionals={"DEMO_WEAK": 9_000}),
        PortfolioSnapshot(cash=9_000, position_notionals={"DEMO_UP": 1_000}),
        PortfolioSnapshot(cash=10_001, position_notionals={"DEMO_UP": -1}),
    ],
)
def test_gate_rejects_unsafe_snapshot(account: PortfolioSnapshot) -> None:
    assert not RiskGate().evaluate(INTENT, account, now=NOW).approved


@pytest.mark.parametrize(
    ("policy", "account", "failed_check"),
    [
        (RiskPolicy(max_order_notional=1919.99), PortfolioSnapshot(), "maximum order notional"),
        (
            RiskPolicy(max_position_notional=1919.99),
            PortfolioSnapshot(),
            "maximum position notional",
        ),
        (RiskPolicy(max_concentration=0.1), PortfolioSnapshot(), "maximum concentration"),
        (
            RiskPolicy(max_concentration=1),
            PortfolioSnapshot(cash=1000, position_notionals={"DEMO_WEAK": 9000}),
            "no leverage",
        ),
        (
            RiskPolicy(max_decision_age_seconds=86_399),
            PortfolioSnapshot(),
            "fresh strategy decision",
        ),
    ],
)
def test_each_risk_limit_is_enforced_independently(
    policy: RiskPolicy, account: PortfolioSnapshot, failed_check: str
) -> None:
    gate = RiskGate(policy)
    decision = gate.evaluate(INTENT, account, now=NOW)
    assert {name for name, passed in decision.checks.items() if not passed} == {failed_check}
    with pytest.raises(DisabledExecutionError, match=failed_check):
        DryRunExecutionAdapter(gate, account, now=NOW).submit(INTENT)


@pytest.mark.parametrize(
    ("intent", "account"),
    [
        (replace(INTENT, reference_price=200), PortfolioSnapshot()),
        (INTENT, PortfolioSnapshot(cash=9420, position_notionals={"DEMO_UP": 580})),
        (replace(INTENT, decision_at=NOW - timedelta(days=2)), PortfolioSnapshot()),
        (replace(INTENT, decision_at=NOW), PortfolioSnapshot()),
    ],
)
def test_risk_limits_accept_exact_boundaries(
    intent: OrderIntent, account: PortfolioSnapshot
) -> None:
    gate = RiskGate()
    assert gate.evaluate(intent, account, now=NOW).approved
    assert DryRunExecutionAdapter(gate, account, now=NOW).submit(intent).mode == "demo"


@pytest.mark.parametrize("flag", [False, True])
def test_live_execution_is_impossible_even_with_policy_flag(flag: bool) -> None:
    gate = RiskGate(RiskPolicy(live_execution_enabled=flag))
    for mode in ("live", "paper"):
        intent = replace(INTENT, mode=mode)
        assert not gate.evaluate(intent, PortfolioSnapshot(), now=NOW).approved
        with pytest.raises(DisabledExecutionError):
            DryRunExecutionAdapter(gate, PortfolioSnapshot(), now=NOW).submit(intent)
    if flag:
        assert not gate.evaluate(INTENT, PortfolioSnapshot(), now=NOW).approved
        with pytest.raises(DisabledExecutionError, match="live execution disabled"):
            DryRunExecutionAdapter(gate, PortfolioSnapshot(), now=NOW).submit(INTENT)
    with pytest.raises(DisabledExecutionError, match="not connected"):
        RobinhoodExecutionAdapter().submit(INTENT)


def test_constitution_change_cannot_enable_demo_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "agentic_quant_lab.risk.constitution", lambda: {"live_execution": {"enabled": True}}
    )
    with pytest.raises(DisabledExecutionError):
        DryRunExecutionAdapter(RiskGate(), PortfolioSnapshot(), now=NOW).submit(INTENT)


def test_dry_run_receipt_and_revalidation() -> None:
    account = PortfolioSnapshot()
    gate = RiskGate()
    assert gate.evaluate(INTENT, account, now=NOW).approved
    adapter = DryRunExecutionAdapter(gate, account, now=NOW)
    receipt = adapter.submit(INTENT)
    assert receipt.status == "SIMULATED / DRY RUN"
    assert receipt.mode == "demo" and receipt.live_trading == "DISABLED"
    assert receipt.estimated_notional == 1920
    assert receipt.intent_hash == digest(
        {**asdict(INTENT), "decision_at": INTENT.decision_at.isoformat()}
    )
    account.position_notionals["DEMO_UP"] = 1_000
    with pytest.raises(DisabledExecutionError):
        adapter.submit(INTENT)


@pytest.mark.parametrize("limit", [0, -1, float("nan"), float("inf")])
def test_invalid_risk_limits_rejected(limit: float) -> None:
    with pytest.raises(ValueError):
        RiskPolicy(max_order_notional=limit)


def test_html_has_no_remote_assets_and_escapes_text(offline: None) -> None:
    result = run_scenario()
    result["experiment"]["hypothesis"]["title"] = "<script>alert(1)</script>"
    html = render_html(result)
    assert "<script" not in html and "&lt;script&gt;" in html
    assert "src=" not in html and "<link" not in html
    assert "Robinhood: future, not connected" in html


def test_readme_command_matches_installed_cli() -> None:
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text()
    assert "uv sync\nuv run aql demo" in readme
    assert "uv run --offline --no-sync aql demo" in readme
