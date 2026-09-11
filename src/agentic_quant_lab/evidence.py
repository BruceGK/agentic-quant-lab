import base64
import hashlib
from datetime import date, datetime
from typing import Any
from uuid import UUID

from agentic_quant_lab.ledger import LedgerError, digest, timestamp
from agentic_quant_lab.sec import (
    Candidate,
    parse_daily_index,
    parse_full_index,
    submission_metadata,
)


def evidence_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if timestamp(parsed) != value:
        raise ValueError("Evidence timestamps must use canonical UTC")
    return parsed


def verify_evidence(records: list[dict[str, Any]]) -> None:
    """Check content and cross-event meaning, in addition to the JSONL envelope chain."""
    discoveries: dict[tuple[str, str], dict[str, Any]] = {}
    filings: set[tuple[str, str]] = set()
    universes: dict[str, set[str]] = {}
    event_ids: set[str] = set()
    for record in records:
        try:
            UUID(record["event_id"])
            evidence_time(record["recorded_at"])
            p = record["payload"]
            kind = record["kind"]
            if not isinstance(p, dict):
                raise ValueError("Payload must be an object")
            if "provenance" in p:
                context = p["provenance"]
                if digest(context["config"]) != context["config_sha256"]:
                    raise ValueError("Provenance configuration hash mismatch")
            if kind in ("discovery", "filing"):
                candidate = Candidate.from_url(p["document_url"])
                if (p["source"], p["external_id"], p["cik"]) != (
                    "sec",
                    candidate.external_id,
                    candidate.cik,
                ):
                    raise ValueError("Filing identity mismatch")
                key = (p["source"], p["external_id"])
                seen = evidence_time(p["first_seen_at"])
                if kind == "discovery":
                    if key in discoveries:
                        raise ValueError("Duplicate discovery identity")
                    discoveries[key] = p
                else:
                    if key in filings or key not in discoveries:
                        raise ValueError("Duplicate filing or missing discovery")
                    original = discoveries[key]
                    if any(
                        p[field] != original[field]
                        for field in ("first_seen_at", "cik", "document_url")
                    ):
                        raise ValueError("Filing disagrees with its first discovery")
                    content = base64.b64decode(p["content_base64"], validate=True)
                    accepted, form = submission_metadata(content, candidate)
                    fetched = evidence_time(p["fetched_at"])
                    eligible = evidence_time(p["decision_eligible_at"])
                    if (
                        hashlib.sha256(content).hexdigest() != p["content_sha256"]
                        or timestamp(accepted) != p["accepted_at"]
                        or form != p["form_type"]
                        or not seen <= fetched == eligible
                        or accepted > fetched
                        or p.get("availability_mode", "observed") != "observed"
                    ):
                        raise ValueError("Content or prospective time mismatch")
                    filings.add(key)
            elif kind == "universe":
                config = {"source": "sec", "ciks": sorted(set(p["ciks"]))}
                if digest(config) != p["universe_hash"]:
                    raise ValueError("Universe configuration hash mismatch")
                if "as_of" in p:
                    evidence_time(p["as_of"])
                universes[p["universe_hash"]] = set(p["ciks"])
            elif kind in ("reconciliation", "archive_recovery"):
                content = base64.b64decode(p["index_base64"], validate=True)
                if hashlib.sha256(content).hexdigest() != p["index_sha256"]:
                    raise ValueError("Index content hash mismatch")
                if ("ingestion_ciks" in p) != ("ingestion_scope_hash" in p):
                    raise ValueError("Ingestion scope metadata must be complete")
                ciks = set(p.get("ingestion_ciks", universes[p["universe_hash"]]))
                if (
                    "ingestion_scope_hash" in p
                    and digest({"source": "sec", "ciks": sorted(ciks)}) != p["ingestion_scope_hash"]
                ):
                    raise ValueError("Ingestion scope hash mismatch")
                candidates = (
                    parse_daily_index(content, date.fromisoformat(p["day"]))
                    if kind == "reconciliation"
                    else parse_full_index(content, p["year"], p["quarter"])
                )
                if any(("sec", c.external_id) not in filings for c in candidates if c.cik in ciks):
                    raise ValueError("Checkpoint precedes required filing evidence")
            elif kind == "correction":
                if (
                    p["supersedes_event_id"] not in event_ids
                    or not isinstance(p["reason"], str)
                    or not p["reason"].strip()
                    or not isinstance(p["changes"], dict)
                    or not p["changes"]
                ):
                    raise ValueError("Invalid correction provenance")
            else:
                raise ValueError("Unknown evidence kind")
            event_ids.add(record["event_id"])
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise LedgerError(
                f"Invalid evidence semantics at sequence {record.get('sequence')}"
            ) from exc
