import json
from pathlib import Path
from unittest.mock import patch

import pytest
from conftest import CANDIDATE, FakeSec

from agentic_quant_lab.cli import main
from agentic_quant_lab.config import Settings

pytestmark = pytest.mark.postgres


def test_cli_ingest_verify_anchor_reconcile_and_restart(
    settings: Settings, capsys: pytest.CaptureFixture[str]
) -> None:
    client = FakeSec()

    def invoke(*args: str) -> dict:
        with (
            patch("sys.argv", ["quant-recorder", *args]),
            patch("agentic_quant_lab.cli.Settings.from_env", return_value=settings),
            patch("agentic_quant_lab.cli.SecClient", return_value=client),
        ):
            main()
        return json.loads(capsys.readouterr().out)

    first = invoke("ingest-one", CANDIDATE.document_url)
    assert first["new_filings"] == 1
    assert first["sequence"] == 2
    original = settings.ledger_path.read_bytes()
    second = invoke("ingest-one", CANDIDATE.document_url)
    assert second["new_filings"] == 0
    assert second["sequence"] == first["sequence"]
    assert second["hash"] == first["hash"]
    verified = invoke(
        "verify",
        str(settings.ledger_path),
        "--expected-head",
        first["hash"],
        "--expected-sequence",
        str(first["sequence"]),
    )
    assert verified["verified_records"] == 2
    assert invoke("reconcile")["status"] == "success"
    assert invoke("replay")["status"] == "success"
    assert settings.ledger_path.read_bytes() == original
    assert client.fetch_count == 1


def test_cli_independent_anchor_detects_valid_suffix_removal(
    settings: Settings, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    from agentic_quant_lab.ledger import Ledger
    from agentic_quant_lab.recorder import Recorder

    with Recorder(settings, FakeSec()) as recorder:
        recorder.ingest(CANDIDATE)
    records = Ledger.verify(settings.ledger_path)
    truncated = tmp_path / "truncated-test-copy.jsonl"
    truncated.write_bytes(settings.ledger_path.read_bytes().splitlines(keepends=True)[0])
    with (
        patch(
            "sys.argv",
            [
                "quant-recorder",
                "verify",
                str(truncated),
                "--expected-head",
                records[-1]["hash"],
                "--expected-sequence",
                "2",
            ],
        ),
        pytest.raises(SystemExit) as exc,
    ):
        main()
    assert exc.value.code == 1
    assert json.loads(capsys.readouterr().err)["error"] == "integrity_check_failed"
