import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest

from agentic_quant_lab.cli import main
from agentic_quant_lab.config import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url="postgresql:///unused",
        ledger_path=tmp_path / "unused.jsonl",
        sec_user_agent="quant-tests test@example.invalid",
        heartbeat_url="https://example.invalid/heartbeat",
    )


def test_heartbeat_contains_committed_head(settings: Settings) -> None:
    recorder = MagicMock()
    recorder.__enter__.return_value = recorder
    recorder.record.return_value = 2
    recorder.ledger.records = [{"sequence": 5, "hash": "a" * 64}]
    with (
        patch("sys.argv", ["quant-recorder", "record"]),
        patch("agentic_quant_lab.cli.Settings.from_env", return_value=settings),
        patch("agentic_quant_lab.cli.Recorder", return_value=recorder),
        patch("agentic_quant_lab.cli.build_opener") as opener,
    ):
        main()
        request = opener.return_value.open.call_args.args[0]
        assert request.method == "POST"
        assert json.loads(request.data) == {"new_filings": 2, "sequence": 5, "hash": "a" * 64}


def test_failed_record_does_not_send_success_heartbeat(settings: Settings) -> None:
    recorder = MagicMock()
    recorder.__enter__.return_value = recorder
    recorder.record.side_effect = URLError("SEC unavailable")
    with (
        patch("sys.argv", ["quant-recorder", "record"]),
        patch("agentic_quant_lab.cli.Settings.from_env", return_value=settings),
        patch("agentic_quant_lab.cli.Recorder", return_value=recorder),
        patch("agentic_quant_lab.cli.build_opener") as opener,
        pytest.raises(URLError),
    ):
        main()
    opener.assert_not_called()
