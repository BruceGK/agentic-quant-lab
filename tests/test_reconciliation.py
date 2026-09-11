from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import psycopg
import pytest
from conftest import CANDIDATE, DatabaseConfig, FakeSec
from psycopg import sql

from agentic_quant_lab.config import Settings
from agentic_quant_lab.database import same_json
from agentic_quant_lab.evidence import verify_evidence
from agentic_quant_lab.ledger import Ledger, LedgerError
from agentic_quant_lab.recorder import FilingFetchError, Recorder

pytestmark = pytest.mark.postgres
SEEN = datetime(2026, 9, 10, 10, tzinfo=UTC)


@pytest.mark.parametrize(
    "table, alteration",
    [
        ("filings", sql.SQL("UPDATE filings SET form_type = 'WRONG'")),
        ("filings", sql.SQL("UPDATE filings SET content_sha256 = repeat('0', 64)")),
        (
            "audit_events",
            sql.SQL("UPDATE audit_events SET payload = '{}'::jsonb WHERE kind = 'filing'"),
        ),
        ("audit_events", sql.SQL("UPDATE audit_events SET prev_hash = repeat('0', 64)")),
        (
            "discoveries",
            sql.SQL("UPDATE discoveries SET first_seen_at = first_seen_at - interval '1 day'"),
        ),
        ("corrections", sql.SQL("UPDATE corrections SET reason = 'changed'")),
    ],
)
def test_reconcile_detects_modified_projection_despite_unchanged_record_hash(
    settings: Settings, database: DatabaseConfig, table: str, alteration: sql.SQL
) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.ingest(CANDIDATE)
        recorder.correct(recorder.ledger.records[-1]["event_id"], "annotation", {"note": "x"})
    original = settings.ledger_path.read_bytes()
    # Deliberately corrupt only disposable test state using the administrator.
    with psycopg.connect(database.admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("ALTER TABLE {} DISABLE TRIGGER USER").format(sql.Identifier(table)))
        admin.execute(alteration)
        admin.execute(
            sql.SQL("ALTER TABLE {} ENABLE ALWAYS TRIGGER {}").format(
                sql.Identifier(table), sql.Identifier(table + "_append_only")
            )
        )
    with pytest.raises(LedgerError, match="diverge"), Recorder(settings, FakeSec()):
        pass
    assert settings.ledger_path.read_bytes() == original


def test_missing_materialized_row_is_detected_and_replayed(
    settings: Settings, database: DatabaseConfig
) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.ingest(CANDIDATE)
    original = settings.ledger_path.read_bytes()
    with psycopg.connect(database.admin_dsn, autocommit=True) as admin:
        admin.execute("ALTER TABLE filings DISABLE TRIGGER USER")
        admin.execute("DELETE FROM filings")
        admin.execute("ALTER TABLE filings ENABLE ALWAYS TRIGGER filings_append_only")
    with pytest.raises(LedgerError, match="missing"), Recorder(settings, FakeSec(), replay=False):
        pass
    client = FakeSec()
    with Recorder(settings, client) as recorder:
        recorder.reconcile()
        assert not recorder.ingest(CANDIDATE)
    assert client.fetch_count == 0
    assert settings.ledger_path.read_bytes() == original
    with psycopg.connect(database.writer_dsn) as connection:
        assert connection.execute("SELECT count(*) FROM filings").fetchone() == (1,)


@pytest.mark.parametrize(
    "field, value",
    [
        ("content_sha256", "0" * 64),
        ("decision_eligible_at", "2024-11-01T10:01:36+00:00"),
        ("availability_mode", "inferred"),
    ],
)
def test_self_consistent_chain_with_invalid_content_fails_semantic_verification(
    settings: Settings, tmp_path: Path, field: str, value: str
) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.ingest(CANDIDATE)
    records = Ledger.verify(settings.ledger_path)
    path = tmp_path / "invalid-test-ledger.jsonl"
    with Ledger(path) as ledger:
        ledger.append("discovery", records[0]["payload"])
        payload = dict(records[1]["payload"]) | {field: value}
        ledger.append("filing", payload)
    with pytest.raises(LedgerError, match="semantics"):
        verify_evidence(Ledger.verify(path))


def test_duplicate_external_identity_in_valid_chain_is_rejected(settings: Settings) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.ingest(CANDIDATE)
    with Ledger(settings.ledger_path) as ledger:
        ledger.append("filing", ledger.records[-1]["payload"])
    with pytest.raises(LedgerError, match="semantics"), Recorder(settings, FakeSec()):
        pass


def test_future_accepted_timestamp_is_not_eligible(settings: Settings) -> None:
    client = FakeSec()
    client.content = client.content.replace(b"20241101060136", b"20270910060136")
    with Recorder(settings, client, lambda: SEEN) as recorder:
        with pytest.raises(FilingFetchError):
            recorder.ingest(CANDIDATE)
        assert [r["kind"] for r in recorder.ledger.records] == ["discovery"]


def test_backward_fetch_clock_keeps_discovery_only(settings: Settings) -> None:
    times = iter([SEEN, SEEN - timedelta(seconds=1)])
    with Recorder(settings, FakeSec(), lambda: next(times)) as recorder:
        with pytest.raises(FilingFetchError):
            recorder.ingest(CANDIDATE)
        assert [r["kind"] for r in recorder.ledger.records] == ["discovery"]


def test_preheartbeat_reconciliation_detects_missing_filing(settings: Settings) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.ingest(CANDIDATE)
        with patch(
            "agentic_quant_lab.database.Projection.reconcile", side_effect=LedgerError("bad")
        ):
            with pytest.raises(LedgerError):
                recorder.reconcile()


def test_jsonb_numeric_normalization_is_not_divergence(settings: Settings) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.ingest(CANDIDATE)
        recorder.correct(
            recorder.ledger.records[-1]["event_id"],
            "numeric annotation",
            {"large": 1e20, "small": 1e-20, "fraction": 1.0},
        )
        recorder.reconcile()
    with Recorder(settings, FakeSec()) as recorder:
        recorder.reconcile()
    assert not same_json({"x": False}, {"x": 0})
    assert not same_json({"x": 1e20}, {"x": 100000000000000000001})
