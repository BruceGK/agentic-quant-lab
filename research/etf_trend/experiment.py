"""Only the two frozen calendar-month rules and four fixed benchmarks."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from research.engine import (
    AvailabilityError,
    Plan,
    Run,
    date_index,
    row_at,
    simulate,
    summary,
)

START = pd.Timestamp("2016-01-01")
END = pd.Timestamp("2026-07-31")
MODELS = ("SPY", "DEFENSIVE", "STATIC80", "STATIC70", "ABS12", "SMA10")
COSTS = (0, 10, 20)


@dataclass(frozen=True)
class ExperimentRun:
    model: str
    defense: str
    cost_bps: int
    run: Run
    decisions: pd.DataFrame


def month_end_levels(prices: pd.DataFrame) -> pd.DataFrame:
    index = date_index(prices.index)
    if index.has_duplicates or not index.is_monotonic_increasing:
        raise ValueError("ETF observations must be unique and increasing")
    if list(prices.columns) != ["SPY", "DEFENSIVE"]:
        raise ValueError("The frozen experiment accepts SPY and one defensive asset only")
    if not np.isfinite(prices.to_numpy()).all() or (prices <= 0).any().any():
        raise ValueError("No missing, nonpositive or nonfinite ETF levels may be simulated")
    positions = pd.Series(np.arange(len(index)), index=index).groupby(index.to_period("M")).last()
    return prices.iloc[positions.to_numpy()].copy()


def frozen_signals(prices: pd.DataFrame) -> pd.DataFrame:
    monthly = month_end_levels(prices)
    months = date_index(monthly.index).to_period("M")
    if len(months) and not months.equals(pd.period_range(months[0], months[-1], freq="M")):
        raise ValueError("Calendar-month history has gaps")
    spy = monthly.SPY
    momentum = spy / spy.shift(12) - 1
    average = spy.rolling(10, min_periods=10).mean()
    return pd.DataFrame(
        {
            "ABS12": momentum.gt(0).where(momentum.notna()).astype(float),
            "SMA10": spy.gt(average).where(average.notna()).astype(float),
            "spy_level": spy,
            "momentum12": momentum,
            "sma10": average,
        }
    )


def frozen_plan(
    prices: pd.DataFrame,
    model: str,
    *,
    zero_cash: bool = False,
    start: pd.Timestamp = START,
    advance_signal: bool = False,
) -> Plan:
    if model not in MODELS:
        raise ValueError("No additional model is allowed by the frozen protocol")
    signals = frozen_signals(prices)
    decision_month = start.to_period("M") - 1
    dates = date_index(signals.index)
    eligible = dates[dates.to_period("M") >= decision_month]
    if not len(eligible) or eligible[0].to_period("M") != decision_month:
        raise ValueError("The first evaluation month needs its preceding month-end decision")
    if row_at(signals, eligible[0]).loc[["ABS12", "SMA10"]].isna().any():
        raise ValueError("At least 13 month-end levels are needed before evaluation")
    weights = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    availability = pd.Series(pd.NaT, index=prices.index, dtype="datetime64[ns]")
    static = {"SPY": 1.0, "DEFENSIVE": 0.0, "STATIC80": 0.8, "STATIC70": 0.7}
    for decision in eligible:
        if model in ("SPY", "DEFENSIVE") and decision != eligible[0]:
            continue
        source = decision
        if model in ("ABS12", "SMA10"):
            position = dates.get_loc(decision)
            if not isinstance(position, (int, np.integer)):
                raise ValueError("Expected a unique monthly decision")
            if advance_signal:
                if position + 1 == len(dates):
                    continue
                source = dates[position + 1]
            fraction = float(row_at(signals, source).loc[model])
        else:
            fraction = static[model]
        weights.loc[decision] = [fraction, 0.0 if zero_cash else 1 - fraction]
        availability.at[decision] = source
    return Plan(weights, availability)


def run_fixed(
    prices: pd.DataFrame, model: str, cost_bps: int, defense: str, start: pd.Timestamp = START
) -> ExperimentRun:
    if cost_bps not in COSTS or defense not in ("BIL", "ZERO_CASH", "MATCHED_ZERO"):
        raise ValueError("Only the frozen cost and defensive scenarios are permitted")
    plan = frozen_plan(prices, model, zero_cash=defense == "ZERO_CASH", start=start)
    used_prices = prices.copy()
    if defense == "MATCHED_ZERO":
        used_prices["DEFENSIVE"] = 1.0
    cash = pd.Series(0.0, index=prices.index)
    run = simulate(used_prices, plan, cash, fee_bps=cost_bps, delay=1)
    decision_log = plan.weights.dropna().copy()
    index = date_index(prices.index)
    positions = index.get_indexer(decision_log.index)
    execution = [index[int(i) + 1] if i + 1 < len(index) else pd.NaT for i in positions]
    decision_log["execution_date"] = execution
    decision_log["available_at"] = plan.available_at.loc[decision_log.index]
    return ExperimentRun(model, defense, cost_bps, run, decision_log)


def switches(run: Run, start: pd.Timestamp = START) -> dict[str, float | int]:
    # End-of-close weights apply only to the NEXT session's return.
    weights = run.weights.SPY.loc[start:]
    starts = weights.to_numpy()
    if len(starts) == 0:
        raise ValueError("Empty evaluation interval")
    eligible_return_weights = run.weights.SPY.shift(1, fill_value=0).loc[weights.index]
    states = weights.ge(0.5).to_numpy()
    return {
        "equity_state_switches_excluding_initial": int(np.count_nonzero(states[1:] != states[:-1])),
        "initial_equity_entry": int(states[0]),
        "fraction_sessions_with_equity": float((eligible_return_weights > 1e-10).mean()),
        "fraction_sessions_fully_equity": float(eligible_return_weights.ge(1 - 1e-8).mean()),
        "mean_equity_weight_earning_returns": float(eligible_return_weights.mean()),
        "mean_defensive_weight_earning_returns": float((1 - eligible_return_weights).mean()),
    }


def metrics(
    experiment: ExperimentRun,
    rf: pd.Series,
    benchmark: pd.Series,
    start: pd.Timestamp = START,
) -> dict:
    selected = experiment.run.returns.loc[start:]
    ix = selected.index
    result = summary(
        selected,
        rf.loc[ix],
        benchmark.loc[ix],
        252,
        source_calendar=date_index(experiment.run.returns.index),
    )
    zero = summary(
        selected,
        rf.loc[ix] * 0,
        benchmark.loc[ix],
        252,
        source_calendar=date_index(experiment.run.returns.index),
    )
    years = len(selected) / 252
    return {
        "model": experiment.model,
        "defense": experiment.defense,
        "one_way_cost_bps": experiment.cost_bps,
        **result,
        "sharpe_zero_rf": zero["sharpe"],
        "annual_traded_notional": float(experiment.run.traded.loc[ix].sum() / years),
        "annual_one_way_equivalent_turnover": float(
            experiment.run.traded.loc[ix].sum() / years / 2
        ),
        "annual_cost_fraction": float(experiment.run.costs.loc[ix].sum() / years),
        **switches(experiment.run, start),
    }


def reject_advanced_signals(prices: pd.DataFrame, start: pd.Timestamp = START) -> list[dict]:
    outcomes = []
    for model in ("ABS12", "SMA10"):
        plan = frozen_plan(prices, model, start=start, advance_signal=True)
        try:
            simulate(prices, plan, pd.Series(0.0, index=prices.index), fee_bps=0)
        except AvailabilityError:
            outcomes.append({"model": model, "future_month_signal": "REJECTED_LOOKAHEAD"})
        else:
            raise AssertionError("Future monthly signal incorrectly passed the availability guard")
    return outcomes
