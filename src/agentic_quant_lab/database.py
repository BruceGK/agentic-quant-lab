import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb, set_json_loads

from agentic_quant_lab.ledger import LedgerError, timestamp

WRITER_LOCK = 728415920001
TABLE_FIELDS = {
    "discoveries": ("source", "external_id", "first_seen_at"),
    "filings": (
        "source",
        "external_id",
        "cik",
        "form_type",
        "document_url",
        "accepted_at",
        "first_seen_at",
        "fetched_at",
        "decision_eligible_at",
        "content_sha256",
    ),
    "corrections": ("supersedes_event_id", "reason", "changes"),
}
KIND_TABLE = {"discovery": "discoveries", "filing": "filings", "correction": "corrections"}


def projected_rows(records: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    tables: dict[str, dict[str, dict[str, Any]]] = {
        "audit_events": {},
        **{table: {} for table in TABLE_FIELDS},
    }
    for record in records:
        event_id = record["event_id"]
        tables["audit_events"][event_id] = {
            key: record[key]
            for key in ("sequence", "event_id", "kind", "recorded_at", "prev_hash", "payload")
        } | {"record_hash": record["hash"]}
        if table := KIND_TABLE.get(record["kind"]):
            tables[table][event_id] = {
                "event_id": event_id,
                **{key: record["payload"][key] for key in TABLE_FIELDS[table]},
            }
    return tables


def normalized_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: timestamp(value)
        if isinstance(value, datetime)
        else str(value)
        if isinstance(value, UUID)
        else value
        for key, value in row.items()
    }


def same_json(left: Any, right: Any) -> bool:
    # JSONB normalizes exponent notation; boolean/number distinctions still matter.
    if type(left) in (int, float, Decimal) and type(right) in (int, float, Decimal):
        return Decimal(str(left)) == Decimal(str(right))
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_json(v, right[k]) for k, v in left.items())
    if isinstance(left, list):
        return len(left) == len(right) and all(
            same_json(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


class Projection:
    def __init__(self, connection: psycopg.Connection[Any]):
        self.connection = connection

    def validate_payload(self, payload: dict[str, Any]) -> None:
        # JSONL accepts values (e.g. NUL strings) that PostgreSQL JSONB cannot store.
        # Validate without writing evidence before making the durable append.
        self.connection.execute("SELECT jsonb_typeof(%s)", (Jsonb(payload),))

    def reconcile(self, records: list[dict[str, Any]], *, allow_missing: bool = False) -> set[str]:
        missing: set[str] = set()
        for table, expected in projected_rows(records).items():
            with self.connection.cursor(row_factory=dict_row) as cursor:
                set_json_loads(lambda raw: json.loads(raw, parse_float=Decimal), cursor)
                rows = cursor.execute(
                    sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
                ).fetchall()
            actual = {str(row["event_id"]): normalized_row(row) for row in rows}
            if actual.keys() - expected.keys():
                raise LedgerError(f"Database is ahead of ledger: unexpected {table} evidence")
            for event_id, row in actual.items():
                if not same_json(row, expected[event_id]):
                    raise LedgerError(f"Database and ledger diverge in {table}")
            missing.update(expected.keys() - actual.keys())
        if missing and not allow_missing:
            raise LedgerError("Database evidence is missing; run replay from the verified ledger")
        return missing

    def replay(self, records: list[dict[str, Any]]) -> None:
        from agentic_quant_lab.evidence import verify_evidence

        verify_evidence(records)
        missing = self.reconcile(records, allow_missing=True)
        for record in records:
            if record["event_id"] in missing:
                self.apply(record)
        self.reconcile(records)

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
