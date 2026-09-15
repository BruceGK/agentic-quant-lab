"""Small deterministic long-only simulator. Signals and execution are separate events."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


class AvailabilityError(ValueError):
    pass


def date_index(index: pd.Index) -> pd.DatetimeIndex:
    if not isinstance(index, pd.DatetimeIndex):
        raise ValueError("A dated research series requires a DatetimeIndex")
    return index


def column(frame: pd.DataFrame, name: str) -> pd.Series:
    values = frame[name]
    if not isinstance(values, pd.Series):
        raise ValueError("A security name must identify exactly one column")
    return values


def row_at(frame: pd.DataFrame, date: pd.Timestamp) -> pd.Series:
    values = frame.loc[date]
    if not isinstance(values, pd.Series):
        raise ValueError("A decision date must identify exactly one row")
    return values


@dataclass(frozen=True)
class Plan:
    weights: pd.DataFrame
    available_at: pd.Series


@dataclass(frozen=True)
class Run:
    returns: pd.Series
    weights: pd.DataFrame
    traded: pd.Series
    costs: pd.Series


def validate_plan(plan: Plan, prices: pd.DataFrame) -> None:
    if not plan.weights.index.equals(prices.index) or not plan.weights.columns.equals(
        prices.columns
    ):
        raise ValueError("Plan and price axes must match exactly")
    for decision in date_index(plan.weights.dropna(how="all").index):
        row = row_at(plan.weights, decision)
        available = plan.available_at.loc[decision]
        if not isinstance(available, pd.Timestamp) or available > decision:
            raise AvailabilityError("Feature was unavailable at its decision timestamp")
        if not np.isfinite(row.to_numpy()).all() or (row < 0).any() or row.sum() > 1 + 1e-10:
            raise ValueError("Targets must be finite, long-only and unlevered")


def rebalance(pretrade: np.ndarray, target: np.ndarray, fee: float) -> tuple[float, float]:
    if not 0 <= fee < 0.05:
        raise ValueError("Fee must be a one-way decimal below 5%")
    retained = 1.0
    for _ in range(30):
        traded = float(np.abs(retained * target - pretrade).sum())
        updated = 1 - fee * traded
        if abs(updated - retained) < 1e-13:
            return 1 - updated, traded
        retained = updated
    raise ArithmeticError("Self-financing cost solve did not converge")


def simulate(
    prices: pd.DataFrame, plan: Plan, cash: pd.Series, *, fee_bps: float, delay: int = 1
) -> Run:
    if delay < 1:
        raise AvailabilityError("A close-based signal cannot execute at that same close")
    if prices.index.has_duplicates or not prices.index.is_monotonic_increasing:
        raise ValueError("Dates must be unique and increasing")
    if not cash.index.equals(prices.index) or not np.isfinite(cash.to_numpy()).all():
        raise ValueError("Cash returns must cover the exact price calendar")
    if ((cash <= -1) | (cash > 1)).any() or (prices <= 0).any().any():
        raise ValueError("Invalid prices or cash returns")
    validate_plan(plan, prices)
    asset_returns = prices.pct_change(fill_method=None).to_numpy()
    targets = plan.weights.to_numpy()
    cash_values = cash.to_numpy()
    n, assets = prices.shape
    w = np.zeros(assets)
    returns, traded, costs = np.zeros(n), np.zeros(n), np.zeros(n)
    holdings = np.zeros((n, assets))
    for i in range(n):
        changes = asset_returns[i]
        if i and np.any((w > 1e-12) & ~np.isfinite(changes)):
            raise ValueError("Missing held-security return; do not silently fill or drop")
        asset_gains = np.where(w > 0, w * np.nan_to_num(changes, nan=0.0), 0.0)
        gross = float(asset_gains.sum() + (1 - w.sum()) * cash_values[i]) if i else 0.0
        if gross <= -1:
            raise ValueError("Portfolio exhausted its wealth")
        drift = (w + asset_gains) / (1 + gross)
        cost = 0.0
        if i >= delay and np.isfinite(targets[i - delay]).any():
            desired = targets[i - delay]
            if np.any((desired > 0) & ~np.isfinite(prices.iloc[i].to_numpy())):
                raise ValueError("Cannot trade an unavailable security")
            cost, traded[i] = rebalance(drift, desired, fee_bps / 10000)
            w = desired.copy()
        else:
            w = drift
        returns[i] = (1 + gross) * (1 - cost) - 1
        costs[i] = (1 + gross) * cost
        holdings[i] = w
    index = prices.index
    return Run(
        pd.Series(returns, index=index, name="return"),
        pd.DataFrame(holdings, index=index, columns=prices.columns),
        pd.Series(traded, index=index, name="traded_notional"),
        pd.Series(costs, index=index, name="cost"),
    )


def rebalance_dates(index: pd.Index, frequency: str = "monthly") -> pd.DatetimeIndex:
    index = date_index(index)
    if frequency == "monthly":
        return pd.DatetimeIndex(pd.Series(index, index=index).groupby(index.to_period("M")).last())
    if frequency == "biweekly":
        return pd.DatetimeIndex(index[::10])
    if frequency == "every":
        return index
    raise ValueError("Unknown decision frequency")


def plan_frame(prices: pd.DataFrame, weights: pd.DataFrame) -> Plan:
    return Plan(weights, pd.Series(prices.index, index=prices.index))


def constant_plan(
    prices: pd.DataFrame, allocations: dict[str, float], frequency: str = "monthly"
) -> Plan:
    targets = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    for decision in rebalance_dates(prices.index, frequency):
        weights = pd.Series(allocations).reindex(prices.columns, fill_value=0.0)
        if row_at(prices, decision).loc[weights > 0].notna().all():
            targets.loc[decision] = weights
    return plan_frame(prices, targets)


def trend_plan(
    prices: pd.DataFrame,
    *,
    kind: str,
    lookback: int,
    frequency: str = "monthly",
    vol_target: float | None = None,
    periods_per_year: int = 252,
    cash_index: pd.Series | None = None,
) -> Plan:
    if lookback < 2:
        raise ValueError("Trend history must be at least two periods")
    if kind == "absolute":
        change = prices / prices.shift(lookback) - 1
        hurdle = (
            cash_index / cash_index.shift(lookback) - 1
            if cash_index is not None
            else pd.Series(0.0, index=prices.index)
        )
        active = change.gt(hurdle, axis=0).where(change.notna())
    elif kind == "sma":
        average = pd.DataFrame(prices.rolling(lookback, min_periods=lookback).mean())
        active = prices.gt(average).where(average.notna())
    elif kind == "dual":
        average = pd.DataFrame(prices.rolling(lookback, min_periods=lookback).mean())
        fast = pd.DataFrame(prices.rolling(max(2, round(lookback * 0.3))).mean())
        active = fast.gt(average).where(average.notna())
    else:
        raise ValueError("Unknown trend rule")
    allocation = active.astype(float) / len(prices.columns)
    if vol_target is not None:
        window = 63 if periods_per_year == 252 else 12
        vol = prices.pct_change(fill_method=None).rolling(window).std() * np.sqrt(periods_per_year)
        scale = (vol_target / vol).clip(upper=1.0).fillna(0.0)
        allocation *= scale
    targets = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    dates = rebalance_dates(prices.index, frequency)
    ready = allocation.loc[dates].dropna()
    targets.loc[ready.index] = ready
    return plan_frame(prices, targets)


def momentum_plan(
    prices: pd.DataFrame,
    raw: pd.DataFrame,
    volume: pd.DataFrame,
    *,
    lookbacks: tuple[int, ...] = (252,),
    breadth: int = 20,
    frequency: str = "monthly",
    minimum_dollars: float = 50_000_000,
    buffer: float = 1.0,
    sectors: dict[str, str] | None = None,
    sector_cap: float | None = None,
    random_seed: int | None = None,
) -> Plan:
    ranks = [
        (prices.shift(21) / prices.shift(horizon) - 1).rank(axis=1, pct=True)
        for horizon in lookbacks
    ]
    scores = ranks[0].copy()
    for rank in ranks[1:]:
        scores = scores.add(rank)
    scores /= len(ranks)
    liquidity = (raw * volume).rolling(63, min_periods=63).median()
    eligible = (raw >= 5) & (liquidity >= minimum_dollars) & prices.shift(max(lookbacks)).notna()
    targets = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    previous: list[str] = []
    rng = np.random.default_rng(random_seed)
    for decision in rebalance_dates(prices.index, frequency):
        score = row_at(scores, decision).where(row_at(eligible, decision)).dropna()
        if score.empty:
            continue
        order = score.sort_values(ascending=False, kind="mergesort").index.tolist()
        if random_seed is not None:
            order = rng.permutation(order).tolist()
        desired_count = min(breadth, len(order))
        if buffer > 1:
            retained = [name for name in previous if name in order[: int(breadth * buffer)]]
            order = retained + [name for name in order if name not in retained]
        chosen = []
        counts: dict[str, int] = {}
        for symbol in order:
            sector = sectors[symbol] if sectors else symbol
            if sector_cap is not None and (counts.get(sector, 0) + 1) / desired_count > sector_cap:
                continue
            chosen.append(symbol)
            counts[sector] = counts.get(sector, 0) + 1
            if len(chosen) == desired_count:
                break
        targets.loc[decision] = 0.0
        # A sector cap can leave cash; do not renormalize past the cap.
        targets.loc[decision, chosen] = 1 / desired_count
        previous = chosen
    return plan_frame(prices, targets)


def monthly(series: pd.Series, periods_per_year: int) -> pd.Series:
    if periods_per_year == 12:
        return series.copy()
    return (1 + series).resample("ME").prod() - 1


def summary(
    returns: pd.Series, cash: pd.Series, benchmark: pd.Series, periods_per_year: int
) -> dict[str, float | str | int | None]:
    if not returns.index.equals(cash.index) or not returns.index.equals(benchmark.index):
        raise ValueError("Metrics require aligned calendars; do not compare different samples")
    if returns.empty or not np.isfinite(returns.to_numpy()).all() or (returns <= -1).any():
        raise ValueError("Invalid metric returns")
    years = len(returns) / periods_per_year
    wealth = np.r_[1.0, np.cumprod(1 + returns.to_numpy())]
    dd = wealth / np.maximum.accumulate(wealth) - 1
    cagr = float(wealth[-1] ** (1 / years) - 1)
    vol = float(returns.std(ddof=1) * np.sqrt(periods_per_year))
    excess = returns - cash
    sigma = float(excess.std(ddof=1))
    downside = float(np.sqrt(np.mean(np.minimum(excess, 0) ** 2)))
    benchmark_cagr = float(np.prod(1 + benchmark.to_numpy()) ** (1 / years) - 1)
    benchmark_excess = benchmark - cash
    variance = float(benchmark_excess.var(ddof=1))
    beta = float(excess.cov(benchmark_excess) / variance) if variance > 1e-16 else None
    corr = float(returns.corr(benchmark)) if vol > 1e-12 else None
    mr = monthly(returns, periods_per_year)
    dates = date_index(returns.index)
    years_data = mr.groupby(date_index(mr.index).year)
    complete = {
        int(str(year)): float(np.prod(1 + values.to_numpy()) - 1)
        for year, values in years_data
        if len(values) == 12
        and date_index(values.index)[0].month == 1
        and date_index(values.index)[-1].month == 12
    }
    worst = min(complete, key=lambda y: complete[y]) if complete else None
    best = max(complete, key=lambda y: complete[y]) if complete else None
    maximum_dd = float(dd.min())
    return {
        "start": str(dates[0].date()),
        "end": str(dates[-1].date()),
        "observations": len(returns),
        "cagr": cagr,
        "annualized_volatility": vol,
        "sharpe": float(excess.mean() / sigma * np.sqrt(periods_per_year)) if sigma > 0 else None,
        "sortino": float(excess.mean() / downside * np.sqrt(periods_per_year))
        if downside > 0
        else None,
        "max_drawdown": maximum_dd,
        "calmar": cagr / abs(maximum_dd) if maximum_dd < 0 else None,
        "beta": beta,
        "correlation": corr,
        "excess_cagr": cagr - benchmark_cagr,
        "annualized_mean_excess_vs_benchmark": float(
            (returns - benchmark).mean() * periods_per_year
        ),
        "monthly_positive_rate": float((mr > 0).mean()),
        "worst_year": worst,
        "worst_year_return": complete[worst] if worst is not None else None,
        "best_year": best,
        "best_year_return": complete[best] if best is not None else None,
    }


def holding_spells(weights: pd.DataFrame, periods_per_year: int) -> dict[str, float | int | None]:
    durations, censored = [], 0
    for symbol in weights:
        start = None
        for i, held in enumerate(weights[symbol].to_numpy() > 1e-10):
            if held and start is None:
                start = i
            elif not held and start is not None:
                durations.append(i - start)
                start = None
        if start is not None:
            censored += 1
    return {
        "completed_holding_spells": len(durations),
        "censored_open_spells": censored,
        "mean_completed_holding_months": float(np.mean(durations) / periods_per_year * 12)
        if durations
        else None,
    }


def block_interval(
    differences: pd.Series, *, block: int = 12, draws: int = 1000, seed: int = 20260915
) -> tuple[float, float]:
    values = differences.to_numpy()
    if len(values) < block * 2:
        raise ValueError("Too few monthly observations for block bootstrap")
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(values), size=(draws, int(np.ceil(len(values) / block))))
    indices = (starts[..., None] + np.arange(block)) % len(values)
    samples = values[indices.reshape(draws, -1)[:, : len(values)]].mean(axis=1) * 12
    low, high = np.quantile(samples, [0.025, 0.975])
    return float(low), float(high)
