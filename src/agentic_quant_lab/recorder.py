import base64
import hashlib
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import date, datetime, timedelta
from http.client import HTTPException
from typing import Any, Self
from urllib.error import HTTPError

import psycopg

from agentic_quant_lab.blob_ledger import BlobLedger
from agentic_quant_lab.config import Settings
from agentic_quant_lab.database import WRITER_LOCK, Projection, connect_database
from agentic_quant_lab.ledger import Ledger, digest, timestamp, utc_now
from agentic_quant_lab.provenance import provenance
from agentic_quant_lab.sec import (
    EASTERN,
    Candidate,
    SecClient,
    SecIndexNotPublished,
    parse_daily_index,
    parse_full_index,
    scheduled_sec_closure,
    submission_metadata,
)


class FilingFetchError(RuntimeError):
    pass


class Recorder:
    def __init__(
        self,
        settings: Settings,
        client: SecClient,
        clock: Callable[[], datetime] = utc_now,
        *,
        replay: bool = True,
    ):
        self.settings = settings
        self.client = client
        self.clock = clock
        self.replay = replay
        self.provenance = provenance(settings)
        self.ledger = (
            BlobLedger(settings.azure_ledger)
            if settings.azure_ledger
            else Ledger(settings.ledger_path)
        )
        self.connection: psycopg.Connection[Any] | None = None
        self._projection: Projection | None = None
        self._discoveries: dict[str, dict[str, Any]] = {}
        self._filings: dict[str, dict[str, Any]] = {}

    def __enter__(self) -> Self:
        self.connection = connect_database(self.settings)
        try:
            locked = self.connection.execute(
                "SELECT pg_try_advisory_lock(%s)", (WRITER_LOCK,)
            ).fetchone()
            if not locked or not locked[0]:
                raise RuntimeError("Another recorder holds the database writer lock")
            self.ledger.__enter__()
            self._projection = Projection(self.connection)
            if self.replay:
                self._projection.replay(self.ledger.records)
            else:
                self.reconcile()
            self._discoveries = {
                r["payload"]["external_id"]: r
                for r in self.ledger.records
                if r["kind"] == "discovery"
            }
            self._filings = {
                r["payload"]["external_id"]: r for r in self.ledger.records if r["kind"] == "filing"
            }
        except BaseException:
            self.__exit__()
            raise
        return self

    def __exit__(self, *_: Any) -> None:
        self.ledger.__exit__()
        if self.connection:
            self.connection.close()
            self.connection = None
        self._projection = None

    def _append(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self._projection is None:
            raise RuntimeError("Recorder is not open")
        payload = {**payload, "provenance": self.provenance}
        self._projection.validate_payload(payload)
        record = self.ledger.append(kind, payload)
        try:
            self._projection.apply(record)
        except BaseException:
            self._projection = None
            raise
        return record

    def discover(self, candidate: Candidate, seen: datetime | None = None) -> dict[str, Any]:
        if candidate != Candidate.from_url(candidate.document_url):
            raise ValueError("Candidate identity is inconsistent with its URL")
        if candidate.external_id not in self._discoveries:
            record = self._append(
                "discovery",
                {
                    "source": "sec",
                    "external_id": candidate.external_id,
                    "cik": candidate.cik,
                    "document_url": candidate.document_url,
                    "first_seen_at": timestamp(seen or self.clock()),
                },
            )
            self._discoveries[candidate.external_id] = record
        return self._discoveries[candidate.external_id]

    def ingest(self, candidate: Candidate) -> bool:
        discovery = self.discover(candidate)
        if candidate.external_id in self._filings:
            return False
        p = discovery["payload"]
        # Always retry the original observed URL, not metadata from a later discovery.
        candidate = Candidate.from_url(p["document_url"])
        try:
            content = self.client.fetch(candidate)
            fetched = timestamp(self.clock())
            accepted, form_type = submission_metadata(content, candidate)
            if datetime.fromisoformat(fetched) < datetime.fromisoformat(p["first_seen_at"]):
                raise ValueError("Recorder clock moved backwards")
            if accepted > datetime.fromisoformat(fetched):
                raise ValueError("SEC acceptance time is later than our fetch clock")
        except (OSError, ValueError, HTTPException) as exc:
            raise FilingFetchError(f"Fetch/validation failed for {candidate.external_id}") from exc
        record = self._append(
            "filing",
            {
                **p,
                "accepted_at": timestamp(accepted),
                "fetched_at": fetched,
                "decision_eligible_at": fetched,
                "availability_mode": "observed",
                "form_type": form_type,
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "content_base64": base64.b64encode(content).decode("ascii"),
            },
        )
        self._filings[candidate.external_id] = record
        return True

    def ingest_many(self, candidates: list[Candidate]) -> int:
        return self._ingest_batch([c for c in candidates if c.cik in self.settings.ingestion_scope])

    def _ingest_batch(self, candidates: list[Candidate]) -> int:
        seen = self.clock()
        for candidate in candidates:
            self.discover(candidate, seen)
        count = 0
        failures: list[Exception] = []
        for candidate in candidates:
            try:
                count += self.ingest(candidate)
            except FilingFetchError as exc:
                failures.append(exc)
        if failures:
            raise ExceptionGroup("Some SEC filings remain unresolved", failures)
        return count

    def snapshot_universe(self) -> str:
        if not self.settings.universe_ciks:
            raise ValueError("Set an explicit, nonempty UNIVERSE_CIKS for scheduled recording")
        payload = {"source": "sec", "ciks": sorted(set(self.settings.universe_ciks))}
        universe_hash = digest(payload)
        latest = next((r for r in reversed(self.ledger.records) if r["kind"] == "universe"), None)
        if latest is None or latest["payload"]["universe_hash"] != universe_hash:
            self._append(
                "universe",
                {
                    **payload,
                    "universe_hash": universe_hash,
                    "as_of": timestamp(self.clock()),
                    "screen_version": "explicit-cik-list-v1",
                    "screen_config_sha256": universe_hash,
                    "reason": "Explicit configured research eligibility; not a trading signal",
                },
            )
        return universe_hash

    def catch_up(self, start: date, end: date, force: bool = False) -> int:
        today = self.clock().astimezone(EASTERN).date()
        if end >= today or start > end:
            raise ValueError("Catch-up requires start <= end < today's SEC Eastern date")
        universe_hash = self.snapshot_universe()
        ingestion_ciks = sorted(set(self.settings.ingestion_scope))
        scope_hash = digest({"source": "sec", "ciks": ingestion_ciks})
        checkpoints = {
            (r["payload"]["day"], r["payload"]["index_sha256"])
            for r in self.ledger.records
            if r["kind"] == "reconciliation"
            and r["payload"].get("ingestion_scope_hash", r["payload"]["universe_hash"])
            == scope_hash
        }
        completed = {day for day, _ in checkpoints}
        count = 0
        failures: list[Exception] = []
        day = start
        while day <= end:
            # Recheck recent indexes for late publication; older gaps are never skipped.
            if not force and day.isoformat() in completed and day < end - timedelta(days=2):
                day += timedelta(days=1)
                continue
            try:
                content = self.client.daily_index(day)
            except SecIndexNotPublished as exc:
                if exc.day != day or not scheduled_sec_closure(day):
                    raise ValueError(
                        "SEC closure evidence does not match the requested date"
                    ) from exc
                day += timedelta(days=1)
                continue
            except HTTPError as exc:
                # Only a known closure may explain a missing index; other gaps fail closed.
                if exc.code == 404 and scheduled_sec_closure(day):
                    day += timedelta(days=1)
                    continue
                failures.append(exc)
                day += timedelta(days=1)
                continue
            except (OSError, ValueError, HTTPException) as exc:
                failures.append(exc)
                day += timedelta(days=1)
                continue
            try:
                candidates = parse_daily_index(content, day)
            except ValueError as exc:
                failures.append(exc)
                day += timedelta(days=1)
                continue
            try:
                count += self.ingest_many(candidates)
            except ExceptionGroup as exc:
                failures.append(exc)
                day += timedelta(days=1)
                continue
            index_hash = hashlib.sha256(content).hexdigest()
            if (day.isoformat(), index_hash) not in checkpoints:
                self._append(
                    "reconciliation",
                    {
                        "day": day.isoformat(),
                        "universe_hash": universe_hash,
                        "ingestion_scope_hash": scope_hash,
                        "ingestion_ciks": ingestion_ciks,
                        "index_sha256": index_hash,
                        "index_base64": base64.b64encode(content).decode("ascii"),
                    },
                )
            day += timedelta(days=1)
        if failures:
            raise ExceptionGroup("SEC reconciliation is incomplete", failures)
        return count

    def record(self) -> int:
        if self.settings.catchup_start is None:
            raise ValueError("CATCHUP_START must be explicit; gaps must not be silently skipped")
        if self.settings.catchup_start > self.clock().astimezone(EASTERN).date():
            raise ValueError("CATCHUP_START cannot be in the future")
        self.snapshot_universe()
        pending = [
            Candidate.from_url(r["payload"]["document_url"])
            for key, r in self._discoveries.items()
            if key not in self._filings
        ]
        count = 0
        failures: list[Exception] = []
        try:
            candidates = self.client.latest()
        except (OSError, ValueError, HTTPException, ET.ParseError) as exc:
            failures.append(exc)
        else:
            try:
                count += self.ingest_many(candidates)
            except ExceptionGroup as exc:
                failures.append(exc)
        try:
            count += self._ingest_batch(pending)
        except ExceptionGroup as exc:
            failures.append(exc)
        end = self.clock().astimezone(EASTERN).date() - timedelta(days=1)
        if self.settings.catchup_start <= end:
            try:
                count += self.catch_up(self.settings.catchup_start, end)
            except ExceptionGroup as exc:
                failures.append(exc)
        if failures:
            raise ExceptionGroup("SEC recording is incomplete; no success heartbeat", failures)
        return count

    def recover_quarter(self, year: int, quarter: int) -> int:
        today = self.clock().astimezone(EASTERN).date()
        if (
            year < 1994
            or quarter not in (1, 2, 3, 4)
            or (year, quarter) >= (today.year, (today.month - 1) // 3 + 1)
        ):
            raise ValueError("Archive recovery requires a completed EDGAR quarter")
        universe_hash = self.snapshot_universe()
        content = self.client.full_index(year, quarter)
        count = self.ingest_many(parse_full_index(content, year, quarter))
        ciks = sorted(set(self.settings.ingestion_scope))
        payload = {
            "year": year,
            "quarter": quarter,
            "universe_hash": universe_hash,
            "ingestion_ciks": ciks,
            "ingestion_scope_hash": digest({"source": "sec", "ciks": ciks}),
            "index_sha256": hashlib.sha256(content).hexdigest(),
            "index_base64": base64.b64encode(content).decode("ascii"),
        }
        if not any(
            r["kind"] == "archive_recovery"
            and all(r["payload"].get(k) == v for k, v in payload.items())
            for r in self.ledger.records
        ):
            self._append("archive_recovery", payload)
        return count

    def reconcile(self) -> None:
        from agentic_quant_lab.evidence import verify_evidence

        if self._projection is None:
            raise RuntimeError("Recorder is not open")
        records = self.ledger.read_records()
        verify_evidence(records)
        self._projection.reconcile(records)

    def correct(self, event_id: str, reason: str, changes: dict[str, Any]) -> dict[str, Any]:
        if not reason.strip() or not changes:
            raise ValueError("A correction requires a reason and nonempty changes")
        if not any(r["event_id"] == event_id for r in self.ledger.records):
            raise ValueError("Correction target does not exist")
        payload = {"supersedes_event_id": event_id, "reason": reason, "changes": changes}
        existing = next(
            (
                r
                for r in self.ledger.records
                if r["kind"] == "correction"
                and all(r["payload"].get(k) == v for k, v in payload.items())
            ),
            None,
        )
        return existing or self._append("correction", payload)
