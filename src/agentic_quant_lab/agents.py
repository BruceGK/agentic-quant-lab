from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Hypothesis:
    title: str
    rationale: str
    source: str


@dataclass(frozen=True)
class ExperimentSpec:
    hypothesis: Hypothesis
    universe: tuple[str, ...]
    signal: str = "3-period momentum, skip latest period (compressed demo, NOT real 12-1)"
    rebalance: str = "monthly fixture observations; execute one observation later"
    fee_bps: float = 10
    delay: int = 1
    lookback: int = 3
    allocation: float = 0.2
    constraints: tuple[str, ...] = (
        "long-only; no leverage",
        "features available by decision time; no same-close execution",
        "null and planted-positive controls; deterministic reproduction",
        "fixture results cannot promote a real research candidate",
    )


class ResearchAgent(Protocol):
    def propose(self, universe: tuple[str, ...]) -> ExperimentSpec: ...


class DemoResearchAgent:
    """Deterministic stand-in for a future hypothesis-generating LLM, not a live agent."""

    def propose(self, universe: tuple[str, ...]) -> ExperimentSpec:
        return ExperimentSpec(
            hypothesis=Hypothesis(
                title="Sector Relative Momentum",
                rationale="Can lagged relative strength recover a deliberately planted trend?",
                source="deterministic demo agent; synthetic illustration, not investment advice",
            ),
            universe=universe,
        )
