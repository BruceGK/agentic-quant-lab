from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from research.engine import (
    AvailabilityError,
    Plan,
    block_interval,
    constant_plan,
    momentum_plan,
    rebalance,
    simulate,
    summary,
    trend_plan,
)


def frame(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"asset": values}, index=pd.bdate_range("2000-01-03", periods=len(values)))


def test_signal_cannot_earn_same_close_or_next_session_return():
    prices = frame([100.0, 110.0, 121.0, 242.0, 242.0])
    targets = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    targets.iloc[1] = 1.0
    plan = Plan(targets, pd.Series(prices.index, index=prices.index))
    run = simulate(prices, plan, pd.Series(0.0, index=prices.index), fee_bps=0)
    assert run.returns.tolist() == [0, 0, 0, 1, 0]
    with pytest.raises(AvailabilityError):
        simulate(prices, plan, pd.Series(0.0, index=prices.index), fee_bps=0, delay=0)


def test_exact_entry_and_exit_cost_is_self_financing():
    cost, traded = rebalance(np.array([0.0]), np.array([1.0]), 0.01)
    assert 1 - cost == pytest.approx(1 / 1.01)
    assert traded == pytest.approx(1 / 1.01)
    cost, traded = rebalance(np.array([1.0]), np.array([0.0]), 0.01)
    assert cost == pytest.approx(0.01)
    assert traded == pytest.approx(1.0)


def test_turnover_uses_drifted_weights_not_previous_targets():
    prices = pd.DataFrame(
        {"a": [1.0, 1.0, 2.0], "b": [1.0, 1.0, 1.0]},
        index=pd.bdate_range("2000-01-03", periods=3),
    )
    plan = constant_plan(prices, {"a": 0.5, "b": 0.5}, "every")
    run = simulate(prices, plan, pd.Series(0.0, index=prices.index), fee_bps=0)
    assert run.returns.iloc[-1] == pytest.approx(0.5)
    assert run.traded.iloc[-1] == pytest.approx(1 / 3)


def test_constant_cash_preserves_realized_interest():
    prices = frame([1.0] * 4)
    run = simulate(
        prices,
        constant_plan(prices, {"asset": 0.0}, "every"),
        pd.Series(0.001, index=prices.index),
        fee_bps=15,
    )
    assert run.returns.iloc[1:].tolist() == pytest.approx([0.001] * 3)
    assert run.costs.sum() == 0


def test_future_availability_is_rejected_not_just_shifted():
    prices = frame([1.0] * 20)
    plan = constant_plan(prices, {"asset": 1.0}, "every")
    leaked = replace(plan, available_at=plan.available_at + pd.Timedelta(days=1))
    with pytest.raises(AvailabilityError, match="unavailable"):
        simulate(prices, leaked, pd.Series(0.0, index=prices.index), fee_bps=0)


def test_future_price_changes_cannot_change_past_signals_or_returns():
    rng = np.random.default_rng(42)
    prices = frame((100 * np.cumprod(1 + rng.normal(0, 0.01, 300))).tolist())
    altered = prices.copy()
    altered.iloc[200:] *= np.linspace(1, 20, 100)[:, None]
    cash = pd.Series(0.0, index=prices.index)
    for rule in ("sma", "absolute", "dual"):
        original = simulate(prices, trend_plan(prices, kind=rule, lookback=30), cash, fee_bps=5)
        future = simulate(altered, trend_plan(altered, kind=rule, lookback=30), cash, fee_bps=5)
        pd.testing.assert_series_equal(original.returns.iloc[:200], future.returns.iloc[:200])


def test_missing_held_return_fails_instead_of_silent_zero():
    prices = frame([1.0, 1.0, np.nan, 1.0])
    with pytest.raises(ValueError, match="Missing held"):
        simulate(
            prices,
            constant_plan(prices, {"asset": 1.0}, "every"),
            pd.Series(0.0, index=prices.index),
            fee_bps=0,
        )


@pytest.mark.parametrize("weight", [-0.1, 1.2, np.inf])
def test_short_or_leveraged_or_nonfinite_targets_rejected(weight):
    prices = frame([1.0, 1.0, 1.0])
    with pytest.raises(ValueError, match="long-only"):
        simulate(
            prices,
            constant_plan(prices, {"asset": weight}, "every"),
            pd.Series(0.0, index=prices.index),
            fee_bps=0,
        )


def test_max_drawdown_includes_initial_capital_and_sharpe_is_excess():
    dates = pd.date_range("2020-01-31", periods=12, freq="ME")
    r = pd.Series([-0.1] + [0.01] * 11, index=dates)
    cash = pd.Series(0.002, index=dates)
    metric = summary(r, cash, r, 12)
    assert metric["max_drawdown"] == pytest.approx(-0.1)
    assert metric["cagr"] == pytest.approx(0.9 * 1.01**11 - 1)
    assert metric["sharpe"] == pytest.approx((r - cash).mean() / (r - cash).std() * np.sqrt(12))
    assert metric["beta"] == pytest.approx(1.0)


def test_planted_persistent_trend_is_recovered_after_costs():
    returns = np.tile(np.r_[np.repeat(0.01, 100), np.repeat(-0.01, 100)], 5)
    prices = frame((100 * np.cumprod(1 + returns)).tolist())
    cash = pd.Series(0.0, index=prices.index)
    run = simulate(
        prices,
        trend_plan(prices, kind="sma", lookback=10, frequency="every"),
        cash,
        fee_bps=10,
    )
    values = prices.to_numpy(dtype=float)
    assert np.prod(1 + run.returns) > 20 * (values[-1, 0] / values[0, 0])


def test_iid_null_ensemble_does_not_manufacture_durable_alpha():
    differences = []
    for seed in range(40):
        rng = np.random.default_rng(seed)
        returns = rng.normal(0, 0.01, 600)
        prices = frame((100 * np.cumprod(1 + returns)).tolist())
        cash = pd.Series(0.0, index=prices.index)
        run = simulate(
            prices, trend_plan(prices, kind="sma", lookback=30, frequency="every"), cash, fee_bps=0
        )
        differences.append(float(run.returns.iloc[40:].mean() - np.mean(returns[40:])))
    average, se = np.mean(differences), np.std(differences, ddof=1) / np.sqrt(len(differences))
    assert abs(average) < 3 * se


def test_planted_cross_sectional_signal_selects_winners_after_skip():
    index = pd.bdate_range("2000-01-03", periods=400)
    prices = pd.DataFrame(
        {f"a{i}": 100 * np.cumprod(np.repeat(1 + (i - 2) * 0.001, 400)) for i in range(6)},
        index=index,
    )
    plan = momentum_plan(
        prices, prices, prices * 1_000_000, lookbacks=(126,), breadth=2, minimum_dollars=0
    )
    last = plan.weights.dropna().iloc[-1]
    assert last[last > 0].index.tolist() == ["a4", "a5"]
    assert last.sum() == pytest.approx(1.0)


def test_bootstrap_is_seeded_and_reports_uncertainty():
    series = pd.Series(np.tile([-0.03, 0.04, 0.01], 100))
    interval = block_interval(series, block=12, draws=100)
    assert interval == block_interval(series, block=12, draws=100)
    assert interval[0] <= series.mean() * 12 <= interval[1]
