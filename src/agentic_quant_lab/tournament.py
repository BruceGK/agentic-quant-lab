import json
from dataclasses import dataclass
from importlib.resources import files
from typing import Literal


@dataclass(frozen=True)
class StrategyCandidate:
    id: str
    name: str
    status: str
    metrics: dict[str, float]
    evidence_quality: str
    data_quality: str
    known_limitations: tuple[str, ...]
    source: Literal["demo", "real_research"]
    report: str = ""
    branch: str = ""
    commit: str = ""


def research_candidates() -> list[StrategyCandidate]:
    source = files("agentic_quant_lab").joinpath("resources/research_status.json")
    records = json.loads(source.read_text(encoding="utf-8"))["candidates"]
    return [
        StrategyCandidate(**{**row, "known_limitations": tuple(row["known_limitations"])})
        for row in records
    ]


def rank_demo(candidates: list[StrategyCandidate]) -> list[StrategyCandidate]:
    if any(candidate.source != "demo" for candidate in candidates):
        raise ValueError("Synthetic tournament must never rank real research")
    return sorted(candidates, key=lambda c: (-c.metrics["total_return"], c.id))
