import base64
import hashlib
import os
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import patch

import psycopg
import pytest
from conftest import CANDIDATE, SUBMISSION, DatabaseConfig, FakeSec
from psycopg import sql

from agentic_quant_lab.config import Settings
from agentic_quant_lab.database import Projection
from agentic_quant_lab.ledger import Ledger, LedgerError
from agentic_quant_lab.recorder import Recorder
from agentic_quant_lab.sec import Candidate, SecClient

pytestmark = pytest.mark.postgres
SEEN = datetime(2026, 9, 10, 10, tzinfo=UTC)
FETCHED = datetime(2026, 9, 10, 10, 1, tzinfo=UTC)


def test_ingest_timestamps_and_rerun(settings: Settings) -> None:
    client = FakeSec()
    times = iter([SEEN, FETCHED])
    with Recorder(settings, client, lambda: next(times)) as recorder:
        assert recorder.ingest(CANDIDATE)
    original = settings.ledger_path.read_bytes()
    with Recorder(settings, client) as recorder:
        assert not recorder.ingest(CANDIDATE)
    assert settings.ledger_path.read_bytes() == original
    assert client.fetch_count == 1
    with psycopg.connect(settings.database_url) as connection:
        rows = connection.execute(
            """SELECT accepted_at, first_seen_at, fetched_at, decision_eligible_at
               FROM filings"""
        ).fetchall()
        assert rows == [(datetime(2024, 11, 1, 10, 1, 36, tzinfo=UTC), SEEN, FETCHED, FETCHED)]
        assert connection.execute("SELECT count(*) FROM discoveries").fetchone() == (1,)
    payload = Ledger.verify(settings.ledger_path)[-1]["payload"]
    assert base64.b64decode(payload["content_base64"]) == SUBMISSION
    assert payload["content_sha256"] == hashlib.sha256(SUBMISSION).hexdigest()


def test_failed_fetch_preserves_first_seen(settings: Settings) -> None:
    client = FakeSec()
    client.fail = True
    with Recorder(settings, client, lambda: SEEN) as recorder:
        with pytest.raises(TimeoutError):
            recorder.ingest(CANDIDATE)
    assert [r["kind"] for r in Ledger.verify(settings.ledger_path)] == ["discovery"]
    client.fail = False
    with Recorder(settings, client, lambda: FETCHED) as recorder:
        assert recorder.ingest(CANDIDATE)
    filing = Ledger.verify(settings.ledger_path)[-1]["payload"]
    assert datetime.fromisoformat(filing["first_seen_at"]) == SEEN
    assert datetime.fromisoformat(filing["decision_eligible_at"]) == FETCHED


def test_crash_after_fsync_replays_projection(settings: Settings) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.discover(CANDIDATE)
        with patch.object(Projection, "apply", side_effect=RuntimeError("database unavailable")):
            with pytest.raises(RuntimeError, match="unavailable"):
                recorder.ingest(CANDIDATE)
    assert len(Ledger.verify(settings.ledger_path)) == 2
    client = FakeSec()
    with Recorder(settings, client) as recorder:
        assert not recorder.ingest(CANDIDATE)
    assert client.fetch_count == 0
    with psycopg.connect(settings.database_url) as connection:
        assert connection.execute("SELECT count(*) FROM filings").fetchone() == (1,)


def test_projection_replay_is_idempotent(settings: Settings, database: DatabaseConfig) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.ingest(CANDIDATE)
    records = Ledger.verify(settings.ledger_path)
    # Project the same event again: ON CONFLICT must be harmless.
    with psycopg.connect(database.writer_dsn, autocommit=True) as connection:
        projection = Projection(connection)
        projection.apply(records[-1])
        projection.replay(records)
        assert connection.execute("SELECT count(*) FROM filings").fetchone() == (1,)


def index(day: str, candidate: Candidate = CANDIDATE) -> bytes:
    return (
        "Description: synthetic daily index\n"
        "CIK|Company Name|Form Type|Date Filed|Filename\n"
        "------------------------------------------\n"
        f"{candidate.cik}|Example|10-K|{day}|edgar/data/{candidate.cik}/"
        f"{candidate.external_id}.txt\n"
    ).encode()


