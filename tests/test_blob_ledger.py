import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import psycopg
import pytest
from azure.core.exceptions import ResourceExistsError, ServiceResponseError
from conftest import CANDIDATE, FakeSec

from agentic_quant_lab.blob_ledger import BlobLedger
from agentic_quant_lab.cli import main
from agentic_quant_lab.config import BlobSettings, Settings
from agentic_quant_lab.ledger import Ledger, LedgerError, canonical, digest, export_records
from agentic_quant_lab.recorder import Recorder

BLOB_SETTINGS = BlobSettings("https://aqltest.blob.core.windows.net")


class MemoryContainer:
    def __init__(self) -> None:
        self.blobs: dict[str, bytes] = {}
        self.upload_options: list[dict[str, Any]] = []
        self.failure: Exception | None = None
        self.commit_before_failure = False

    def list_blobs(self, *, name_starts_with: str) -> list[SimpleNamespace]:
        return [
            SimpleNamespace(name=name)
            for name in reversed(self.blobs)
            if name.startswith(name_starts_with)
        ]

    def download_blob(self, name: str) -> SimpleNamespace:
        return SimpleNamespace(readall=lambda: self.blobs[name])

    def upload_blob(self, name: str, data: bytes, **options: Any) -> None:
        self.upload_options.append(options)
        assert options["overwrite"] is False
        if name in self.blobs:
            raise ResourceExistsError("synthetic sequence collision")
        if self.failure is None or self.commit_before_failure:
            self.blobs[name] = data
        if self.failure:
            raise self.failure

    def close(self) -> None:
        pass


@pytest.fixture
def container():
    client = MemoryContainer()
    with (
        patch("agentic_quant_lab.blob_ledger.ContainerClient", return_value=client),
        patch("agentic_quant_lab.blob_ledger.azure_credential", return_value=MagicMock()),
    ):
        yield client


def test_blob_chain_roundtrip_and_independent_jsonl_export(
    container: MemoryContainer, tmp_path: Path
) -> None:
    with BlobLedger(BLOB_SETTINGS) as ledger:
        first = ledger.append("universe", {"ciks": ["320193"]})
        second = ledger.append("universe", {"ciks": ["789019"]})
        assert second["prev_hash"] == first["hash"]
        assert ledger.read_records() == ledger.records
        records = list(ledger.records)
    with BlobLedger(BLOB_SETTINGS) as reopened:
        assert reopened.records == records
    assert list(container.blobs) == [
        "sec/records/00000000000000000001.jsonl",
        "sec/records/00000000000000000002.jsonl",
    ]
    destination = tmp_path / "restored.jsonl"
    export_records(records, destination)
    assert Ledger.verify(destination) == records
    assert destination.read_bytes() == b"".join(container.blobs.values())
    with pytest.raises(FileExistsError):
        export_records(records, destination)


@pytest.mark.parametrize("corruption", ["content", "tail", "missing", "unexpected"])
def test_blob_corruption_fails_closed(container: MemoryContainer, corruption: str) -> None:
    with BlobLedger(BLOB_SETTINGS) as ledger:
        ledger.append("universe", {"ciks": ["1"]})
        ledger.append("universe", {"ciks": ["2"]})
    first = "sec/records/00000000000000000001.jsonl"
    if corruption == "content":
        record = json.loads(container.blobs[first])
        record["payload"]["ciks"] = ["3"]
        container.blobs[first] = canonical(record) + b"\n"
    elif corruption == "tail":
        container.blobs[first] = container.blobs[first][:-1]
    elif corruption == "missing":
        del container.blobs[first]
    else:
        container.blobs["sec/records/unexpected.jsonl"] = container.blobs[first]
    original = dict(container.blobs)
    with pytest.raises(LedgerError), BlobLedger(BLOB_SETTINGS):
        pass
    assert container.blobs == original


def test_concurrent_blob_writers_cannot_fork_sequence(container: MemoryContainer) -> None:
    with BlobLedger(BLOB_SETTINGS) as first, BlobLedger(BLOB_SETTINGS) as second:
        winner = first.append("universe", {"ciks": ["1"]})
        with pytest.raises(LedgerError, match="sequence already exists"):
            second.append("universe", {"ciks": ["2"]})
        with pytest.raises(LedgerError, match="prior write failed"):
            second.append("universe", {"ciks": ["3"]})
        assert second.records == []
    with BlobLedger(BLOB_SETTINGS) as reopened:
        assert reopened.records == [winner]


