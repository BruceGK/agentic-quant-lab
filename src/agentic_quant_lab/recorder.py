import base64
import hashlib
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any, Self
from urllib.error import HTTPError

import psycopg

from agentic_quant_lab.config import Settings
from agentic_quant_lab.database import WRITER_LOCK, Projection
from agentic_quant_lab.ledger import Ledger, digest, timestamp, utc_now
from agentic_quant_lab.sec import (
    EASTERN,
    Candidate,
    SecClient,
    parse_daily_index,
    submission_metadata,
)


class Recorder:
    def __init__(
        self, settings: Settings, client: SecClient, clock: Callable[[], datetime] = utc_now
    ):
        self.settings = settings
        self.client = client
        self.clock = clock
        self.ledger = Ledger(settings.ledger_path)
        self.connection: psycopg.Connection[Any] | None = None
        self._projection: Projection | None = None
        self._discoveries: dict[str, dict[str, Any]] = {}
        self._filings: dict[str, dict[str, Any]] = {}

    def __enter__(self) -> Self:
        self.connection = psycopg.connect(self.settings.database_url, autocommit=True)
        try:
            locked = self.connection.execute(
                "SELECT pg_try_advisory_lock(%s)", (WRITER_LOCK,)
            ).fetchone()
            if not locked or not locked[0]:
                raise RuntimeError("Another recorder holds the database writer lock")
            self.ledger.__enter__()
            self._projection = Projection(self.connection)
            self._projection.replay(self.ledger.records)
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
        record = self.ledger.append(kind, payload)
        try:
            self._projection.apply(record)
        except BaseException:
            self._projection = None
            raise
        return record

    def discover(self, candidate: Candidate, seen: datetime | None = None) -> dict[str, Any]:
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
        content = self.client.fetch(candidate)
        fetched = timestamp(self.clock())
        accepted, form_type = submission_metadata(content, candidate)
        if fetched < p["first_seen_at"]:
            raise ValueError("Recorder clock moved backwards")
        record = self._append(
            "filing",
            {
                **p,
                "accepted_at": timestamp(accepted),
                "fetched_at": fetched,
                "decision_eligible_at": fetched,
                "form_type": form_type,
                "content_sha256": hashlib.sha256(content).hexdigest(),
                "content_base64": base64.b64encode(content).decode("ascii"),
            },
        )
        self._filings[candidate.external_id] = record
        return True

    def ingest_many(self, candidates: list[Candidate]) -> int:
        selected = [c for c in candidates if c.cik in self.settings.universe_ciks]
        seen = self.clock()
        for candidate in selected:
            self.discover(candidate, seen)
        return sum(self.ingest(candidate) for candidate in selected)

    def snapshot_universe(self) -> str:
        if not self.settings.universe_ciks:
            raise ValueError("Set an explicit, nonempty UNIVERSE_CIKS for scheduled recording")
        payload = {"source": "sec", "ciks": sorted(set(self.settings.universe_ciks))}
        universe_hash = digest(payload)
        latest = next((r for r in reversed(self.ledger.records) if r["kind"] == "universe"), None)
        if latest is None or latest["payload"]["universe_hash"] != universe_hash:
            self._append("universe", {**payload, "universe_hash": universe_hash})
        return universe_hash

    def catch_up(self, start: date, end: date, force: bool = False) -> int:
        today = self.clock().astimezone(EASTERN).date()
        if end >= today or start > end:
            raise ValueError("Catch-up requires start <= end < today's SEC Eastern date")
        universe_hash = self.snapshot_universe()
        checkpoints = {
            (r["payload"]["day"], r["payload"]["index_sha256"])
            for r in self.ledger.records
            if r["kind"] == "reconciliation" and r["payload"]["universe_hash"] == universe_hash
        }
        completed = {day for day, _ in checkpoints}
        count = 0
        day = start
        while day <= end:
            # Recheck recent indexes for late publication; older gaps are never skipped.
            if not force and day.isoformat() in completed and day < end - timedelta(days=2):
                day += timedelta(days=1)
                continue
            try:
                content = self.client.daily_index(day)
            except HTTPError as exc:
                # EDGAR does not accept filings on weekends. Weekday 404s fail closed:
                # holidays and not-yet-published indexes must not hide an unresolved gap.
                if exc.code == 404 and day.weekday() >= 5:
                    day += timedelta(days=1)
                    continue
                raise
            count += self.ingest_many(parse_daily_index(content, day))
            index_hash = hashlib.sha256(content).hexdigest()
            if (day.isoformat(), index_hash) not in checkpoints:
                self._append(
                    "reconciliation",
                    {
                        "day": day.isoformat(),
                        "universe_hash": universe_hash,
                        "index_sha256": index_hash,
                        "index_base64": base64.b64encode(content).decode("ascii"),
                    },
                )
            day += timedelta(days=1)
        return count

    def record(self) -> int:
        if self.settings.catchup_start is None:
            raise ValueError("CATCHUP_START must be explicit; gaps must not be silently skipped")
        self.snapshot_universe()
        count = self.ingest_many(self.client.latest())
        for record in list(self._discoveries.values()):
            count += self.ingest(Candidate.from_url(record["payload"]["document_url"]))
        end = self.clock().astimezone(EASTERN).date() - timedelta(days=1)
        if self.settings.catchup_start <= end:
            count += self.catch_up(self.settings.catchup_start, end)
        return count

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
                if r["kind"] == "correction" and r["payload"] == payload
            ),
            None,
        )
        return existing or self._append("correction", payload)
