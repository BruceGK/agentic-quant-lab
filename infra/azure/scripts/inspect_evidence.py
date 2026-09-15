"""Read-only acceptance metadata from the private runtime, without SEC contact access."""

import json
import sys

import psycopg
from azure.core.exceptions import AzureError

from agentic_quant_lab.config import Settings
from agentic_quant_lab.ledger import GENESIS_HASH
from agentic_quant_lab.recorder import Recorder
from agentic_quant_lab.sec import SecClient

FIELDS = (
    "source",
    "external_id",
    "cik",
    "accepted_at",
    "first_seen_at",
    "fetched_at",
    "decision_eligible_at",
    "content_sha256",
)


def main() -> None:
    try:
        settings = Settings.from_env(require_sec=False)
        with Recorder(settings, SecClient(""), replay=False) as recorder:
            records = recorder.ledger.records
            filings = [record for record in records if record["kind"] == "filing"]
            for record in filings:
                print(
                    json.dumps(
                        {
                            "event": "aql.acceptance.filing",
                            "sequence": record["sequence"],
                            "record_hash": record["hash"],
                            "prev_hash": record["prev_hash"],
                            **{field: record["payload"][field] for field in FIELDS},
                        }
                    ),
                    flush=True,
                )
            print(
                json.dumps(
                    {
                        "event": "aql.acceptance.state",
                        "sequence": len(records),
                        "hash": records[-1]["hash"] if records else GENESIS_HASH,
                        "filings": len(filings),
                        "reconciled": True,
                        "checkpoint_days": [
                            record["payload"]["day"]
                            for record in records
                            if record["kind"] == "reconciliation"
                        ],
                    }
                ),
                flush=True,
            )
    except (AzureError, psycopg.Error, OSError, ValueError, KeyError, RuntimeError):
        print(
            json.dumps({"event": "aql.acceptance.state", "status": "failed"}),
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
