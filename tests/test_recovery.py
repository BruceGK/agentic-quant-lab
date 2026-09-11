from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, date, datetime
from unittest.mock import patch

import psycopg
import pytest
from conftest import CANDIDATE, FakeSec

from agentic_quant_lab.config import Settings
from agentic_quant_lab.ledger import Ledger, LedgerError
from agentic_quant_lab.recorder import Recorder
from agentic_quant_lab.sec import parse_full_index

pytestmark = pytest.mark.postgres
SEEN = datetime(2026, 9, 10, 10, tzinfo=UTC)
ARCHIVE = (
    b"Description: Synthetic quarter index\n"
    b"CIK|Company Name|Form Type|Date Filed|Filename\n"
    b"320193|Example|10-K|20241101|edgar/data/320193/0000320193-24-000123.txt\n"
)


def test_explicit_archive_recovery_is_observed_idempotent_and_not_a_daily_checkpoint(
    settings: Settings,
) -> None:
    client = FakeSec()
    with patch.object(client, "full_index", return_value=ARCHIVE):
        with Recorder(settings, client, lambda: SEEN) as recorder:
            assert recorder.recover_quarter(2024, 4) == 1
            recorder.reconcile()
        original = settings.ledger_path.read_bytes()
        with Recorder(settings, client, lambda: SEEN) as recorder:
            assert recorder.recover_quarter(2024, 4) == 0
            assert not any(r["kind"] == "reconciliation" for r in recorder.ledger.records)
            archive = recorder.ledger.records[-1]
            assert archive["kind"] == "archive_recovery"
            filing = next(r for r in recorder.ledger.records if r["kind"] == "filing")
            assert filing["payload"]["decision_eligible_at"] == SEEN.isoformat()
    assert settings.ledger_path.read_bytes() == original


def test_incomplete_archive_does_not_claim_recovery(settings: Settings) -> None:
    client = FakeSec()
    client.fail = True
    with (
        patch.object(client, "full_index", return_value=ARCHIVE),
        Recorder(settings, client, lambda: SEEN) as recorder,
    ):
        with pytest.raises(ExceptionGroup):
            recorder.recover_quarter(2024, 4)
        assert not any(r["kind"] == "archive_recovery" for r in recorder.ledger.records)


def test_archive_quarter_cannot_be_future_or_current(settings: Settings) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        with pytest.raises(ValueError, match="completed"):
            recorder.recover_quarter(2026, 3)
    with pytest.raises(ValueError):
        parse_full_index(ARCHIVE, 2024, 3)
    with pytest.raises(ValueError):
        parse_full_index(b"CIK|Company Name|Form Type|Date Filed|Filename\n", 2024, 4)


def test_durable_unique_constraint_handles_concurrent_duplicate_insertions(
    settings: Settings,
) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.ingest(CANDIDATE)

    def attempt(_: int) -> int:
        with psycopg.connect(settings.database_url, autocommit=True) as connection:
            return connection.execute(
                """INSERT INTO filings SELECT * FROM filings
                   ON CONFLICT (source, external_id) DO NOTHING"""
            ).rowcount

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(attempt, range(8))) == [0] * 8
    with Recorder(settings, FakeSec()) as recorder:
        recorder.reconcile()


def test_stale_checkpoint_with_missing_prerequisite_is_rejected(settings: Settings) -> None:
    from test_recorder import index

    client = FakeSec()
    client.indexes["2026-09-09"] = index("2026-09-09")
    with Recorder(settings, client, lambda: SEEN) as recorder:
        recorder.catch_up(date(2026, 9, 9), date(2026, 9, 9))
    records = Ledger.verify(settings.ledger_path)
    # Construct a separate, self-consistently hashed invalid fixture; never alter real history.
    invalid_path = settings.ledger_path.with_name("invalid-checkpoint.jsonl")
    with Ledger(invalid_path) as ledger:
        ledger.append("universe", records[0]["payload"])
        ledger.append("reconciliation", records[-1]["payload"])
    with (
        pytest.raises(LedgerError, match="semantics"),
        Recorder(replace(settings, ledger_path=invalid_path), FakeSec()),
    ):
        pass


@pytest.mark.parametrize("missing", ["ingestion_ciks", "ingestion_scope_hash"])
def test_incomplete_checkpoint_scope_cannot_certify_missing_filings(
    settings: Settings, missing: str
) -> None:
    from test_recorder import index

    from agentic_quant_lab.evidence import verify_evidence

    client = FakeSec()
    client.indexes["2026-09-09"] = index("2026-09-09")
    with Recorder(settings, client, lambda: SEEN) as recorder:
        recorder.catch_up(date(2026, 9, 9), date(2026, 9, 9))
    records = Ledger.verify(settings.ledger_path)
    payload = records[-1]["payload"]
    del payload[missing]
    with pytest.raises(LedgerError, match="semantics"):
        verify_evidence(records)


def test_future_catchup_start_does_not_report_success(settings: Settings) -> None:
    settings = replace(settings, catchup_start=date(2027, 1, 1))
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        with pytest.raises(ValueError, match="future"):
            recorder.record()
        assert not recorder.ledger.records
