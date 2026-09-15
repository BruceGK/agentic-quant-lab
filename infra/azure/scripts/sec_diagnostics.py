"""Bounded SEC checks inside the job; never log request headers or provider messages."""

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from http.client import HTTPException
from urllib.error import HTTPError

from agentic_quant_lab.config import Settings
from agentic_quant_lab.sec import (
    SEC_ORIGIN,
    Candidate,
    SecClient,
    parse_daily_index,
    parse_latest,
    submission_metadata,
)


def main(*, directory_only: bool = False) -> None:
    try:
        settings = Settings.from_env()
    except (ValueError, KeyError):
        print(
            json.dumps(
                {"event": "aql.diagnostics.sec", "stage": "configuration", "status": "failed"}
            )
        )
        raise SystemExit(1) from None
    if settings.catchup_start is None:
        raise ValueError("An explicit catch-up date is required")
    days = [settings.catchup_start + timedelta(days=offset) for offset in range(-2, 4)]
    quarter_path = (
        f"/Archives/edgar/daily-index/{settings.catchup_start.year}/"
        f"QTR{(settings.catchup_start.month - 1) // 3 + 1}"
    )
    requests: list[tuple[str, str, date | None]] = [
        (
            "latest",
            f"{SEC_ORIGIN}/cgi-bin/browse-edgar?action=getcurrent"
            "&owner=include&count=100&output=atom",
            None,
        ),
        *[
            (
                "daily-index",
                f"{SEC_ORIGIN}/Archives/edgar/daily-index/{day.year}/"
                f"QTR{(day.month - 1) // 3 + 1}/master.{day:%Y%m%d}.idx",
                day,
            )
            for day in days
        ],
        (
            "submission",
            f"{SEC_ORIGIN}/Archives/edgar/data/320193/0000320193-24-000123.txt",
            None,
        ),
        ("quarter-directory", f"{SEC_ORIGIN}{quarter_path}/index.json", None),
    ]
    client = SecClient(settings.sec_user_agent)
    failures = 0
    for operation, url, day in requests:
        if directory_only and operation != "quarter-directory":
            continue
        result: dict[str, object] = {
            "event": "aql.diagnostics.sec",
            "operation": operation,
            "day": day.isoformat() if day else None,
        }
        try:
            body = client.get(url)
            if operation == "latest":
                count = len(parse_latest(body))
            elif operation == "daily-index" and day is not None:
                candidates = parse_daily_index(body, day)
                count = len(candidates)
                result["selected_accessions"] = [
                    candidate.external_id
                    for candidate in candidates
                    if candidate.cik in settings.ingestion_scope
                ]
            elif operation == "quarter-directory":
                directory = json.loads(body)["directory"]
                name = directory["name"]
                if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9/_.-]+", name):
                    raise ValueError("Unexpected index directory name")
                result["directory_path"] = name
                if name.rstrip("/") not in (
                    quarter_path,
                    quarter_path.removeprefix("/Archives/edgar/"),
                ):
                    raise ValueError("Unexpected index directory")
                names = {item["name"] for item in directory["item"]}
                count = len(names)
                result["published_days"] = [
                    day.isoformat() for day in days if f"master.{day:%Y%m%d}.idx" in names
                ]
            else:
                submission_metadata(body, Candidate.from_url(url))
                count = 1
            result.update(
                status="success",
                parsed_records=count,
                content_bytes=len(body),
                content_sha256=hashlib.sha256(body).hexdigest(),
            )
        except (OSError, ValueError, HTTPException, ET.ParseError) as error:
            failures += 1
            result.update(
                status="failed",
                errorType=type(error).__name__,
                httpStatus=error.code if isinstance(error, HTTPError) else None,
            )
        print(json.dumps(result), flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main(directory_only="--directory-only" in sys.argv[1:])
