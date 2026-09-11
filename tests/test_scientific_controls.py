import math
from dataclasses import replace
from statistics import mean, stdev

import pytest
from scientific_controls import (
    PointInTimeViolation,
    estimate_control,
    generate_control,
)


@pytest.mark.parametrize("effect", [0.0, 0.75])
def test_null_and_positive_controls_recover_known_effect_with_calibrated_uncertainty(
    effect: float,
) -> None:
    estimates = [estimate_control(generate_control(seed, effect)) for seed in range(100)]
    average = mean(e.effect for e in estimates)
    empirical_se = stdev(e.effect for e in estimates)
    assert abs(average - effect) < 3 * empirical_se / math.sqrt(len(estimates))
    assert 0.8 < mean(e.standard_error for e in estimates) / empirical_se < 1.2
    coverage = mean(e.lower <= effect <= e.upper for e in estimates)
    assert 0.88 <= coverage <= 1.0  # Monte Carlo tolerance, not a real-data calibration claim.
    if effect:
        assert all(e.lower > 0 for e in estimates)


def test_generator_is_seeded_attributable_and_immutable() -> None:
    experiment = generate_control(42, 0.0)
    assert experiment == generate_control(42, 0.0)
    assert experiment != generate_control(43, 0.0)
    assert experiment.generator_version == "iid-linear-controls-v1"
    assert experiment.synthetic_only
    assert isinstance(experiment.observations, tuple)


def test_deliberate_future_information_invalidates_experiment() -> None:
    experiment = generate_control(42, 0.0)
    leaked = replace(
        experiment,
        observations=tuple(
            replace(row, score=row.outcome, available_at=row.outcome_at)
            for row in experiment.observations
        ),
    )
    with pytest.raises(PointInTimeViolation, match="not available"):
        estimate_control(leaked)


def test_naive_time_cannot_bypass_availability_guard() -> None:
    experiment = generate_control(42, 0.0)
    first = experiment.observations[0]
    invalid = replace(
        experiment,
        observations=(
            replace(first, available_at=first.available_at.replace(tzinfo=None)),
            *experiment.observations[1:],
        ),
    )
    with pytest.raises(PointInTimeViolation, match="Naive"):
        estimate_control(invalid)


def test_fixture_estimator_cannot_be_used_as_real_research_evidence() -> None:
    with pytest.raises(ValueError, match="synthetic controls"):
        estimate_control(replace(generate_control(42, 0.0), synthetic_only=False))
