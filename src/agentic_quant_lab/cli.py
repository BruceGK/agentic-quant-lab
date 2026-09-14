import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from urllib.request import Request, build_opener

from agentic_quant_lab.blob_ledger import BlobLedger
from agentic_quant_lab.config import BlobSettings, Settings
from agentic_quant_lab.constitution import check_recording_policy
from agentic_quant_lab.evidence import verify_evidence
from agentic_quant_lab.ledger import GENESIS_HASH, Ledger, LedgerError, canonical, export_records
from agentic_quant_lab.recorder import Recorder
from agentic_quant_lab.sec import Candidate, NoRedirect, SecClient


def main() -> None:
    try:
        run()
    except Exception as exc:
        # Provider exceptions can include credential fragments, even when the complete
        # secret is masked by CI. Never print messages or chained tracebacks here.
        code = "integrity_check_failed" if isinstance(exc, LedgerError) else "recorder_failed"
        print(json.dumps({"status": "failed", "error": code}), file=sys.stderr)
        raise SystemExit(1) from None


def run() -> None:
    parser = argparse.ArgumentParser(description="Prospective SEC evidence recorder")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest-one")
    ingest.add_argument("url")
    commands.add_parser("record")
    catchup = commands.add_parser("catch-up")
    catchup.add_argument("--start", type=date.fromisoformat, required=True)
    catchup.add_argument("--end", type=date.fromisoformat, required=True)
    archive = commands.add_parser("recover-quarter")
    archive.add_argument("--year", type=int, required=True)
    archive.add_argument("--quarter", type=int, required=True)
    commands.add_parser("replay")
    commands.add_parser("reconcile")
    commands.add_parser("snapshot")
    verify = commands.add_parser("verify")
    verify.add_argument("ledger", type=Path)
    verify_blob = commands.add_parser("verify-blob")
    export = commands.add_parser("export-ledger")
    export.add_argument("destination", type=Path)
    for command in (verify, verify_blob, export):
        command.add_argument("--expected-head")
        command.add_argument("--expected-sequence", type=int)
    correction = commands.add_parser("correct")
    correction.add_argument("event_id")
    correction.add_argument("--reason", required=True)
    correction.add_argument("--changes", type=Path, required=True)
    args = parser.parse_args()
    if args.command in ("record", "catch-up", "ingest-one", "recover-quarter"):
        check_recording_policy(os.getenv("RECORDER_RUN_MODE", "local"))
    if args.command in ("verify", "verify-blob", "export-ledger"):
        if args.command == "verify":
            records = Ledger.verify(args.ledger)
        else:
            blob_settings = BlobSettings.from_env()
            if blob_settings is None:
                raise ValueError("This command requires LEDGER_BACKEND=azure")
            with BlobLedger(blob_settings) as ledger:
                records = ledger.records
        verify_evidence(records)
        head = records[-1]["hash"] if records else GENESIS_HASH
        if (args.expected_head is not None and args.expected_head != head) or (
            args.expected_sequence is not None and args.expected_sequence != len(records)
        ):
            raise LedgerError("Ledger does not match the independently retained head")
        if args.command == "export-ledger":
            export_records(records, args.destination)
        print(json.dumps({"verified_records": len(records), "hash": head}))
        return
    settings = Settings.from_env(
        require_sec=args.command in ("record", "catch-up", "ingest-one", "recover-quarter")
    )
    with Recorder(
        settings, SecClient(settings.sec_user_agent), replay=args.command != "reconcile"
    ) as recorder:
        count = 0
        if args.command == "ingest-one":
            count = int(recorder.ingest(Candidate.from_url(args.url)))
        elif args.command == "record":
            count = recorder.record()
        elif args.command == "catch-up":
            count = recorder.catch_up(args.start, args.end, force=True)
        elif args.command == "recover-quarter":
            count = recorder.recover_quarter(args.year, args.quarter)
        elif args.command == "snapshot":
            recorder.snapshot_universe()
        elif args.command == "correct":
            changes = json.loads(args.changes.read_text())
            if not isinstance(changes, dict):
                raise ValueError("Correction changes must be a JSON object")
            recorder.correct(args.event_id, args.reason, changes)
        head = recorder.ledger.records[-1] if recorder.ledger.records else None
        status = {
            "status": "success",
            "new_filings": count,
            "sequence": head["sequence"] if head else 0,
            "hash": head["hash"] if head else GENESIS_HASH,
            "heartbeat": "not_requested",
        }
        if args.command != "reconcile":
            recorder.reconcile()
        if args.command in ("record", "catch-up"):
            status["heartbeat"] = "disabled"
        if settings.heartbeat_url and args.command in ("record", "catch-up"):
            request = Request(
                settings.heartbeat_url,
                data=canonical({k: v for k, v in status.items() if k != "heartbeat"}),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with build_opener(NoRedirect()).open(request, timeout=20) as response:
                if not 200 <= response.status < 300:
                    raise RuntimeError("Heartbeat was not acknowledged")
                response.read(1024)
            status["heartbeat"] = "sent"
        status.update(
            command=args.command,
            ledger_backend="azure" if settings.azure_ledger else "local",
            reconciliation="passed",
        )
        if args.command in ("record", "catch-up"):
            status["event"] = "aql.recorder.completed"
    print(json.dumps(status))


if __name__ == "__main__":
    main()