def test_missed_interval_recovered_and_rerunnable(settings: Settings) -> None:
    client = FakeSec()
    missed = Candidate.from_url(CANDIDATE.document_url.replace("000123", "000124"))
    client.indexes = {
        "2026-09-08": index("2026-09-08"),
        "2026-09-09": index("2026-09-09", missed),
    }
    settings = replace(settings, catchup_start=date(2026, 9, 8))
    with Recorder(settings, client, lambda: SEEN) as recorder:
        assert recorder.record() == 2  # Neither filing was in the latest feed.
    original = settings.ledger_path.read_bytes()
    with Recorder(settings, client, lambda: FETCHED) as recorder:
        assert recorder.record() == 0
    assert settings.ledger_path.read_bytes() == original
    assert client.fetch_count == 2
    records = Ledger.verify(settings.ledger_path)
    assert len([r for r in records if r["kind"] == "reconciliation"]) == 2
    assert all(
        r["payload"]["decision_eligible_at"] == SEEN.isoformat()
        for r in records
        if r["kind"] == "filing"
    )


def test_failed_catchup_does_not_checkpoint(settings: Settings) -> None:
    client = FakeSec()
    client.indexes["2026-09-09"] = index("2026-09-09")
    client.fail = True
    with Recorder(settings, client, lambda: SEEN) as recorder:
        with pytest.raises(TimeoutError):
            recorder.catch_up(date(2026, 9, 9), date(2026, 9, 9))
        assert not any(r["kind"] == "reconciliation" for r in recorder.ledger.records)
    client.fail = False
    with Recorder(settings, client, lambda: FETCHED) as recorder:
        assert recorder.catch_up(date(2026, 9, 9), date(2026, 9, 9)) == 1


@pytest.mark.parametrize("table", ["audit_events", "discoveries", "filings", "corrections"])
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE"])
@pytest.mark.parametrize("as_owner", [False, True])
def test_database_append_only(
    settings: Settings, database: DatabaseConfig, table: str, operation: str, as_owner: bool
) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.ingest(CANDIDATE)
        recorder.correct(recorder.ledger.records[-1]["event_id"], "Test correction", {"note": "x"})
    dsn = database.admin_dsn if as_owner else settings.database_url
    with psycopg.connect(dsn, autocommit=True) as connection:
        command = {
            "UPDATE": sql.SQL("UPDATE {} SET event_id = event_id"),
            "DELETE": sql.SQL("DELETE FROM {}"),
            "TRUNCATE": sql.SQL("TRUNCATE {} CASCADE"),
        }[operation]
        with pytest.raises(psycopg.Error) as exc:
            connection.execute(command.format(sql.Identifier(table)))
        assert exc.value.sqlstate in ("42501", "55000")


def test_corrections_append_and_are_idempotent(settings: Settings) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.ingest(CANDIDATE)
        before = settings.ledger_path.read_bytes()
        event_id = recorder.ledger.records[-1]["event_id"]
        first = recorder.correct(event_id, "Documented annotation", {"note": "reviewed"})
        assert recorder.correct(event_id, "Documented annotation", {"note": "reviewed"}) == first
        assert settings.ledger_path.read_bytes().startswith(before)
        with pytest.raises(ValueError):
            recorder.correct("not-an-event", "reason", {"note": "x"})


def test_database_ahead_of_truncated_ledger_fails(settings: Settings) -> None:
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.ingest(CANDIDATE)
    lines = settings.ledger_path.read_bytes().splitlines(keepends=True)
    settings.ledger_path.write_bytes(lines[0])
    with pytest.raises(LedgerError, match="ahead"), Recorder(settings, FakeSec()):
        pass


def test_database_lock_prevents_second_writer(settings: Settings, tmp_path: Path) -> None:
    other = replace(settings, ledger_path=tmp_path / "other.jsonl")
    with Recorder(settings, FakeSec()):
        with pytest.raises(RuntimeError, match="writer lock"), Recorder(other, FakeSec()):
            pass


@pytest.mark.live_sec
@pytest.mark.skipif(os.getenv("RUN_LIVE_SEC") != "1", reason="Opt-in real SEC network test")
def test_ingest_real_sec_filing(settings: Settings) -> None:
    user_agent = os.environ["SEC_USER_AGENT"]
    candidate = Candidate.from_url(os.environ["TEST_SEC_URL"])
    settings = replace(settings, sec_user_agent=user_agent)
    with Recorder(settings, SecClient(user_agent)) as recorder:
        assert recorder.ingest(candidate)
        assert not recorder.ingest(candidate)
    with psycopg.connect(settings.database_url) as connection:
        row = connection.execute(
            """SELECT accepted_at, first_seen_at, fetched_at, decision_eligible_at
               FROM filings"""
        ).fetchone()
        assert row is not None
        assert row[0] <= row[1] <= row[2] == row[3]
