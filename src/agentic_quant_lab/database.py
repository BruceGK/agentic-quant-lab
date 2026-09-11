from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from agentic_quant_lab.ledger import LedgerError

WRITER_LOCK = 728415920001


class Projection:
    def __init__(self, connection: psycopg.Connection[Any]):
        self.connection = connection

    def validate_payload(self, payload: dict[str, Any]) -> None:
        # JSONL accepts values (e.g. NUL strings) that PostgreSQL JSONB cannot store.
        # Validate without writing evidence before making the durable append.
        self.connection.execute("SELECT jsonb_typeof(%s)", (Jsonb(payload),))

    def replay(self, records: list[dict[str, Any]]) -> None:
        existing = self.connection.execute(
            "SELECT sequence, record_hash FROM audit_events ORDER BY sequence"
        ).fetchall()
        if len(existing) > len(records):
            raise LedgerError("Database is ahead of ledger; restore the durable ledger")
        for row, record in zip(existing, records, strict=False):
            if (row[0], row[1]) != (record["sequence"], record["hash"]):
                raise LedgerError("Database and ledger diverge")
        for record in records[len(existing) :]:
            self.apply(record)

    def apply(self, record: dict[str, Any]) -> None:
        p = record["payload"]
        with self.connection.transaction():
            inserted = self.connection.execute(
                """INSERT INTO audit_events
                   (sequence, event_id, kind, recorded_at, prev_hash, record_hash, payload)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT DO NOTHING RETURNING event_id""",
                (
                    record["sequence"],
                    record["event_id"],
                    record["kind"],
                    record["recorded_at"],
                    record["prev_hash"],
                    record["hash"],
                    Jsonb(p),
                ),
            ).fetchone()
            if inserted is None:
                row = self.connection.execute(
                    "SELECT record_hash FROM audit_events WHERE sequence = %s",
                    (record["sequence"],),
                ).fetchone()
                if row is None or row[0] != record["hash"]:
                    raise LedgerError("Projection conflict")
                return
            if record["kind"] == "discovery":
                self.connection.execute(
                    """INSERT INTO discoveries (source, external_id, event_id, first_seen_at)
                       VALUES (%s, %s, %s, %s) ON CONFLICT (source, external_id) DO NOTHING""",
                    (p["source"], p["external_id"], record["event_id"], p["first_seen_at"]),
                )
            elif record["kind"] == "filing":
                self.connection.execute(
                    """INSERT INTO filings
                       (event_id, source, external_id, cik, form_type, document_url,
                        accepted_at, first_seen_at, fetched_at, decision_eligible_at,
                        content_sha256)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (source, external_id) DO NOTHING""",
                    (
                        record["event_id"],
                        p["source"],
                        p["external_id"],
                        p["cik"],
                        p["form_type"],
                        p["document_url"],
                        p["accepted_at"],
                        p["first_seen_at"],
                        p["fetched_at"],
                        p["decision_eligible_at"],
                        p["content_sha256"],
                    ),
                )
            elif record["kind"] == "correction":
                self.connection.execute(
                    """INSERT INTO corrections (event_id, supersedes_event_id, reason, changes)
                       VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                    (
                        record["event_id"],
                        p["supersedes_event_id"],
                        p["reason"],
                        Jsonb(p["changes"]),
                    ),
                )
