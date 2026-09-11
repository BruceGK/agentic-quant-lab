import argparse
import json
from datetime import date
from pathlib import Path
from urllib.request import Request, build_opener

from agentic_quant_lab.config import Settings
from agentic_quant_lab.evidence import verify_evidence
from agentic_quant_lab.ledger import Ledger, canonical
from agentic_quant_lab.recorder import Recorder
from agentic_quant_lab.sec import Candidate, NoRedirect, SecClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Prospective SEC evidence recorder")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest-one")
    ingest.add_argument("url")
    commands.add_parser("record")
    catchup = commands.add_parser("catch-up")
    catchup.add_argument("--start", type=date.fromisoformat, required=True)
    catchup.add_argument("--end", type=date.fromisoformat, required=True)
    commands.add_parser("replay")
    commands.add_parser("reconcile")
    commands.add_parser("snapshot")
    verify = commands.add_parser("verify")
    verify.add_argument("ledger", type=Path)
    correction = commands.add_parser("correct")
    correction.add_argument("event_id")
    correction.add_argument("--reason", required=True)
    correction.add_argument("--changes", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "verify":
        records = Ledger.verify(args.ledger)
        verify_evidence(records)
        print(json.dumps({"verified_records": len(records)}))
        return
    settings = Settings.from_env()
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
        elif args.command == "snapshot":
            recorder.snapshot_universe()
        elif args.command == "correct":
            changes = json.loads(args.changes.read_text())
            if not isinstance(changes, dict):
                raise ValueError("Correction changes must be a JSON object")
            recorder.correct(args.event_id, args.reason, changes)
        head = recorder.ledger.records[-1] if recorder.ledger.records else None
        status = {
            "new_filings": count,
            "sequence": head["sequence"] if head else 0,
            "hash": head["hash"] if head else None,
        }
        if args.command in ("record", "catch-up"):
            recorder.reconcile()
        if settings.heartbeat_url and args.command in ("record", "catch-up"):
            request = Request(
                settings.heartbeat_url,
                data=canonical(status),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with build_opener(NoRedirect()).open(request, timeout=20) as response:
                response.read(1024)
        print(json.dumps(status))


if __name__ == "__main__":
    main()
