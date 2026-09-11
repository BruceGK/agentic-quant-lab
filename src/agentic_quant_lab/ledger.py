import fcntl
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO, Self
from uuid import uuid4

GENESIS_HASH = "0" * 64


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def utc_now() -> datetime:
    return datetime.now(UTC)


def timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Naive timestamps are not evidence")
    return value.astimezone(UTC).isoformat()


class LedgerError(RuntimeError):
    pass


class Ledger:
    """Exclusive, fsync-before-projection JSONL writer. Never repairs evidence silently."""

    def __init__(self, path: Path):
        self.path = path
        self.records: list[dict[str, Any]] = []
        self._file: BinaryIO | None = None
        self._failed = False

    def __enter__(self) -> Self:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a+b")
        try:
            fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            self.records = self.verify(self.path)
        except BaseException:
            self._file.close()
            self._file = None
            raise
        return self

    def __exit__(self, *_: Any) -> None:
        if self._file:
            self._file.close()
            self._file = None

    @staticmethod
    def verify(path: Path) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        previous = GENESIS_HASH
        ids: set[str] = set()
        with path.open("rb") as stream:
            for sequence, line in enumerate(stream, 1):
                try:
                    if not line.endswith(b"\n"):
                        raise ValueError("incomplete final line")
                    record = json.loads(line)
                    expected_keys = {
                        "version",
                        "sequence",
                        "event_id",
                        "kind",
                        "recorded_at",
                        "prev_hash",
                        "payload",
                        "hash",
                    }
                    if set(record) != expected_keys:
                        raise ValueError("invalid envelope")
                    claimed = record["hash"]
                    unsigned = {k: v for k, v in record.items() if k != "hash"}
                    if (
                        record["version"] != 1
                        or record["sequence"] != sequence
                        or record["prev_hash"] != previous
                        or claimed != digest(unsigned)
                        or record["event_id"] in ids
                        or canonical(record) + b"\n" != line
                    ):
                        raise ValueError("hash, sequence, identity, or encoding mismatch")
                    records.append(record)
                    ids.add(record["event_id"])
                    previous = claimed
                except (ValueError, KeyError, TypeError) as exc:
                    raise LedgerError(f"Invalid ledger record at line {sequence}") from exc
        return records

    def append(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self._file is None or self._failed:
            raise LedgerError("Ledger is closed or a prior write failed; reopen and verify")
        record = {
            "version": 1,
            "sequence": len(self.records) + 1,
            "event_id": str(uuid4()),
            "kind": kind,
            "recorded_at": timestamp(utc_now()),
            "prev_hash": self.records[-1]["hash"] if self.records else GENESIS_HASH,
            "payload": payload,
        }
        record["hash"] = digest(record)
        line = canonical(record) + b"\n"
        try:
            self._file.write(line)
            self._file.flush()
            os.fsync(self._file.fileno())
        except BaseException:
            self._failed = True
            raise
        self.records.append(record)
        return record
