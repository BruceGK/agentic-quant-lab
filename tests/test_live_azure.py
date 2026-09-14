import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from azure.storage.blob import ContainerClient
from conftest import DatabaseConfig

from agentic_quant_lab.azure_auth import azure_credential
from agentic_quant_lab.blob_ledger import BlobLedger
from agentic_quant_lab.config import BlobSettings, Settings
from agentic_quant_lab.evidence import verify_evidence
from agentic_quant_lab.ledger import Ledger, LedgerError, digest, export_records
from agentic_quant_lab.recorder import Recorder
from agentic_quant_lab.sec import SecClient

pytestmark = [
    pytest.mark.live_azure,
    pytest.mark.postgres,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_AZURE") != "1", reason="Set RUN_LIVE_AZURE=1 for real Azure persistence"
    ),
]


def test_real_blob_conditional_commit_and_independent_postgres_replay(
    database: DatabaseConfig, tmp_path: Path
) -> None:
    settings = BlobSettings(
        os.environ["TEST_AZURE_STORAGE_ACCOUNT_URL"],
        os.getenv("TEST_AZURE_STORAGE_CONTAINER", "aql-audit-acceptance"),
        f"acceptance/{uuid4().hex}",
    )
    created: list[str] = []
    try:
        with BlobLedger(settings) as first, BlobLedger(settings) as competing:
            payload = {"source": "sec", "ciks": ["320193"]}
            record = first.append("universe", {**payload, "universe_hash": digest(payload)})
            created.append(f"{settings.prefix}/records/{record['sequence']:020d}.jsonl")
            with pytest.raises(LedgerError, match="sequence already exists"):
                competing.append("universe", {**payload, "universe_hash": digest(payload)})
            correction = first.append(
                "correction",
                {
                    "supersedes_event_id": record["event_id"],
                    "reason": "Isolated Azure persistence acceptance; not SEC filing evidence",
                    "changes": {"acceptance_only": True},
                },
            )
            created.append(f"{settings.prefix}/records/{correction['sequence']:020d}.jsonl")
            assert first.read_records() == first.records
        with BlobLedger(settings) as restarted:
            records = restarted.records
            assert len(records) == 2
            assert records[1]["prev_hash"] == records[0]["hash"]
            verify_evidence(records)
            destination = tmp_path / "independent-export.jsonl"
            export_records(records, destination)
        assert Ledger.verify(destination) == records
        local_settings = Settings(database.writer_dsn, destination, "")
        for _ in range(2):
            with Recorder(local_settings, SecClient("")) as restored:
                restored.reconcile()
        with psycopg.connect(database.writer_dsn) as connection:
            assert connection.execute("SELECT count(*) FROM audit_events").fetchone() == (2,)
            assert connection.execute("SELECT count(*) FROM corrections").fetchone() == (1,)
            assert connection.execute("SELECT count(*) FROM filings").fetchone() == (0,)
    finally:
        with (
            azure_credential() as credential,
            ContainerClient(
                settings.account_url, settings.container, credential=credential
            ) as container,
        ):
            for name in created:
                container.delete_blob(name)
