import json
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
    assert result["receipt"]["strategy_config_hash"] == digest(result["configuration"])
    payload = {
        key: value for key, value in result.items() if key not in ("receipt", "configuration")
    }
    assert result["receipt"]["result_hash"] == digest(payload)
    fixture, prices = load_fixture()
    assert result["receipt"]["input_hash"] == digest(
        {"fixture": fixture, "realized_prices": prices.to_numpy().tolist()}
    )
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
    monkeypatch.setattr(sys, "argv", ["aql", "demo", "--reset", "--output-dir", str(tmp_path)])
    main()
    assert capsys.readouterr().out == first
    assert outputs == {name: (tmp_path / name).read_bytes() for name in outputs}
    assert marker.read_text() == "keep me"
    assert set(outputs) == {"index.html", "receipt.json", "result.json"}
    assert json.loads(outputs["receipt.json"])["execution"] == "dry_run"


def test_installed_entrypoint_twice_in_network_blocked_process(tmp_path: Path) -> None:
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
    command = [sys.executable, "-c", code, "demo", "--output-dir", str(tmp_path)]
    first = subprocess.run(command, check=True, capture_output=True, text=True, cwd=tmp_path)
    receipt = (tmp_path / "receipt.json").read_bytes()
    second = subprocess.run(
        command + ["--reset"], check=True, capture_output=True, text=True, cwd=tmp_path
    )
    assert first.stdout == second.stdout
    assert not first.stderr and not second.stderr
    assert "Demo complete. No live capital was used." in first.stdout
    assert receipt == (tmp_path / "receipt.json").read_bytes()
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
    "change",
    [
        {"mode": "live"},
        {"mode": "paper"},
        {"symbol": "UNKNOWN"},
        {"instrument_type": "option"},
        {"quantity": -1},
        {"quantity": 0},
        {"quantity": 1.5},
        {"quantity": True},
        {"side": "SELL"},
        {"reference_price": -1},
        {"reference_price": float("nan")},
        {"reference_price": float("inf")},
        {"quantity": 11},
        {"decision_at": NOW - timedelta(days=3)},
        {"decision_at": NOW + timedelta(seconds=1)},
        {"decision_at": NOW.replace(tzinfo=None)},
    ],
)
def test_gate_and_adapter_reject_unsafe_intent(change: dict[str, Any]) -> None:
    intent = replace(INTENT, **change)
    gate = RiskGate()
    assert not gate.evaluate(intent, PortfolioSnapshot(), now=NOW).approved
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


@pytest.mark.parametrize("flag", [False, True])
def test_live_execution_is_impossible_even_with_policy_flag(flag: bool) -> None:
    gate = RiskGate(RiskPolicy(live_execution_enabled=flag))
    assert not gate.evaluate(replace(INTENT, mode="live"), PortfolioSnapshot(), now=NOW).approved
    if flag:
        assert not gate.evaluate(INTENT, PortfolioSnapshot(), now=NOW).approved
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
    receipt = DryRunExecutionAdapter(gate, account, now=NOW).submit(INTENT)
    assert receipt.status == "SIMULATED / DRY RUN"
    assert receipt.mode == "demo" and receipt.live_trading == "DISABLED"
    assert receipt.estimated_notional == 1920
    assert receipt.intent_hash == digest(
        {**asdict(INTENT), "decision_at": INTENT.decision_at.isoformat()}
    )
    account.position_notionals["DEMO_UP"] = 1_000
    with pytest.raises(DisabledExecutionError):
        DryRunExecutionAdapter(gate, account, now=NOW).submit(INTENT)


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
