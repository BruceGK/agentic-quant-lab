from dataclasses import dataclass

import pandas as pd

from agentic_quant_lab.agents import ExperimentSpec
from agentic_quant_lab.strategies import Strategy
from research.engine import Plan, Run, simulate


@dataclass(frozen=True)
class ExperimentResult:
    plan: Plan
    run: Run
    metrics: dict[str, float]


def run_experiment(
    strategy: Strategy, prices: pd.DataFrame, spec: ExperimentSpec
) -> ExperimentResult:
    if tuple(prices.columns) != spec.universe:
        raise ValueError("Experiment universe must match fixture columns")
    plan = strategy.build_target(prices)
    run = simulate(
        prices,
        plan,
        pd.Series(0.0, index=prices.index),
        fee_bps=spec.fee_bps,
        delay=spec.delay,
    )
    wealth = (1 + run.returns).cumprod()
    peak = wealth.cummax().clip(lower=1.0)
    return ExperimentResult(
        plan=plan,
        run=run,
        metrics={
            "total_return": round(float(wealth.iloc[-1] - 1), 10),
            "max_drawdown": round(float((wealth / peak - 1).min()), 10),
            "sum_period_costs": round(float(run.costs.sum()), 10),
        },
    )
