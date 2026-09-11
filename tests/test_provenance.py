import os
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from conftest import CANDIDATE, FakeSec

from agentic_quant_lab.config import Settings
from agentic_quant_lab.ledger import digest
from agentic_quant_lab.provenance import provenance
from agentic_quant_lab.recorder import Recorder
from agentic_quant_lab.sec import Candidate

SEEN = datetime(2026, 9, 10, 10, tzinfo=UTC)


def test_code_and_nonsecret_config_are_attributable(settings: Settings) -> None:
    secret = "synthetic-private-value"
    settings = replace(
        settings, database_url=secret, heartbeat_url=secret, sec_user_agent=secret, git_sha="a" * 40
    )
    context = provenance(settings)
    assert context["git_sha"] == "a" * 40
    assert len(context["source_tree_sha256"]) == 64
    assert context["config_sha256"] == digest(context["config"])
    assert secret not in str(context)
    assert secret not in repr(settings)
    assert provenance(settings) == context


def test_raw_ingestion_scope_does_not_define_research_eligibility(settings: Settings) -> None:
    other = Candidate.from_url(
        "https://www.sec.gov/Archives/edgar/data/789019/0000789019-24-000123.txt"
    )
    settings = replace(settings, ingestion_ciks=("320193", "789019"))
    with Recorder(settings, FakeSec(), lambda: SEEN) as recorder:
        recorder.snapshot_universe()
        assert recorder.ingest_many([CANDIDATE, other]) == 2
        snapshot = recorder.ledger.records[0]["payload"]
        assert snapshot["ciks"] == ["320193"]
        assert snapshot["as_of"] == SEEN.isoformat()
        assert snapshot["screen_version"] == "explicit-cik-list-v1"
        assert snapshot["screen_config_sha256"] == snapshot["universe_hash"]
        filings = [r["payload"] for r in recorder.ledger.records if r["kind"] == "filing"]
        assert all(p["availability_mode"] == "observed" for p in filings)
        assert all("source_tree_sha256" in p["provenance"] for p in filings)
        recorder.reconcile()


def test_offline_settings_do_not_require_sec_contact(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql:///unused")
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    assert Settings.from_env(require_sec=False).sec_user_agent == ""
    with pytest.raises(ValueError):
        Settings.from_env()
    assert os.getenv("SEC_USER_AGENT") is None
