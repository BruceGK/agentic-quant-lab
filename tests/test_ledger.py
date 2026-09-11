import json
from pathlib import Path

import pytest

from agentic_quant_lab.ledger import Ledger, LedgerError, canonical


def test_hash_chain_and_tampering(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    with Ledger(path) as ledger:
        first = ledger.append("universe", {"ciks": ["320193"]})
        second = ledger.append("universe", {"ciks": ["789019"]})
    assert second["prev_hash"] == first["hash"]
    assert len(Ledger.verify(path)) == 2
    lines = path.read_bytes().splitlines(keepends=True)
    changed = json.loads(lines[0])
    changed["payload"]["ciks"] = ["1"]
    lines[0] = canonical(changed) + b"\n"
    path.write_bytes(b"".join(lines))
    with pytest.raises(LedgerError, match="line 1"):
        Ledger.verify(path)


def test_incomplete_tail_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    with Ledger(path) as ledger:
        ledger.append("universe", {"ciks": ["1"]})
    original = path.read_bytes()
    path.write_bytes(original[:-1])
    with pytest.raises(LedgerError):
        with Ledger(path):
            pass
    assert path.read_bytes() == original[:-1]


def test_exclusive_writer(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    with Ledger(path), pytest.raises(BlockingIOError), Ledger(path):
        pass
