"""Recover a deliberately unrecorded SEC interval in the isolated acceptance projection."""

import json
import sys
from dataclasses import replace
from datetime import datetime

import psycopg
from azure.core.exceptions import AzureError
from azure.storage.blob import ContainerClient
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from agentic_quant_lab.azure_auth import azure_credential
from agentic_quant_lab.blob_ledger import BlobLedger
from agentic_quant_lab.config import BlobSettings, Settings
from agentic_quant_lab.database import Projection, connect_database
from agentic_quant_lab.evidence import verify_evidence
from agentic_quant_lab.ledger import canonical, utc_now
from agentic_quant_lab.recorder import Recorder
from agentic_quant_lab.sec import SecClient


def main() -> None:
    try:
        settings = Settings.from_env()
        if (
            settings.azure_ledger is None
            or settings.catchup_start is None
            or conninfo_to_dict(settings.database_url).get("dbname") != "aql"
        ):
            raise ValueError("Acceptance requires the provisioned Azure recorder")
        day = settings.catchup_start
        with BlobLedger(settings.azure_ledger) as production:
            baseline = production.records[:1]
            if len(baseline) != 1 or baseline[0]["kind"] != "universe":
                raise ValueError("An independently restorable universe baseline is required")
            verify_evidence(baseline)
        prefix = f"acceptance/missed-sec-{day.isoformat()}"
        target_blob = BlobSettings(
            settings.azure_ledger.account_url, settings.azure_ledger.container, prefix
        )
        target = replace(
            settings,
            database_url=make_conninfo(settings.database_url, dbname="aql_test"),
            azure_ledger=target_blob,
            heartbeat_url=None,
        )
        with connect_database(target) as connection:
            Projection(connection).reconcile(baseline)
        with BlobLedger(target_blob) as isolated:
            if isolated.records:
                raise ValueError("Acceptance namespace is already used; do not overwrite it")
        with (
            azure_credential() as credential,
            ContainerClient(
                target_blob.account_url, target_blob.container, credential=credential
            ) as container,
        ):
            container.upload_blob(
                f"{prefix}/records/00000000000000000001.jsonl",
                canonical(baseline[0]) + b"\n",
                overwrite=False,
            )
        started = utc_now()
        # The restored baseline has no filing or daily checkpoint; latest() is never called.
        with Recorder(target, SecClient(target.sec_user_agent)) as recorder:
            recovered = recorder.catch_up(day, day, force=True)
            recorder.reconcile()
            records = list(recorder.ledger.records)
            filings = [record["payload"] for record in records if record["kind"] == "filing"]
            if recovered < 1 or any(
                datetime.fromisoformat(payload["first_seen_at"]) < started
                or payload["fetched_at"] != payload["decision_eligible_at"]
                for payload in filings
            ):
                raise ValueError("Real recovery did not preserve prospective evidence")
        with Recorder(target, SecClient(target.sec_user_agent)) as restarted:
            duplicates = restarted.catch_up(day, day, force=True)
            restarted.reconcile()
            if duplicates != 0 or restarted.ledger.records != records:
                raise ValueError("Recovered interval is not idempotent")
        print(
            json.dumps(
                {
                    "event": "aql.acceptance.missed-interval",
                    "status": "success",
                    "database": "aql_test",
                    "prefix": prefix,
                    "day": day.isoformat(),
                    "latest_feed_used": False,
                    "recovered_filings": recovered,
                    "rerun_new_filings": duplicates,
                    "prospective_timestamps": "passed",
                    "sequence": len(records),
                    "hash": records[-1]["hash"],
                    "reconciliation": "passed",
                    "external_ids": [payload["external_id"] for payload in filings],
                }
            ),
            flush=True,
        )
    except (AzureError, psycopg.Error, OSError, ValueError, KeyError, RuntimeError, ExceptionGroup):
        print(
            json.dumps({"event": "aql.acceptance.missed-interval", "status": "failed"}),
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
