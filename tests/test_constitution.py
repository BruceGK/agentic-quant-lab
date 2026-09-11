from unittest.mock import patch

import pytest

from agentic_quant_lab.cli import main
from agentic_quant_lab.constitution import check_recording_policy, constitution


def test_constitution_keeps_risk_and_scheduler_disabled() -> None:
    policy = constitution()
    assert policy["project"] == {"weekly_hours_budget": 6, "total_hours_before_review": 120}
    assert policy["live_execution"]["enabled"] is False
    assert policy["live_execution"]["requires_compliance_review"] is True
    assert policy["compliance"]["automated_trading_allowed"] == "unknown"
    assert not policy["compliance"]["insider_trading_policy_reviewed"]
    assert not policy["compliance"]["restricted_trading_policy_reviewed"]
    assert policy["phase0"]["scheduled_recording_enabled"] is False
    assert policy["phase0"]["external_acceptance_complete"] is False
    assert policy["research"]["real_alpha_research_enabled"] is False


@pytest.mark.parametrize("mode", ["local", "acceptance"])
def test_manual_modes_do_not_enable_scheduled_recording(mode: str) -> None:
    check_recording_policy(mode)
    with pytest.raises(ValueError, match="Scheduled recording is disabled"):
        check_recording_policy("scheduled")


def test_scheduled_command_is_blocked_before_any_credentials_or_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RECORDER_RUN_MODE", "scheduled")
    with (
        patch("sys.argv", ["quant-recorder", "record"]),
        patch("agentic_quant_lab.cli.Settings.from_env") as settings,
        pytest.raises(SystemExit),
    ):
        main()
    settings.assert_not_called()