def test_blob_records_can_exceed_legacy_append_block_limit(container: MemoryContainer) -> None:
    payload = {"synthetic": "x" * (4 * 1024 * 1024 + 1)}
    with BlobLedger(BLOB_SETTINGS) as ledger:
        record = ledger.append("universe", payload)
        assert ledger.read_records() == [record]


@pytest.mark.parametrize("committed", [False, True])
def test_failed_or_ambiguous_upload_requires_reopen(
    container: MemoryContainer, committed: bool
) -> None:
    container.failure = ServiceResponseError("synthetic lost acknowledgement")
    container.commit_before_failure = committed
    with BlobLedger(BLOB_SETTINGS) as ledger:
        with pytest.raises(ServiceResponseError):
            ledger.append("universe", {"ciks": ["1"]})
        assert ledger.records == []
        with pytest.raises(LedgerError, match="prior write failed"):
            ledger.append("universe", {"ciks": ["2"]})
    container.failure = None
    with BlobLedger(BLOB_SETTINGS) as ledger:
        assert len(ledger.records) == int(committed)


def test_offline_blob_verification_and_anchored_export(
    container: MemoryContainer,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = {"source": "sec", "ciks": ["320193"]}
    with BlobLedger(BLOB_SETTINGS) as ledger:
        record = ledger.append("universe", {**payload, "universe_hash": digest(payload)})
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    monkeypatch.setenv("LEDGER_BACKEND", "azure")
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_URL", BLOB_SETTINGS.account_url)
    destination = tmp_path / "export.jsonl"
    for args in (["verify-blob"], ["export-ledger", str(destination)]):
        with patch(
            "sys.argv",
            [
                "quant-recorder",
                *args,
                "--expected-head",
                record["hash"],
                "--expected-sequence",
                "1",
            ],
        ):
            main()
        assert json.loads(capsys.readouterr().out) == {
            "verified_records": 1,
            "hash": record["hash"],
        }
    assert Ledger.verify(destination) == [record]
    with (
        patch("sys.argv", ["quant-recorder", "verify-blob", "--expected-sequence", "2"]),
        pytest.raises(SystemExit) as exc,
    ):
        main()
    assert exc.value.code == 1
    assert json.loads(capsys.readouterr().err)["error"] == "integrity_check_failed"


@pytest.mark.postgres
def test_blob_recorder_rerun_reconcile_and_local_replay(
    container: MemoryContainer, settings: Settings
) -> None:
    settings = replace(settings, azure_ledger=BLOB_SETTINGS)
    client = FakeSec()
    with Recorder(settings, client) as recorder:
        assert recorder.ingest(CANDIDATE)
        recorder.reconcile()
        records = list(recorder.ledger.records)
    with Recorder(settings, client) as recorder:
        assert not recorder.ingest(CANDIDATE)
        recorder.reconcile()
        assert recorder.ledger.records == records
    assert client.fetch_count == 1
    export_records(records, settings.ledger_path)
    with Recorder(replace(settings, azure_ledger=None), client) as recorder:
        recorder.reconcile()
        assert recorder.ledger.records == records


@pytest.mark.postgres
def test_blob_commit_without_db_acknowledgement_is_recovered(
    container: MemoryContainer, settings: Settings
) -> None:
    settings = replace(settings, azure_ledger=BLOB_SETTINGS)
    container.failure = ServiceResponseError("synthetic lost acknowledgement")
    container.commit_before_failure = True
    with Recorder(settings, FakeSec()) as recorder:
        with pytest.raises(ServiceResponseError):
            recorder.discover(CANDIDATE)
    with psycopg.connect(settings.database_url) as connection:
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone() == (0,)
    container.failure = None
    with Recorder(settings, FakeSec()) as recorder:
        assert len(recorder.ledger.records) == 1
        assert recorder.ingest(CANDIDATE)
        recorder.reconcile()
    with psycopg.connect(settings.database_url) as connection:
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone() == (2,)


@pytest.mark.postgres
def test_failed_blob_upload_never_writes_database(
    container: MemoryContainer, settings: Settings
) -> None:
    settings = replace(settings, azure_ledger=BLOB_SETTINGS)
    container.failure = ServiceResponseError("synthetic upload failure")
    with Recorder(settings, FakeSec()) as recorder:
        with pytest.raises(ServiceResponseError):
            recorder.discover(CANDIDATE)
    assert container.blobs == {}
    with psycopg.connect(settings.database_url) as connection:
        assert connection.execute("SELECT count(*) FROM audit_events").fetchone() == (0,)
