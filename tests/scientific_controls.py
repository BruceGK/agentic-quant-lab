"""Synthetic IID control fixtures, not a market-data or investment-evidence implementation."""

import math
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from statistics import mean


class PointInTimeViolation(ValueError):
    pass


@dataclass(frozen=True)
class SyntheticObservation:
    score: float
    outcome: float
    available_at: datetime
    decision_at: datetime
    outcome_at: datetime


@dataclass(frozen=True)
class SyntheticExperiment:
    seed: int
    planted_effect: float
    observations: tuple[SyntheticObservation, ...]
    generator_version: str = "iid-linear-controls-v1"
    synthetic_only: bool = True


@dataclass(frozen=True)
class EffectEstimate:
    effect: float
    standard_error: float
    lower: float
    upper: float


def generate_control(seed: int, effect: float, n: int = 256) -> SyntheticExperiment:
    rng = random.Random(seed)
    epoch = datetime(2020, 1, 1, tzinfo=UTC)
    rows = []
    for i in range(n):
        score = rng.gauss(0, 1)
        outcome = effect * score + rng.gauss(0, 1)
        decision = epoch + timedelta(days=i)
        rows.append(
            SyntheticObservation(score, outcome, decision, decision, decision + timedelta(days=1))
        )
    return SyntheticExperiment(seed, effect, tuple(rows))


def estimate_control(experiment: SyntheticExperiment) -> EffectEstimate:
    if not experiment.synthetic_only or len(experiment.observations) < 3:
        raise ValueError("This fixture estimator accepts synthetic controls with n >= 3 only")
    rows = experiment.observations
    for row in rows:
        if any(
            t.tzinfo is None or t.utcoffset() is None
            for t in (row.available_at, row.decision_at, row.outcome_at)
        ):
            raise PointInTimeViolation("Naive timestamps cannot establish availability")
        if not row.available_at <= row.decision_at < row.outcome_at:
            raise PointInTimeViolation("Feature not available at decision time, or outcome leaked")
        if not math.isfinite(row.score) or not math.isfinite(row.outcome):
            raise ValueError("Synthetic observations must be finite")
    x_bar = mean(r.score for r in rows)
    y_bar = mean(r.outcome for r in rows)
    sxx = sum((r.score - x_bar) ** 2 for r in rows)
    if sxx == 0:
        raise ValueError("Control scores must vary")
    slope = sum((r.score - x_bar) * (r.outcome - y_bar) for r in rows) / sxx
    intercept = y_bar - slope * x_bar
    residual_variance = sum((r.outcome - intercept - slope * r.score) ** 2 for r in rows) / (
        len(rows) - 2
    )
    se = math.sqrt(residual_variance / sxx)
    return EffectEstimate(slope, se, slope - 1.96 * se, slope + 1.96 * se)
